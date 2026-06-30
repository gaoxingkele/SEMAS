"""Rank all factors across Tushare and Qlib cross-universe audits."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _composite_score(row: pd.Series) -> float:
    """Composite score balancing IC, Sharpe, test IC, and penalizing drawdown/turnover."""
    ic = row.get("ic", 0)
    sharpe = row.get("sharpe", 0)
    test_ic = row.get("test_ic", 0)
    mdd = row.get("max_drawdown", 0)
    turnover = row.get("turnover", 0)

    # Normalize signs: higher is better, except mdd which is negative.
    mdd_penalty = max(0, -mdd)  # positive number
    turnover_penalty = min(turnover, 2.0)  # cap

    # Weighted sum. RankIC is more important than raw IC for non-linear factors.
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
    parser.add_argument("--tushare-csv", type=Path,
                        default=Path("china_a_share_alpha_output/cross_universe_audit/cross_universe_comparison.csv"))
    parser.add_argument("--qlib-csv", type=Path,
                        default=Path("china_a_share_alpha_output/qlib_factor_audit/qlib_comparison.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/factor_ranking"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    if args.tushare_csv.exists():
        df = pd.read_csv(args.tushare_csv)
        df["data_source"] = "tushare"
        frames.append(df)
    if args.qlib_csv.exists():
        df = pd.read_csv(args.qlib_csv)
        df["data_source"] = "qlib"
        frames.append(df)

    if not frames:
        raise SystemExit("No input CSVs found.")

    combined = pd.concat(frames, ignore_index=True)
    combined["composite_score"] = combined.apply(_composite_score, axis=1)

    # 1. Per-observation ranking (factor x universe x data_source).
    ranked = combined.sort_values("composite_score", ascending=False).reset_index(drop=True)
    ranked["global_rank"] = np.arange(1, len(ranked) + 1)

    per_obs_path = args.output_dir / "factor_ranking_all_observations.csv"
    ranked.to_csv(per_obs_path, index=False)
    print(f"Per-observation ranking: {per_obs_path}")

    # 2. Aggregated ranking by factor name (median composite score across all observations).
    agg = combined.groupby(["factor", "group"]).agg(
        n_obs=("composite_score", "count"),
        mean_ic=("ic", "mean"),
        median_ic=("ic", "median"),
        mean_rank_ic=("rank_ic", "mean"),
        mean_test_ic=("test_ic", "mean"),
        mean_sharpe=("sharpe", "mean"),
        median_sharpe=("sharpe", "median"),
        mean_mdd=("max_drawdown", "mean"),
        mean_turnover=("turnover", "mean"),
        median_composite=("composite_score", "median"),
        mean_composite=("composite_score", "mean"),
        std_composite=("composite_score", "std"),
        universes=("universe", lambda x: ", ".join(sorted(set(x)))),
        data_sources=("data_source", lambda x: ", ".join(sorted(set(x)))),
    ).reset_index()

    agg["sharpe_ratio_of_score"] = agg["mean_composite"] / (agg["std_composite"] + 1e-8)
    agg["consistency"] = agg["n_obs"] / (agg["std_composite"] + 1)

    # Final aggregated score: median composite with penalty for high volatility across observations.
    agg["final_score"] = agg["median_composite"] - 0.1 * agg["std_composite"]
    agg = agg.sort_values("final_score", ascending=False).reset_index(drop=True)
    agg["aggregate_rank"] = np.arange(1, len(agg) + 1)

    agg_path = args.output_dir / "factor_ranking_aggregated.csv"
    agg.to_csv(agg_path, index=False)
    print(f"Aggregated ranking: {agg_path}")

    # 3. Markdown summary report.
    report_lines = ["# Factor Ranking Across All Audits\n"]
    report_lines.append("Composite score weights:\n")
    report_lines.append("- IC: 35%\n")
    report_lines.append("- Test IC: 25%\n")
    report_lines.append("- Sharpe: 25%\n")
    report_lines.append("- Rank IC: 15%\n")
    report_lines.append("- Penalty: max_drawdown (10%) + turnover (5%)\n\n")

    report_lines.append("## Top 30 Factor-Universes (All Observations)\n\n")
    top_obs = ranked.head(30)[["global_rank", "factor", "group", "universe", "data_source",
                                "ic", "rank_ic", "test_ic", "sharpe", "max_drawdown",
                                "turnover", "composite_score"]]
    report_lines.append(top_obs.to_markdown(index=False))
    report_lines.append("\n\n")

    report_lines.append("## Top 30 Aggregated Factors\n\n")
    top_agg = agg.head(30)[["aggregate_rank", "factor", "group", "n_obs", "mean_ic",
                            "mean_rank_ic", "mean_test_ic", "mean_sharpe", "median_composite",
                            "std_composite", "final_score", "universes", "data_sources"]]
    report_lines.append(top_agg.to_markdown(index=False))
    report_lines.append("\n\n")

    report_path = args.output_dir / "factor_ranking_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report: {report_path}")

    # 4. Summary JSON.
    summary = {
        "total_observations": len(ranked),
        "n_unique_factors": combined["factor"].nunique(),
        "data_sources": combined["data_source"].unique().tolist(),
        "universes": combined["universe"].unique().tolist(),
        "top_factor_observation": ranked.iloc[0][["factor", "universe", "data_source", "composite_score"]].to_dict(),
        "top_factor_aggregated": agg.iloc[0][["factor", "group", "final_score", "mean_sharpe", "mean_ic"]].to_dict(),
    }
    summary_path = args.output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"Summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
