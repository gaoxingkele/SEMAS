"""Runnable SEMAS implementation of the five-agent mingli architecture."""

from __future__ import annotations

import json
import hashlib
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from semas.mutator.mutator import Mutator
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox

from examples.mingli_5agents.classical_text_index import classical_index_audit
from examples.mingli_5agents.evolution import MingliPopulationEvolver
from examples.mingli_5agents.evaluators.capability_audit_evaluator import capability_audit_score
from examples.mingli_5agents.evaluators.chinese_render_evaluator import chinese_render_score
from examples.mingli_5agents.evaluators.citation_evaluator import citation_score
from examples.mingli_5agents.evaluators.consistency_evaluator import consistency_score
from examples.mingli_5agents.evaluators.evidence_provenance_evaluator import evidence_provenance_score
from examples.mingli_5agents.evaluators.feedback_evaluator import feedback_score
from examples.mingli_5agents.evaluators.provider_contract_evaluator import provider_contract_score
from examples.mingli_5agents.evaluators.report_schema_evaluator import report_schema_score
from examples.mingli_5agents.evaluators.schema_contract_evaluator import schema_contract_score
from examples.mingli_5agents.evaluators.safety_evaluator import safety_score
from examples.mingli_5agents.evaluators.workflow_evaluator import workflow_score
from examples.mingli_5agents.evidence import retrieve_many
from examples.mingli_5agents.knowledge_base import SOURCE_REGISTRY, format_source
from examples.mingli_5agents.llm_synthesis import synthesize_with_llm
from examples.mingli_5agents.memory import MingliFeedbackMemory
from examples.mingli_5agents.provider_contracts import chart_contract
from examples.mingli_5agents.provider_protocols import provider_protocol_document
from examples.mingli_5agents.report_renderers import render_chinese_markdown
from examples.mingli_5agents.topic_synthesis import build_topic_synthesis
from examples.mingli_5agents.tools.annual_luck import build_annual_luck
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.auspicious_calendar import build_auspicious_calendar
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.monthly_luck import build_monthly_luck
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart
from examples.mingli_5agents.workflow import MingliWorkflow, workflow_from_meta


GENOME_FILES = [
    "orchestrator_v1.yaml",
    "bazi_v1.yaml",
    "ziwei_v1.yaml",
    "qimen_v1.yaml",
    "astrology_v1.yaml",
]


def _stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _annual_topic_evidence_complete(topic: dict[str, Any]) -> bool:
    return (
        isinstance(topic.get("message"), str)
        and bool(topic.get("message"))
        and topic.get("source") == "annual_luck.rows"
        and isinstance(topic.get("source_row_index"), int)
        and isinstance(topic.get("source_field"), str)
        and isinstance(topic.get("bazi_evidence_sha256"), str)
        and len(topic.get("bazi_evidence_sha256", "")) == 64
        and isinstance(topic.get("provider_quality"), str)
        and bool(topic.get("provider_quality"))
        and isinstance(topic.get("boundary"), str)
        and bool(topic.get("boundary"))
    )


def _monthly_topic_evidence_complete(topic: dict[str, Any]) -> bool:
    return (
        isinstance(topic.get("message"), str)
        and bool(topic.get("message"))
        and topic.get("source") == "monthly_luck.rows"
        and isinstance(topic.get("source_row_index"), int)
        and isinstance(topic.get("source_field"), str)
        and isinstance(topic.get("bazi_evidence_sha256"), str)
        and len(topic.get("bazi_evidence_sha256", "")) == 64
        and isinstance(topic.get("provider_quality"), str)
        and bool(topic.get("provider_quality"))
        and isinstance(topic.get("boundary"), str)
        and bool(topic.get("boundary"))
    )


def _current_major_luck(deep_analysis: dict[str, Any]) -> str:
    """Return a compact current major-luck label for BaZi specialist text."""
    current_year = date.today().year
    for item in deep_analysis.get("major_luck", []):
        if item.get("start_year", 0) <= current_year <= item.get("end_year", 0):
            label = item.get("ganzhi") or "pre-luck"
            return f"{label} {item.get('start_year')}-{item.get('end_year')}"
    return "outside listed major-luck range"


def _current_ziwei_major_limit(deep_analysis: dict[str, Any]) -> str:
    """Return a compact current Zi Wei major-limit label."""
    current_year = date.today().year
    for item in deep_analysis.get("major_limits", []):
        if item.get("start_year", 0) <= current_year <= item.get("end_year", 0):
            return f"{item.get('palace')} {item.get('start_year')}-{item.get('end_year')}"
    return "outside listed major-limit range"


