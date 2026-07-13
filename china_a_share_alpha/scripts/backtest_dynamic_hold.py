"""Backtest a dynamic trim hold strategy vs simple H-day hold.

The user's proposed strategy:
1. At each rebalance date, sort stocks by factor and go long the top 20%.
2. Clear any held stocks that fall into the bottom 20%.
3. Within the H-day holding window, if a held stock's cross-sectional rank drops:
   - 20%-40%  -> sell 30% of current position
   - 40%-60%  -> sell 50% of current position
   - bottom 40% -> clear position
4. If the H-day window expires and the stock is still in the top 20%, keep holding.

We compare this to a baseline that simply rebalances every H days.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_multihizon_audit import _hold_backtest, _smooth, _zscore


def _build_signal(lib: pd.DataFrame, data: pd.DataFrame, smooth_span: int = 10) -> pd.Series:
    frames = {}
    for _, row in lib.iterrows():
        try:
            expr = parse_expression(row["expression"])
            frames[row.get("factor", f"f_{len(frames)}")] = _zscore(expr.eval(data))
        except Exception as exc:
            print(f"  skipping {row.get('factor')}: {exc}")
    if not frames:
        raise ValueError("No valid factors")
    mat = pd.concat(frames.values(), axis=1).dropna()
    weights = np.ones(len(frames)) / len(frames)
    signal = _smooth((mat @ weights).clip(-5, 5), smooth_span)
    return signal


def _dynamic_trim_backtest(
    signal: pd.Series,
    daily_returns: pd.Series,
    horizon: int = 5,
    cost: float = 0.001,
) -> dict:
    """Dynamic trim strategy: trim long positions if rank deteriorates mid-cycle.

    - Rebalance every `horizon` days.
    - Long target: top 20% by factor; short target: bottom 20%.
    - Short leg is held constant over the horizon (no trimming).
    - Long leg is trimmed daily based on cross-sectional percentile:
        * rank 20%-40%  -> position * 0.7
        * rank 40%-60%  -> position * 0.5
        * rank 60%-100% -> exit (position 0)
    - At rebalance, reset long target to full position; if a held stock is still
      in top 20%, continue holding it (i.e. do not force a round-trip).
    """
    dates = daily_returns.index.get_level_values("date").unique().sort_values()
    rebalance = set(range(0, len(dates), horizon))
    # positions: symbol -> {"side": 1 or -1, "w": current weight}
    positions: dict[str, dict] = {}
    records = []
    prev_long_target = set()

    for i, d in enumerate(dates):
        # 1. Expire positions whose horizon ended and are not still top 20%
        expired = [s for s, info in positions.items() if info.get("entry_idx", 0) + horizon <= i]
        try:
            sig = signal.xs(d, level="date")
        except KeyError:
            sig = pd.Series(dtype=float)
        sig = sig.dropna()
        ranked = sig.rank(pct=True, ascending=False) if len(sig) > 0 else pd.Series(dtype=float)
        top20 = set(ranked[ranked <= 0.2].index)
        bot20 = set(ranked[ranked >= 0.8].index)

        for s in expired:
            if s not in top20:
                del positions[s]
            else:
                # Still top 20% -> keep holding, reset entry_idx to current
                positions[s]["entry_idx"] = i

        # 2. Rebalance day
        turnover = 0.0
        if i in rebalance and len(sig) >= 20:
            n = max(1, len(sig) // 5)  # 20%
            longs = sig.sort_values().tail(n).index.tolist()
            shorts = sig.sort_values().head(n).index.tolist()
            new_long_target = set(longs)
            # turnover: change in long target set
            turnover += len(new_long_target ^ prev_long_target) / (len(new_long_target) + len(prev_long_target) + 1e-8)
            # reset positions
            for s in list(positions.keys()):
                if positions[s]["side"] == 1:
                    del positions[s]
            for s in longs:
                positions[s] = {"side": 1, "w": 1.0 / n, "entry_idx": i}
            for s in shorts:
                positions[s] = {"side": -1, "w": 1.0 / n, "entry_idx": i}
            prev_long_target = new_long_target

        # 3. Mid-cycle trimming for long positions
        for s in list(positions.keys()):
            if positions[s]["side"] != 1:
                continue
            if s not in ranked.index:
                del positions[s]
                continue
            r = ranked[s]
            if r >= 0.8:  # bottom 40% (user said last 40%)
                del positions[s]
            elif r >= 0.6:  # 40-60%
                positions[s]["w"] *= 0.5
            elif r >= 0.4:  # 20-40%
                positions[s]["w"] *= 0.7

        # 4. Compute daily P&L
        if positions:
            try:
                dr = daily_returns.xs(d, level="date")
            except KeyError:
                dr = pd.Series(dtype=float)
            pnl = 0.0
            long_w_sum = 0.0
            short_w_sum = 0.0
            for s, info in positions.items():
                if s in dr.index and pd.notna(dr[s]):
                    if info["side"] == 1:
                        pnl += info["w"] * dr[s]
                        long_w_sum += info["w"]
                    else:
                        pnl -= info["w"] * dr[s]
                        short_w_sum += info["w"]
            # Normalize legs
            if long_w_sum > 0:
                pnl /= long_w_sum
            if short_w_sum > 0:
                pnl /= short_w_sum
            # Apply transaction cost proportional to turnover
            pnl -= cost * turnover
            records.append({"date": d, "ret": pnl})

    port = pd.DataFrame(records).set_index("date")["ret"].dropna()
    if port.empty:
        return {"sharpe": 0.0, "annualized_return": 0.0, "cost_adjusted_return": 0.0, "max_drawdown": 0.0}
    sharpe = port.mean() / (port.std() + 1e-12) * np.sqrt(252)
    ann_ret = (1 + port).prod() ** (252 / len(port)) - 1
    cum = (1 + port).cumprod()
    maxdd = (cum / cum.cummax() - 1).min()
    return {
        "sharpe": float(sharpe),
        "annualized_return": float(ann_ret),
        "cost_adjusted_return": float(ann_ret),
        "max_drawdown": float(maxdd),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config with val_date")
    parser.add_argument("--factor-csv", type=Path, required=True)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--cost", type=float, default=0.001)
    parser.add_argument("--smooth-span", type=int, default=10)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print("Loading data...")
    train, val, test = load_tushare_data_with_val(cfg)
    print("Building signal...")
    lib = pd.read_csv(args.factor_csv)
    signal = _build_signal(lib, test, args.smooth_span)

    print("\n=== Baseline simple hold (top/bottom decile) ===")
    base = _hold_backtest(signal, test["return"], args.horizon, args.cost)
    print(base)

    print("\n=== Dynamic trim strategy (top/bottom 20%) ===")
    dyn = _dynamic_trim_backtest(signal, test["return"], args.horizon, args.cost)
    print(dyn)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
