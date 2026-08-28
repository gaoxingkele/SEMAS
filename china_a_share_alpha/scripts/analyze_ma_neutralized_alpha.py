"""Compare a 20d factor ensemble before and after MA cross-sectional neutralization."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.analyze_factor_ma_correlation import (
    build_ma_deviation,
    daily_cross_sectional_spearman,
    summarize_correlations,
)
from china_a_share_alpha.scripts.evolve_20d_position_schedule import (
    backtest_schedule,
    prepare_fold,
)
from china_a_share_alpha.scripts.run_frozen_promotion_audit import verify_snapshot
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _build_equal_weight_signal,
    _zscore,
)


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def cross_sectional_neutralize(
    signal: pd.Series,
    exposures: dict[str, pd.Series],
    min_symbols: int,
) -> tuple[pd.Series, pd.DataFrame]:
    """Regress a signal on standardized exposures independently each day."""
    frame = pd.concat({"signal": signal, **exposures}, axis=1)
    exposure_names = list(exposures)
    residual_parts = []
    diagnostics = []
    for date, daily in frame.groupby(level="date", sort=True):
        valid = daily[["signal", *exposure_names]].dropna()
        if len(valid) < min_symbols:
            continue
        x = valid[exposure_names].to_numpy(dtype=float)
        means = x.mean(axis=0)
        standard_deviations = x.std(axis=0, ddof=0)
        usable = standard_deviations > 1e-12
        if not np.any(usable):
            continue
        standardized = (x[:, usable] - means[usable]) / standard_deviations[usable]
        design = np.column_stack([np.ones(len(valid)), standardized])
        y = valid["signal"].to_numpy(dtype=float)
        coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
        fitted = design @ coefficients
        residual = pd.Series(y - fitted, index=valid.index, dtype=float)
        residual_parts.append(residual)
        total_variance = float(np.sum((y - y.mean()) ** 2))
        residual_variance = float(np.sum((y - fitted) ** 2))
        diagnostics.append(
            {
                "date": pd.Timestamp(date),
                "n_symbols": int(len(valid)),
                "design_rank": int(rank),
                "r_squared": (
                    float(1.0 - residual_variance / total_variance)
                    if total_variance > 1e-15
                    else float("nan")
                ),
            }
        )
    if not residual_parts:
        raise ValueError("no daily cross-section met the neutralization requirements")
    residuals = pd.concat(residual_parts).sort_index().rename("ma_neutral")
    return residuals, pd.DataFrame(diagnostics).set_index("date")


def forward_compound_return(returns: pd.Series, horizon: int) -> pd.Series:
    """Compound returns from day d+1 through d+horizon for each symbol."""

    def _future(values: pd.Series) -> pd.Series:
        clipped = values.astype(float).clip(lower=-0.999999)
        shifted_log = np.log1p(clipped).shift(-1)
        future_log = shifted_log.iloc[::-1].rolling(horizon, min_periods=horizon).sum().iloc[::-1]
        return np.expm1(future_log)

    result = returns.groupby(level="symbol", group_keys=False).apply(_future)
    result.index = result.index.droplevel(0) if result.index.nlevels == 3 else result.index
    return result.sort_index().rename(f"forward_{horizon}d_return")


def layer_return_summary(
    signal: pd.Series,
    forward_return: pd.Series,
    n_layers: int,
    min_symbols: int,
    hac_lag: int,
) -> dict[str, Any]:
    """Summarize daily equal-weight forward returns by signal quantile."""
    frame = pd.concat(
        [signal.rename("signal"), forward_return.rename("forward_return")], axis=1
    ).dropna()
    daily_rows = []
    for date, daily in frame.groupby(level="date", sort=True):
        if len(daily) < max(min_symbols, n_layers * 2):
            continue
        ranks = daily["signal"].rank(method="first", pct=True)
        layers = np.clip(np.ceil(ranks * n_layers).astype(int), 1, n_layers)
        means = daily.groupby(layers)["forward_return"].mean()
        if len(means) != n_layers:
            continue
        row = {f"q{layer}": float(means.loc[layer]) for layer in range(1, n_layers + 1)}
        row["date"] = pd.Timestamp(date)
        row["spread"] = row[f"q{n_layers}"] - row["q1"]
        daily_rows.append(row)
    daily = pd.DataFrame(daily_rows).set_index("date")
    if daily.empty:
        raise ValueError("no valid daily layer returns")
    spread_stats = summarize_correlations(daily["spread"], hac_lag=hac_lag)
    layer_means = {
        f"q{layer}": float(daily[f"q{layer}"].mean()) for layer in range(1, n_layers + 1)
    }
    values = [layer_means[f"q{layer}"] for layer in range(1, n_layers + 1)]
    return {
        "n_dates": int(len(daily)),
        "mean_forward_returns": layer_means,
        "top_minus_bottom": float(daily["spread"].mean()),
        "spread_hac_t_stat": float(spread_stats["hac_t_stat"]),
        "monotonic_steps": int(sum(right > left for left, right in zip(values, values[1:]))),
        "daily": [
            {"date": date.isoformat(), **{key: float(value) for key, value in row.items()}}
            for date, row in daily.iterrows()
        ],
    }


def evaluate_signal(
    name: str,
    signal: pd.Series,
    fold_panel: pd.DataFrame,
    forward_return: pd.Series,
    horizon: int,
    transaction_cost: float,
    min_symbols: int,
    hac_lag: int,
) -> dict[str, Any]:
    ic_daily = daily_cross_sectional_spearman(signal, forward_return, min_symbols)
    ic_summary = summarize_correlations(ic_daily, hac_lag=hac_lag)
    layers = layer_return_summary(
        signal,
        forward_return,
        n_layers=5,
        min_symbols=min_symbols,
        hac_lag=hac_lag,
    )
    prepared = prepare_fold(
        name=name,
        signal=signal,
        panel=fold_panel,
        horizon=horizon,
        selection_fraction=0.2,
    )
    hold = backtest_schedule(prepared, [1.0] * 10, transaction_cost=transaction_cost)
    return {"ic_20d": ic_summary, "layers_20d": layers, "hold_20d": hold}


def analyze(
    snapshot_dir: Path,
    library_path: Path,
    output_dir: Path,
    horizon: int,
    transaction_cost: float,
    smooth_span: int,
    min_factor_coverage: float,
    min_symbols: int,
    hac_lag: int,
) -> dict[str, Any]:
    manifest = verify_snapshot(snapshot_dir)
    fold_names = ["train", "val", "test"]
    fold_panels = {
        name: pd.read_parquet(snapshot_dir / manifest["files"][name]["file"]) for name in fold_names
    }
    panel = pd.concat(fold_panels.values()).sort_index()
    library = pd.read_csv(library_path)

    factor_signals = {}
    factor_errors = []
    for row_index, row in library.reset_index(drop=True).iterrows():
        name = f"{row.get('factor', 'factor')}__row_{row_index + 1}"
        try:
            factor_signals[name] = _zscore(parse_expression(row["expression"]).eval(panel))
        except Exception as exc:
            factor_errors.append({"factor": name, "error": str(exc)})
    if not factor_signals:
        raise ValueError("no factor expressions could be evaluated")

    raw, raw_coverage = _build_equal_weight_signal(
        factor_signals, smooth_span=1, min_factor_coverage=min_factor_coverage
    )
    smoothed, smoothed_coverage = _build_equal_weight_signal(
        factor_signals,
        smooth_span=smooth_span,
        min_factor_coverage=min_factor_coverage,
    )
    ma_exposures = {f"ma{window}": build_ma_deviation(panel, window) for window in (5, 10, 20)}

    signal_versions = {}
    neutralization_diagnostics = {}
    for name, original in {"ensemble_raw": raw, f"ensemble_ema{smooth_span}": smoothed}.items():
        neutral, diagnostics = cross_sectional_neutralize(
            original, ma_exposures, min_symbols=min_symbols
        )
        comparable_original = original.reindex(neutral.index).rename("original")
        signal_versions[name] = {"original": comparable_original, "ma_neutral": neutral}
        neutralization_diagnostics[name] = {
            "n_dates": int(len(diagnostics)),
            "mean_r_squared": float(diagnostics["r_squared"].mean()),
            "median_r_squared": float(diagnostics["r_squared"].median()),
            "mean_symbols": float(diagnostics["n_symbols"].mean()),
        }

    results = {}
    for fold_name, fold_panel in fold_panels.items():
        forward_return = forward_compound_return(fold_panel["return"], horizon)
        results[fold_name] = {}
        for signal_name, versions in signal_versions.items():
            results[fold_name][signal_name] = {}
            for version_name, full_signal in versions.items():
                fold_signal = full_signal.reindex(fold_panel.index).dropna()
                results[fold_name][signal_name][version_name] = evaluate_signal(
                    name=f"{fold_name}_{signal_name}_{version_name}",
                    signal=fold_signal,
                    fold_panel=fold_panel,
                    forward_return=forward_return,
                    horizon=horizon,
                    transaction_cost=transaction_cost,
                    min_symbols=min_symbols,
                    hac_lag=hac_lag,
                )

    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "library_path": str(library_path.resolve()),
        "library_sha256": _sha256_file(library_path),
        "contract": {
            "neutralization": "daily cross-sectional OLS residual on standardized MA5/10/20 deviations",
            "ma_signal": "close / trailing_MA(close, window) - 1",
            "forward_return": f"compound return from d+1 through d+{horizon}, within each fold",
            "ic": "daily cross-sectional Spearman",
            "layers": "five equal-count daily signal layers",
            "hold": f"non-overlapping {horizon}d cohorts, positions from d earn d+1 returns",
            "transaction_cost": transaction_cost,
            "hac_lag": hac_lag,
            "same_sample": True,
        },
        "factor_errors": factor_errors,
        "coverage": {
            "ensemble_raw": raw_coverage,
            f"ensemble_ema{smooth_span}": smoothed_coverage,
        },
        "neutralization_diagnostics": neutralization_diagnostics,
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ma_neutralized_alpha_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=True, allow_nan=False),
        encoding="utf-8",
    )
    _write_summary_csv(output_dir / "ma_neutralized_alpha_summary.csv", receipt)
    _write_markdown(output_dir / "ma_neutralized_alpha_report.md", receipt)
    return receipt


def _summary_rows(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for fold, signals in receipt["results"].items():
        for signal, versions in signals.items():
            for version, result in versions.items():
                layers = result["layers_20d"]
                rows.append(
                    {
                        "fold": fold,
                        "signal": signal,
                        "version": version,
                        "ic_mean": result["ic_20d"]["mean_spearman"],
                        "ic_hac_t": result["ic_20d"]["hac_t_stat"],
                        "q1": layers["mean_forward_returns"]["q1"],
                        "q2": layers["mean_forward_returns"]["q2"],
                        "q3": layers["mean_forward_returns"]["q3"],
                        "q4": layers["mean_forward_returns"]["q4"],
                        "q5": layers["mean_forward_returns"]["q5"],
                        "q5_minus_q1": layers["top_minus_bottom"],
                        "spread_hac_t": layers["spread_hac_t_stat"],
                        "monotonic_steps": layers["monotonic_steps"],
                        "hold_sharpe": result["hold_20d"]["sharpe"],
                        "hold_annualized_return": result["hold_20d"]["annualized_return"],
                        "hold_max_drawdown": result["hold_20d"]["max_drawdown"],
                    }
                )
    return rows


def _write_summary_csv(path: Path, receipt: dict[str, Any]) -> None:
    pd.DataFrame(_summary_rows(receipt)).to_csv(path, index=False)


def _write_markdown(path: Path, receipt: dict[str, Any]) -> None:
    lines = [
        "# MA-Neutralized 20d Alpha Audit",
        "",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        f"- Library SHA-256: `{receipt['library_sha256']}`",
        "- Neutralization: joint daily cross-sectional OLS on MA5/10/20 deviations",
        "- Comparison: same dates and symbols before/after neutralization",
        "",
        "| Fold | Signal | Version | 20d IC | IC HAC t | Q5-Q1 | Spread t | Hold Sharpe |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in _summary_rows(receipt):
        lines.append(
            f"| {row['fold']} | {row['signal']} | {row['version']} | "
            f"{row['ic_mean']:.4f} | {row['ic_hac_t']:.2f} | "
            f"{row['q5_minus_q1']:.2%} | {row['spread_hac_t']:.2f} | "
            f"{row['hold_sharpe']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Neutralized performance estimates alpha remaining after linear MA exposure is removed.",
            "They do not establish future profitability.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--horizon", type=int, default=20)
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--min-factor-coverage", type=float, default=0.5)
    parser.add_argument("--min-symbols", type=int, default=30)
    parser.add_argument("--hac-lag", type=int, default=20)
    args = parser.parse_args()
    analyze(
        snapshot_dir=args.snapshot_dir,
        library_path=args.library,
        output_dir=args.output_dir,
        horizon=args.horizon,
        transaction_cost=args.transaction_cost,
        smooth_span=args.smooth_span,
        min_factor_coverage=args.min_factor_coverage,
        min_symbols=args.min_symbols,
        hac_lag=args.hac_lag,
    )


if __name__ == "__main__":
    main()
