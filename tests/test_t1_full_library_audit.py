from pathlib import Path

import pandas as pd

from china_a_share_alpha.scripts.run_t1_full_library_audit import discover_libraries


def test_discover_libraries_collapses_identical_expression_sets(tmp_path: Path) -> None:
    loop = tmp_path / "factor_mining_loop"
    first = loop / "iter_0001" / "combined_library.csv"
    second = loop / "iter_0002" / "combined_library.csv"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    pd.DataFrame({"expression": ["close", "volume"]}).to_csv(first, index=False)
    pd.DataFrame({"expression": ["volume", "close"]}).to_csv(second, index=False)

    found = discover_libraries(tmp_path)

    assert len(found) == 1
    assert found.iloc[0].expression_count == 2
    assert found.iloc[0].source_count == 2
