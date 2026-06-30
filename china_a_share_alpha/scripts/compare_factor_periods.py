"""Compare factor performance between two time periods (Tushare audits)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _composite_score(row: pd.Series) -> float:
    ic = row.get("ic", 0)
    sharpe = row.get("sharpe", 0)
    test_ic = row.get("test_ic", 0)
    mdd = row.get("max_drawdown", 0)
    turnover = row.get("turnover", 0)
    mdd_penalty = max(0, -mdd)
    turnover_penalty = min(turnover, 2.0)
    score = (
        0.35 * np.sign(ic) * abs(ic)
        + 0.25 * np.sign(test_ic) * abs(test_ic)
        + 0.25 * sharpe
        + 0.15 * row.get("rank_ic", 0)
        - 0.10 * mdd_penalty
        - 0.05 * turnover_penalty
    )
    return float(score)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period1-csv", type=Path,
                        default=Path("china_a_share_alpha_output/cross_universe_audit/cross_universe_comparison.csv"))
    parser.add_argument("--period1-label", default="2021-2026")
    parser.add_argument("--period2-csv", type=Path,
                        default=Path("china_a_share_alpha_output/cross_universe_audit_2025h1_2026h1/cross_universe_comparison.csv"))
    parser.add_argument("--period2-label", default="2025-2026H1")
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/factor_period_comparison"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    p1 = pd.read_csv(args.period1_csv)
    p1["period"] = args.period1_label
    p1["composite_score"] = p1.apply(_composite_score, axis=1)

    p2 = pd.read_csv(args.period2_csv)
    p2["period"] = args.period2_label
    p2["composite_score"] = p2.apply(_composite_score, axis=1)

    # Aggregate by factor.
    def _agg(df: pd.DataFrame, period: str) -> pd.DataFrame:
        out = df.groupby(["factor", "group"]).agg(
            n_obs=("composite_score", "count"),
            mean_ic=("ic", "mean"),
            mean_rank_ic=("rank_ic", "mean"),
            mean_test_ic=("test_ic", "mean"),
            mean_sharpe=("sharpe", "mean"),
            mean_mdd=("max_drawdown", "mean"),
            mean_turnover=("turnover", "mean"),
            median_composite=("composite_score", "median"),
            mean_composite=("composite_score", "mean"),
            std_composite=("composite_score", "std"),
            universes=("universe", lambda x: ", ".join(sorted(set(x)))),
        ).reset_index()
        out["period"] = period
        return out

    a1 = _agg(p1, args.period1_label)
    a2 = _agg(p2, args.period2_label)

    # Merge side by side.
    merged = pd.merge(
        a1, a2,
        on=["factor", "group"],
        suffixes=(f"_{args.period1_label}", f"_{args.period2_label}"),
        how="outer",
    )

    # Compute changes.
    merged["composite_change"] = merged[f"median_composite_{args.period2_label}"].fillna(0) - merged[f"median_composite_{args.period1_label}"].fillna(0)
    merged["sharpe_change"] = merged[f"mean_sharpe_{args.period2_label}"].fillna(0) - merged[f"mean_sharpe_{args.period1_label}"].fillna(0)
    merged["ic_change"] = merged[f"mean_ic_{args.period2_label}"].fillna(0) - merged[f"mean_ic_{args.period1_label}"].fillna(0)

    # Sort by recent median composite.
    merged = merged.sort_values(f"median_composite_{args.period2_label}", ascending=False).reset_index(drop=True)
    merged["recent_rank"] = np.arange(1, len(merged) + 1)

    csv_path = args.output_dir / "factor_period_comparison.csv"
    merged.to_csv(csv_path, index=False)
    print(f"Comparison CSV: {csv_path}")

    # Markdown report.
    report_lines = [f"# Factor Comparison: {args.period1_label} vs {args.period2_label}\n\n"]
    report_lines.append(f"**Period 1:** {args.period1_label} (train/test split 2024-01-01)\n")
    report_lines.append(f"**Period 2:** {args.period2_label} (train/test split 2025-07-01)\n\n")

    report_lines.append(f"## Top 15 Factors in {args.period2_label} (aggregated across universes)\n\n")
    top_recent = merged.head(15)[[
        "recent_rank", "factor", "group",
        f"median_composite_{args.period2_label}",
        f"mean_sharpe_{args.period2_label}",
        f"mean_ic_{args.period2_label}",
        "composite_change", "sharpe_change", "ic_change",
    ]]
    report_lines.append(top_recent.to_markdown(index=False))
    report_lines.append("\n\n")

    report_lines.append(f"## Factors that Improved Most ({args.period2_label} vs {args.period1_label})\n\n")
    improved = merged.sort_values("composite_change", ascending=False).head(15)[[
        "factor", "group",
        f"median_composite_{args.period1_label}",
        f"median_composite_{args.period2_label}",
        "composite_change", "sharpe_change", "ic_change",
    ]]
    report_lines.append(improved.to_markdown(index=False))
    report_lines.append("\n\n")

    report_lines.append(f"## Factors that Deteriorated Most ({args.period2_label} vs {args.period1_label})\n\n")
    deteriorated = merged.sort_values("composite_change", ascending=True).head(15)[[
        "factor", "group",
        f"median_composite_{args.period1_label}",
        f"median_composite_{args.period2_label}",
        "composite_change", "sharpe_change", "ic_change",
    ]]
    report_lines.append(deteriorated.to_markdown(index=False))
    report_lines.append("\n\n")

    report_path = args.output_dir / "factor_period_comparison_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report: {report_path}")

    summary = {
        "period1": args.period1_label,
        "period2": args.period2_label,
        "n_factors": len(merged),
        "top_recent": merged.iloc[0]["factor"],
        "most_improved": merged.sort_values("composite_change", ascending=False).iloc[0]["factor"],
        "most_deteriorated": merged.sort_values("composite_change", ascending=True).iloc[0]["factor"],
    }
    summary_path = args.output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"Summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
