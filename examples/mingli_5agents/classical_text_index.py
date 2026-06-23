"""Auditable classical-text index for source-grounded mingli evidence.

The index uses copyright-safe paraphrased seed records by default and can be
extended with JSONL files from a local corpus directory. Each passage keeps
provenance metadata so source review can audit where a symbolic claim came from.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ClassicalPassage:
    """A searchable, provenance-bearing passage tied to one source ID."""

    source_id: str
    passage_id: str
    title: str
    tradition: str
    keywords: tuple[str, ...]
    summary: str
    provenance: dict[str, str]
    caution: str


SEED_PASSAGES: tuple[ClassicalPassage, ...] = (
    ClassicalPassage(
        source_id="bazi_ziping",
        passage_id="seed_bazi_ziping_balance",
        title="Ziping balance and useful-element method",
        tradition="bazi",
        keywords=("pillar", "element", "balance", "useful", "pattern"),
        summary="Ziping-style analysis treats the four pillars as a structured symbolic system, then weighs element balance, seasonal strength, pattern, and useful-element selection.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Tradition-grounded symbolism, not empirical proof.",
    ),
    ClassicalPassage(
        source_id="bazi_sanming",
        passage_id="seed_bazi_sanming_life_stage",
        title="Sanming pattern and life-stage framing",
        tradition="bazi",
        keywords=("classical", "life-stage", "pattern", "luck", "cycle"),
        summary="Sanming-oriented readings organize pillar relationships, pattern language, and luck-cycle symbolism as staged interpretive context.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Do not convert symbolic pattern labels into certain predictions.",
    ),
    ClassicalPassage(
        source_id="bazi_shensha",
        passage_id="seed_bazi_shensha_auxiliary",
        title="Shensha auxiliary marker usage",
        tradition="bazi",
        keywords=("auxiliary", "stars", "shensha", "secondary", "symbolic"),
        summary="Shensha tables are best treated as auxiliary symbolic markers that can enrich, but should not override, core pillar and element analysis.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Do not over-weight auxiliary star labels.",
    ),
    ClassicalPassage(
        source_id="ziwei_palace",
        passage_id="seed_ziwei_twelve_palaces",
        title="Zi Wei twelve-palace frame",
        tradition="ziwei",
        keywords=("palace", "ming", "body", "twelve", "relationship"),
        summary="Zi Wei Dou Shu organizes interpretation through the Ming palace, body palace, and twelve-palace relationships for life-domain symbolism.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Birth-hour and calendar conversion affect palace placement.",
    ),
    ClassicalPassage(
        source_id="ziwei_four_transformations",
        passage_id="seed_ziwei_four_transformations",
        title="Zi Wei four transformations",
        tradition="ziwei",
        keywords=("lu", "quan", "ke", "ji", "transformation"),
        summary="The four transformations provide symbolic movement labels for gain, authority, reputation or study, and friction or constraint.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Treat transformations as tendencies, not guaranteed events.",
    ),
    ClassicalPassage(
        source_id="qimen_plate",
        passage_id="seed_qimen_layered_plate",
        title="Qi Men layered plate method",
        tradition="qimen",
        keywords=("heaven", "earth", "human", "spirit", "plate", "timing"),
        summary="Qi Men analysis reads heaven, earth, human, and spirit layers together to relate symbolic timing, direction, role, and circumstance.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Timing symbolism is not tactical certainty.",
    ),
    ClassicalPassage(
        source_id="qimen_door_star_spirit",
        passage_id="seed_qimen_door_star_spirit",
        title="Qi Men door-star-spirit combinations",
        tradition="qimen",
        keywords=("door", "star", "spirit", "combination", "judgment"),
        summary="Door, star, and spirit combinations are read jointly, so a single auspicious or inauspicious label should not be isolated from the plate context.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "classical_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Avoid deterministic auspicious or inauspicious claims.",
    ),
    ClassicalPassage(
        source_id="western_natal",
        passage_id="seed_western_natal_symbols",
        title="Western natal symbolism",
        tradition="astrology",
        keywords=("sun", "moon", "ascendant", "planet", "house", "sign"),
        summary="Western natal chart interpretation commonly combines planets, signs, houses, and angles as symbolic descriptors of temperament and life topics.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "modern_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Use as cultural symbolism, not scientific diagnosis.",
    ),
    ClassicalPassage(
        source_id="western_transit",
        passage_id="seed_western_transit_cycles",
        title="Western transit cycle framing",
        tradition="astrology",
        keywords=("transit", "annual", "monthly", "cycle", "planet"),
        summary="Transit interpretation frames annual and monthly themes through moving-planet symbolism and house activation.",
        provenance={
            "corpus": "built_in_seed",
            "source_type": "modern_method_summary",
            "citation_policy": "paraphrase_only",
        },
        caution="Not evidence-based prediction.",
    ),
)


def load_classical_index(corpus_dir: Path | None = None) -> tuple[ClassicalPassage, ...]:
    """Load built-in seed passages plus optional JSONL corpus records."""
    directory = corpus_dir or _corpus_dir_from_env()
    records = list(SEED_PASSAGES)
    if directory and directory.exists():
        records.extend(_load_jsonl_records(directory))
    return tuple(records)


def retrieve_classical_passages(
    source_id: str,
    query: str = "",
    *,
    limit: int = 2,
    corpus_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Retrieve provenance-bearing classical passages by source ID."""
    query_terms = _terms(query)
    candidates = [item for item in load_classical_index(corpus_dir) if item.source_id == source_id]
    scored = []
    for item in candidates:
        overlap = len(query_terms & set(item.keywords))
        scored.append((overlap, item.passage_id, item))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [_to_evidence_dict(item) for _score, _passage_id, item in scored[:limit]]


