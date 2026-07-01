"""Smoke test for Qlib data loading."""
import pandas as pd
from china_a_share_alpha.data.qlib_loader import load_data


def main() -> int:
    cfg = {
        "data_source": "qlib",
        "data_dir": "C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data",
        "instruments": "csi300",
        "start_time": "2020-01-01",
        "end_time": "2020-12-31",
        "split_date": "2020-07-01",
        "forward_period": 5,
    }
    train, test = load_data(cfg)
    print("Train rows:", len(train), "symbols:", train.index.get_level_values("symbol").nunique())
    print("Test rows:", len(test), "symbols:", test.index.get_level_values("symbol").nunique())
    print("Columns:", train.columns.tolist())
    print(train.head())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
