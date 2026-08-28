"""Create a Sharpe-first utility ranking from a frozen external factor audit.

The ranking is descriptive, not a promotion decision.  It preserves every
factor with a finite external Sharpe while flagging insufficient observations
and cross-year instability so that a high but degenerate Sharpe cannot be
mistaken for usable utility.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "factor_id",
    "horizon",
    "iteration",
    "expression",
    "period",
    "sharpe",
    "ic",
    "rank_ic",
    "annualized_return",
    "max_drawdown",
    "turnover",
    "cost_adjusted_return",
    "observations",
}


def _format(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.{digits}f}"


def build_ranking(results: pd.DataFrame, minimum_observations: int) -> pd.DataFrame:
    """Rank full-period rows by external Sharpe and attach year-stability flags."""
    missing = REQUIRED_COLUMNS.difference(results.columns)
    if missing:
        raise ValueError(f"Missing required result columns: {sorted(missing)}")

    full = results.loc[results["period"] == "full"].copy()
    yearly = results.loc[results["period"].isin(["2025", "2026"])].copy()
    yearly["sharpe"] = pd.to_numeric(yearly["sharpe"], errors="coerce")
    yearly["ic"] = pd.to_numeric(yearly["ic"], errors="coerce")
    yearly_pivot = yearly.pivot(
        index="factor_id", columns="period", values=["sharpe", "ic", "observations"]
    )
    yearly_pivot.columns = [f"{metric}_{period}" for metric, period in yearly_pivot.columns]
    full = full.join(yearly_pivot, on="factor_id")

    numeric_columns = [
        "sharpe",
        "ic",
        "rank_ic",
        "annualized_return",
        "max_drawdown",
        "turnover",
        "cost_adjusted_return",
        "observations",
        "sharpe_2025",
        "sharpe_2026",
        "ic_2025",
        "ic_2026",
    ]
    for column in numeric_columns:
        if column in full:
            full[column] = pd.to_numeric(full[column], errors="coerce")

    full["eligible_observations"] = full["observations"] >= minimum_observations
    full["two_year_positive"] = (
        (full["sharpe_2025"] > 0)
        & (full["sharpe_2026"] > 0)
        & (full["ic_2025"] > 0)
        & (full["ic_2026"] > 0)
    )
    full["utility_status"] = np.select(
        [
            full["sharpe"].isna(),
            ~full["eligible_observations"],
            ~full["two_year_positive"],
        ],
        ["invalid_or_degenerate", "insufficient_observations", "cross_year_unstable"],
        default="externally_consistent",
    )
    full = full.sort_values(
        ["sharpe", "observations"], ascending=[False, False], na_position="last"
    )
    full.insert(0, "sharpe_rank", range(1, len(full) + 1))
    eligible = full[full["eligible_observations"] & full["sharpe"].notna()].copy()
    eligible.insert(1, "eligible_sharpe_rank", range(1, len(eligible) + 1))
    full = full.merge(eligible[["factor_id", "eligible_sharpe_rank"]], on="factor_id", how="left")
    columns = [
        "sharpe_rank",
        "eligible_sharpe_rank",
        "utility_status",
        "factor_id",
        "horizon",
        "iteration",
        "sharpe",
        "sharpe_2025",
        "sharpe_2026",
        "ic",
        "rank_ic",
        "ic_2025",
        "ic_2026",
        "annualized_return",
        "cost_adjusted_return",
        "max_drawdown",
        "turnover",
        "observations",
        "expression",
    ]
    return full[columns]


def write_wiki(
    ranking: pd.DataFrame, wiki_path: Path, ranking_path: Path, minimum_observations: int
) -> None:
    consistent = ranking[ranking["utility_status"] == "externally_consistent"]
    lines = [
        "# Sharpe-first external factor utility ranking",
        "",
        "This is a descriptive research ordering, not an automatic promotion rule. "
        "Candidates are ranked by full-period Sharpe from the frozen, stock-disjoint "
        "external CSI500 audit. [source: local artifact "
        "china_a_share_alpha_output/external_unused_csi500_2025_2026/external_validation_results.csv]",
        "",
        f"The raw ranking contains {len(ranking)} frozen factors. `eligible_observations` requires "
        f"at least {minimum_observations:,} factor-return observations; `externally_consistent` also "
        "requires positive Sharpe and IC in both 2025 and 2026. High-Sharpe rows failing these flags "
        "remain visible but are not usable evidence of factor utility.",
        "",
        "## Full Sharpe order",
        "",
        f"The complete machine-readable order is [`external_factor_utility_sharpe_ranking.csv`](../{ranking_path.as_posix()}).",
        "",
        "## Top externally consistent factors",
        "",
        "| Eligible rank | Horizon | Iteration | Full Sharpe | 2025 | 2026 | IC | Max DD | Turnover | Expression |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, row in consistent.head(30).iterrows():
        lines.append(
            f"| {int(row.eligible_sharpe_rank)} | {int(row.horizon)}D | {int(row.iteration)} | "
            f"{_format(row.sharpe)} | {_format(row.sharpe_2025)} | {_format(row.sharpe_2026)} | "
            f"{_format(row.ic, 4)} | {_format(row.max_drawdown)} | {_format(row.turnover)} | "
            f"`{row.expression}` |"
        )
    lines += [
        "",
        "## Utility metrics already implemented",
        "",
        "- **Sharpe**: primary risk-adjusted return ordering used here.",
        "- **IC / RankIC**: linear and rank-based cross-sectional predictive association with future returns.",
        "- **ICIR**: stability of daily IC; implemented in `evaluator/metrics.py`, though not yet persisted in this external audit CSV.",
        "- **Annualized long-short return**: gross five-quantile spread return.",
        "- **Cost-adjusted return**: annualized spread return after the configured transaction-cost estimate.",
        "- **Maximum drawdown**: worst peak-to-trough cumulative spread loss.",
        "- **Turnover**: average signal/portfolio turnover proxy, which determines cost sensitivity.",
        "- **Cross-year stability**: 2025/2026 Sharpe and IC signs, added here as a utility-validity diagnostic.",
        "- **Selection correlation**: existing combination workflows record the maximum selected-factor correlation to prevent redundant portfolios.",
        "",
        "For deployment research, Sharpe must remain primary only within comparable horizons and implementation assumptions; "
        "drawdown, cost, observation coverage, year stability, and correlation are necessary constraints rather than secondary decoration.",
    ]
    wiki_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--minimum-observations", type=int, default=3000)
    args = parser.parse_args()
    results = pd.read_csv(args.results)
    ranking = build_ranking(results, args.minimum_observations)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.wiki.parent.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(args.output_csv, index=False)
    write_wiki(ranking, args.wiki, args.output_csv, args.minimum_observations)
    print(
        f"ranked={len(ranking)} consistent={(ranking.utility_status == 'externally_consistent').sum()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
