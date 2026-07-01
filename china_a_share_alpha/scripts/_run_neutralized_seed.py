"""Helper to run one neutralized factor-loop seed."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from china_a_share_alpha.run_factor_loop import run_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--library-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("china_a_share_alpha/examples/tushare_loop_config.yaml"))
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["seed"] = args.seed
    cfg["neutralize_sector"] = True
    cfg["neutralize_market_cap"] = True
    cfg["output_dir"] = str(args.library_dir / f"seed_{args.seed}")
    cfg["repo_dir"] = str(args.library_dir / f".semas_repo_seed_{args.seed}")

    result = run_config(cfg)
    print(f"Seed {args.seed} completed. Best test_ic={result['best'].get('test_ic')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
