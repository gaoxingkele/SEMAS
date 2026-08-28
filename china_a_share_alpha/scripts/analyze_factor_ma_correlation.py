"""Measure frozen factor exposure to normalized moving-average signals."""

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


def build_ma_deviation(panel: pd.DataFrame, window: int) -> pd.Series:
    """Return close/MA(window)-1 using only current and past closes."""
    close = panel["close"].astype(float)
    moving_average = close.groupby(level="symbol").transform(
        lambda values: values.rolling(window, min_periods=window).mean()
    )
    return (close / moving_average - 1.0).replace([np.inf, -np.inf], np.nan)


def newey_west_mean_t(values: pd.Series, max_lag: int) -> tuple[float, float]:
    """Return HAC standard error and t-statistic for a sample mean."""
    sample = values.dropna().to_numpy(dtype=float)
    n_obs = len(sample)
    if n_obs < 2:
        return float("nan"), float("nan")
    centered = sample - sample.mean()
    long_run_variance = float(np.dot(centered, centered) / n_obs)
    usable_lag = min(max_lag, n_obs - 1)
    for lag in range(1, usable_lag + 1):
        weight = 1.0 - lag / (usable_lag + 1.0)
        covariance = float(np.dot(centered[lag:], centered[:-lag]) / n_obs)
        long_run_variance += 2.0 * weight * covariance
    standard_error = float(np.sqrt(max(long_run_variance, 0.0) / n_obs))
    if standard_error <= 1e-15:
        return standard_error, float("nan")
    return standard_error, float(sample.mean() / standard_error)


def daily_cross_sectional_spearman(
    factor_signal: pd.Series,
    ma_signal: pd.Series,
    min_symbols: int,
) -> pd.Series:
    """Calculate one cross-sectional Spearman correlation per trading day."""
    frame = pd.concat([factor_signal.rename("factor"), ma_signal.rename("ma")], axis=1).dropna()
    correlations: dict[pd.Timestamp, float] = {}
    for date, daily in frame.groupby(level="date", sort=True):
        if len(daily) >= min_symbols:
            correlations[pd.Timestamp(date)] = float(
                daily["factor"].corr(daily["ma"], method="spearman")
            )
    return pd.Series(correlations, dtype=float, name="rank_correlation")


def summarize_correlations(
    correlations: pd.Series,
    hac_lag: int,
) -> dict[str, float | int]:
    sample = correlations.dropna()
    standard_error, t_stat = newey_west_mean_t(sample, hac_lag)
    return {
        "n_dates": int(len(sample)),
        "mean_spearman": float(sample.mean()) if len(sample) else float("nan"),
        "median_spearman": float(sample.median()) if len(sample) else float("nan"),
        "std_spearman": float(sample.std()) if len(sample) > 1 else float("nan"),
        "positive_fraction": float((sample > 0).mean()) if len(sample) else float("nan"),
        "hac_standard_error": standard_error,
        "hac_t_stat": t_stat,
    }


