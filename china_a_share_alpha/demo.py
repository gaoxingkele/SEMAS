"""Minimal deterministic demo of China A-share alpha factor evolution.

The demo starts with a raw `close` price factor, which has no predictive
power on synthetic mean-reverting returns. After a few SEMAS evolution rounds
it discovers a ranked rolling-mean factor with positive IC.
"""

from __future__ import annotations

from pathlib import Path

from china_a_share_alpha.run_factor_mining import run


CONFIG_PATH = Path(__file__).parent / "examples" / "sample_config.yaml"


def main() -> int:
    print("=== China A-Share Alpha Evolver Demo ===\n")
    result = run(CONFIG_PATH, max_rounds=4)

    print("\n=== Result ===")
    print(f"Passed: {result['passed']}")
    print(f"Final score: {result['final_score']:.4f}")
    print(f"Train IC: {result['train_ic']:.4f}")
    print(f"Train RankIC: {result['train_rank_ic']:.4f}")
    print(f"Test IC: {result['test_ic']:.4f}")
    print(f"Test RankIC: {result['test_rank_ic']:.4f}")
    print(f"Expression: {result['expression']}")
    print(f"Train backtest: {result['train_backtest']}")
    print(f"Test backtest: {result['test_backtest']}")

    if result["passed"]:
        print("\n[OK] Factor evolved to meet quality threshold.")
    else:
        print("\n[~] Factor improved but did not meet threshold.")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
