"""Rank historical unique factors and iteration ensembles at 5d / 10d.

Collects expressions from all available factor_mining_loop iter libraries +
current live libraries, evaluates each unique factor once, then ranks by
dynamic-trim hold Sharpe (and reports IC diagnostics) for horizons 5 and 10.
Also ranks each iteration ensemble under the same contracts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.evaluator.metrics import ic_score
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _backtest,
    _compute_forward,
    _dynamic_trim_backtest,
    _zscore,
    evaluate_library_hold,
)

ROOT = Path(__file__).resolve().parents[2]
LOOP = ROOT / "china_a_share_alpha_output/factor_mining_loop"
OUT = LOOP / "historical_horizon_rankings"
CONFIG = ROOT / "china_a_share_alpha/examples/enhanced_loop_config_val_frozen.yaml"
HORIZONS = (5, 10)
COST = 0.001
SMOOTH = 10


def _collect_expressions() -> pd.DataFrame:
    rows: list[dict] = []
    seen: dict[str, dict] = {}

    def _add(expression: str, source: str, iteration: int | None) -> None:
        expr = str(expression).strip()
        if not expr or expr.lower() == "nan":
            return
        if expr not in seen:
            seen[expr] = {
                "expression": expr,
                "first_iteration": iteration,
                "last_iteration": iteration,
                "iterations": set(),
                "sources": set(),
            }
        meta = seen[expr]
        if iteration is not None:
            meta["iterations"].add(iteration)
            if meta["first_iteration"] is None or iteration < meta["first_iteration"]:
                meta["first_iteration"] = iteration
            if meta["last_iteration"] is None or iteration > meta["last_iteration"]:
                meta["last_iteration"] = iteration
        meta["sources"].add(source)

    for child in sorted(LOOP.glob("iter_*")):
        if not child.is_dir():
            continue
        m = re.match(r"iter_(\d+)$", child.name)
        if not m:
            continue
        iteration = int(m.group(1))
        for name in ("cleaned_library.csv", "combined_library.csv"):
            path = child / name
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for expr in df["expression"].astype(str):
                _add(expr, f"{child.name}/{name}", iteration)
            break

    for name in ("live_library.csv", "live_library_iter28_best_hold.csv"):
        path = LOOP / name
        if path.exists():
            df = pd.read_csv(path)
            for expr in df["expression"].astype(str):
                _add(expr, name, None)

    state = json.loads((LOOP / "state.json").read_text(encoding="utf-8"))
    promoted_iters = {h["iteration"] for h in state.get("history", []) if h.get("promoted")}

    for meta in seen.values():
        iters = sorted(meta["iterations"])
        rows.append(
            {
                "expression": meta["expression"],
                "first_iteration": meta["first_iteration"],
                "last_iteration": meta["last_iteration"],
                "n_iterations": len(iters),
                "iterations": ",".join(str(i) for i in iters),
                "appeared_in_promoted_iter": bool(set(iters) & promoted_iters),
                "in_current_live": "live_library.csv" in meta["sources"],
                "sources": ";".join(sorted(meta["sources"])),
            }
        )
    return pd.DataFrame(rows)


def _smooth(series: pd.Series, span: int) -> pd.Series:
    return series.groupby(level="symbol").transform(
        lambda s: s.ewm(span=span, adjust=False).mean()
    )


def _eval_factor(
    expression: str,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    full: pd.DataFrame,
) -> list[dict]:
    expr = parse_expression(expression)
    f_train = _zscore(expr.eval(train))
    f_val = _zscore(expr.eval(val))
    f_test = _zscore(expr.eval(test))
    f_full = _zscore(expr.eval(full))
    signal = _smooth(f_full, SMOOTH).reindex(test.index)

    rows = []
    for h in HORIZONS:
        fwd_train = _compute_forward(train, h)
        fwd_val = _compute_forward(val, h)
        fwd_test = _compute_forward(test, h)
        bt = _backtest(f_test, fwd_test, COST)
        hold = _dynamic_trim_backtest(signal.dropna(), test["return"], h, COST)
        rows.append(
            {
                "horizon": h,
                "train_ic": ic_score(f_train, fwd_train),
                "val_ic": ic_score(f_val, fwd_val),
                "test_ic": ic_score(f_test, fwd_test),
                "test_sharpe": bt["sharpe"],
                "test_cost_adj_return": bt["cost_adjusted_return"],
                "test_max_drawdown": bt["max_drawdown"],
                "hold_sharpe": hold.get("sharpe"),
                "hold_annualized_return": hold.get("annualized_return"),
                "hold_max_drawdown": hold.get("max_drawdown"),
                "hold_n_observations": hold.get("n_observations"),
            }
        )
    return rows


def _eval_iteration_ensembles(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> pd.DataFrame:
    hist = pd.concat([train, val, test]).sort_index()
    hist = hist[~hist.index.duplicated(keep="last")]
    rows = []
    for child in sorted(LOOP.glob("iter_*")):
        if not child.is_dir():
            continue
        m = re.match(r"iter_(\d+)$", child.name)
        if not m:
            continue
        iteration = int(m.group(1))
        lib_path = None
        for name in ("cleaned_library.csv", "combined_library.csv"):
            if (child / name).exists():
                lib_path = child / name
                break
        if lib_path is None:
            continue
        lib = pd.read_csv(lib_path)
        if "factor" not in lib.columns:
            lib["factor"] = [f"factor_{i+1}" for i in range(len(lib))]
        for h in HORIZONS:
            hold = evaluate_library_hold(
                lib,
                test,
                horizon=h,
                transaction_cost=COST,
                smooth_span=SMOOTH,
                evaluation_mode="dynamic_trim",
                min_factor_coverage=0.5,
                history_data=hist,
            )
            rows.append(
                {
                    "iteration": iteration,
                    "library": str(lib_path.relative_to(ROOT)),
                    "n_factors": len(lib),
                    "horizon": h,
                    "hold_valid": hold.get("valid"),
                    "hold_sharpe": hold.get("sharpe"),
                    "hold_annualized_return": hold.get("annualized_return"),
                    "hold_max_drawdown": hold.get("max_drawdown"),
                    "hold_error": hold.get("error"),
                }
            )
        print(f"[ensemble] iter {iteration} done", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    print("loading panel...", flush=True)
    train, val, test = load_tushare_data_with_val(cfg)
    if "return" not in test.columns:
        for frame in (train, val, test):
            frame["return"] = frame.groupby(level="symbol")["close"].pct_change()
    full = pd.concat([train, val, test]).sort_index()
    full = full[~full.index.duplicated(keep="last")]

    catalog = _collect_expressions()
    catalog.to_csv(OUT / "expression_catalog.csv", index=False, encoding="utf-8")
    print(f"unique expressions: {len(catalog)}", flush=True)

    factor_rows = []
    for i, row in catalog.iterrows():
        expr = row["expression"]
        try:
            metrics = _eval_factor(expr, train, val, test, full)
            for m in metrics:
                factor_rows.append({**row.to_dict(), **m})
        except Exception as exc:  # noqa: BLE001
            for h in HORIZONS:
                factor_rows.append(
                    {
                        **row.to_dict(),
                        "horizon": h,
                        "error": str(exc),
                        "hold_sharpe": None,
                    }
                )
        if (i + 1) % 10 == 0 or (i + 1) == len(catalog):
            print(f"[factor] {i+1}/{len(catalog)}", flush=True)

    factors = pd.DataFrame(factor_rows)
    factors.to_csv(OUT / "per_factor_5d_10d.csv", index=False, encoding="utf-8")

    print("evaluating iteration ensembles...", flush=True)
    ensembles = _eval_iteration_ensembles(train, val, test)
    ensembles.to_csv(OUT / "per_iteration_ensemble_5d_10d.csv", index=False, encoding="utf-8")

    # Rankings
    lines = [
        "# 历史迭代因子：5日 / 10日表现排序",
        "",
        "合约：冻结快照 CSI300；单因子与合奏均为 **dynamic-trim hold**，EMA10，成本 10bps。",
        f"覆盖：{len(catalog)} 个唯一表达式（iter 目录现存库 + live）；合奏覆盖有 cleaned/combined 的迭代。",
        "",
    ]

    for h in HORIZONS:
        sub = factors[factors["horizon"] == h].copy()
        sub = sub[sub["hold_sharpe"].notna()].sort_values("hold_sharpe", ascending=False)
        sub.insert(0, "rank", range(1, len(sub) + 1))
        sub.to_csv(OUT / f"rank_factors_{h}d_by_hold.csv", index=False, encoding="utf-8")

        lines.append(f"## 单因子排序（{h}日 Hold Sharpe Top 25）")
        lines.append("")
        lines.append(
            f"| # | Hold Sharpe | 年化 | 最大回撤 | Test IC | Val IC | 首现iter | 末现iter | Live | 表达式 |"
        )
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---|")
        for _, r in sub.head(25).iterrows():
            expr = str(r["expression"]).replace("|", "\\|")
            if len(expr) > 90:
                expr = expr[:87] + "..."
            lines.append(
                "| {rank} | {hs:.4f} | {ann:.2%} | {dd:.2%} | {tic:.4f} | {vic:.4f} | {fi} | {li} | {live} | `{expr}` |".format(
                    rank=int(r["rank"]),
                    hs=float(r["hold_sharpe"]),
                    ann=float(r["hold_annualized_return"] or 0),
                    dd=float(r["hold_max_drawdown"] or 0),
                    tic=float(r["test_ic"] or 0),
                    vic=float(r["val_ic"] or 0),
                    fi=r["first_iteration"] if pd.notna(r["first_iteration"]) else "",
                    li=r["last_iteration"] if pd.notna(r["last_iteration"]) else "",
                    live="Y" if r["in_current_live"] else "",
                    expr=expr,
                )
            )
        lines.append("")

        # also by test IC
        by_ic = sub.sort_values("test_ic", ascending=False).head(15)
        lines.append(f"### 同周期按 Test IC Top 15（{h}日）")
        lines.append("")
        lines.append("| # | Test IC | Hold Sharpe | Val IC | 表达式 |")
        lines.append("|---:|---:|---:|---:|---|")
        for i, (_, r) in enumerate(by_ic.iterrows(), 1):
            expr = str(r["expression"]).replace("|", "\\|")
            if len(expr) > 80:
                expr = expr[:77] + "..."
            lines.append(
                f"| {i} | {float(r['test_ic']):.4f} | {float(r['hold_sharpe']):.4f} | {float(r['val_ic'] or 0):.4f} | `{expr}` |"
            )
        lines.append("")

    for h in HORIZONS:
        sub = ensembles[ensembles["horizon"] == h].copy()
        sub = sub[sub["hold_valid"] == True].sort_values("hold_sharpe", ascending=False)  # noqa: E712
        sub.insert(0, "rank", range(1, len(sub) + 1))
        sub.to_csv(OUT / f"rank_ensembles_{h}d_by_hold.csv", index=False, encoding="utf-8")
        lines.append(f"## 迭代合奏排序（{h}日 Hold Sharpe）")
        lines.append("")
        lines.append("| # | Iter | Hold Sharpe | 年化 | 最大回撤 | n_factors |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.head(20).iterrows():
            lines.append(
                "| {rank} | {it} | {hs:.4f} | {ann:.2%} | {dd:.2%} | {n} |".format(
                    rank=int(r["rank"]),
                    it=int(r["iteration"]),
                    hs=float(r["hold_sharpe"]),
                    ann=float(r["hold_annualized_return"] or 0),
                    dd=float(r["hold_max_drawdown"] or 0),
                    n=int(r["n_factors"]),
                )
            )
        lines.append("")

    # Cross-horizon comparison for top factors
    wide5 = factors[factors["horizon"] == 5][["expression", "hold_sharpe", "test_ic"]].rename(
        columns={"hold_sharpe": "hold_5d", "test_ic": "test_ic_5d"}
    )
    wide10 = factors[factors["horizon"] == 10][["expression", "hold_sharpe", "test_ic"]].rename(
        columns={"hold_sharpe": "hold_10d", "test_ic": "test_ic_10d"}
    )
    cross = wide5.merge(wide10, on="expression", how="inner")
    cross = cross.merge(
        catalog[["expression", "in_current_live", "first_iteration", "last_iteration"]],
        on="expression",
        how="left",
    )
    cross["best_horizon"] = cross.apply(
        lambda r: "5d"
        if float(r["hold_5d"] or -999) >= float(r["hold_10d"] or -999)
        else "10d",
        axis=1,
    )
    cross["best_hold"] = cross[["hold_5d", "hold_10d"]].max(axis=1)
    cross = cross.sort_values("best_hold", ascending=False)
    cross.to_csv(OUT / "cross_horizon_factor_comparison.csv", index=False, encoding="utf-8")

    lines.append("## 5日 vs 10日交叉（按最优 Hold 排序 Top 20）")
    lines.append("")
    lines.append("| # | 更优周期 | Hold 5d | Hold 10d | Live | 表达式 |")
    lines.append("|---:|:---:|---:|---:|:---:|---|")
    for i, (_, r) in enumerate(cross.head(20).iterrows(), 1):
        expr = str(r["expression"]).replace("|", "\\|")
        if len(expr) > 80:
            expr = expr[:77] + "..."
        lines.append(
            "| {i} | {bh} | {h5:.4f} | {h10:.4f} | {live} | `{expr}` |".format(
                i=i,
                bh=r["best_horizon"],
                h5=float(r["hold_5d"] or 0),
                h10=float(r["hold_10d"] or 0),
                live="Y" if r["in_current_live"] else "",
                expr=expr,
            )
        )
    lines.append("")
    lines.append(f"输出目录：`{OUT.as_posix()}`")

    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT / "REPORT.md").read_text(encoding="utf-8")[:4000])
    print("DONE", OUT)


if __name__ == "__main__":
    main()
