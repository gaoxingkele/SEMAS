"""Example JSON-CLI adapter for a Zi Wei provider.

This script is a protocol template. It returns deterministic fixture-like data
so `providers --live` and integration wiring can be tested before connecting a
real Zi Wei engine such as an iztro wrapper.
"""

from __future__ import annotations

import json
import sys


PALACES = [
    "Ming",
    "Siblings",
    "Spouse",
    "Children",
    "Wealth",
    "Health",
    "Travel",
    "Friends",
    "Career",
    "Property",
    "Fortune",
    "Parents",
]


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    fallback = payload.get("fallback", {})
    protocol = payload.get("protocol", {})
    palaces = [
        {
            "index": index,
            "name": name,
            "theme": f"example provider palace: {name}",
            "primary_stars": ["Ziwei", "Wuqu"] if name == "Career" else ["Tianji"],
            "auxiliary_stars": [],
            "markers": ["ming"] if name == "Career" else ["body"] if name == "Wealth" else [],
            "strength": "example",
        }
        for index, name in enumerate(PALACES)
    ]
    result = {
        "protocol": {"version": protocol.get("version"), "hash": protocol.get("hash")},
        "ming_palace": fallback.get("ming_palace") or "Career",
        "body_palace": fallback.get("body_palace") or "Wealth",
        "major_stars": fallback.get("major_stars") or ["Ziwei", "Wuqu"],
        "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
        "calculation_basis": {
            "provider": "bundled ziwei json-cli example",
            "rule_set": "example_ziwei_rules",
            "rule_set_version": "fixture-1.0",
            "rule_source": "bundled protocol fixture",
            "rule_source_sha256": "0" * 64,
            "license_or_review": "protocol fixture only; not production certified",
            "calculation_scope": "twelve palaces, major stars, sihua, major limits, annual activation",
        },
        "palaces": palaces,
        "major_limits": [{"start_year": 1990, "end_year": 1999, "palace": "Career"}],
        "annual_activation": [{"year": 2026, "palace": "Career"}],
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
