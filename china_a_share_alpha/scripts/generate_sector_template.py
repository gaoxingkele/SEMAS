"""Generate a sector/market-cap CSV template from a Qlib instrument list.

Users can fill in real sector names and market caps, then point the factor
config at the CSV via `sector_csv: path/to/sectors.csv`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def generate_template(instruments: list[str], output: Path) -> None:
    """Write a CSV template with symbol, sector, market_cap columns."""
    df = pd.DataFrame(
        {
            "symbol": instruments,
            "sector": "",
            "market_cap": "",
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Template written to: {output}")


def load_instruments_from_qlib(instrument_name: str = "csi300") -> list[str]:
    try:
        import qlib
        from qlib.data import D
    except ImportError as exc:
        raise RuntimeError("Qlib is required to load instrument lists.") from exc

    qlib.init()
    df = D.instruments(instrument_name)
    return sorted(df["instrument"].unique().tolist())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sector/market-cap CSV template")
    parser.add_argument("--instrument", default="csi300", help="Qlib instrument name")
    parser.add_argument("--output", type=Path, default="sectors.csv", help="Output CSV path")
    parser.add_argument("--symbols", nargs="+", default=None, help="Optional explicit symbol list")
    args = parser.parse_args()

    if args.symbols:
        instruments = args.symbols
    else:
        instruments = load_instruments_from_qlib(args.instrument)

    generate_template(instruments, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
