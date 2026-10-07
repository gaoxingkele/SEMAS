"""One iteration of the continuous factor-mining loop.

The loop is designed around the loop-engineering principles:

1. STATE — durable memory across runs (`state.json` + `live_library.csv`).
2. TRIGGER — scheduled or manual invocation.
3. EVOLVE — run one seed of the enhanced factor loop, seeded with the live
   library from the previous iteration.
4. EVALUATE — clean the merged library on a hold-out validation fold and run
   an equal-weight combination.
5. DECIDE — promote the new library only if the test cost-adjusted return or
   Sharpe improves over the previous best.
6. REPORT — append a structured loop report.

No git mutations are performed automatically; human review is required before
committing a promoted genome.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import (
    load_tushare_data,
    load_tushare_data_with_val,
)
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _zscore,
    evaluate_library_hold,
)

DEFAULT_STATE = {
    "iteration": 0,
    "last_run": None,
    "best_test_sharpe": 0.0,
    "best_cost_adjusted_return": 0.0,
    "best_hold_sharpe": 0.0,
    "live_library_path": None,
    "history": [],
}


@contextmanager
def exclusive_output_lock(output_dir: Path):
    """Prevent two loop iterations from writing the same state/output tree."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / ".factor_mining_iteration.lock"
    payload = json.dumps(
        {
            "pid": os.getpid(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "output_dir": str(output_dir.resolve()),
        },
        ensure_ascii=False,
    )
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        owner = lock_path.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(f"factor-mining output is already locked: {owner}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        yield lock_path
    finally:
        lock_path.unlink(missing_ok=True)


def load_state(state_path: Path) -> dict:
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = json.loads(json.dumps(DEFAULT_STATE))

    history_by_iteration = {}
    for entry in state.get("history", []):
        iteration = entry.get("iteration")
        if isinstance(iteration, int):
            history_by_iteration[iteration] = entry
    state["history"] = [history_by_iteration[key] for key in sorted(history_by_iteration)]
    if history_by_iteration:
        state["iteration"] = max(history_by_iteration)
    state.setdefault("best_hold_sharpe", 0.0)
    state.setdefault("promotion_baseline", None)
    state["state_schema_version"] = 2
    return state


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    """Run a command; raise on error.  Output is streamed to a log file to avoid
    filling memory buffers during long-running evolution subprocesses."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    log_name = "run_cmd.log"
    for i, part in enumerate(cmd):
        if part == "-m" and i + 1 < len(cmd):
            log_name = cmd[i + 1].replace(".", "_").replace("-", "_") + ".log"
            break
    log_path = Path(cwd if cwd else ".") / log_name
    with open(log_path, "a", encoding="utf-8") as log_file:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return ""


def merge_libraries(library_paths: list[Path], output_path: Path) -> int:
    """Merge multiple factor library CSVs, deduplicating by expression."""
    frames = []
    for p in library_paths:
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if "factor" not in df.columns:
            df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")
        frames.append(df)
    if not frames:
        return 0
    merged = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["expression"])
    merged["rank"] = range(1, len(merged) + 1)
    merged.to_csv(output_path, index=False)
    return len(merged)


def add_high_zscore(library_path: Path, output_path: Path) -> None:
    df = pd.read_csv(library_path)
    if "factor" not in df.columns:
        df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")
    high = pd.DataFrame(
        [
            {
                "factor": "high_zscore_20",
                "expression": "cs_rank(ts_zscore(high, 20))",
                "train_ic": 0.0,
                "test_ic": 0.0,
                "test_sharpe": 0.0,
                "test_turnover": 0.0,
            }
        ]
    )
    merged = pd.concat([df, high], ignore_index=True)
    merged["rank"] = range(1, len(merged) + 1)
    merged.to_csv(output_path, index=False)


def compute_hold_sharpe(
    library_path: Path,
    data_config: dict,
    horizon: int = 5,
    transaction_cost: float = 0.001,
    smooth_span: int = 10,
    use_dynamic_trim: bool = False,
    min_factor_coverage: float = 0.5,
    test_data: pd.DataFrame | None = None,
    history_data: pd.DataFrame | None = None,
) -> dict:
    """Compute realistic non-overlapping hold Sharpe for a factor library.

    Equal-weight ensemble of all expressions in ``library_path``; evaluated on
    the test fold only (the fold that should determine production readiness).
    Returns a dict with ``sharpe``, ``annualized_return``, ``cost_adjusted_return``,
    and ``max_drawdown``.
    """
    if isinstance(data_config, (str, Path)):
        with open(data_config, "r", encoding="utf-8") as f:
            data_config = yaml.safe_load(f)

    if test_data is None:
        train_data, val_data, test_data = load_tushare_data_with_val(data_config)
        history_data = pd.concat([train_data, val_data, test_data]).sort_index()
    lib = pd.read_csv(library_path)
    evaluation_mode = "dynamic_trim" if use_dynamic_trim else "simple_hold"
    return evaluate_library_hold(
        lib,
        test_data,
        horizon=horizon,
        transaction_cost=transaction_cost,
        smooth_span=smooth_span,
        evaluation_mode=evaluation_mode,
        min_factor_coverage=min_factor_coverage,
        history_data=history_data,
    )


def semantic_deduplicate(
    library_path: Path,
    data_config: dict,
    output_path: Path,
    corr_threshold: float = 0.95,
    keep_diversity_slots: int = 0,
) -> int:
    """Drop semantically duplicate expressions based on train-set correlation.

    Keeps the first expression in library order and removes any later
    expression whose absolute Spearman correlation with an already-kept
    expression exceeds ``corr_threshold``.

    ``keep_diversity_slots`` (RSI outer-loop knob) allows up to N near-duplicate
    survivors to be retained anyway — used when meta-diagnosis finds that
    aggressive dedup destroyed useful ensemble diversity.
    """
    if isinstance(data_config, (str, Path)):
        with open(data_config, "r", encoding="utf-8") as f:
            data_config = yaml.safe_load(f)

    df = pd.read_csv(library_path)
    if "factor" not in df.columns:
        df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")

    if "val_date" in data_config:
        train, _, _ = load_tushare_data_with_val(data_config)
    else:
        train, _ = load_tushare_data(data_config)

    frames = []
    frame_meta = []  # (unique_col_name, original_factor_name, row)
    for idx, row in df.iterrows():
        try:
            expr = parse_expression(row["expression"])
            f = _zscore(expr.eval(train))
            base = row["factor"]
            # Ensure unique column names in case of duplicate factor labels.
            col_name = f"{base}_dup{idx}" if base in [m[0] for m in frame_meta] else base
            frames.append(f.rename(col_name))
            frame_meta.append((col_name, base, row))
        except Exception as exc:
            print(f"  [dedup] skipping invalid expression {row.get('factor')}: {exc}")

    if not frames:
        df.to_csv(output_path, index=False)
        return 0

    mat = pd.concat(frames, axis=1)

    # Drop degenerate columns (constant or zero variance) before correlation checks.
    valid_meta = []
    for col_name, base, row in frame_meta:
        if col_name not in mat.columns:
            continue
        std = mat[col_name].dropna().std()
        if pd.isna(std) or float(std) < 1e-12:
            print(f"  [dedup] dropping {base}: constant/degenerate series")
        else:
            valid_meta.append((col_name, base, row))
    mat = mat[[m[0] for m in valid_meta]]

    kept_rows = []
    kept_cols = []
    diversity_kept = 0
    for col_name, base, row in valid_meta:
        if kept_cols:
            corr_values = mat[kept_cols].corrwith(mat[col_name], method="spearman").abs()
            corr_max = float(corr_values.max()) if not corr_values.empty else 0.0
            if pd.isna(corr_max):
                corr_max = 0.0
        else:
            corr_max = 0.0
        if corr_max < corr_threshold:
            kept_rows.append(row)
            kept_cols.append(col_name)
        elif diversity_kept < int(keep_diversity_slots):
            diversity_kept += 1
            print(
                f"  [dedup] diversity-slot keep {base} "
                f"(max |corr|={corr_max:.3f}, slot {diversity_kept}/{keep_diversity_slots})"
            )
            kept_rows.append(row)
            kept_cols.append(col_name)
        else:
            print(f"  [dedup] dropping {base} (max |corr|={corr_max:.3f})")

    out = pd.DataFrame(kept_rows)
    out["rank"] = range(1, len(out) + 1)
    out.to_csv(output_path, index=False)
    return len(out)


def parse_combination_result(output_dir: Path) -> dict:
    result_file = output_dir / "combination_result.json"
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = {r["period"]: r for r in data["results"]}
    return {
        "test_sharpe": results.get("test", {}).get("sharpe", 0.0),
        "test_cost_adjusted_return": results.get("test", {}).get("cost_adjusted_return", 0.0),
        "test_ic": results.get("test", {}).get("ic", 0.0),
        "train_sharpe": results.get("train", {}).get("sharpe", 0.0),
        "train_cost_adjusted_return": results.get("train", {}).get("cost_adjusted_return", 0.0),
        "selection_correlation_max": data.get("selection_correlation_max", 1.0),
    }


def _run_loop_iteration_unlocked(
    cfg: dict,
    output_dir: Path,
    dry_run: bool = False,
    use_live_seed: bool = True,
) -> dict:
    """Execute one factor-mining loop iteration."""
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "state.json"
    state = load_state(state_path)

    iteration = state["iteration"] + 1
    iteration_dir = output_dir / f"iter_{iteration:04d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    live_library_path = (
        Path(state["live_library_path"])
        if state.get("live_library_path") and use_live_seed
        else None
    )

    # Build the seed library by merging the live library with any extra seed
    # libraries configured for this iteration (e.g., domain-specific priors).
    seed_library_path = iteration_dir / "seed_library.csv"
    extra_seed_paths = [Path(p) for p in cfg.get("extra_seed_libraries", []) if Path(p).exists()]
    seed_sources = []
    if live_library_path and live_library_path.exists():
        seed_sources.append(live_library_path)
    seed_sources.extend(extra_seed_paths)
    if seed_sources:
        merge_libraries(seed_sources, seed_library_path)

    # ---- 1. EVOLVE ----
    seed = int(cfg.get("rsi_evaluation_seed", cfg.get("seed_base", 42) + iteration))
    seed_output = iteration_dir / "evolution"
    seed_output.mkdir(parents=True, exist_ok=True)

    evolve_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.run_enhanced_factor_loop",
        cfg["evolution_config"],
        "--output-dir",
        str(seed_output),
        "--seed",
        str(seed),
    ]
    if seed_library_path.exists() and not dry_run:
        evolve_cmd += ["--seed-library", str(seed_library_path)]

    print(f"[iter {iteration}] Running evolution seed={seed} ...")
    if not dry_run:
        run_cmd(evolve_cmd)
    else:
        print("  (dry-run: skipped evolution)")

    new_leaderboard = seed_output / "factor_loop_leaderboard.csv"

    # ---- 2. MERGE ----
    merged_library = iteration_dir / "merged_library.csv"
    merge_paths = [new_leaderboard]
    if live_library_path and live_library_path.exists():
        merge_paths.append(live_library_path)
    n_merged = merge_libraries(merge_paths, merged_library)
    print(f"[iter {iteration}] Merged library: {n_merged} expressions")

    # ---- 3. CLEAN ----
    cleaned_library = iteration_dir / "cleaned_library.csv"
    clean_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.clean_factor_library",
        cfg["data_config"],
        "--library",
        str(merged_library),
        "--output",
        str(cleaned_library),
        "--min-train-ic",
        str(cfg.get("min_train_ic", 0.001)),
        "--min-test-ic",
        str(cfg.get("min_test_ic", 0.001)),
        "--min-test-sharpe",
        str(cfg.get("min_test_sharpe", 0.0)),
        "--max-turnover",
        str(cfg.get("max_turnover", 0.5)),
        "--max-nan-frac",
        str(cfg.get("max_nan_frac", 0.5)),
        "--min-daily-coverage",
        str(cfg.get("min_daily_coverage", 0.8)),
    ]
    if cfg.get("min_val_ic") is not None:
        clean_cmd += ["--min-val-ic", str(cfg["min_val_ic"])]
    if cfg.get("min_val_sharpe") is not None:
        clean_cmd += ["--min-val-sharpe", str(cfg["min_val_sharpe"])]

    print(f"[iter {iteration}] Cleaning merged library ...")
    run_cmd(clean_cmd)
    n_cleaned = len(pd.read_csv(cleaned_library)) if cleaned_library.exists() else 0
    print(f"[iter {iteration}] Cleaned library: {n_cleaned} expressions")

    # ---- 4. ADD high_zscore + SEMANTIC DEDUP ----
    combined_pre = iteration_dir / "combined_library_pre.csv"
    add_high_zscore(cleaned_library, combined_pre)

    combined_library = iteration_dir / "combined_library.csv"
    n_deduped = semantic_deduplicate(
        combined_pre,
        cfg["data_config"],
        combined_library,
        corr_threshold=cfg.get("semantic_dedup_corr_threshold", 0.95),
        keep_diversity_slots=int(cfg.get("keep_diversity_slots", 0)),
    )
    print(f"[iter {iteration}] After semantic dedup: {n_deduped} expressions")

    if cfg.get("ast_regularizer_enabled", False):
        from china_a_share_alpha.evolution.ast_regularizer import (
            RegularizerConfig,
            filter_library_by_ast,
        )

        pre_ast = pd.read_csv(combined_library)
        kept = filter_library_by_ast(
            pre_ast["expression"].astype(str).tolist(),
            RegularizerConfig(
                enabled=True,
                similarity_tau=float(cfg.get("ast_similarity_tau", 0.85)),
                max_depth=int(cfg.get("ast_max_depth", 6)),
                max_nodes=int(cfg.get("ast_max_nodes", 40)),
            ),
        )
        filtered = pre_ast[pre_ast["expression"].astype(str).isin(kept)].copy()
        filtered.to_csv(combined_library, index=False)
        n_deduped = len(filtered)
        print(f"[iter {iteration}] After AST filter: {n_deduped} expressions")

    combo_output = iteration_dir / "combination"
    combo_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.run_factor_combination",
        cfg["data_config"],
        "--factor-csv",
        str(combined_library),
        "--top-n",
        str(cfg.get("top_n", 10)),
        "--weight-method",
        cfg.get("weight_method", "equal"),
        "--smooth-span",
        str(cfg.get("smooth_span", 10)),
        "--output-dir",
        str(combo_output),
    ]
    if cfg.get("sort_by"):
        combo_cmd += ["--sort-by", cfg["sort_by"]]
    if cfg.get("max_pairwise_corr") is not None:
        combo_cmd += [
            "--max-pairwise-corr",
            str(cfg["max_pairwise_corr"]),
        ]

    print(f"[iter {iteration}] Running combination ...")
    run_cmd(combo_cmd)
    metrics = parse_combination_result(combo_output)

    # ---- D1 pool IC diagnostics (optional; does not replace hold gate) ----
    if cfg.get("report_pool_ic", True):
        try:
            from china_a_share_alpha.loop.synergy_objective import (
                load_expressions_from_csv,
                pool_ic_metrics,
            )

            _, _, test_panel = load_tushare_data_with_val(cfg["data_config"])
            exprs = load_expressions_from_csv(
                combined_library, top_n=int(cfg.get("top_n", 10))
            )
            pool = pool_ic_metrics(
                exprs,
                test_panel,
                smooth_span=int(cfg.get("smooth_span", 10)),
                min_factor_coverage=float(cfg.get("min_factor_coverage", 0.5)),
            )
            metrics["pool_ic"] = pool.get("pool_ic")
            metrics["pool_rank_ic"] = pool.get("pool_rank_ic")
            metrics["pool_ic_valid"] = pool.get("valid")
            if pool.get("valid"):
                print(
                    f"[iter {iteration}] Pool IC={pool['pool_ic']:.4f}, "
                    f"RankIC={pool['pool_rank_ic']:.4f}"
                )
        except Exception as exc:  # noqa: BLE001
            metrics["pool_ic_error"] = str(exc)
            print(f"[iter {iteration}] Pool IC skipped: {exc}")

    # ---- HOLD SHARPE GATE (optional) ----
    use_hold_gate = cfg.get("use_hold_sharpe_gate", False)
    candidate_hold = None
    baseline_hold = None
    if use_hold_gate:
        evaluation_mode = cfg.get(
            "promotion_evaluation_mode",
            "dynamic_trim" if cfg.get("use_dynamic_trim_hold", False) else "simple_hold",
        )
        min_factor_coverage = cfg.get("min_factor_coverage", 0.5)
        promotion_train, promotion_val, promotion_test = load_tushare_data_with_val(
            cfg["data_config"]
        )
        promotion_history = pd.concat([promotion_train, promotion_val, promotion_test]).sort_index()
        print(
            f"[iter {iteration}] Computing {evaluation_mode} promotion metrics "
            "for candidate and live baseline ..."
        )
        candidate_hold = compute_hold_sharpe(
            combined_library,
            cfg["data_config"],
            horizon=cfg.get("hold_horizon", 5),
            transaction_cost=cfg.get("hold_transaction_cost", 0.001),
            smooth_span=cfg.get("smooth_span", 10),
            use_dynamic_trim=evaluation_mode == "dynamic_trim",
            min_factor_coverage=min_factor_coverage,
            test_data=promotion_test,
            history_data=promotion_history,
        )
        if live_library_path and live_library_path.exists():
            baseline_hold = compute_hold_sharpe(
                live_library_path,
                cfg["data_config"],
                horizon=cfg.get("hold_horizon", 5),
                transaction_cost=cfg.get("hold_transaction_cost", 0.001),
                smooth_span=cfg.get("smooth_span", 10),
                use_dynamic_trim=evaluation_mode == "dynamic_trim",
                min_factor_coverage=min_factor_coverage,
                test_data=promotion_test,
                history_data=promotion_history,
            )
            baseline_hold["library_path"] = str(live_library_path)
        else:
            baseline_hold = {
                "valid": True,
                "sharpe": 0.0,
                "evaluation_mode": evaluation_mode,
                "reason": "no live library; using zero initialization baseline",
            }

        metrics["hold_evaluation"] = candidate_hold
        metrics["hold_sharpe"] = candidate_hold.get("sharpe")
        metrics["hold_annualized_return"] = candidate_hold.get("annualized_return")
        metrics["hold_cost_adjusted_return"] = candidate_hold.get("cost_adjusted_return")
        metrics["hold_max_drawdown"] = candidate_hold.get("max_drawdown")
        if candidate_hold["valid"]:
            print(
                f"[iter {iteration}] Candidate hold metrics: "
                f"sharpe={candidate_hold['sharpe']:.3f}, "
                f"ret={candidate_hold['annualized_return']:.2%}, "
                f"dd={candidate_hold['max_drawdown']:.2%}"
            )
        else:
            print(
                f"[iter {iteration}] Candidate hold evaluation INVALID: "
                f"{candidate_hold.get('error', 'unknown error')}"
            )

    # ---- 5. DECIDE with gates ----
    improvement_sharpe = metrics["test_sharpe"] - state["best_test_sharpe"]
    improvement_return = metrics["test_cost_adjusted_return"] - state["best_cost_adjusted_return"]
    improvement_hold = None
    if (
        use_hold_gate
        and candidate_hold
        and baseline_hold
        and candidate_hold["valid"]
        and baseline_hold["valid"]
    ):
        improvement_hold = candidate_hold["sharpe"] - baseline_hold["sharpe"]

    gates = {
        "promotion_enabled": bool(cfg.get("promotion_enabled", True)),
        "train_sharpe_positive": metrics["train_sharpe"] > cfg.get("min_train_sharpe_gate", 0.0),
        "min_cleaned_count": n_deduped >= cfg.get("min_cleaned_gate", 1),
        "max_corr_ok": metrics["selection_correlation_max"]
        <= cfg.get("max_selection_correlation_gate", 1.0),
    }
    if use_hold_gate:
        gates["candidate_evaluation_valid"] = bool(candidate_hold["valid"])
        gates["baseline_evaluation_valid"] = bool(baseline_hold["valid"])
        gates["hold_sharpe_ok"] = bool(
            candidate_hold["valid"]
            and candidate_hold["sharpe"] >= cfg.get("min_hold_sharpe_gate", 0.0)
        )
    gates_passed = all(gates.values())

    improved = improvement_sharpe >= cfg.get(
        "promote_sharpe_threshold", 0.05
    ) or improvement_return >= cfg.get("promote_return_threshold", 0.005)
    if use_hold_gate:
        improved = bool(
            improvement_hold is not None
            and improvement_hold >= cfg.get("promote_hold_sharpe_threshold", 0.05)
        )
    promote = improved and gates_passed

    if promote:
        new_live = output_dir / "live_library.csv"
        pd.read_csv(combined_library).to_csv(new_live, index=False)
        state["live_library_path"] = str(new_live)
        state["best_test_sharpe"] = max(
            float(state["best_test_sharpe"]), float(metrics["test_sharpe"])
        )
        state["best_cost_adjusted_return"] = max(
            float(state["best_cost_adjusted_return"]),
            float(metrics["test_cost_adjusted_return"]),
        )
        state["live_test_sharpe"] = float(metrics["test_sharpe"])
        state["live_cost_adjusted_return"] = float(metrics["test_cost_adjusted_return"])
        if use_hold_gate:
            state["best_hold_sharpe"] = float(candidate_hold["sharpe"])
            candidate_hold["library_path"] = str(new_live)
            state["promotion_baseline"] = candidate_hold
        print(
            f"[iter {iteration}] PROMOTED new live library "
            f"(sharpe={metrics['test_sharpe']:.3f}, "
            f"cost_adj={metrics['test_cost_adjusted_return']:.3%}"
            + (f", hold_sharpe={candidate_hold['sharpe']:.3f}" if use_hold_gate else "")
            + ")"
        )
    else:
        reasons = []
        if not improved:
            reasons.append("not improved")
        for name, ok in gates.items():
            if not ok:
                reasons.append(name)
        reason_str = ", ".join(reasons) if reasons else "unknown"
        print(
            f"[iter {iteration}] KEPT existing live library "
            f"(reason: {reason_str}; "
            f"new sharpe={metrics['test_sharpe']:.3f}, "
            f"new cost_adj={metrics['test_cost_adjusted_return']:.3%}; "
            f"best sharpe={state['best_test_sharpe']:.3f}, "
            f"best cost_adj={state['best_cost_adjusted_return']:.3%}"
            + (
                f", new hold_sharpe={candidate_hold['sharpe']:.3f}, "
                f"baseline hold_sharpe={baseline_hold['sharpe']:.3f}"
                if use_hold_gate and candidate_hold["valid"] and baseline_hold["valid"]
                else ""
            )
            + ")"
        )

    if use_hold_gate and not promote:
        state["promotion_baseline"] = baseline_hold
        if baseline_hold["valid"]:
            state["best_hold_sharpe"] = float(baseline_hold["sharpe"])

    # ---- 6. STATE + REPORT ----
    entry = {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "rsi_policy_id": cfg.get("rsi_policy_id"),
        "rsi_parent_id": cfg.get("rsi_parent_id"),
        "rsi_policy_version": cfg.get("rsi_policy_version"),
        "rsi_island": cfg.get("rsi_island"),
        "rsi_mutation_surface": cfg.get("rsi_mutation_surface"),
        "rsi_mutation_field": cfg.get("rsi_mutation_field"),
        "rsi_evaluation_group_id": cfg.get("rsi_evaluation_group_id"),
        "rsi_proposal_seed": cfg.get("rsi_proposal_seed"),
        "evolution_dir": str(seed_output),
        "n_merged": n_merged,
        "n_cleaned": n_cleaned,
        "n_deduped": n_deduped,
        "metrics": metrics,
        "gates": {k: bool(v) for k, v in gates.items()},
        "promotion_baseline": baseline_hold,
        "improved": improved,
        "promoted": promote,
    }
    state["iteration"] = iteration
    state["last_run"] = entry["timestamp"]
    state["history"].append(entry)
    save_state(state_path, state)

    if entry.get("rsi_policy_id"):
        (iteration_dir / "rsi_execution_receipt.json").write_text(
            json.dumps(entry, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    report_path = write_report(output_dir, iteration_dir, state, entry, promote, cfg)
    print(f"[iter {iteration}] Report: {report_path}")

    return state


def run_loop_iteration(
    cfg: dict,
    output_dir: Path,
    dry_run: bool = False,
    use_live_seed: bool = True,
) -> dict:
    """Execute one iteration while holding an exclusive output-directory lock."""
    with exclusive_output_lock(output_dir):
        return _run_loop_iteration_unlocked(
            cfg,
            output_dir,
            dry_run=dry_run,
            use_live_seed=use_live_seed,
        )


def write_report(
    output_dir: Path,
    iteration_dir: Path,
    state: dict,
    entry: dict,
    promoted: bool,
    cfg: dict,
) -> Path:
    """Write a human-readable loop report."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"loop_report_{ts}.md"
    metrics = entry["metrics"]

    has_hold = "hold_sharpe" in metrics
    hold_evaluation = metrics.get("hold_evaluation", {})
    lines = [
        f"# Factor Mining Loop Report — Iteration {entry['iteration']}",
        "",
        f"- **Timestamp**: {entry['timestamp']}",
        f"- **Evolution seed**: {entry['seed']}",
        f"- **RSI policy**: {entry.get('rsi_policy_id') or 'none'}",
        f"- **RSI parent**: {entry.get('rsi_parent_id') or 'none'}",
        f"- **RSI mutation**: {entry.get('rsi_mutation_surface') or 'none'} / "
        f"{entry.get('rsi_mutation_field') or 'none'}",
        f"- **Merged expressions**: {entry['n_merged']}",
        f"- **Cleaned expressions**: {entry['n_cleaned']}",
        f"- **Deduplicated expressions**: {entry.get('n_deduped', entry['n_cleaned'])}",
        f"- **Promoted**: {'YES' if promoted else 'NO'}",
        "",
        "## Metrics",
        "",
        "| Period | Sharpe | Cost-adj return | IC |",
        "|---|---|---|---|",
        (
            f"| Train | {metrics['train_sharpe']:.4f} | "
            f"{metrics['train_cost_adjusted_return']:.4f} | - |"
        ),
        (
            f"| Test | {metrics['test_sharpe']:.4f} | "
            f"{metrics['test_cost_adjusted_return']:.4f} | {metrics['test_ic']:.4f} |"
        ),
    ]
    if has_hold:
        lines += ["", "### Realistic Hold Backtest", ""]
        lines.append(f"- Evaluation mode: {hold_evaluation.get('evaluation_mode', 'unknown')}")
        lines.append(f"- Valid: {hold_evaluation.get('valid', False)}")
        if hold_evaluation.get("valid"):
            lines += [
                f"- Hold Sharpe: {metrics['hold_sharpe']:.4f}",
                f"- Hold annualized return: {metrics['hold_annualized_return']:.2%}",
                f"- Hold cost-adjusted return: {metrics['hold_cost_adjusted_return']:.2%}",
                f"- Hold max drawdown: {metrics['hold_max_drawdown']:.2%}",
                f"- Valid rows: {hold_evaluation.get('valid_rows', 0)}",
            ]
        else:
            lines.append(f"- Error: {hold_evaluation.get('error', 'unknown error')}")
    lines += [
        "",
        "## Gates",
        "",
        f"- train_sharpe_positive: {entry['gates']['train_sharpe_positive']}",
        f"- min_cleaned_count: {entry['gates']['min_cleaned_count']}",
        (
            f"- max_corr_ok: {entry['gates']['max_corr_ok']} "
            f"(max corr = {metrics.get('selection_correlation_max', 1.0):.4f})"
        ),
    ]
    if has_hold:
        lines += [
            (
                "- candidate_evaluation_valid: "
                f"{entry['gates'].get('candidate_evaluation_valid', False)}"
            ),
            (
                "- baseline_evaluation_valid: "
                f"{entry['gates'].get('baseline_evaluation_valid', False)}"
            ),
            f"- hold_sharpe_ok: {entry['gates'].get('hold_sharpe_ok', False)}",
        ]
    lines += [
        "",
        "## Decision",
        "",
    ]
    if promoted:
        lines += [
            "The new library improved on the previous best and has been promoted to live library.",
            "",
            f"- Historical best diagnostic Sharpe: {state['best_test_sharpe']:.4f}",
            (
                "- Historical best diagnostic cost-adjusted return: "
                f"{state['best_cost_adjusted_return']:.4f}"
            ),
        ]
        if has_hold:
            lines.append(f"- New best hold Sharpe: {state['best_hold_sharpe']:.4f}")
        lines += [
            "",
            "> Human gate: review the new `live_library.csv` before committing.",
        ]
    else:
        lines += [
            (
                "The new library did not improve on the previous best. "
                "The existing live library is retained."
            ),
            "",
            f"- Previous best Sharpe: {state['best_test_sharpe']:.4f}",
            f"- Previous best cost-adjusted return: {state['best_cost_adjusted_return']:.4f}",
        ]
        if has_hold:
            baseline = entry.get("promotion_baseline") or {}
            if baseline.get("valid"):
                lines.append(f"- Live baseline hold Sharpe: {baseline['sharpe']:.4f}")
            else:
                lines.append("- Live baseline hold Sharpe: unavailable")

    lines += [
        "",
        "## Artifacts",
        "",
        f"- Evolution: `{iteration_dir / 'evolution'}`",
        f"- Merged library: `{iteration_dir / 'merged_library.csv'}`",
        f"- Cleaned library: `{iteration_dir / 'cleaned_library.csv'}`",
        f"- Combination: `{iteration_dir / 'combination'}`",
        "",
        "---",
        "",
        "Next iteration will use the current live library as its seed.",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Loop config YAML")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop"),
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip evolution")
    parser.add_argument(
        "--no-live-seed",
        action="store_true",
        help="Start evolution from scratch instead of seeding with the live library",
    )
    parser.add_argument(
        "--repair-state-only",
        action="store_true",
        help="Normalize and rewrite state.json without running an iteration",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if args.repair_state_only:
        state_path = args.output_dir / "state.json"
        state = load_state(state_path)
        save_state(state_path, state)
        print(
            f"Repaired {state_path}: iteration={state['iteration']}, "
            f"history_entries={len(state['history'])}"
        )
        return 0

    run_loop_iteration(
        cfg,
        args.output_dir,
        dry_run=args.dry_run,
        use_live_seed=not args.no_live_seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
