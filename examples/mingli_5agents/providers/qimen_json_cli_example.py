"""Example JSON-CLI adapter for a Qi Men provider.

This script is a protocol template. It returns deterministic fixture-like data
so `providers --live` and integration wiring can be tested before connecting a
real Qi Men engine or service.
"""

from __future__ import annotations

import json
import sys


PALACES = [
    ("Kan", "North", "Water"),
    ("Kun", "Southwest", "Earth"),
    ("Zhen", "East", "Wood"),
    ("Xun", "Southeast", "Wood"),
    ("Center", "Center", "Earth"),
    ("Qian", "Northwest", "Metal"),
    ("Dui", "West", "Metal"),
    ("Gen", "Northeast", "Earth"),
    ("Li", "South", "Fire"),
]


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    protocol = payload.get("protocol", {})
    palace_rows = [
        {
            "number": index + 1,
            "name": name,
            "direction": direction,
            "element": element,
            "door": "Open" if index == 0 else "Rest",
            "star": "Tianxin" if index == 0 else "Tianfu",
            "spirit": "Nine Heaven" if index == 0 else "Six Harmony",
            "heaven_stem": "Jia",
            "earth_stem": "Yi",
            "theme": f"example provider palace: {name}",
            "judgment": "example",
        }
        for index, (name, direction, element) in enumerate(PALACES)
    ]
    result = {
        "protocol": {"version": protocol.get("version"), "hash": protocol.get("hash")},
        "duty_door": "Open",
        "duty_star": "Tianxin",
        "spirit": "Nine Heaven",
        "pattern": "example qimen cli plate",
        "calculation_basis": {
            "provider": "bundled qimen json-cli example",
            "rule_set": "example_qimen_rules",
            "rule_set_version": "fixture-1.0",
            "rule_source": "bundled protocol fixture",
            "rule_source_sha256": "0" * 64,
            "license_or_review": "protocol fixture only; not production certified",
            "calculation_scope": "nine palaces, duty door, duty star, spirits, useful gods, annual timing",
        },
        "palaces": palace_rows,
        "useful_gods": {
            "career": _useful("Kan"),
            "wealth": _useful("Kun"),
            "relationship": _useful("Kun"),
            "study": _useful("Kan"),
            "health": _useful("Kun"),
        },
        "annual_timing": [{"year": 2026, "palace": "Kan", "door": "Open", "judgment": "example"}],
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _useful(palace: str) -> dict[str, str]:
    return {
        "palace": palace,
        "door": "Open" if palace == "Kan" else "Rest",
        "star": "Tianxin" if palace == "Kan" else "Tianfu",
        "spirit": "Nine Heaven" if palace == "Kan" else "Six Harmony",
        "judgment": "example",
    }


if __name__ == "__main__":
    raise SystemExit(main())
