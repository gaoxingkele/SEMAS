"""Run a checkpointed 5D/10D factor-evolution campaign on a frozen snapshot.

Each horizon evolves independently for a fixed number of rounds. Candidate
selection for the next round uses validation metrics only; test metrics remain
in the per-round artifacts for later audit and never decide the research live
library.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from china_a_share_alpha.scripts.run_factor_mining_loop import run_loop_iteration


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _initial_loop_state(seed_library: Path) -> dict[str, Any]:
    return {
        "iteration": 0,
        "last_run": None,
        "best_test_sharpe": 0.0,
        "best_cost_adjusted_return": 0.0,
        "best_hold_sharpe": 0.0,
        "live_library_path": str(seed_library),
        "history": [],
        "campaign_mode": "validation_selected_research_archive",
    }


def _validation_score(combination_dir: Path) -> float:
    result_path = combination_dir / "combination_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validation = next(item for item in result["results"] if item["period"] == "val")
    return float(validation["sharpe"])


def _promote_research_archive(output_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Advance the campaign seed only when validation Sharpe improves."""
    iteration = int(state["iteration"])
    iteration_dir = output_dir / f"iter_{iteration:04d}"
    candidate = iteration_dir / "combined_library.csv"
    score = _validation_score(iteration_dir / "combination")
    baseline = float(state.get("campaign_best_validation_sharpe", float("-inf")))
    accepted = score > baseline
    if accepted:
        live_path = output_dir / "research_live_library.csv"
        shutil.copyfile(candidate, live_path)
        state["live_library_path"] = str(live_path)
        state["campaign_best_validation_sharpe"] = score
    state.setdefault("campaign_history", []).append(
        {
            "iteration": iteration,
            "validation_sharpe": score,
            "accepted_for_next_round": accepted,
            "candidate_library": str(candidate),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_json(output_dir / "state.json", state)
    return state["campaign_history"][-1]


def _horizon_loop_config(
    *, snapshot_dir: Path, horizon: int, seed_base: int, search: dict[str, Any]
) -> dict[str, Any]:
    data = {
        "data_source": "tushare",
        "snapshot_dir": str(snapshot_dir),
        "val_date": "20230101",
        "forward_period": horizon,
        "population_size": search["population_size"],
        "max_generations": search["max_generations"],
        "patience": search["patience"],
        "elite_fraction": 0.2,
        "crossover_fraction": 0.3,
        "leaderboard_size": search["leaderboard_size"],
        "threshold": 0.005,
        "transaction_cost": 0.001,
        "neutralize_sector": True,
        "neutralize_market_cap": True,
        "sector_csv": None,
    }
    return {
        "seed_base": seed_base,
        "data": data,
        "min_train_ic": 0.001,
        "min_val_ic": 0.0,
        "min_val_sharpe": 0.0,
        "min_test_ic": 0.001,
        "min_test_sharpe": 0.0,
        "max_turnover": 0.6,
        "max_nan_frac": 0.5,
        "min_daily_coverage": 0.5,
        "semantic_dedup_corr_threshold": 0.95,
        "top_n": 10,
        "weight_method": "equal",
        "smooth_span": 10,
        "sort_by": "val_ic",
        "max_pairwise_corr": 0.4,
        "promotion_enabled": False,
        "use_hold_sharpe_gate": False,
        "min_train_sharpe_gate": -999.0,
        "min_cleaned_gate": 1,
        "max_selection_correlation_gate": 1.0,
    }


def _write_round_configs(output_dir: Path, template: dict[str, Any]) -> dict[str, Any]:
    config_dir = output_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    evolution_path = config_dir / "evolution.yaml"
    data_path = config_dir / "evaluation.yaml"
    yaml.safe_dump(template["data"], evolution_path.open("w", encoding="utf-8"), sort_keys=False)
    yaml.safe_dump(template["data"], data_path.open("w", encoding="utf-8"), sort_keys=False)
    cfg = {key: value for key, value in template.items() if key != "data"}
    cfg["evolution_config"] = str(evolution_path)
    cfg["data_config"] = str(data_path)
    return cfg


def run_campaign(config: dict[str, Any]) -> None:
    snapshot_dir = Path(config["snapshot_dir"])
    campaign_root = Path(config["output_dir"])
    search = config.get(
        "search",
        {"population_size": 16, "max_generations": 5, "patience": 2, "leaderboard_size": 30},
    )
    rounds = int(config.get("rounds", 30))
    tracks = {
        "5d": {"horizon": 5, "seed_base": 5000, "seed_library": Path(config["seed_library_5d"])},
        "10d": {
            "horizon": 10,
            "seed_base": 10000,
            "seed_library": Path(config["seed_library_10d"]),
        },
    }
    history_path = campaign_root / "campaign_history.json"
    campaign_history = _read_json(history_path, {"rounds": []})

    for _ in range(rounds):
        for name, track in tracks.items():
            output_dir = campaign_root / name
            output_dir.mkdir(parents=True, exist_ok=True)
            state_path = output_dir / "state.json"
            state = _read_json(state_path, _initial_loop_state(track["seed_library"]))
            if not state_path.exists():
                _write_json(state_path, state)
            template = _horizon_loop_config(
                snapshot_dir=snapshot_dir,
                horizon=track["horizon"],
                seed_base=track["seed_base"],
                search=search,
            )
            loop_cfg = _write_round_configs(output_dir, template)
            print(f"[{name}] campaign round {state['iteration'] + 1}/{rounds}", flush=True)
            state = run_loop_iteration(loop_cfg, output_dir)
            archive_event = _promote_research_archive(output_dir, state)
            campaign_history["rounds"].append({"horizon": name, **archive_event})
            _write_json(history_path, campaign_history)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 5D and 10D frozen-snapshot evolution campaigns"
    )
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    with args.config.open("r", encoding="utf-8") as handle:
        run_campaign(yaml.safe_load(handle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
