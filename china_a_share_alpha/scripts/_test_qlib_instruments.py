"""Test Qlib instrument loading."""
import qlib
from qlib.data import D

qlib.init(provider_uri='C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data')

for inst in ["csi300", "csi500", "csi1000", "csiall", "all"]:
    try:
        df = D.features(D.instruments(inst), ["$close"], start_time="2020-01-01", end_time="2020-12-31")
        print(f"{inst}: {len(df)} rows, {df.index.get_level_values('instrument').nunique()} symbols")
    except Exception as exc:
        print(f"{inst}: ERROR {exc}")
