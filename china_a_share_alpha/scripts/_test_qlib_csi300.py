"""Test Qlib CSI300 loading via project loader."""
from china_a_share_alpha.data.qlib_loader import _load_qlib_data


def main() -> int:
    cfg = {
        "data_source": "qlib",
        "data_dir": "C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data",
        "instruments": "csi300",
        "start_time": "2018-01-01",
        "end_time": "2023-12-31",
        "split_date": "2021-01-04",
        "forward_period": 5,
        "load_sector": True,
        "load_market_cap": True,
    }
    from china_a_share_alpha.data.qlib_loader import _load_qlib_data as orig_load
    import pandas as pd
    import qlib
    from qlib.data import D

    qlib.init(provider_uri=cfg["data_dir"])
    fields = ["$open", "$high", "$low", "$close", "$volume", "$vwap"]
    df = D.features(D.instruments("csi300"), fields, start_time="2018-01-01", end_time="2023-12-31")
    print("Raw Qlib df:", len(df))
    print(df.head())
    print("Index levels:", df.index.names)

    fwd = D.features(D.instruments("csi300"), ["Ref($close, -5) / $close - 1"], start_time="2018-01-01", end_time="2023-12-31")
    print("Forward return df:", len(fwd))
    print(fwd.head())
    print("Forward return NaN count:", fwd.isna().sum().sum())

    # Reproduce _load_qlib_data step by step
    rename = {"$open": "open", "$high": "high", "$low": "low", "$close": "close", "$volume": "volume", "$vwap": "vwap"}
    df2 = df.rename(columns=rename)
    df2["forward_return"] = fwd.iloc[:, 0].rename("forward_return")
    df2 = df2.reset_index()
    df2 = df2.rename(columns={"instrument": "symbol", "datetime": "date"})
    print("After rename/reset:", len(df2))
    print(df2.head())
    print("NaN per column:", df2.isna().sum().to_dict())
    df2["date"] = pd.to_datetime(df2["date"])
    df2 = df2.set_index(["symbol", "date"]).sort_index()
    print("After set_index:", len(df2))
    df2 = df2.dropna()
    print("After dropna:", len(df2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