def analyze(
    snapshot_dir: Path,
    library_path: Path,
    output_dir: Path,
    windows: list[int],
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

    factor_signals: dict[str, pd.Series] = {}
    factor_errors = []
    for row_index, row in library.reset_index(drop=True).iterrows():
        name = f"{row.get('factor', 'factor')}__row_{row_index + 1}"
        try:
            factor_signals[name] = _zscore(parse_expression(row["expression"]).eval(panel))
        except Exception as exc:
            factor_errors.append({"factor": name, "error": str(exc)})
    if not factor_signals:
        raise ValueError("no factor expressions could be evaluated")

    raw_ensemble, raw_coverage = _build_equal_weight_signal(
        factor_signals,
        smooth_span=1,
        min_factor_coverage=min_factor_coverage,
    )
    smoothed_ensemble, smoothed_coverage = _build_equal_weight_signal(
        factor_signals,
        smooth_span=smooth_span,
        min_factor_coverage=min_factor_coverage,
    )
    analyzed_signals = {
        **factor_signals,
        "ensemble_raw": raw_ensemble,
        f"ensemble_ema{smooth_span}": smoothed_ensemble,
    }
    ma_signals = {f"close_to_ma{window}": build_ma_deviation(panel, window) for window in windows}

    rows = []
    daily_receipts: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for fold_name, fold_panel in fold_panels.items():
        fold_index = fold_panel.index
        daily_receipts[fold_name] = {}
        for signal_name, signal in analyzed_signals.items():
            daily_receipts[fold_name][signal_name] = {}
            for ma_name, ma_signal in ma_signals.items():
                daily = daily_cross_sectional_spearman(
                    signal.reindex(fold_index),
                    ma_signal.reindex(fold_index),
                    min_symbols=min_symbols,
                )
                summary = summarize_correlations(daily, hac_lag=hac_lag)
                rows.append(
                    {
                        "fold": fold_name,
                        "signal": signal_name,
                        "ma_signal": ma_name,
                        **summary,
                    }
                )
                daily_receipts[fold_name][signal_name][ma_name] = [
                    {"date": date.isoformat(), "spearman": float(value)}
                    for date, value in daily.items()
                ]

    summary_frame = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_frame.to_csv(output_dir / "factor_ma_correlation_summary.csv", index=False)
    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "library_path": str(library_path.resolve()),
        "library_sha256": _sha256_file(library_path),
        "definition": {
            "ma_signal": "close / trailing_MA(close, window) - 1",
            "correlation": "daily cross-sectional Spearman",
            "hac_lag": hac_lag,
            "min_symbols_per_day": min_symbols,
            "smooth_span": smooth_span,
            "min_factor_coverage": min_factor_coverage,
        },
        "factor_errors": factor_errors,
        "coverage": {
            "raw_ensemble": raw_coverage,
            f"ensemble_ema{smooth_span}": smoothed_coverage,
        },
        "summary": rows,
        "daily": daily_receipts,
    }
    (output_dir / "factor_ma_correlation_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=True, allow_nan=False),
        encoding="utf-8",
    )
    _write_markdown(output_dir / "factor_ma_correlation_report.md", receipt, summary_frame)
    return receipt


def _write_markdown(path: Path, receipt: dict[str, Any], summary: pd.DataFrame) -> None:
    ensemble = summary[summary["signal"].str.startswith("ensemble")].copy()
    lines = [
        "# Factor / Moving-Average Correlation",
        "",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        f"- Library SHA-256: `{receipt['library_sha256']}`",
        "- MA signal: `close / trailing_MA(close, n) - 1`",
        "- Statistic: daily cross-sectional Spearman; Newey-West lag "
        f"{receipt['definition']['hac_lag']}",
        "",
        "## Ensemble Summary",
        "",
        "| Fold | Signal | MA | Mean rho | HAC t | Positive days | Dates |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in ensemble.itertuples(index=False):
        lines.append(
            f"| {row.fold} | {row.signal} | {row.ma_signal} | "
            f"{row.mean_spearman:.4f} | {row.hac_t_stat:.2f} | "
            f"{row.positive_fraction:.1%} | {row.n_dates} |"
        )
    lines.extend(
        [
            "",
            "Positive rho means the factor ranks stocks farther above their trailing MA higher.",
            "Correlation measures style exposure or redundancy, not predictive quality.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--windows", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--min-factor-coverage", type=float, default=0.5)
    parser.add_argument("--min-symbols", type=int, default=30)
    parser.add_argument("--hac-lag", type=int, default=20)
    args = parser.parse_args()
    analyze(
        snapshot_dir=args.snapshot_dir,
        library_path=args.library,
        output_dir=args.output_dir,
        windows=args.windows,
        smooth_span=args.smooth_span,
        min_factor_coverage=args.min_factor_coverage,
        min_symbols=args.min_symbols,
        hac_lag=args.hac_lag,
    )


if __name__ == "__main__":
    main()
