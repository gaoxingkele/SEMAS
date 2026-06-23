"""Example JSON-CLI adapter for a tongshu/xuanze provider."""

from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    fallback = payload.get("fallback", {})
    protocol = payload.get("protocol", {})
    rows = []
    for row in fallback.get("rows", []):
        rows.append(
            {
                **row,
                "twelve_officer": "Open",
                "twenty_eight_mansion": "Well",
                "huangdao": True,
                "rating": "favorable",
                "suitable": ["professional almanac review", "meetings", "planning"],
                "avoid": ["high-stakes decisions without ordinary verification"],
                "risk_notes": ["Example provider fixture; replace with verified tongshu tables."],
            }
        )
    result = {
        "protocol": {"version": protocol.get("version"), "hash": protocol.get("hash")},
        "range": {**fallback.get("range", {}), "count": len(rows)},
        "basis": {
            "provider": "example_xuanze_json_cli",
            "provider_quality": "example_fixture",
            "rule_set": "example_tongshu_protocol",
            "rule_table_source": "example deterministic protocol fixture",
            "rule_table_version": "fixture-1.0",
            "rule_table_sha256": "0" * 64,
            "license_or_review": "example fixture only; replace with reviewed tongshu rule-table license before production",
            "calculation_scope": "twelve officers, twenty-eight mansions, huangdao rating, recommended hours",
        },
        "rows": rows,
        "summary": {
            "favorable_dates": [row["date"] for row in rows],
            "cautious_dates": [],
            "best_date": rows[0]["date"] if rows else None,
        },
        "caution": "Example protocol output only; connect verified tongshu rules for production.",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
