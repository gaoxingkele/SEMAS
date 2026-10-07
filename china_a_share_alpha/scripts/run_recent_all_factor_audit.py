"""Audit every discovered factor expression across recent T+1 contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import run_t1_exit_backtest
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.audit_recent_market_gate import (
    continuous_market_trend_gate,
)
from china_a_share_alpha.scripts.evolve_recent_regime_matching import (
    return_concentration,
)
from china_a_share_alpha.scripts.evolve_stock_factor_matching import (
    fold_forward_returns,
)
from china_a_share_alpha.scripts.run_t1_full_library_audit import (
    _load_snapshot,
    discover_libraries,
)


_WORKER_PANEL: pd.DataFrame | None = None
_WORKER_METADATA: pd.DataFrame | None = None
_WORKER_CONFIG: dict[str, Any] | None = None
_WORKER_GATES: dict[str, pd.Series] | None = None


def expression_id(expression: str) -> str:
    return hashlib.sha256(expression.encode()).hexdigest()[:16]


def build_expression_catalog(libraries: pd.DataFrame) -> pd.DataFrame:
    sources: dict[str, set[str]] = {}
    library_ids: dict[str, set[str]] = {}
    for _, library in libraries.iterrows():
        for expression in library.expressions:
            sources.setdefault(expression, set()).update(library.source_paths)
            library_ids.setdefault(expression, set()).add(library.library_id)
    rows = []
    for expression in sorted(sources):
        rows.append(
            {
                "expression_id": expression_id(expression),
                "expression": expression,
                "library_count": len(library_ids[expression]),
                "library_ids": json.dumps(sorted(library_ids[expression])),
                "source_paths": json.dumps(sorted(sources[expression])),
            }
        )
    catalog = pd.DataFrame(rows)
    if catalog["expression_id"].duplicated().any():
        raise RuntimeError("expression id collision")
    return catalog


def catalog_digest(catalog: pd.DataFrame) -> str:
    payload = "\n".join(catalog.sort_values("expression_id")["expression"].tolist())
    return hashlib.sha256(payload.encode()).hexdigest()


def build_expression_signal_cache(
    panel: pd.DataFrame,
    catalog: pd.DataFrame,
    cache_dir: Path,
    snapshot_id: str,
) -> pd.DataFrame:
    """Build resumable one-file-per-expression signal cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    raw_panel = panel.drop(columns="audit_fold")
    for position, row in enumerate(catalog.itertuples(index=False), start=1):
        path = cache_dir / f"{row.expression_id}.parquet"
        if path.exists():
            continue
        try:
            signal = parse_expression(row.expression).eval(raw_panel)
            signal = pd.to_numeric(signal, errors="coerce").reindex(panel.index)
            signal = signal.replace([np.inf, -np.inf], np.nan)
            signal.astype(np.float32).rename("signal").to_frame().to_parquet(
                path, compression="zstd"
            )
        except Exception as exc:  # pragma: no cover - real catalog protection
            errors.append(
                {
                    "expression_id": row.expression_id,
                    "expression": row.expression,
                    "error": str(exc),
                }
            )
        if position % 10 == 0 or position == len(catalog):
            print(
                f"SIGNAL CACHE {position}/{len(catalog)} errors={len(errors)}",
                flush=True,
            )
    error_frame = pd.DataFrame(errors, columns=["expression_id", "expression", "error"])
    error_frame.to_csv(cache_dir / "expression_errors.csv", index=False)
    manifest = {
        "snapshot_id": snapshot_id,
        "catalog_digest": catalog_digest(catalog),
        "expression_count": int(len(catalog)),
        "cached_count": len(list(cache_dir.glob("*.parquet"))),
        "error_count": int(len(error_frame)),
    }
    (cache_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return error_frame


def daily_cross_sectional_ic(
    signal: pd.Series,
    panel: pd.DataFrame,
    horizon: int,
) -> dict[str, float | int]:
    labels = fold_forward_returns(panel, horizon)
    frame = pd.concat([signal.rename("signal"), labels.rename("label")], axis=1)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    if frame.empty:
        return {"ic_mean": np.nan, "rank_ic_mean": np.nan, "ic_days": 0}

    def correlation(block: pd.DataFrame, method: str) -> float:
        if len(block) < 5 or block["signal"].nunique() < 2 or block["label"].nunique() < 2:
            return np.nan
        return float(block["signal"].corr(block["label"], method=method))

    grouped = frame.groupby(level="date", sort=False)
    ic = grouped.apply(lambda block: correlation(block, "pearson"), include_groups=False)
    rank_ic = grouped.apply(
        lambda block: correlation(block, "spearman"), include_groups=False
    )
    return {
        "ic_mean": float(ic.mean()),
        "rank_ic_mean": float(rank_ic.mean()),
        "ic_days": int(ic.notna().sum()),
    }


def expected_result_rows(
    expression_count: int,
    period_count: int,
    horizon_count: int,
    gate_count: int,
    universe_count: int,
) -> int:
    return expression_count * period_count * horizon_count * gate_count * universe_count


def _worker_init(snapshot_dir: str, config: dict[str, Any]) -> None:
    global _WORKER_PANEL, _WORKER_METADATA, _WORKER_CONFIG, _WORKER_GATES
    _WORKER_PANEL, _WORKER_METADATA, _ = _load_snapshot(Path(snapshot_dir))
    _WORKER_CONFIG = config
    _WORKER_GATES = {"none": pd.Series(True, index=pd.DatetimeIndex([]))}
    for window in config.get("market_ma_windows", [20]):
        name = f"ma{int(window)}"
        _WORKER_GATES[name] = continuous_market_trend_gate(_WORKER_PANEL, int(window))


def _period_mask(index: pd.Index, start: str, end: str) -> np.ndarray:
    dates = pd.to_datetime(index.get_level_values("date"))
    return np.asarray((dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end)))


