"""Export the final available daily TOP100 membership snapshot in rank order."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--date", default=None, help="YYYY-MM-DD; defaults to latest available date."
    )
    args = parser.parse_args()
    membership = pd.read_csv(args.membership)
    required = {"date", "daily_rank", "factor_id", "horizon", "iteration", "expression"}
    missing = required.difference(membership.columns)
    if missing:
        raise ValueError(f"Membership file is missing: {sorted(missing)}")
    selected_date = args.date or str(membership["date"].max())
    latest = membership.loc[membership["date"] == selected_date].copy()
    if latest.empty:
        raise ValueError(f"No TOP100 membership for {selected_date}.")
    score_column = "rolling_sharpe" if "rolling_sharpe" in latest.columns else "ranking_score"
    latest = latest.sort_values("daily_rank").reset_index(drop=True)
    latest.insert(0, "top100_rank", range(1, len(latest) + 1))
    latest = latest.rename(columns={score_column: "ranking_score"})
    latest.to_csv(args.output, index=False)
    print(f"date={selected_date} factors={len(latest)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