class MingliFiveAgentSystem:
    """Deterministic executor for coordinator + four specialist agents."""

    specialist_names = {
        "bazi": "bazi_analyst",
        "ziwei": "ziwei_analyst",
        "qimen": "qimen_analyst",
        "astrology": "astrology_analyst",
    }

    def __init__(self, repo: GenomeRepository):
        self.repo = repo

    def __call__(self, coordinator: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
        birth = normalize_birth_input(task_input["birth"])
        if task_input.get("calendar_provider") and not birth.get("calendar_provider"):
            birth = {**birth, "calendar_provider": task_input["calendar_provider"]}
        for key in ("annual_start_year", "annual_end_year"):
            if task_input.get(key) is not None and birth.get(key) is None:
                birth = {**birth, key: task_input[key]}
        strategies = set(coordinator.meta.get("mingli_evolution", []))
        workflow = workflow_from_meta(coordinator.meta)
        reports = {
            "bazi": self._bazi_report(birth),
            "ziwei": self._ziwei_report(birth),
            "qimen": self._qimen_report(birth),
            "astrology": self._astrology_report(birth),
        }
        discussion = self._discuss(reports, strategies, workflow)
        votes = self._vote(reports, workflow)
        source_review = self._review_sources(reports, workflow)
        conflicts = self._find_conflicts(reports, workflow)
        annual_luck = build_annual_luck(
            birth,
            reports["bazi"]["chart"],
            start_year=task_input.get("annual_start_year"),
            end_year=task_input.get("annual_end_year"),
        )
        monthly_luck = build_monthly_luck(
            birth,
            reports["bazi"]["chart"],
            years=task_input.get("monthly_years"),
        )
        auspicious_calendar = build_auspicious_calendar(
            {**birth, "useful_element": reports["bazi"]["chart"].get("useful_element")},
            start_date=task_input.get("auspicious_start_date"),
            end_date=task_input.get("auspicious_end_date"),
        )
        final_report = self._build_final_report(
            coordinator,
            task_input,
            birth,
            reports,
            discussion,
            votes,
            source_review,
            conflicts,
            strategies,
            workflow,
            annual_luck,
            monthly_luck,
            auspicious_calendar,
        )
        rendered_reports = {
            "en": self._render_final_report(final_report),
            "zh": render_chinese_markdown(final_report),
        }
        final_report["rendered_reports"] = rendered_reports
        language = task_input.get("language", "en")
        llm_config = task_input.get("llm_synthesis", {})
        if isinstance(llm_config, bool):
            llm_enabled = llm_config
        elif isinstance(llm_config, dict):
            llm_enabled = bool(llm_config.get("enabled", False))
        else:
            llm_enabled = False
        final_report["llm_synthesis"] = synthesize_with_llm(
            final_report,
            language=language,
            enabled=llm_enabled,
        )
        adapted_to_feedback = (
            coordinator.version > 1
            or coordinator.system_prompt.startswith("[MUTATED]")
            or "feedback_adaptation" in strategies
        )
        return {
            "output": rendered_reports.get(language, rendered_reports["en"]),
            "final_report": final_report,
            "specialists": reports,
            "discussion": discussion,
            "votes": votes,
            "source_review": source_review,
            "conflicts": conflicts,
            "adapted_to_feedback": adapted_to_feedback,
            "workflow": workflow.to_meta(),
            "version": coordinator.version,
        }

    def _bazi_report(self, birth: dict[str, Any]) -> dict[str, Any]:
        chart = build_bazi_chart(birth)
        deep = chart["deep_analysis"]
        current_luck = _current_major_luck(deep)
        month_ten_god = deep["ten_gods"]["month"]["stem"]
        return self._with_layers({
            "agent": self.specialist_names["bazi"],
            "chart": chart,
            "macro": f"BaZi structure is {chart['structure']} with {chart['dominant_element']} emphasis.",
            "micro": (
                f"Day master: {deep['day_master']}; month stem ten-god: {month_ten_god}; "
                f"useful element focus: {chart['useful_element']}. Pillars: {chart['pillars']}."
            ),
            "yearly": (
                "Yearly trend should be read through element balance, ten-god emphasis, "
                f"and major-luck interaction ({current_luck})."
            ),
            "monthly": "Monthly focus should watch the dominant-useful element tension.",
            "uncertainty": "Symbolic BaZi reading; not deterministic prediction.",
            "sources": [format_source(source_id) for source_id in chart["sources"]],
        })

    def _ziwei_report(self, birth: dict[str, Any]) -> dict[str, Any]:
        chart = build_ziwei_chart(birth)
        deep = chart["deep_analysis"]
        current_limit = _current_ziwei_major_limit(deep)
        return self._with_layers({
            "agent": self.specialist_names["ziwei"],
            "chart": chart,
            "macro": f"Zi Wei Ming palace sits at {chart['ming_palace']} with {chart['major_stars'][0]} emphasis.",
            "micro": (
                f"Body palace {chart['body_palace']}; twelve palace rows: {len(deep['palaces'])}; "
                f"four transformations {chart['transformations']} shape detail."
            ),
            "yearly": (
                "Yearly trend is interpreted through palace activation, transformation movement, "
                f"and major-limit focus ({current_limit})."
            ),
            "monthly": "Monthly refinement focuses on activated palace themes.",
            "uncertainty": "Symbolic Zi Wei reading; chart precision depends on calendar conversion.",
            "sources": [format_source(source_id) for source_id in chart["sources"]],
        })

    def _qimen_report(self, birth: dict[str, Any]) -> dict[str, Any]:
        chart = build_qimen_chart(birth)
        deep = chart["deep_analysis"]
        career_useful = deep["useful_gods"]["career"]
        return self._with_layers({
            "agent": self.specialist_names["qimen"],
            "chart": chart,
            "macro": f"Qi Men pattern suggests {chart['pattern']} through {chart['duty_door']} door.",
            "micro": (
                f"Nine-palace plate has {len(deep['palaces'])} rows; duty door palace "
                f"{deep['duty']['door_palace']}; career useful god sits in {career_useful['palace']}."
            ),
            "yearly": "Yearly trend is framed through palace timing, useful-god placement, and pattern flags.",
            "monthly": "Monthly refinement watches door-star-spirit resonance.",
            "uncertainty": "Symbolic Qi Men reading; not a tactical guarantee.",
            "sources": [format_source(source_id) for source_id in chart["sources"]],
        })

    def _astrology_report(self, birth: dict[str, Any]) -> dict[str, Any]:
        chart = build_astrology_chart(birth)
        deep = chart["deep_analysis"]
        active_transit = deep["annual_transits"][-1] if deep["annual_transits"] else {}
        return self._with_layers({
            "agent": self.specialist_names["astrology"],
            "chart": chart,
            "macro": f"Western chart highlights Sun {chart['sun']} and Ascendant {chart['ascendant']}.",
            "micro": (
                f"Moon {chart['moon']} adds emotional tone; natal planets: {len(deep['planets'])}; "
                f"major aspects tracked: {len(deep['aspects'])}."
            ),
            "yearly": (
                "Yearly trend is interpreted through transit symbolism, activated houses, "
                f"and current focus: {active_transit.get('focus', chart['annual_theme'])}."
            ),
            "monthly": "Monthly focus follows lunar and personal-cycle themes.",
            "uncertainty": "Symbolic astrology reading; not evidence-based prediction.",
            "sources": [format_source(source_id) for source_id in chart["sources"]],
        })

    def _with_layers(self, report: dict[str, Any]) -> dict[str, Any]:
        """Attach machine-readable macro/micro/year/month/uncertainty layers."""
        source_ids = [
            source["source_id"]
            for source in report.get("sources", [])
            if isinstance(source, dict) and source.get("source_id")
        ]
        labels = {
            "macro": "overall pattern",
            "micro": "chart-detail interpretation",
            "yearly": "annual timing interpretation",
            "monthly": "monthly refinement",
            "uncertainty": "scope and uncertainty boundary",
        }
        report["layers"] = {
            key: {
                "level": key,
                "focus": labels[key],
                "text": str(report[key]),
                "source_ids": source_ids,
                "evidence_required": key != "uncertainty",
                "boundary_type": "uncertainty" if key == "uncertainty" else "symbolic_interpretation",
            }
            for key in labels
        }
        return report

    def _discuss(
        self,
        reports: dict[str, dict[str, Any]],
        strategies: set[str],
        workflow: MingliWorkflow,
    ) -> list[dict[str, str]]:
        discussion = [
            {"round": "claim", "speaker": name, "point": report["macro"]}
            for name, report in reports.items()
        ]
        for round_idx in range(2, workflow.discussion_rounds + 1):
            discussion += [
                {
                    "round": f"discussion_{round_idx}",
                    "speaker": name,
                    "point": f"{name} refines yearly/monthly view: {report['yearly']} {report['monthly']}",
                }
                for name, report in reports.items()
            ]
        discussion.append(
            {
                "round": "challenge",
                "speaker": "mingli_orchestrator",
                "point": "Cross-system conclusions must keep uncertainty and source labels.",
            }
        )
        if workflow.cross_check_enabled or "debate_depth" in strategies:
            discussion += [
                {
                    "round": "cross_check",
                    "speaker": name,
                    "point": f"{name} checks whether other systems conflict with: {report['micro']}",
                }
                for name, report in reports.items()
            ]
        if workflow.reconciliation_enabled or "debate_depth" in strategies:
            discussion.append(
                {
                    "round": "reconciliation",
                    "speaker": "mingli_orchestrator",
                    "point": "Conflicts are preserved as uncertainty instead of being forced into one answer.",
                }
            )
        return discussion

    def _vote(
        self,
        reports: dict[str, dict[str, Any]],
        workflow: MingliWorkflow,
    ) -> dict[str, Any]:
        votes = {}
        for name, report in reports.items():
            votes[name] = {
                "stance": "support",
                "reason": f"{name} supports final synthesis if it preserves: {report['uncertainty']}",
                "weight": 1.0,
            }
        support = sum(1 for vote in votes.values() if vote["stance"] == "support")
        claim_votes = self._claim_votes(reports, workflow)
        passed_claims = sum(1 for item in claim_votes if item["passed"])
        votes["_summary"] = {
            "support_ratio": support / len(reports),
            "threshold": workflow.vote_threshold,
            "passed": support / len(reports) >= workflow.vote_threshold,
        }
        votes["_claims"] = claim_votes
        votes["_audit"] = {
            "claim_count": len(claim_votes),
            "passed_claim_count": passed_claims,
            "claim_pass_rate": passed_claims / len(claim_votes) if claim_votes else 0.0,
            "threshold": workflow.vote_threshold,
            "evidence_bound": all(item["source_ids"] for item in claim_votes),
            "minority_positions_preserved": any(item["challenges"] for item in claim_votes),
        }
        return votes

    def _claim_votes(
        self,
        reports: dict[str, dict[str, Any]],
        workflow: MingliWorkflow,
    ) -> list[dict[str, Any]]:
        """Create claim-level voting records for auditable multi-agent synthesis."""
        claim_specs = [
            {
                "id": "macro_structure",
                "topic": "overall_pattern",
                "claim": "Final synthesis may combine the four macro readings only with explicit uncertainty.",
                "primary_agents": ["bazi", "ziwei", "qimen", "astrology"],
                "challenge_agents": [],
            },
            {
                "id": "yearly_timing",
                "topic": "annual_luck",
                "claim": "Yearly timing claims require BaZi annual rows and cross-system timing checks.",
                "primary_agents": ["bazi", "qimen", "astrology"],
                "challenge_agents": ["ziwei"],
            },
            {
                "id": "relationship_family",
                "topic": "relationship_children_family",
                "claim": "Relationship and family language must stay symbolic and avoid deterministic decisions.",
                "primary_agents": ["ziwei", "bazi", "astrology"],
                "challenge_agents": ["qimen"],
            },
            {
                "id": "career_finance_boundary",
                "topic": "career_finance",
                "claim": "Career and finance themes may be surfaced as reflective prompts, not advice.",
                "primary_agents": ["bazi", "qimen", "ziwei"],
                "challenge_agents": ["astrology"],
            },
        ]
        claim_votes = []
        for spec in claim_specs:
            source_ids = sorted(
                {
                    source_id
                    for agent in spec["primary_agents"]
                    for source_id in reports.get(agent, {}).get("layers", {}).get("yearly", {}).get("source_ids", [])
                }
                | {
                    source_id
                    for agent in spec["challenge_agents"]
                    for source_id in reports.get(agent, {}).get("layers", {}).get("uncertainty", {}).get("source_ids", [])
                }
            )
            primary_support_ratio = len(spec["primary_agents"]) / len(reports)
            deliberation_ratio = (len(spec["primary_agents"]) + len(spec["challenge_agents"])) / len(reports)
            claim_votes.append(
                {
                    "id": spec["id"],
                    "topic": spec["topic"],
                    "claim": spec["claim"],
                    "supporters": spec["primary_agents"],
                    "challenges": [
                        {
                            "agent": agent,
                            "reason": reports[agent]["uncertainty"],
                            "preserved_as": "boundary_condition",
                        }
                        for agent in spec["challenge_agents"]
                    ],
                    "primary_support_ratio": primary_support_ratio,
                    "support_ratio": deliberation_ratio,
                    "threshold": workflow.vote_threshold,
                    "passed": deliberation_ratio >= workflow.vote_threshold,
                    "source_ids": source_ids,
                    "decision": "include_with_boundary" if source_ids else "hold_for_source_review",
                }
            )
        return claim_votes

    def _review_sources(
        self,
        reports: dict[str, dict[str, Any]],
        workflow: MingliWorkflow,
    ) -> dict[str, Any]:
        source_ids = sorted(
            {
                source["source_id"]
                for report in reports.values()
                for source in report["sources"]
                if isinstance(source, dict) and source.get("source_id")
            }
        )
        unknown = [source_id for source_id in source_ids if source_id not in SOURCE_REGISTRY]
        traditions = sorted(
            {
                SOURCE_REGISTRY[source_id].tradition
                for source_id in source_ids
                if source_id in SOURCE_REGISTRY
            }
        )
        required = {"bazi", "ziwei", "qimen", "astrology"}
        missing = sorted(required - set(traditions))
        min_sources = 8 if workflow.source_review_strictness == "standard" else 9
        evidence_query = " ".join(
            str(report.get("macro", "")) + " " + str(report.get("micro", ""))
            for report in reports.values()
        )
        evidence = retrieve_many(source_ids, query=evidence_query)
        missing_evidence = sorted(source_id for source_id, snippets in evidence.items() if not snippets)
        return {
            "covered_sources": source_ids,
            "covered_traditions": traditions,
            "unknown_sources": unknown,
            "missing_traditions": missing,
            "evidence": evidence,
            "evidence_index": classical_index_audit(),
            "missing_evidence": missing_evidence,
            "strictness": workflow.source_review_strictness,
            "min_sources": min_sources,
            "status": "pass" if not unknown and not missing and not missing_evidence and len(source_ids) >= min_sources else "needs_more_sources",
        }

    def _find_conflicts(
        self,
        reports: dict[str, dict[str, Any]],
        workflow: MingliWorkflow,
    ) -> list[str]:
        if not workflow.preserve_conflicts:
            return []
        conflicts = []
        if "active transition" in reports["qimen"]["macro"] and "integration" in reports["astrology"]["micro"]:
            conflicts.append("Qi Men activity and astrology integration need careful synthesis.")
        return conflicts

    def _build_final_report(
        self,
        coordinator: AgentGenome,
        task_input: dict[str, Any],
        birth: dict[str, Any],
        reports: dict[str, dict[str, Any]],
        discussion: list[dict[str, str]],
        votes: dict[str, Any],
        source_review: dict[str, Any],
        conflicts: list[str],
        strategies: set[str],
        workflow: MingliWorkflow,
        annual_luck: dict[str, Any],
        monthly_luck: dict[str, Any],
        auspicious_calendar: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a structured final report before rendering text."""
        summary = [
            reports["bazi"]["macro"],
            reports["ziwei"]["macro"],
            reports["qimen"]["macro"],
            reports["astrology"]["macro"],
        ]
        boundaries = [
            "Purpose: cultural research and entertainment only.",
            "Do not use this report for medical, investment, marriage, legal, or other high-stakes decisions.",
            "All conclusions are symbolic interpretations with uncertainty.",
        ]
        strategy_notes = []
        if "citation_precision" in strategies:
            strategy_notes.append("Citation mode: source-backed symbolism is separated from cross-system synthesis.")
        if "feedback_adaptation" in strategies:
            strategy_notes.append("Feedback mode: corrections are answered with sharper structure and uncertainty labels.")
        if "synthesis_calibration" in strategies:
            strategy_notes.append("Calibration mode: final themes are ranked by cross-agent support and conflict visibility.")
        if "safety_guardrails" in strategies:
            strategy_notes.append("Safety mode: deterministic predictions and high-stakes advice are outside scope.")
        provider_summary = self._provider_summary(reports, auspicious_calendar)
        monthly_luck = self._monthly_luck_with_topic_evidence(monthly_luck)
        topic_synthesis = build_topic_synthesis(reports, annual_luck, monthly_luck, provider_summary)
        annual_timeline = self._annual_timeline(annual_luck)
        annual_timeline_receipt = self._annual_timeline_receipt(annual_luck, annual_timeline)
        monthly_luck_receipt = self._monthly_luck_receipt(monthly_luck)
        auspicious_calendar_receipt = self._auspicious_calendar_receipt(auspicious_calendar)
        report = {
            "title": f"Mingli five-agent report for {birth['name']}",
            "birth_profile": self._birth_profile(birth),
            "coordinator_version": coordinator.version,
            "summary": summary,
            "votes": votes,
            "deliberation_receipt": self._deliberation_receipt(discussion, votes, source_review, conflicts, workflow),
            "source_review": source_review,
            "evidence_summary": self._evidence_summary(source_review),
            "conflicts": conflicts,
            "annual_luck": annual_luck,
            "annual_timeline": annual_timeline,
            "annual_timeline_receipt": annual_timeline_receipt,
            "monthly_luck": monthly_luck,
            "monthly_luck_receipt": monthly_luck_receipt,
            "auspicious_calendar": auspicious_calendar,
            "auspicious_calendar_receipt": auspicious_calendar_receipt,
            "provider_summary": provider_summary,
            "bazi_profile": self._bazi_profile(reports["bazi"]["chart"]),
            "ziwei_profile": self._ziwei_profile(reports["ziwei"]["chart"]),
            "qimen_profile": self._qimen_profile(reports["qimen"]["chart"]),
            "astrology_profile": self._astrology_profile(reports["astrology"]["chart"]),
            "topic_synthesis": topic_synthesis,
            "strategy_notes": strategy_notes,
            "boundaries": boundaries,
            "workflow": workflow.to_meta(),
        }
        report["request_provenance"] = self._request_provenance(task_input, birth, reports, report)
        return report

    def _deliberation_receipt(
        self,
        discussion: list[dict[str, str]],
        votes: dict[str, Any],
        source_review: dict[str, Any],
        conflicts: list[str],
        workflow: MingliWorkflow,
    ) -> dict[str, Any]:
        """Bind discussion, voting, source review, and conflict handling into one stable receipt."""
        material = {
            "schema_version": "deliberation-receipt-v1",
            "discussion_sha256": _stable_sha256(discussion),
            "votes_sha256": _stable_sha256(votes),
            "source_review_sha256": _stable_sha256(source_review),
            "conflicts_sha256": _stable_sha256(conflicts),
            "workflow_sha256": _stable_sha256(workflow.to_meta()),
            "discussion_count": len(discussion),
            "claim_count": votes.get("_audit", {}).get("claim_count", 0) if isinstance(votes.get("_audit"), dict) else 0,
            "passed_claim_count": votes.get("_audit", {}).get("passed_claim_count", 0)
            if isinstance(votes.get("_audit"), dict)
            else 0,
            "source_review_status": source_review.get("status"),
            "conflict_count": len(conflicts),
            "minority_positions_preserved": votes.get("_audit", {}).get("minority_positions_preserved") is True
            if isinstance(votes.get("_audit"), dict)
            else False,
        }
        return {**material, "sha256": _stable_sha256(material)}

    def _birth_profile(self, birth: dict[str, Any]) -> dict[str, Any]:
        """Return the normalized birth input used by every specialist."""
        annual_start = birth.get("annual_start_year")
        annual_end = birth.get("annual_end_year")
        return {
            "name": birth.get("name", ""),
            "birth_date": birth.get("birth_date", ""),
            "birth_time": birth.get("birth_time", ""),
            "gender": birth.get("gender", ""),
            "birthplace": birth.get("birthplace", ""),
            "birthplace_normalized": birth.get("birthplace_normalized", ""),
            "birthplace_region": birth.get("birthplace_region", ""),
            "latitude": birth.get("latitude"),
            "longitude": birth.get("longitude"),
            "timezone_offset": birth.get("timezone_offset"),
            "geocoding_provider": birth.get("geocoding_provider", ""),
            "geocoding_quality": birth.get("geocoding_quality", ""),
            "year": birth.get("year"),
            "month": birth.get("month"),
            "day": birth.get("day"),
            "hour": birth.get("hour"),
            "minute": birth.get("minute"),
            "calendar_provider": birth.get("calendar_provider", "auto"),
            "lunar_note": birth.get("lunar_note", ""),
            "annual_start_year": annual_start,
            "annual_end_year": annual_end,
        }

    def _request_provenance(
        self,
        task_input: dict[str, Any],
        birth: dict[str, Any],
        reports: dict[str, dict[str, Any]],
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """Bind request input, normalized birth data, specialist contexts, and report artifacts."""
        birth_profile = self._birth_profile(birth)
        specialist_contexts = {}
        for domain, specialist in reports.items():
            chart = specialist.get("chart", {}) if isinstance(specialist, dict) else {}
            context = chart.get("context", {}) if isinstance(chart, dict) else {}
            material = {
                "domain": domain,
                "agent": specialist.get("agent") if isinstance(specialist, dict) else None,
                "birth_profile_sha256": _stable_sha256(birth_profile),
                "provider": chart.get("provider") if isinstance(chart, dict) else None,
                "provider_quality": chart.get("provider_quality") if isinstance(chart, dict) else None,
                "context": context,
            }
            specialist_contexts[domain] = {
                "provider": material["provider"] or context.get("domain_provider") or context.get("provider"),
                "provider_quality": material["provider_quality"]
                or context.get("domain_provider_quality")
                or context.get("provider_quality"),
                "context_sha256": _stable_sha256(material),
                "birth_profile_sha256": material["birth_profile_sha256"],
                "provider_request_receipt_sha256": context.get("provider_request_receipt", {}).get("sha256")
                if isinstance(context.get("provider_request_receipt"), dict)
                else None,
                "external_payload_receipt_sha256": context.get("external_payload_receipt", {}).get("sha256")
                if isinstance(context.get("external_payload_receipt"), dict)
                else None,
            }
        xuanze_receipt = (
            report.get("auspicious_calendar", {}).get("provider_request_receipt")
            if isinstance(report.get("auspicious_calendar"), dict)
            else None
        )
        report_material = {
            "title": report.get("title"),
            "coordinator_version": report.get("coordinator_version"),
            "birth_profile_sha256": _stable_sha256(birth_profile),
            "xuanze_provider_request_receipt_sha256": xuanze_receipt.get("sha256")
            if isinstance(xuanze_receipt, dict)
            else None,
            "xuanze_external_payload_receipt_sha256": report.get("auspicious_calendar", {})
            .get("basis", {})
            .get("external_payload_receipt", {})
            .get("sha256")
            if isinstance(report.get("auspicious_calendar", {}).get("basis", {}).get("external_payload_receipt"), dict)
            else None,
            "provider_summary": report.get("provider_summary", {}),
            "annual_luck_range": report.get("annual_luck", {}).get("range", {}),
            "annual_timeline_receipt_sha256": report.get("annual_timeline_receipt", {}).get("sha256")
            if isinstance(report.get("annual_timeline_receipt"), dict)
            else None,
            "monthly_luck_range": report.get("monthly_luck", {}).get("range", {}),
            "monthly_luck_receipt_sha256": report.get("monthly_luck_receipt", {}).get("sha256")
            if isinstance(report.get("monthly_luck_receipt"), dict)
            else None,
            "auspicious_calendar_range": report.get("auspicious_calendar", {}).get("range", {}),
            "auspicious_calendar_receipt_sha256": report.get("auspicious_calendar_receipt", {}).get("sha256")
            if isinstance(report.get("auspicious_calendar_receipt"), dict)
            else None,
            "topic_keys": sorted((report.get("topic_synthesis") or {}).keys()),
            "source_review_status": report.get("source_review", {}).get("status"),
            "vote_summary": report.get("votes", {}).get("_summary", {}),
            "deliberation_receipt_sha256": report.get("deliberation_receipt", {}).get("sha256")
            if isinstance(report.get("deliberation_receipt"), dict)
            else None,
            "deliberation_claim_count": report.get("deliberation_receipt", {}).get("claim_count")
            if isinstance(report.get("deliberation_receipt"), dict)
            else None,
        }
        chain_material = {
            "schema_version": "request-provenance-v1",
            "raw_task_input_sha256": _stable_sha256(task_input),
            "birth_profile_sha256": _stable_sha256(birth_profile),
            "specialist_contexts": specialist_contexts,
            "report_material_sha256": _stable_sha256(report_material),
        }
        return {
            **chain_material,
            "report_material": report_material,
            "chain_sha256": _stable_sha256(chain_material),
        }

    def _annual_timeline(self, annual_luck: dict[str, Any]) -> list[dict[str, Any]]:
        """Expose yearly luck rows as a stable API/UI timeline."""
        topic_keys = [
            "finance",
            "official_career",
            "career",
            "study",
            "relationship",
            "friends",
            "leadership",
            "children_family",
        ]
        timeline = []
        basis = annual_luck.get("basis", {}) if isinstance(annual_luck.get("basis"), dict) else {}
        provider_quality = basis.get("provider_quality")
        for index, row in enumerate(annual_luck.get("rows", [])):
            if not isinstance(row, dict):
                continue
            evidence_sha256 = _stable_sha256(row.get("bazi_evidence", {}))
            topics = {
                key: {
                    "message": row.get(key),
                    "category": row.get("category"),
                    "intensity": row.get("intensity"),
                    "source": "annual_luck.rows",
                    "source_row_index": index,
                    "source_field": key,
                    "bazi_evidence_sha256": evidence_sha256,
                    "provider_quality": provider_quality,
                    "boundary": "Symbolic yearly topic prompt; not deterministic prediction.",
                }
                for key in topic_keys
            }
            timeline.append(
                {
                    "year": row.get("year"),
                    "age": row.get("age"),
                    "ganzhi": row.get("ganzhi"),
                    "phase": row.get("phase"),
                    "category": row.get("category"),
                    "intensity": row.get("intensity"),
                    "element_focus": row.get("elements", {}).get("focus") if isinstance(row.get("elements"), dict) else None,
                    "bazi_evidence": row.get("bazi_evidence", {}),
                    "topics": topics,
                    "risk_notes": row.get("risk_notes", []),
                    "source": "annual_luck.rows",
                    "source_row_index": index,
                    "boundary": "Symbolic yearly timeline for reflection; not deterministic prediction.",
                }
            )
        return timeline

    def _annual_timeline_receipt(
        self,
        annual_luck: dict[str, Any],
        annual_timeline: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bind annual rows to a stable receipt for retrospective validation."""
        years = [row.get("year") for row in annual_timeline if isinstance(row.get("year"), int)]
        topic_keys = sorted(
            {
                topic
                for row in annual_timeline
                if isinstance(row.get("topics"), dict)
                for topic in row["topics"]
            }
        )
        category_counts: dict[str, int] = {}
        intensity_counts: dict[str, int] = {}
        row_fingerprints = []
        topic_evidence_missing = []
        for row in annual_timeline:
            category = str(row.get("category") or "")
            intensity = str(row.get("intensity") or "")
            category_counts[category] = category_counts.get(category, 0) + 1
            intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1
            topics = row.get("topics", {})
            if isinstance(topics, dict):
                for topic_key in topic_keys:
                    topic = topics.get(topic_key)
                    if not isinstance(topic, dict) or not _annual_topic_evidence_complete(topic):
                        topic_evidence_missing.append(
                            {
                                "year": row.get("year"),
                                "source_row_index": row.get("source_row_index"),
                                "topic": topic_key,
                            }
                        )
            row_material = {
                "year": row.get("year"),
                "age": row.get("age"),
                "ganzhi": row.get("ganzhi"),
                "category": row.get("category"),
                "intensity": row.get("intensity"),
                "topics": row.get("topics"),
                "bazi_evidence": row.get("bazi_evidence"),
                "boundary": row.get("boundary"),
            }
            row_fingerprints.append(
                {
                    "year": row.get("year"),
                    "source_row_index": row.get("source_row_index"),
                    "sha256": _stable_sha256(row_material),
                }
            )
        material = {
            "schema_version": "annual-timeline-receipt-v1",
            "annual_luck_range": annual_luck.get("range", {}),
            "annual_luck_rows_sha256": _stable_sha256(annual_luck.get("rows", [])),
            "annual_timeline_sha256": _stable_sha256(annual_timeline),
            "row_count": len(annual_timeline),
            "start_year": min(years) if years else None,
            "end_year": max(years) if years else None,
            "topic_keys": topic_keys,
            "category_counts": dict(sorted(category_counts.items())),
            "intensity_counts": dict(sorted(intensity_counts.items())),
            "row_fingerprints": row_fingerprints,
            "topic_evidence_complete": not topic_evidence_missing,
            "topic_evidence_missing": topic_evidence_missing,
            "validation_boundary": (
                "Receipt supports retrospective quality checks and user feedback binding; "
                "it does not certify predictive truth."
            ),
        }
        return {**material, "sha256": _stable_sha256(material)}

    def _monthly_luck_with_topic_evidence(self, monthly_luck: dict[str, Any]) -> dict[str, Any]:
        """Bind monthly row topics to row indexes and BaZi evidence hashes."""
        rows = monthly_luck.get("rows", [])
        if not isinstance(rows, list):
            return monthly_luck
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            evidence_sha256 = _stable_sha256(row.get("bazi_evidence", {}))
            topics = row.get("topics")
            if not isinstance(topics, dict):
                topics = {}
                row["topics"] = topics
            for key in (
                "finance",
                "official_career",
                "career",
                "study",
                "relationship",
                "friends",
                "leadership",
                "children_family",
            ):
                topic = topics.get(key)
                if not isinstance(topic, dict):
                    topic = {
                        "message": row.get(key),
                        "category": row.get("category"),
                        "intensity": row.get("intensity"),
                        "source": "monthly_luck.rows",
                        "source_field": key,
                        "provider_quality": monthly_luck.get("basis", {}).get("provider_quality")
                        if isinstance(monthly_luck.get("basis"), dict)
                        else None,
                        "boundary": "Symbolic monthly topic prompt; not deterministic prediction.",
                    }
                    topics[key] = topic
                topic["source"] = "monthly_luck.rows"
                topic["source_row_index"] = index
                topic["source_field"] = key
                topic["bazi_evidence_sha256"] = evidence_sha256
                topic.setdefault(
                    "provider_quality",
                    monthly_luck.get("basis", {}).get("provider_quality")
                    if isinstance(monthly_luck.get("basis"), dict)
                    else None,
                )
                topic.setdefault("boundary", "Symbolic monthly topic prompt; not deterministic prediction.")
        return monthly_luck

    def _monthly_luck_receipt(self, monthly_luck: dict[str, Any]) -> dict[str, Any]:
        """Bind selected monthly rows to a stable receipt for focused validation."""
        rows = [row for row in monthly_luck.get("rows", []) if isinstance(row, dict)]
        years = sorted({row.get("year") for row in rows if isinstance(row.get("year"), int)})
        months_by_year: dict[str, list[int]] = {}
        category_counts: dict[str, int] = {}
        intensity_counts: dict[str, int] = {}
        row_fingerprints = []
        topic_evidence_missing = []
        for index, row in enumerate(rows):
            year = row.get("year")
            month = row.get("month")
            if isinstance(year, int) and isinstance(month, int):
                key = str(year)
                months_by_year.setdefault(key, []).append(month)
            category = str(row.get("category") or "")
            intensity = str(row.get("intensity") or "")
            category_counts[category] = category_counts.get(category, 0) + 1
            intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1
            topics = row.get("topics", {})
            if isinstance(topics, dict):
                for topic_key in (
                    "finance",
                    "official_career",
                    "career",
                    "study",
                    "relationship",
                    "friends",
                    "leadership",
                    "children_family",
                ):
                    topic = topics.get(topic_key)
                    if not isinstance(topic, dict) or not _monthly_topic_evidence_complete(topic):
                        topic_evidence_missing.append(
                            {
                                "year": row.get("year"),
                                "month": row.get("month"),
                                "source_row_index": index,
                                "topic": topic_key,
                            }
                        )
            row_material = {
                "year": row.get("year"),
                "month": row.get("month"),
                "ganzhi": row.get("ganzhi"),
                "category": row.get("category"),
                "intensity": row.get("intensity"),
                "topics": row.get("topics"),
                "bazi_evidence": row.get("bazi_evidence"),
                "risk_notes": row.get("risk_notes"),
            }
            row_fingerprints.append(
                {
                    "year": row.get("year"),
                    "month": row.get("month"),
                    "source_row_index": index,
                    "sha256": _stable_sha256(row_material),
                }
            )
        material = {
            "schema_version": "monthly-luck-receipt-v1",
            "monthly_luck_range": monthly_luck.get("range", {}),
            "monthly_luck_basis": monthly_luck.get("basis", {}),
            "monthly_luck_rows_sha256": _stable_sha256(rows),
            "row_count": len(rows),
            "years": years,
            "months_by_year": {key: sorted(values) for key, values in sorted(months_by_year.items())},
            "category_counts": dict(sorted(category_counts.items())),
            "intensity_counts": dict(sorted(intensity_counts.items())),
            "row_fingerprints": row_fingerprints,
            "topic_evidence_complete": not topic_evidence_missing,
            "topic_evidence_missing": topic_evidence_missing,
            "validation_boundary": (
                "Receipt supports selected monthly-row regression and feedback binding; "
                "it does not certify predictive truth."
            ),
        }
        return {**material, "sha256": _stable_sha256(material)}

    def _auspicious_calendar_receipt(self, auspicious_calendar: dict[str, Any]) -> dict[str, Any]:
        """Bind auspicious-day rows and method layers to a stable receipt."""
        rows = [row for row in auspicious_calendar.get("rows", []) if isinstance(row, dict)]
        dates = [row.get("date") for row in rows if isinstance(row.get("date"), str)]
        rating_counts: dict[str, int] = {}
        officer_counts: dict[str, int] = {}
        mansion_counts: dict[str, int] = {}
        row_fingerprints = []
        for index, row in enumerate(rows):
            rating = str(row.get("rating") or "")
            officer = str(row.get("twelve_officer") or "")
            mansion = str(row.get("twenty_eight_mansion") or "")
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
            officer_counts[officer] = officer_counts.get(officer, 0) + 1
            mansion_counts[mansion] = mansion_counts.get(mansion, 0) + 1
            row_material = {
                "date": row.get("date"),
                "weekday": row.get("weekday"),
                "ganzhi": row.get("ganzhi"),
                "solar_term": row.get("solar_term"),
                "twelve_officer": row.get("twelve_officer"),
                "twenty_eight_mansion": row.get("twenty_eight_mansion"),
                "huangdao": row.get("huangdao"),
                "rating": row.get("rating"),
                "suitable": row.get("suitable"),
                "avoid": row.get("avoid"),
                "recommended_hours": row.get("recommended_hours"),
                "risk_notes": row.get("risk_notes"),
            }
            row_fingerprints.append(
                {
                    "date": row.get("date"),
                    "source_row_index": index,
                    "sha256": _stable_sha256(row_material),
                }
            )
        provider_request_receipt = auspicious_calendar.get("provider_request_receipt")
        basis = auspicious_calendar.get("basis", {}) if isinstance(auspicious_calendar.get("basis"), dict) else {}
        external_payload_receipt = basis.get("external_payload_receipt") if isinstance(basis, dict) else None
        method_layers = {
            "twelve_officer_analysis": auspicious_calendar.get("twelve_officer_analysis", {}),
            "mansion_analysis": auspicious_calendar.get("mansion_analysis", {}),
            "huangdao_analysis": auspicious_calendar.get("huangdao_analysis", {}),
            "hour_selection_analysis": auspicious_calendar.get("hour_selection_analysis", {}),
            "risk_boundary_analysis": auspicious_calendar.get("risk_boundary_analysis", {}),
            "provider_quality_analysis": auspicious_calendar.get("provider_quality_analysis", {}),
            "method_matrix": auspicious_calendar.get("method_matrix", []),
        }
        material = {
            "schema_version": "auspicious-calendar-receipt-v1",
            "calendar_range": auspicious_calendar.get("range", {}),
            "calendar_basis": basis,
            "calendar_rows_sha256": _stable_sha256(rows),
            "method_layers_sha256": _stable_sha256(method_layers),
            "row_count": len(rows),
            "start_date": min(dates) if dates else None,
            "end_date": max(dates) if dates else None,
            "rating_counts": dict(sorted(rating_counts.items())),
            "officer_counts": dict(sorted(officer_counts.items())),
            "mansion_counts": dict(sorted(mansion_counts.items())),
            "row_fingerprints": row_fingerprints,
            "provider_request_receipt_sha256": provider_request_receipt.get("sha256")
            if isinstance(provider_request_receipt, dict)
            else None,
            "external_payload_receipt_sha256": external_payload_receipt.get("sha256")
            if isinstance(external_payload_receipt, dict)
            else None,
            "validation_boundary": (
                "Receipt supports auspicious-day row regression and provider boundary checks; "
                "it does not certify real-world scheduling outcomes."
            ),
        }
        return {**material, "sha256": _stable_sha256(material)}

    def _provider_summary(
        self,
        reports: dict[str, dict[str, Any]],
        auspicious_calendar: dict[str, Any],
    ) -> dict[str, Any]:
        """Summarize provider readiness for report consumers and production audits."""
        domains = {
            "bazi": self._provider_row(
                "bazi",
                reports["bazi"]["chart"].get("context", {}),
                professional_qualities={"lunar_python", "sxtwl", "external_bazi"},
                contract_valid=chart_contract("bazi", reports["bazi"]["chart"])["valid"],
            ),
            "ziwei": self._provider_row(
                "ziwei",
                reports["ziwei"]["chart"].get("context", {}),
                provider_key="domain_provider",
                quality_key="domain_provider_quality",
                professional_qualities={"ziwei_json_cli", "external_ziwei"},
                contract_valid=chart_contract("ziwei", reports["ziwei"]["chart"])["valid"],
            ),
            "qimen": self._provider_row(
                "qimen",
                reports["qimen"]["chart"].get("context", {}),
                provider_key="domain_provider",
                quality_key="domain_provider_quality",
                professional_qualities={"kinqimen", "qimen_json_cli", "external_qimen"},
                contract_valid=chart_contract("qimen", reports["qimen"]["chart"])["valid"],
            ),
            "astrology": self._provider_row(
                "astrology",
                reports["astrology"]["chart"].get("context", {}),
                provider_key="domain_provider",
                quality_key="domain_provider_quality",
                professional_qualities={"swiss_ephemeris", "astrology_json_cli", "external_astrology"},
                contract_valid=chart_contract("astrology", reports["astrology"]["chart"])["valid"],
            ),
            "xuanze": self._xuanze_provider_row(auspicious_calendar),
        }
        blockers = [key for key, item in domains.items() if not item["production_ready"]]
        action_plan = self._provider_action_plan(domains, blockers)
        readiness_matrix = self._provider_readiness_matrix(domains)
        return {
            "status": "production_ready" if not blockers else "ready_with_provider_gaps",
            "production_ready": not blockers,
            "domains": domains,
            "readiness_matrix": readiness_matrix,
            "professional_domain_count": sum(1 for item in domains.values() if item["production_ready"]),
            "fallback_domain_count": sum(1 for item in domains.values() if not item["production_ready"]),
            "production_blockers": blockers,
            "action_plan": action_plan,
            "boundary": "Symbolic fallbacks are allowed for research demos; production use requires verified professional providers for every listed domain.",
        }

    def _provider_readiness_matrix(self, domains: dict[str, Any]) -> list[dict[str, Any]]:
        """Expose domain readiness as a compact machine-readable matrix."""
        return [
            {
                "domain": domain,
                "provider": row.get("provider"),
                "provider_quality": row.get("provider_quality"),
                "production_ready": row.get("production_ready") is True,
                "interpretation_mode": row.get("interpretation_mode"),
                "confidence_level": row.get("confidence_level"),
                "blocking_reasons": row.get("blocking_reasons", []),
            }
            for domain, row in domains.items()
        ]

    def _provider_action_plan(self, domains: dict[str, Any], blockers: list[str]) -> list[dict[str, Any]]:
        protocols = provider_protocol_document().get("domains", {})
        actions = []
        for domain in blockers:
            row = domains.get(domain, {})
            protocol = protocols.get(domain, {}) if isinstance(protocols, dict) else {}
            actions.append(
                {
                    "domain": domain,
                    "status": row.get("status"),
                    "current_provider": row.get("provider"),
                    "provider_quality": row.get("provider_quality"),
                    "reason": row.get("replacement_boundary") or "Production requires a verified professional provider.",
                    "env_var": protocol.get("env_var"),
                    "provenance_env_var": protocol.get("provenance_env_var"),
                    "certification_command_template": protocol.get("certification_command_template"),
                    "production_readiness_command_template": protocol.get("production_readiness_command_template"),
                    "deployment_checklist": protocol.get("deployment_checklist", []),
                }
            )
        return actions

    def _provider_row(
        self,
        domain: str,
        context: dict[str, Any],
        *,
        provider_key: str = "provider",
        quality_key: str = "provider_quality",
        professional_qualities: set[str],
        contract_valid: bool,
    ) -> dict[str, Any]:
        provider = context.get(provider_key) or "unknown"
        quality = context.get(quality_key) or "unknown"
        provenance = context.get(f"{provider_key}_provenance") or context.get("provider_provenance")
        provenance_valid = self._provider_provenance_valid(quality, provenance)
        receipt = context.get("external_payload_receipt")
        receipt_valid = self._external_payload_receipt_valid(quality, receipt)
        birth_match_status = self._external_payload_birth_match_status(quality, receipt)
        birth_match_valid = self._external_payload_birth_match_valid(quality, receipt)
        production_ready = str(quality) in professional_qualities and contract_valid and provenance_valid and receipt_valid
        production_ready = production_ready and birth_match_valid
        blocking_reasons = self._provider_blocking_reasons(
            quality,
            professional_qualities,
            contract_valid=contract_valid,
            provenance_valid=provenance_valid,
            receipt_valid=receipt_valid,
            birth_match_valid=birth_match_valid,
            birth_match_status=birth_match_status,
        )
        interpretation_mode = self._provider_interpretation_mode(production_ready, quality, blocking_reasons)
        return {
            "domain": domain,
            "provider": provider,
            "provider_quality": quality,
            "status": "professional" if production_ready else "fallback",
            "interpretation_mode": interpretation_mode,
            "confidence_level": self._provider_confidence_level(production_ready, interpretation_mode),
            "blocking_reasons": blocking_reasons,
            "contract_valid": contract_valid,
            "provider_source": context.get(f"{provider_key}_source") or context.get("provider_source"),
            "provider_provenance_valid": provenance_valid,
            "provider_provenance_missing": self._provider_provenance_missing(quality, provenance),
            "external_payload_receipt_valid": receipt_valid,
            "external_payload_receipt_sha256": receipt.get("sha256") if isinstance(receipt, dict) else None,
            "external_payload_birth_match_status": birth_match_status,
            "external_payload_birth_mismatch_fields": self._external_payload_birth_mismatch_fields(quality, receipt),
            "external_payload_declared_birth_profile_sha256": receipt.get("declared_birth_profile_sha256")
            if isinstance(receipt, dict)
            else None,
            "production_ready": production_ready,
            "replacement_boundary": "Production reports should use a verified provider." if not production_ready else "",
        }

    def _xuanze_provider_row(self, auspicious_calendar: dict[str, Any]) -> dict[str, Any]:
        basis = auspicious_calendar.get("basis", {})
        quality = basis.get("provider_quality") or "unknown"
        contract_valid = chart_contract("xuanze", auspicious_calendar)["valid"]
        provenance = basis.get("provider_provenance")
        provenance_valid = self._provider_provenance_valid(quality, provenance)
        receipt = basis.get("external_payload_receipt")
        receipt_valid = self._external_payload_receipt_valid(quality, receipt)
        birth_match_status = self._external_payload_birth_match_status(quality, receipt)
        birth_match_valid = self._external_payload_birth_match_valid(quality, receipt)
        production_ready = (
            str(quality) in {"xuanze_json_cli", "external_xuanze", "verified_tongshu"}
            and contract_valid
            and provenance_valid
            and receipt_valid
            and birth_match_valid
        )
        blocking_reasons = self._provider_blocking_reasons(
            quality,
            {"xuanze_json_cli", "external_xuanze", "verified_tongshu"},
            contract_valid=contract_valid,
            provenance_valid=provenance_valid,
            receipt_valid=receipt_valid,
            birth_match_valid=birth_match_valid,
            birth_match_status=birth_match_status,
        )
        interpretation_mode = self._provider_interpretation_mode(production_ready, quality, blocking_reasons)
        return {
            "domain": "xuanze",
            "provider": basis.get("provider") or "unknown",
            "provider_quality": quality,
            "status": "professional" if production_ready else "fallback",
            "interpretation_mode": interpretation_mode,
            "confidence_level": self._provider_confidence_level(production_ready, interpretation_mode),
            "blocking_reasons": blocking_reasons,
            "contract_valid": contract_valid,
            "provider_source": basis.get("provider_source"),
            "provider_provenance_valid": provenance_valid,
            "provider_provenance_missing": self._provider_provenance_missing(quality, provenance),
            "external_payload_receipt_valid": receipt_valid,
            "external_payload_receipt_sha256": receipt.get("sha256") if isinstance(receipt, dict) else None,
            "external_payload_birth_match_status": birth_match_status,
            "external_payload_birth_mismatch_fields": self._external_payload_birth_mismatch_fields(quality, receipt),
            "external_payload_declared_birth_profile_sha256": receipt.get("declared_birth_profile_sha256")
            if isinstance(receipt, dict)
            else None,
            "production_ready": production_ready,
            "replacement_boundary": ""
            if production_ready
            else (
                basis.get("replacement_boundary", "")
                or "Production date selection should use a verified tongshu/xuanze provider."
            ),
        }

    def _provider_blocking_reasons(
        self,
        quality: Any,
        professional_qualities: set[str],
        *,
        contract_valid: bool,
        provenance_valid: bool,
        receipt_valid: bool,
        birth_match_valid: bool,
        birth_match_status: str,
    ) -> list[str]:
        reasons = []
        if str(quality) not in professional_qualities:
            reasons.append("non_professional_provider_quality")
        if not contract_valid:
            reasons.append("contract_invalid")
        if not provenance_valid:
            reasons.append("provider_provenance_missing_or_invalid")
        if not receipt_valid:
            reasons.append("external_payload_receipt_invalid")
        if not birth_match_valid:
            reasons.append(f"external_payload_birth_{birth_match_status}")
        return reasons

    def _provider_interpretation_mode(self, production_ready: bool, quality: Any, blocking_reasons: list[str]) -> str:
        if production_ready:
            return "professional_verified"
        if str(quality).startswith("external_") and blocking_reasons:
            return "external_payload_blocked"
        return "symbolic_fallback"

    def _provider_confidence_level(self, production_ready: bool, interpretation_mode: str) -> str:
        if production_ready:
            return "production"
        if interpretation_mode == "external_payload_blocked":
            return "blocked"
        return "research_symbolic"

    def _provider_provenance_valid(self, quality: Any, provenance: Any) -> bool:
        """Require request-scoped external providers to carry source review metadata."""
        if not str(quality).startswith("external_"):
            return True
        return isinstance(provenance, dict) and provenance.get("valid") is True

    def _provider_provenance_missing(self, quality: Any, provenance: Any) -> list[str]:
        if not str(quality).startswith("external_"):
            return []
        if not isinstance(provenance, dict):
            return ["source", "version", "license_or_review"]
        missing = provenance.get("missing_fields", [])
        return [str(item) for item in missing] if isinstance(missing, list) else []

    def _external_payload_receipt_valid(self, quality: Any, receipt: Any) -> bool:
        if not str(quality).startswith("external_"):
            return True
        return (
            isinstance(receipt, dict)
            and receipt.get("schema_version") == "external-payload-receipt-v1"
            and receipt.get("provenance_valid") is True
            and isinstance(receipt.get("birth_profile_sha256"), str)
            and len(receipt.get("birth_profile_sha256", "")) == 64
            and isinstance(receipt.get("payload_sha256"), str)
            and len(receipt.get("payload_sha256", "")) == 64
            and isinstance(receipt.get("sha256"), str)
            and len(receipt.get("sha256", "")) == 64
            and receipt.get("birth_match_status") in {"matched", "not_declared"}
        )

    def _external_payload_birth_match_status(self, quality: Any, receipt: Any) -> str:
        if not str(quality).startswith("external_"):
            return "not_applicable"
        if not isinstance(receipt, dict):
            return "missing_receipt"
        return str(receipt.get("birth_match_status") or "unknown")

    def _external_payload_birth_match_valid(self, quality: Any, receipt: Any) -> bool:
        if not str(quality).startswith("external_"):
            return True
        return isinstance(receipt, dict) and receipt.get("birth_match_status") in {"matched", "not_declared"}

    def _external_payload_birth_mismatch_fields(self, quality: Any, receipt: Any) -> list[str]:
        if not str(quality).startswith("external_") or not isinstance(receipt, dict):
            return []
        fields = receipt.get("birth_mismatch_fields", [])
        return [str(item) for item in fields] if isinstance(fields, list) else []

    def _bazi_profile(self, chart: dict[str, Any]) -> dict[str, Any]:
        """Extract stable BaZi profile fields for final-report rendering."""
        deep = chart.get("deep_analysis", {})
        return {
            "provider": deep.get("provider") or chart.get("context", {}).get("provider"),
            "provider_quality": chart.get("context", {}).get("provider_quality"),
            "pillars": chart.get("pillars", {}),
            "structure": chart.get("structure"),
            "dominant_element": chart.get("dominant_element"),
            "useful_element": chart.get("useful_element"),
            "day_master": deep.get("day_master"),
            "ten_god_distribution": deep.get("ten_god_distribution", {}),
            "hidden_stem_profile": deep.get("hidden_stem_profile", {}),
            "nayin_growth_profile": deep.get("nayin_growth_profile", {}),
            "strength_analysis": deep.get("strength_analysis", {}),
            "pattern_analysis": deep.get("pattern_analysis", {}),
            "useful_god_analysis": deep.get("useful_god_analysis", {}),
            "tiaohou_analysis": deep.get("tiaohou_analysis", {}),
            "image_symbol_analysis": deep.get("image_symbol_analysis", {}),
            "new_school_simplified_analysis": deep.get("new_school_simplified_analysis", {}),
            "data_validation_analysis": deep.get("data_validation_analysis", {}),
            "method_matrix": deep.get("method_matrix", []),
            "luck_start": deep.get("luck_start", {}),
            "major_luck": deep.get("major_luck", []),
            "caution": deep.get("caution"),
        }

    def _qimen_profile(self, chart: dict[str, Any]) -> dict[str, Any]:
        """Extract stable Qi Men profile fields for final-report rendering."""
        deep = chart.get("deep_analysis", {})
        useful_gods = deep.get("useful_gods", {})
        useful_palace_names = {
            item.get("palace")
            for item in useful_gods.values()
            if isinstance(item, dict) and item.get("palace")
        }
        palaces = [
            item for item in deep.get("palaces", [])
            if isinstance(item, dict) and item.get("name") in useful_palace_names
        ]
        if not palaces:
            palaces = [item for item in deep.get("palaces", [])[:3] if isinstance(item, dict)]
        return {
            "provider": deep.get("provider") or chart.get("context", {}).get("domain_provider"),
            "provider_quality": deep.get("provider_quality") or chart.get("context", {}).get("domain_provider_quality"),
            "yin_yang": deep.get("yin_yang"),
            "ju_number": deep.get("ju_number"),
            "duty": deep.get("duty", {}),
            "useful_gods": useful_gods,
            "highlighted_palaces": palaces,
            "pattern_flags": deep.get("pattern_flags", []),
            "door_star_spirit_analysis": deep.get("door_star_spirit_analysis", {}),
            "stem_relation_analysis": deep.get("stem_relation_analysis", {}),
            "useful_god_analysis": deep.get("useful_god_analysis", {}),
            "pattern_risk_analysis": deep.get("pattern_risk_analysis", {}),
            "timing_activation_analysis": deep.get("timing_activation_analysis", {}),
            "method_matrix": deep.get("method_matrix", []),
            "annual_timing": deep.get("annual_timing", []),
            "caution": deep.get("caution"),
        }

    def _ziwei_profile(self, chart: dict[str, Any]) -> dict[str, Any]:
        """Extract stable Zi Wei profile fields for final-report rendering."""
        deep = chart.get("deep_analysis", {})
        palaces = deep.get("palaces", [])
        highlighted_palaces = [
            item for item in palaces
            if isinstance(item, dict) and set(item.get("markers", [])) & {"ming", "body"}
        ]
        if not highlighted_palaces and isinstance(palaces, list):
            highlighted_palaces = [item for item in palaces[:2] if isinstance(item, dict)]
        return {
            "provider": deep.get("provider") or chart.get("context", {}).get("domain_provider"),
            "provider_quality": deep.get("provider_quality") or chart.get("context", {}).get("domain_provider_quality"),
            "ming_palace": deep.get("ming_palace") or chart.get("ming_palace"),
            "body_palace": deep.get("body_palace") or chart.get("body_palace"),
            "major_stars": chart.get("major_stars", []),
            "highlighted_palaces": highlighted_palaces,
            "four_transformations": deep.get("four_transformations", {}),
            "life_focus": deep.get("life_focus", {}),
            "triad_analysis": deep.get("triad_analysis", {}),
            "transformation_analysis": deep.get("transformation_analysis", {}),
            "limit_activation_analysis": deep.get("limit_activation_analysis", {}),
            "method_matrix": deep.get("method_matrix", []),
            "major_limits": deep.get("major_limits", []),
            "annual_activation": deep.get("annual_activation", []),
            "caution": deep.get("caution"),
        }

    def _astrology_profile(self, chart: dict[str, Any]) -> dict[str, Any]:
        """Extract stable Western astrology profile fields for final-report audits."""
        deep = chart.get("deep_analysis", {})
        return {
            "provider": deep.get("provider") or chart.get("context", {}).get("domain_provider"),
            "provider_quality": deep.get("provider_quality") or chart.get("context", {}).get("domain_provider_quality"),
            "zodiac": deep.get("zodiac"),
            "sun": chart.get("sun"),
            "moon": chart.get("moon"),
            "ascendant": chart.get("ascendant"),
            "planets": deep.get("planets", []),
            "houses": deep.get("houses", []),
            "aspects": deep.get("aspects", []),
            "annual_transits": deep.get("annual_transits", []),
            "ephemeris_quality": deep.get("ephemeris_quality", {}),
            "core_identity_analysis": deep.get("core_identity_analysis", {}),
            "house_emphasis_analysis": deep.get("house_emphasis_analysis", {}),
            "aspect_pattern_analysis": deep.get("aspect_pattern_analysis", {}),
            "transit_activation_analysis": deep.get("transit_activation_analysis", {}),
            "method_matrix": deep.get("method_matrix", []),
            "caution": deep.get("caution"),
        }

    def _render_final_report(self, final_report: dict[str, Any]) -> str:
        """Render structured report into the text output expected by SEMAS."""
        lines = [
            f"{final_report['title']} using coordinator v{final_report['coordinator_version']}.",
            self._birth_profile_line(final_report.get("birth_profile", {})),
            *final_report["boundaries"],
            *final_report["summary"],
            f"Voting: {len(final_report['votes']) - 1} specialist supports with uncertainty constraints.",
            f"Source review: {final_report['source_review']['status']}.",
            f"Evidence: {len(final_report['evidence_summary'])} source snippets available.",
            f"Annual luck rows: {final_report['annual_luck']['range']['count']} "
            f"({final_report['annual_luck']['range']['start_year']}-"
            f"{final_report['annual_luck']['range']['end_year']}).",
            f"Annual phase summaries: {len(final_report['annual_luck'].get('phase_summary', []))}.",
            *self._annual_phase_summary_lines(final_report["annual_luck"]),
            f"Annual timeline rows: {len(final_report.get('annual_timeline', []))}.",
            f"Monthly luck rows: {final_report['monthly_luck']['range']['count']} "
            f"for years {final_report['monthly_luck']['range']['years']}.",
            f"Auspicious calendar rows: {final_report['auspicious_calendar']['range']['count']} "
            f"({final_report['auspicious_calendar']['range']['start_date']}-"
            f"{final_report['auspicious_calendar']['range']['end_date']}).",
            f"Provider readiness: {final_report['provider_summary']['status']} "
            f"with blockers {final_report['provider_summary']['production_blockers']}.",
            f"Provider confidence: {final_report['provider_summary']['professional_domain_count']} production domains, "
            f"{final_report['provider_summary']['fallback_domain_count']} research fallback domains.",
            f"Topic synthesis sections: {len(final_report['topic_synthesis'])}.",
            f"Workflow: {final_report['workflow']}.",
            *final_report["strategy_notes"],
        ]
        if final_report["conflicts"]:
            lines.append("Conflicts: " + " | ".join(final_report["conflicts"]))
        return "\n".join(lines)

    def _birth_profile_line(self, birth_profile: dict[str, Any]) -> str:
        if not isinstance(birth_profile, dict):
            return "Birth profile: unavailable."
        annual_start = birth_profile.get("annual_start_year")
        annual_end = birth_profile.get("annual_end_year")
        annual_range = f"; annual range {annual_start}-{annual_end}" if annual_start and annual_end else ""
        geo = birth_profile.get("birthplace_normalized") or "unresolved birthplace"
        lat = birth_profile.get("latitude")
        lon = birth_profile.get("longitude")
        tz = birth_profile.get("timezone_offset") or ""
        return (
            "Birth profile: "
            f"{birth_profile.get('name', '')}, {birth_profile.get('gender', '')}, "
            f"{birth_profile.get('birth_date', '')} {birth_profile.get('birth_time', '')}, "
            f"{birth_profile.get('birthplace', '')}; normalized hour "
            f"{birth_profile.get('hour', '')}:{int(birth_profile.get('minute') or 0):02d}; "
            f"calendar provider {birth_profile.get('calendar_provider', '')}; "
            f"geo {geo} {lat},{lon} {tz}{annual_range}."
        )

    def _annual_phase_summary_lines(self, annual_luck: dict[str, Any]) -> list[str]:
        """Render compact annual phase summaries for plain-text output."""
        lines = []
        for item in annual_luck.get("phase_summary", []):
            if not isinstance(item, dict):
                continue
            high_volatility = item.get("high_volatility_years") or []
            constructive = item.get("constructive_years") or []
            lines.append(
                "Annual phase "
                f"{item.get('phase', '')} ({item.get('start_year', '')}-{item.get('end_year', '')}): "
                f"dominant {item.get('dominant_category', '')}; "
                f"high-volatility years {high_volatility}; constructive years {constructive}."
            )
        return lines

    def _evidence_summary(self, source_review: dict[str, Any]) -> list[dict[str, str]]:
        """Flatten one evidence snippet per covered source for final report artifacts."""
        summary = []
        for source_id, snippets in source_review.get("evidence", {}).items():
            if snippets:
                first = snippets[0]
                summary.append(
                    {
                        "source_id": source_id,
                        "snippet_id": first["snippet_id"],
                        "note": first["note"],
                        "caution": first["caution"],
                    }
                )
        return summary


def bootstrap_repo(base_path: Path) -> GenomeRepository:
    """Load all mingli genomes into a SEMAS repository."""
    repo = GenomeRepository(base_path)
    genome_dir = Path(__file__).parent / "genomes"
    for filename in GENOME_FILES:
        repo.save_agent(repo.load_genome_from_yaml(genome_dir / filename))
    return repo


def build_mingli_evaluator() -> Evaluator:
    """Build the composite SEMAS evaluator for mingli analysis."""
    evaluator = Evaluator(threshold=0.92)
    evaluator.register_metric("consistency", consistency_score)
    evaluator.register_metric("citation", citation_score)
    evaluator.register_metric("feedback", feedback_score)
    evaluator.register_metric("safety", safety_score)
    evaluator.register_metric("workflow", workflow_score)
    evaluator.register_metric("report_schema", report_schema_score)
    evaluator.register_metric("provider_contracts", provider_contract_score)
    evaluator.register_metric("evidence_provenance", evidence_provenance_score)
    evaluator.register_metric("chinese_render", chinese_render_score)
    evaluator.register_metric("capability_audit", capability_audit_score)
    evaluator.register_metric("schema_contract", schema_contract_score)
    evaluator.add_regression_test(
        "required_sections",
        {
            "birth": {
                "name": "Regression Case",
                "birth_date": "1992-06-15",
                "birth_time": "08:30",
                "gender": "unspecified",
                "birthplace": "Shanghai",
            }
        },
        {"feedback": {"satisfaction": 0.9}},
    )
    return evaluator


def build_orchestrator(repo: GenomeRepository) -> Orchestrator:
    """Create a SEMAS orchestrator around the five-agent executor."""
    return Orchestrator(
        repository=repo,
        evaluator=build_mingli_evaluator(),
        mutator=Mutator(),
        sandbox=Sandbox(timeout=5, allowed_modules={"math", "datetime", "json", "re", "typing"}),
        agent_name="mingli_orchestrator",
        topology_name="mingli_5agents",
        executor=MingliFiveAgentSystem(repo),
        cooldown_tasks=1,
    )


def demo_task() -> dict[str, Any]:
    return {
        "birth": {
            "name": "Demo Person",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    }


def population_training_tasks() -> list[dict[str, Any]]:
    """Training cases for domain evolution selection."""
    return [
        {
            "input": demo_task(),
            "expected": {
                "feedback": {
                    "satisfaction": 0.5,
                    "corrections": ["too vague", "weak source labels"],
                }
            },
        },
        {
            "input": {
                "birth": {
                    "name": "Validation Person",
                    "birth_date": "1988-11-03",
                    "birth_time": "21:10",
                    "gender": "unspecified",
                    "birthplace": "Chengdu",
                }
            },
            "expected": {
                "feedback": {
                    "satisfaction": 0.6,
                    "corrections": ["needs uncertainty boundary"],
                }
            },
        },
    ]


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="semas_mingli_"))
    try:
        repo = bootstrap_repo(tmp)
        orchestrator = build_orchestrator(repo)
        baseline_trace = orchestrator.run_task(
            demo_task(),
            expected={"feedback": {"satisfaction": 0.65, "corrections": ["more citations"]}},
            allow_evolution=False,
        )
        memory = MingliFeedbackMemory(tmp / "memory" / "feedback_memory.json")
        for item in population_training_tasks():
            memory.remember_feedback(item.get("expected"), notes="demo training feedback")
        population_evolver = MingliPopulationEvolver(
            repo=repo,
            evaluator=build_mingli_evaluator(),
            executor=MingliFiveAgentSystem(repo),
            memory=memory,
        )
        evolved = population_evolver.evolve(
            train_tasks=population_training_tasks(),
            validation_tasks=population_training_tasks()[:1],
        )
        latest = repo.load_agent("mingli_orchestrator")
        evolved_trace = orchestrator.run_task(
            demo_task(),
            expected={"feedback": {"satisfaction": 0.65, "corrections": ["more citations"]}},
            allow_evolution=False,
        )
        archive_events = population_evolver.archive.load()
        memory_profile = memory.profile()
        print(json.dumps(
            {
                "baseline_passed": baseline_trace.evaluation.passed,
                "baseline_score": baseline_trace.evaluation.score,
                "baseline_metrics": baseline_trace.evaluation.metrics,
                "evolved_passed": evolved_trace.evaluation.passed,
                "evolved_score": evolved_trace.evaluation.score,
                "evolved_metrics": evolved_trace.evaluation.metrics,
                "initial_version": baseline_trace.genome_version,
                "latest_version": latest.version,
                "population_accepted": evolved is not None,
                "latest_evolution": latest.meta.get("candidate_name"),
                "archive_events": len(archive_events),
                "memory_profile": memory_profile,
                "output": evolved_trace.task_output["output"],
            },
            ensure_ascii=False,
            indent=2,
        ))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
