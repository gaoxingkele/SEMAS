"""Local source registry for the mingli five-agent framework.

The registry is intentionally compact. It gives the evaluator stable source IDs
and domain labels so reports can be checked without relying on network access.
Full-text retrieval can later plug into the same IDs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRecord:
    """A source label used to ground symbolic mingli claims."""

    source_id: str
    title: str
    tradition: str
    scope: str
    caution: str


SOURCE_REGISTRY: dict[str, SourceRecord] = {
    "bazi_ziping": SourceRecord(
        source_id="bazi_ziping",
        title="Ziping interpretive tradition",
        tradition="bazi",
        scope="Pillar structure, element balance, pattern/useful-element reasoning.",
        caution="Symbolic tradition label, not empirical validation.",
    ),
    "bazi_sanming": SourceRecord(
        source_id="bazi_sanming",
        title="Sanming classical tradition",
        tradition="bazi",
        scope="Classical BaZi interpretive categories and life-stage symbolism.",
        caution="Use as cultural source context only.",
    ),
    "bazi_shensha": SourceRecord(
        source_id="bazi_shensha",
        title="Shensha symbolic tables",
        tradition="bazi",
        scope="Auxiliary symbolic stars and pattern labels.",
        caution="Do not over-weight auxiliary labels.",
    ),
    "ziwei_palace": SourceRecord(
        source_id="ziwei_palace",
        title="Zi Wei Dou Shu palace tradition",
        tradition="ziwei",
        scope="Ming palace, body palace, twelve-palace symbolic reading.",
        caution="Calendar and hour precision affect symbolic placement.",
    ),
    "ziwei_four_transformations": SourceRecord(
        source_id="ziwei_four_transformations",
        title="Zi Wei four transformations method",
        tradition="ziwei",
        scope="Lu, Quan, Ke, Ji transformation symbolism.",
        caution="Interpret as symbolic tendency, not deterministic event.",
    ),
    "qimen_plate": SourceRecord(
        source_id="qimen_plate",
        title="Qi Men Dun Jia plate tradition",
        tradition="qimen",
        scope="Heaven, earth, human, and spirit plate relationships.",
        caution="Timing symbolism is not tactical certainty.",
    ),
    "qimen_door_star_spirit": SourceRecord(
        source_id="qimen_door_star_spirit",
        title="Door-star-spirit symbolic reading",
        tradition="qimen",
        scope="Door, star, and spirit combinations.",
        caution="Avoid deterministic auspicious/inauspicious claims.",
    ),
    "western_natal": SourceRecord(
        source_id="western_natal",
        title="Western natal chart symbolism",
        tradition="astrology",
        scope="Sun, Moon, Ascendant, planet, sign, and house symbolism.",
        caution="Cultural and interpretive frame only.",
    ),
    "western_transit": SourceRecord(
        source_id="western_transit",
        title="Transit interpretation tradition",
        tradition="astrology",
        scope="Annual and monthly transit themes.",
        caution="Not evidence-based prediction.",
    ),
}


def get_source(source_id: str) -> SourceRecord | None:
    """Return a source record by ID."""
    return SOURCE_REGISTRY.get(source_id)


def source_ids_for_tradition(tradition: str) -> set[str]:
    """Return valid source IDs for one specialist tradition."""
    return {
        source_id
        for source_id, record in SOURCE_REGISTRY.items()
        if record.tradition == tradition
    }


def format_source(source_id: str) -> dict[str, str]:
    """Format a source record for inclusion in report artifacts."""
    record = SOURCE_REGISTRY[source_id]
    return {
        "source_id": record.source_id,
        "title": record.title,
        "tradition": record.tradition,
        "scope": record.scope,
        "caution": record.caution,
    }

