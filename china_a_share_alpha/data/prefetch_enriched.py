"""Prefetch enriched Tushare data into local cache."""
import argparse
import yaml
from ..data.tushare_loader import load_tushare_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="yaml config path")
    args = parser.parse_args()
    cfg = yaml.safe_load(open(args.config))
    print("Loading full panel to populate cache (this may take a while)...")
    train_df, test_df = load_tushare_data(cfg)
    print(f"Train panel: {train_df.shape}, Test panel: {test_df.shape}")
    print("done")


if __name__ == "__main__":
    main()
