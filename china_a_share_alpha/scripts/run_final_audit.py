"""Final production audit of the live library.

Reports per-year performance, sector neutrality, coverage, and transaction-cost
robustness for the selected ensemble.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    return s.groupby(level="symbol").transform(lambda x: x.ewm(span=span, min_periods=1).mean())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config with val_date")
    parser.add_argument("--factor-csv", type=Path, required=True)
    parser.add_argument("--transaction-costs", type=float, nargs="+", default=[0.001, 0.002, 0.003])
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, val, test = load_tushare_data_with_val(cfg)

    lib = pd.read_csv(args.factor_csv)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    # Build combined signal on test (equal weight).
    frames = []
    for _, row in lib.iterrows():
        try:
            f = _zscore(parse_expression(row["expression"]).eval(test)).rename(row["factor"])
            frames.append(f)
        except Exception as exc:
            print(f"Skipping {row.get('factor')}: {exc}")
    mat = pd.concat(frames, axis=1).dropna()
    weights = np.ones(len(lib)) / len(lib)
    combined = _smooth((mat @ weights).clip(-5, 5), args.smooth_span)

    # Sector neutrality: correlation of combined signal with sector codes.
    sectors = test["sector"].dropna()
    common_idx = combined.index.intersection(sectors.index)
    sector_corr = 0.0
    if not sectors.empty:
        sector_numeric = pd.Categorical(sectors.loc[common_idx]).codes
        sector_corr = float(pd.Series(combined.loc[common_idx]).corr(pd.Series(sector_numeric, index=common_idx), method="spearman"))

    # Coverage.
    daily_coverage = combined.groupby(level="date").count()
    avg_coverage = float(daily_coverage.mean())

    # Per-year test performance.
    per_year = []
    combined_dates = combined.index.get_level_values("date")
    for year in sorted(combined_dates.year.unique()):
        mask = combined_dates.year == year
        y_combined = combined.loc[mask]
        y_fwd = test["forward_return"].reindex(y_combined.index)
        bt = run_long_short_backtest(y_combined, y_fwd, transaction_cost=cfg.get("transaction_cost", 0.001))
        per_year.append(
            {
                "year": int(year),
                "sharpe": bt["sharpe"],
                "annualized_return": bt["annualized_return"],
                "cost_adjusted_return": bt["cost_adjusted_return"],
                "max_drawdown": bt["max_drawdown"],
                "turnover": turnover_score(y_combined),
                "ic": ic_score(y_combined, y_fwd),
            }
        )

    # Cost robustness.
    cost_results = []
    for cost in args.transaction_costs:
        bt = run_long_short_backtest(combined, test["forward_return"], transaction_cost=cost)
        cost_results.append(
            {
                "transaction_cost": cost,
                "sharpe": bt["sharpe"],
                "annualized_return": bt["annualized_return"],
                "cost_adjusted_return": bt["cost_adjusted_return"],
                "max_drawdown": bt["max_drawdown"],
            }
        )

    # Full-test summary.
    bt = run_long_short_backtest(combined, test["forward_return"], transaction_cost=cfg.get("transaction_cost", 0.001))
    summary = {
        "test_sharpe": bt["sharpe"],
        "test_annualized_return": bt["annualized_return"],
        "test_cost_adjusted_return": bt["cost_adjusted_return"],
        "test_max_drawdown": bt["max_drawdown"],
        "test_ic": ic_score(combined, test["forward_return"]),
        "test_turnover": turnover_score(combined),
        "avg_daily_coverage": avg_coverage,
        "sector_spearman_corr": sector_corr,
    }

    report = {
        "summary": summary,
        "per_year": per_year,
        "cost_robustness": cost_results,
        "selected_factors": lib.to_dict(orient="records"),
    }
    with open(args.output_dir / "final_audit.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    # Markdown report.
    lines = [
        "# Final Production Audit — Iteration 21",
        "",
        "## Summary (test period)",
        "",
        f"- Test Sharpe: {summary['test_sharpe']:.4f}",
        f"- Test annualized return: {summary['test_annualized_return']:.2%}",
        f"- Test cost-adjusted return: {summary['test_cost_adjusted_return']:.2%}",
        f"- Test max drawdown: {summary['test_max_drawdown']:.2%}",
        f"- Test IC: {summary['test_ic']:.4f}",
        f"- Test turnover: {summary['test_turnover']:.4f}",
        f"- Average daily coverage: {summary['avg_daily_coverage']:.1f} stocks",
        f"- Sector neutrality |Spearman corr|: {abs(summary['sector_spearman_corr']):.4f}",
        "",
        "## Cost Robustness",
        "",
        "| One-way cost | Sharpe | Cost-adj return | Max drawdown |",
        "|---|---|---|---|",
    ]
    for r in cost_results:
        lines.append(
            f"| {r['transaction_cost']:.1%} | {r['sharpe']:.4f} | {r['cost_adjusted_return']:.2%} | {r['max_drawdown']:.2%} |"
        )
    lines += [
        "",
        "## Per-Year Test Performance",
        "",
        "| Year | Sharpe | Ann. return | Cost-adj return | Max drawdown | Turnover | IC |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in per_year:
        lines.append(
            f"| {r['year']} | {r['sharpe']:.4f} | {r['annualized_return']:.2%} | {r['cost_adjusted_return']:.2%} | "
            f"{r['max_drawdown']:.2%} | {r['turnover']:.4f} | {r['ic']:.4f} |"
        )
    lines += ["", "## Selected Factors", ""]
    for _, row in lib.iterrows():
        lines.append(f"- **{row['factor']}**: `{row['expression']}`")
    lines += ["", f"Full JSON: `{args.output_dir / 'final_audit.json'}`"]

    (args.output_dir / "final_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved audit to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