def _gate_signal(signal: pd.Series, gate_name: str) -> pd.Series:
    assert _WORKER_GATES is not None
    if gate_name == "none":
        return signal
    dates = pd.to_datetime(signal.index.get_level_values("date"))
    allowed = _WORKER_GATES[gate_name].reindex(dates).fillna(False).to_numpy()
    return signal.where(allowed)


def signal_quality(
    signal: pd.Series,
    min_coverage: float | None = None,
    min_active_days: int | None = None,
) -> dict[str, float | int | str | bool]:
    coverage = float(signal.notna().mean())
    active_by_date = signal.groupby(level="date").nunique(dropna=True).gt(1)
    active_days = int(active_by_date.sum())
    if min_coverage is None or min_active_days is None:
        assert _WORKER_CONFIG is not None
        min_coverage = float(_WORKER_CONFIG.get("min_factor_coverage", 0.5))
        min_active_days = int(_WORKER_CONFIG.get("min_signal_active_days", 20))
    valid = bool(
        coverage >= min_coverage
        and active_days >= min_active_days
    )
    if coverage < min_coverage:
        status = "insufficient_coverage"
    elif active_days < min_active_days:
        status = "insufficient_cross_sectional_variation"
    else:
        status = "ok"
    return {
        "signal_valid": valid,
        "signal_status": status,
        "signal_coverage": coverage,
        "signal_active_days": active_days,
    }


def invalid_backtest_metrics(horizon: int, observations: int) -> dict[str, Any]:
    return {
        "valid": False,
        "sharpe": np.nan,
        "annualized_return": np.nan,
        "total_return": np.nan,
        "max_drawdown": np.nan,
        "n_observations": observations,
        "horizon": horizon,
        "n_symbols": 0,
        "n_trades": 0,
        "blocked_entries": 0,
        "blocked_exits": 0,
        "open_positions_at_end": 0,
        "average_trade_return": np.nan,
        "win_rate": np.nan,
    }


