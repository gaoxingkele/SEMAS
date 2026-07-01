"""Discover available Qlib fields and instruments."""
import os
os.environ["QLIB_SERIAL_MODE"] = "1"

import pandas as pd
import qlib
from qlib.data import D


def decode_sector(x):
    if pd.isna(x):
        return "NA"
    if isinstance(x, bytes):
        try:
            return x.decode("gbk")
        except Exception:
            return x.decode("utf-8", errors="ignore")
    return str(x)


def main() -> int:
    qlib.init(provider_uri="C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data")

    # List instruments
    print("Available instruments:")
    for inst in ["csi300", "csi500", "csi1000", "csi800", "csiall", "all"]:
        try:
            obj = D.instruments(inst)
            df = D.features(obj, ["$close"], start_time="2020-01-01", end_time="2020-01-10")
            print(f"  {inst}: {len(df)} rows, {df.index.get_level_values('instrument').nunique()} symbols")
        except Exception as e:
            print(f"  {inst}: ERROR {e}")

    # Try common fields
    print("\nField probes on csi300 2020-01-01..2020-01-10:")
    fields_to_try = [
        "$sector", "$industry", "$class", "$market_cap", "$total_mv",
        "$circ_mv", "$pe", "$pb", "$ps", "$pcf", "$roe", "$eps",
        "$amount", "$adjclose", "$factor", "$change_pct", "$status",
    ]
    inst = D.instruments("csi300")
    for f in fields_to_try:
        try:
            df = D.features(inst, [f], start_time="2020-01-01", end_time="2020-01-10")
            nan_count = df.isna().sum().sum()
            sample = df.iloc[:, 0].dropna().head(3).tolist()
            decoded = [decode_sector(x) for x in sample]
            print(f"  {f}: len={len(df)}, NaN={nan_count}, sample={decoded}")
        except Exception as e:
            print(f"  {f}: ERROR {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