def classical_index_audit(corpus_dir: Path | None = None) -> dict[str, Any]:
    """Return a compact audit manifest for the loaded classical-text index."""
    records = load_classical_index(corpus_dir)
    payload = json.dumps([asdict(item) for item in records], sort_keys=True, ensure_ascii=True)
    external_count = sum(1 for item in records if item.provenance.get("corpus") != "built_in_seed")
    return {
        "status": "ready",
        "record_count": len(records),
        "seed_record_count": len(SEED_PASSAGES),
        "external_record_count": external_count,
        "source_ids": sorted({item.source_id for item in records}),
        "traditions": sorted({item.tradition for item in records}),
        "content_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "corpus_dir": str(corpus_dir or _corpus_dir_from_env() or ""),
        "copyright_policy": "paraphrase_or_public_domain_metadata_only",
    }


def _to_evidence_dict(item: ClassicalPassage) -> dict[str, Any]:
    return {
        "source_id": item.source_id,
        "snippet_id": item.passage_id,
        "keywords": item.keywords,
        "note": item.summary,
        "caution": item.caution,
        "provenance": item.provenance,
        "title": item.title,
        "tradition": item.tradition,
        "excerpt_type": "paraphrase",
    }


def _load_jsonl_records(directory: Path) -> list[ClassicalPassage]:
    records: list[ClassicalPassage] = []
    for path in sorted(directory.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(_record_from_payload(payload, path, line_number))
    return records


def _record_from_payload(payload: dict[str, Any], path: Path, line_number: int) -> ClassicalPassage:
    required = {"source_id", "passage_id", "title", "tradition", "keywords", "summary", "caution"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"{path}:{line_number} missing required fields: {', '.join(missing)}")
    provenance = dict(payload.get("provenance") or {})
    provenance.setdefault("corpus", path.stem)
    provenance.setdefault("source_file", str(path))
    provenance.setdefault("line", str(line_number))
    provenance.setdefault("citation_policy", "paraphrase_only")
    return ClassicalPassage(
        source_id=str(payload["source_id"]),
        passage_id=str(payload["passage_id"]),
        title=str(payload["title"]),
        tradition=str(payload["tradition"]),
        keywords=tuple(str(item).lower() for item in payload["keywords"]),
        summary=str(payload["summary"]),
        provenance=provenance,
        caution=str(payload["caution"]),
    )


def _terms(query: str) -> set[str]:
    return {term.strip(".,:;!?()[]{}").lower() for term in query.split() if term.strip()}


def _corpus_dir_from_env() -> Path | None:
    value = os.getenv("SEMAS_CLASSIC_CORPUS_DIR")
    return Path(value) if value else None