def _audit_one_expression(task: dict[str, str]) -> list[dict[str, Any]]:
    assert _WORKER_PANEL is not None
    assert _WORKER_METADATA is not None
    assert _WORKER_CONFIG is not None
    signal = pd.read_parquet(task["signal_path"])["signal"].reindex(_WORKER_PANEL.index)
    rows = []
    universes = {
        "all_stocks": {"main", "innovation", "bse"},
        "main_board": {"main"},
        "innovation": {"innovation"},
    }
    gate_names = ["none"] + [
        f"ma{int(value)}" for value in _WORKER_CONFIG.get("market_ma_windows", [20])
    ]
    for period in _WORKER_CONFIG["periods"]:
        mask = _period_mask(_WORKER_PANEL.index, period["start"], period["end"])
        period_panel = _WORKER_PANEL.loc[mask].drop(columns="audit_fold")
        period_signal = signal.loc[mask]
        quality = signal_quality(period_signal)
        for horizon in _WORKER_CONFIG["horizons"]:
            ic = daily_cross_sectional_ic(period_signal, period_panel, int(horizon))
            for gate_name in gate_names:
                gated_signal = _gate_signal(period_signal, gate_name)
                for universe, groups in universes.items():
                    if quality["signal_valid"]:
                        metrics, trades, _ = run_t1_exit_backtest(
                            gated_signal,
                            period_panel,
                            _WORKER_METADATA,
                            horizon=int(horizon),
                            selection_fraction=float(
                                _WORKER_CONFIG.get("selection_fraction", 0.20)
                            ),
                            transaction_cost=float(
                                _WORKER_CONFIG.get("transaction_cost", 0.001)
                            ),
                            slippage=float(_WORKER_CONFIG.get("slippage", 0.0005)),
                            universe_groups=groups,
                        )
                        concentration = return_concentration(trades)
                    else:
                        metrics = invalid_backtest_metrics(
                            int(horizon),
                            period_panel.index.get_level_values("date").nunique(),
                        )
                        concentration = np.nan
                    rows.append(
                        {
                            "expression_id": task["expression_id"],
                            "expression": task["expression"],
                            "period": period["name"],
                            "horizon": int(horizon),
                            "gate": gate_name,
                            "universe": universe,
                            "return_concentration": concentration,
                            **quality,
                            **ic,
                            **metrics,
                        }
                    )
    return rows


