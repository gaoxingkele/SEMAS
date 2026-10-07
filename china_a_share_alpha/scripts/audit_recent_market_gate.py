"""Select and audit a no-lookahead market trend gate for recent matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import run_t1_exit_backtest
from china_a_share_alpha.scripts.evolve_recent_regime_matching import (
    build_window_contexts,
    return_concentration,
)
from china_a_share_alpha.scripts.evolve_stock_factor_matching import (
    MatchingGenome,
    compose_matched_signal,
    load_or_build_signal_cache,
    matching_weights,
)
from china_a_share_alpha.scripts.run_t1_full_library_audit import (
    _load_snapshot,
    discover_libraries,
)


def continuous_market_trend_gate(panel: pd.DataFrame, window: int) -> pd.Series:
    """Use D-close equal-weight market data to decide whether D+1 entries are allowed."""
    daily_return = panel["return"].groupby(level="date").mean().fillna(0.0)
    market_curve = (1.0 + daily_return).cumprod()
    moving_average = market_curve.rolling(window, min_periods=window).mean()
    return market_curve.ge(moving_average).fillna(False).rename(f"market_ma_{window}")


def select_gate(selection: pd.DataFrame) -> int:
    """Select the gate with the highest worst-window Sharpe, then lowest drawdown."""
    summary = selection.groupby("market_ma").agg(
        worst_sharpe=("sharpe", "min"),
        worst_drawdown=("max_drawdown", "min"),
    )
    eligible = summary.loc[summary["worst_drawdown"].ge(-0.25)]
    if eligible.empty:
        eligible = summary
    return int(
        eligible.sort_values(
            ["worst_sharpe", "worst_drawdown"], ascending=False
        ).index[0]
    )


def _run_window(
    genome: MatchingGenome,
    context: dict[str, Any],
    gate: pd.Series,
    metadata: pd.DataFrame,
    config: dict[str, Any],
    groups: set[str],
) -> dict[str, Any]:
    weights = matching_weights(genome, context["utilities"])
    signal = compose_matched_signal(context["signals"], weights)
    dates = pd.to_datetime(signal.index.get_level_values("date"))
    signal = signal.where(gate.reindex(dates).fillna(False).to_numpy())
    metrics, trades, _ = run_t1_exit_backtest(
        signal,
        context["panel"],
        metadata,
        horizon=int(config["horizon"]),
        selection_fraction=genome.selection_fraction,
        transaction_cost=float(config.get("transaction_cost", 0.001)),
        slippage=float(config.get("slippage", 0.0005)),
        universe_groups=groups,
    )
    return {
        "entry_days": int(gate.loc[context["start"] : context["end"]].sum()),
        "return_concentration": return_concentration(trades),
        **metrics,
    }


def audit(config: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = Path(config["source_campaign_dir"])
    source_receipt = json.loads(
        (source_dir / "campaign_receipt.json").read_text(encoding="utf-8")
    )
    raw_genome = source_receipt["best_genome"]
    genome = MatchingGenome(
        **{
            key: raw_genome[key]
            for key in (
                "top_k",
                "stock_weight",
                "industry_weight",
                "market_weight",
                "temperature",
                "min_observations",
                "selection_fraction",
            )
        }
    )
    panel, metadata, manifest = _load_snapshot(Path(config["snapshot_dir"]))
    libraries = discover_libraries(Path(config["factor_output_root"]))
    signals, _ = load_or_build_signal_cache(
        Path(config["signal_cache"]),
        libraries,
        panel,
        str(manifest.get("snapshot_id")),
        float(config.get("min_factor_coverage", 0.5)),
    )
    gate_windows = [int(value) for value in config.get("market_ma_windows", [5, 10, 20])]
    gates = {window: continuous_market_trend_gate(panel, window) for window in gate_windows}
    selection_contexts = build_window_contexts(
        panel,
        signals,
        metadata,
        config["selection_windows"],
        int(config["horizon"]),
        int(config.get("utility_lookback_days", 504)),
    )
    selection_rows = []
    for context in selection_contexts:
        for window, gate in gates.items():
            selection_rows.append(
                {
                    "evaluation_window": context["name"],
                    "market_ma": window,
                    **_run_window(
                        genome,
                        context,
                        gate,
                        metadata,
                        config,
                        {"main", "innovation", "bse"},
                    ),
                }
            )
    selection = pd.DataFrame(selection_rows)
    selection.to_csv(output_dir / "gate_selection_results.csv", index=False)
    selected_window = select_gate(selection)

    diagnostic_contexts = build_window_contexts(
        panel,
        signals,
        metadata,
        config["diagnostic_windows"],
        int(config["horizon"]),
        int(config.get("utility_lookback_days", 504)),
    )
    diagnostic_rows = []
    for context in diagnostic_contexts:
        for universe, groups in {
            "all_stocks": {"main", "innovation", "bse"},
            "main_board": {"main"},
            "innovation": {"innovation"},
        }.items():
            diagnostic_rows.append(
                {
                    "evaluation_window": context["name"],
                    "universe": universe,
                    "market_ma": selected_window,
                    **_run_window(
                        genome,
                        context,
                        gates[selected_window],
                        metadata,
                        config,
                        groups,
                    ),
                }
            )
    diagnostic = pd.DataFrame(diagnostic_rows)
    diagnostic.to_csv(output_dir / "gated_diagnostic_results.csv", index=False)
    receipt = {
        "snapshot_id": manifest.get("snapshot_id"),
        "source_campaign_dir": str(source_dir),
        "gate_selected_without_diagnostic": True,
        "diagnostic_is_blind": False,
        "researcher_had_prior_diagnostic_exposure": True,
        "selected_market_ma": selected_window,
        "selection_windows": config["selection_windows"],
        "diagnostic_windows": config["diagnostic_windows"],
        "config": config,
    }
    (output_dir / "gate_audit_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    audit(yaml.safe_load(args.config.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