def enrich_signal_quality(
    results: pd.DataFrame,
    catalog: pd.DataFrame,
    cache_dir: Path,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Backfill quality fields so resumable fragments survive schema upgrades."""
    quality_columns = [
        "signal_valid",
        "signal_status",
        "signal_coverage",
        "signal_active_days",
    ]
    for column in quality_columns:
        if column not in results:
            results[column] = np.nan
    for row in catalog.itertuples(index=False):
        signal = pd.read_parquet(cache_dir / f"{row.expression_id}.parquet")["signal"]
        for period in config["periods"]:
            mask = _period_mask(signal.index, period["start"], period["end"])
            quality = signal_quality(
                signal.loc[mask],
                float(config.get("min_factor_coverage", 0.5)),
                int(config.get("min_signal_active_days", 20)),
            )
            result_mask = results["expression_id"].eq(row.expression_id) & results[
                "period"
            ].eq(period["name"])
            for column, value in quality.items():
                results.loc[result_mask, column] = value
    results["signal_valid"] = results["signal_valid"].astype(bool)
    results["signal_active_days"] = results["signal_active_days"].astype(int)
    return results


def _write_unavailable_matrix(
    output_dir: Path,
    config: dict[str, Any],
    expression_count: int,
) -> pd.DataFrame:
    reasons = {
        "bse": "no BSE securities in frozen stock panel",
        "etf": "no ETF OHLC/factor panel in frozen snapshot",
        "index": "no independent index OHLC/factor panel in frozen snapshot",
    }
    gate_names = ["none"] + [
        f"ma{int(value)}" for value in config.get("market_ma_windows", [20])
    ]
    rows = []
    for asset_class, reason in reasons.items():
        for period in config["periods"]:
            for horizon in config["horizons"]:
                for gate in gate_names:
                    rows.append(
                        {
                            "asset_class": asset_class,
                            "period": period["name"],
                            "horizon": int(horizon),
                            "gate": gate,
                            "expression_count": expression_count,
                            "status": "unavailable",
                            "reason": reason,
                        }
                    )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "unavailable_asset_classes.csv", index=False)
    return frame


def build_rankings(results: pd.DataFrame) -> pd.DataFrame:
    """Rank factors with 2025--2026 lower-tail performance as the primary gate."""
    key_columns = ["expression_id", "expression", "horizon", "gate", "universe"]
    rows = []
    for keys, block in results.groupby(key_columns, sort=False):
        periods = block.set_index("period")
        required = {"2024", "2025", "2026_ytd"}
        if not required.issubset(periods.index):
            continue
        recent = periods.loc[["2025", "2026_ytd"]]
        score = (
            0.10 * float(periods.loc["2024", "sharpe"])
            + 0.35 * float(periods.loc["2025", "sharpe"])
            + 0.55 * float(periods.loc["2026_ytd", "sharpe"])
        )
        recent_min_sharpe = float(recent["sharpe"].min())
        recent_worst_drawdown = float(recent["max_drawdown"].min())
        recent_max_concentration = float(recent["return_concentration"].max())
        recent_min_rank_ic = float(recent["rank_ic_mean"].min())
        effective = bool(
            recent["valid"].all()
            and recent_min_sharpe > 0
            and recent_worst_drawdown >= -0.25
            and recent_max_concentration <= 0.10
            and recent_min_rank_ic > 0
        )
        rows.append(
            {
                **dict(zip(key_columns, keys)),
                "effective": effective,
                "recent_score": score,
                "recent_min_sharpe": recent_min_sharpe,
                "recent_worst_drawdown": recent_worst_drawdown,
                "recent_max_concentration": recent_max_concentration,
                "recent_min_rank_ic": recent_min_rank_ic,
                "sharpe_2024": float(periods.loc["2024", "sharpe"]),
                "sharpe_2025": float(periods.loc["2025", "sharpe"]),
                "sharpe_2026_ytd": float(periods.loc["2026_ytd", "sharpe"]),
            }
        )
    ranking = pd.DataFrame(rows)
    if ranking.empty:
        return ranking
    return ranking.sort_values(
        ["effective", "recent_score", "recent_min_sharpe"], ascending=False
    ).reset_index(drop=True)


def write_report(
    output_dir: Path,
    receipt: dict[str, Any],
    results: pd.DataFrame,
    rankings: pd.DataFrame,
) -> None:
    effective = rankings.loc[rankings["effective"]]
    contract_counts = (
        rankings.groupby(["horizon", "gate", "universe"])["effective"]
        .sum()
        .reset_index()
    )
    top = effective.loc[effective["universe"].eq("all_stocks")].head(20)
    invalid = results.loc[~results["signal_valid"]].drop_duplicates(
        ["expression_id", "period"]
    )
    lines = [
        "# 2024--2026 全单因子 T+1 审计",
        "",
        f"- 因子库：{receipt['library_count']}",
        f"- 唯一表达式：{receipt['expression_count']}",
        f"- 完整矩阵：{receipt['actual_result_rows']}/{receipt['expected_result_rows']}",
        f"- 有效/无效结果行：{receipt['valid_result_rows']}/{receipt['invalid_result_rows']}",
        f"- 至少通过一个契约的唯一因子：{receipt['effective_expression_count']}",
        f"- 数据截止：{receipt['data_end']}",
        "",
        "## 各契约有效因子数",
        "",
        "| 周期 | 门控 | 股票范围 | 有效因子数 |",
        "|---:|---|---|---:|",
    ]
    for row in contract_counts.itertuples(index=False):
        lines.append(f"| {row.horizon} | {row.gate} | {row.universe} | {int(row.effective)} |")
    lines.extend(
        [
            "",
            "## 全股票有效因子前20",
            "",
            "| 因子 | 周期 | 门控 | 近期分数 | 2025 Sharpe | 2026 Sharpe | 最差回撤 |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in top.itertuples(index=False):
        lines.append(
            f"| `{row.expression}` | {row.horizon} | {row.gate} | "
            f"{row.recent_score:.3f} | {row.sharpe_2025:.3f} | "
            f"{row.sharpe_2026_ytd:.3f} | {row.recent_worst_drawdown:.2%} |"
        )
    lines.extend(["", "## 无效信号时期", ""])
    if invalid.empty:
        lines.append("无。")
    else:
        for row in invalid.itertuples(index=False):
            lines.append(
                f"- `{row.expression}` / {row.period}: {row.signal_status}; "
                f"active_days={row.signal_active_days}."
            )
    lines.extend(
        [
            "",
            "## 数据边界",
            "",
            "北交所、ETF和独立指数缺少本地因子/行情面板；对应组合已写入",
            "`unavailable_asset_classes.csv`，没有用股票数据替代。",
        ]
    )
    (output_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(config: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(config["output_dir"])
    fragment_dir = output_dir / "fragments"
    cache_dir = Path(config["expression_signal_cache"])
    output_dir.mkdir(parents=True, exist_ok=True)
    fragment_dir.mkdir(parents=True, exist_ok=True)

    panel, _, snapshot_manifest = _load_snapshot(Path(config["snapshot_dir"]))
    libraries = discover_libraries(Path(config["factor_output_root"]))
    catalog = build_expression_catalog(libraries)
    catalog.to_csv(output_dir / "expression_catalog.csv", index=False)
    digest = catalog_digest(catalog)
    errors = build_expression_signal_cache(
        panel,
        catalog,
        cache_dir,
        str(snapshot_manifest.get("snapshot_id")),
    )
    if not errors.empty:
        raise RuntimeError(f"{len(errors)} expression signals failed; audit incomplete")

    tasks = []
    for row in catalog.itertuples(index=False):
        fragment = fragment_dir / f"{row.expression_id}.csv"
        if fragment.exists():
            continue
        tasks.append(
            {
                "expression_id": row.expression_id,
                "expression": row.expression,
                "signal_path": str(cache_dir / f"{row.expression_id}.parquet"),
                "fragment_path": str(fragment),
            }
        )
    print(f"AUDIT pending={len(tasks)} complete={len(catalog) - len(tasks)}", flush=True)
    workers = int(config.get("workers", 2))
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_init,
        initargs=(str(config["snapshot_dir"]), config),
    ) as executor:
        futures = {executor.submit(_audit_one_expression, task): task for task in tasks}
        completed = len(catalog) - len(tasks)
        for future in as_completed(futures):
            task = futures[future]
            rows = future.result()
            pd.DataFrame(rows).to_csv(task["fragment_path"], index=False)
            completed += 1
            print(f"AUDIT EXPRESSIONS {completed}/{len(catalog)}", flush=True)

    fragments = sorted(fragment_dir.glob("*.csv"))
    results = pd.concat([pd.read_csv(path) for path in fragments], ignore_index=True)
    results = enrich_signal_quality(results, catalog, cache_dir, config)
    results.to_parquet(output_dir / "all_factor_results.parquet", index=False)
    rankings = build_rankings(results)
    rankings.to_csv(output_dir / "factor_rankings.csv", index=False)
    unavailable = _write_unavailable_matrix(output_dir, config, len(catalog))
    gate_count = 1 + len(config.get("market_ma_windows", [20]))
    expected = expected_result_rows(
        len(catalog),
        len(config["periods"]),
        len(config["horizons"]),
        gate_count,
        3,
    )
    receipt = {
        "snapshot_id": snapshot_manifest.get("snapshot_id"),
        "data_start": str(panel.index.get_level_values("date").min().date()),
        "data_end": str(panel.index.get_level_values("date").max().date()),
        "library_count": int(len(libraries)),
        "expression_count": int(len(catalog)),
        "catalog_digest": digest,
        "expression_error_count": int(len(errors)),
        "expected_result_rows": expected,
        "actual_result_rows": int(len(results)),
        "matrix_complete": bool(len(results) == expected),
        "valid_result_rows": int(results["valid"].sum()),
        "invalid_result_rows": int((~results["valid"]).sum()),
        "invalid_signal_periods": int(
            len(
                results.loc[~results["signal_valid"]].drop_duplicates(
                    ["expression_id", "period"]
                )
            )
        ),
        "expressions_with_invalid_periods": int(
            results.loc[~results["signal_valid"], "expression_id"].nunique()
        ),
        "fully_evaluable_expression_count": int(
            len(catalog)
            - results.loc[~results["signal_valid"], "expression_id"].nunique()
        ),
        "ic_unavailable_combinations": int(
            len(
                results.loc[results["ic_mean"].isna()].drop_duplicates(
                    ["expression_id", "period", "horizon"]
                )
            )
        ),
        "effective_ranking_rows": int(rankings["effective"].sum()),
        "effective_expression_count": int(
            rankings.loc[rankings["effective"], "expression_id"].nunique()
        ),
        "unavailable_receipt_rows": int(len(unavailable)),
        "config": config,
    }
    (output_dir / "completion_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_report(output_dir, receipt, results, rankings)
    if not receipt["matrix_complete"]:
        raise RuntimeError(f"incomplete matrix: {len(results)} != {expected}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    run_audit(yaml.safe_load(args.config.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
