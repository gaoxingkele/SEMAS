"""Tests for machine-readable JSON-CLI provider protocol contracts."""

from __future__ import annotations

from copy import deepcopy

from examples.mingli_5agents.method_surface import REQUIRED_METHODS
from examples.mingli_5agents.provider_contracts import raw_json_cli_contract
from examples.mingli_5agents.provider_protocols import _stable_hash, provider_protocol_document, provider_protocol_receipt


def test_provider_protocol_document_covers_all_external_json_cli_domains():
    document = provider_protocol_document()
    domains = document["domains"]

    assert document["protocol_version"] == "json-cli-v1"
    assert len(document["protocol_hash"]) == 64
    assert provider_protocol_document()["protocol_hash"] == document["protocol_hash"]
    assert set(domains) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert domains["ziwei"]["env_var"] == "SEMAS_ZIWEI_CLI"
    assert domains["qimen"]["env_var"] == "SEMAS_QIMEN_CLI"
    assert domains["astrology"]["env_var"] == "SEMAS_ASTROLOGY_CLI"
    assert domains["xuanze"]["env_var"] == "SEMAS_XUANZE_CLI"
    assert domains["ziwei"]["provenance_env_var"] == "SEMAS_ZIWEI_PROVIDER_PROVENANCE"
    assert domains["qimen"]["provenance_env_var"] == "SEMAS_QIMEN_PROVIDER_PROVENANCE"
    assert domains["astrology"]["provenance_env_var"] == "SEMAS_ASTROLOGY_PROVIDER_PROVENANCE"
    assert domains["xuanze"]["provenance_env_var"] == "SEMAS_XUANZE_PROVIDER_PROVENANCE"
    assert all("production_requirements" in domains[domain] for domain in domains)
    assert all("not a bundled" in domains[domain]["production_requirements"][0] for domain in domains)
    assert all("license_or_review" in domains[domain]["production_requirements"][1] for domain in domains)
    assert all(any("required_method_surface" in item for item in domains[domain]["production_requirements"]) for domain in domains)
    assert any("ephemeris source" in item for item in domains["astrology"]["production_requirements"])
    assert any("rule-table source" in item for item in domains["xuanze"]["production_requirements"])
    assert any("stdout.calculation_basis" in item for item in domains["ziwei"]["production_requirements"])
    assert any("stdout.calculation_basis" in item for item in domains["qimen"]["production_requirements"])
    assert all(domains[domain]["required_method_surface"] == sorted(REQUIRED_METHODS[domain]) for domain in domains)
    assert all("chart_contract" in domains[domain]["normalized_contract_requirement"] for domain in domains)
    assert all(domains[domain]["required_provenance_fields"] == ["provider", "version", "source", "license_or_review"] for domain in domains)
    assert all(f"certify-provider {domain}" in domains[domain]["certification_command_template"] for domain in domains)
    assert all(f"provider-drift --domain {domain}" in domains[domain]["drift_command_template"] for domain in domains)
    assert all("production-readiness" in domains[domain]["production_readiness_command_template"] for domain in domains)
    assert all(domains[domain]["deployment_checklist"] for domain in domains)
    assert all("required_method_surface" in " ".join(domains[domain]["deployment_checklist"]) for domain in domains)
    assert all("cannot certify production providers" in domains[domain]["bundled_example_policy"] for domain in domains)
    assert all("sample_stdin" in domains[domain] for domain in domains)
    assert all("sample_stdout" in domains[domain] for domain in domains)
    assert all("sample_stdout_contract" in domains[domain] for domain in domains)
    for domain in domains:
        assert domains[domain]["protocol_version"] == document["protocol_version"]
        assert len(domains[domain]["protocol_hash"]) == 64
        assert provider_protocol_document()["domains"][domain]["protocol_hash"] == domains[domain]["protocol_hash"]
        protocol_material = deepcopy(domains[domain])
        protocol_hash = protocol_material.pop("protocol_hash")
        assert _stable_hash(
            {"domain": domain, "protocol_version": document["protocol_version"], "protocol": protocol_material}
        ) == protocol_hash
        protocol_material["required_method_surface"] = []
        assert _stable_hash(
            {"domain": domain, "protocol_version": document["protocol_version"], "protocol": protocol_material}
        ) != protocol_hash
        sample = domains[domain]["sample_stdin"]
        assert set(domains[domain]["stdin_schema"]["required"]).issubset(sample)
        assert set(domains[domain]["stdin_schema"]["properties"]["birth"]["required"]).issubset(sample["birth"])
        assert domains[domain]["stdin_schema"]["properties"]["protocol"]["required"] == ["version", "hash"]
        assert sample["protocol"]["version"] == document["protocol_version"]
        assert len(sample["protocol"]["hash"]) == 64
        assert sample["birth"]["birth_date"] == "1990-04-12"
        assert sample["birth"]["birth_time"] == "09:20"
    assert document["timeout_seconds"] == 10
    receipt = provider_protocol_receipt(document, repo="repo", domain=None)
    assert receipt == provider_protocol_receipt(document, repo="repo", domain=None)
    assert receipt["schema_version"] == "provider-protocols-receipt-v1"
    assert len(receipt["sha256"]) == 64
    assert receipt["material"]["protocol_hash"] == document["protocol_hash"]
    assert receipt["material"]["domain_count"] == 4
    assert set(receipt["material"]["domain_protocol_hashes"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert receipt["material"]["sample_stdout_contracts_valid"] is True
    assert len(receipt["material"]["protocol_document_sha256"]) == 64


def test_provider_protocol_sample_stdout_matches_minimal_contract_shape():
    domains = provider_protocol_document()["domains"]

    for domain, protocol in domains.items():
        sample = protocol["sample_stdout"]
        schema = protocol["stdout_schema"]
        assert set(schema["required"]).issubset(sample), domain
        assert protocol["sample_stdout_contract"] == raw_json_cli_contract(domain, sample)
        assert protocol["sample_stdout_contract"]["valid"] is True
        assert protocol["sample_stdout_contract"]["missing"] == []

    ziwei_sample = domains["ziwei"]["sample_stdout"]
    assert len(ziwei_sample["palaces"]) == 12
    assert set(domains["ziwei"]["stdout_schema"]["properties"]["palaces"]["items"]["required"]).issubset(
        ziwei_sample["palaces"][0]
    )
    assert set(domains["ziwei"]["stdout_schema"]["properties"]["transformations"]["required"]).issubset(
        ziwei_sample["transformations"]
    )
    assert ziwei_sample["major_limits"]
    assert ziwei_sample["annual_activation"]
    assert set(domains["ziwei"]["stdout_schema"]["properties"]["calculation_basis"]["required"]).issubset(
        ziwei_sample["calculation_basis"]
    )
    assert len(ziwei_sample["calculation_basis"]["rule_source_sha256"]) == 64

    qimen_sample = domains["qimen"]["sample_stdout"]
    assert len(qimen_sample["palaces"]) == 9
    assert set(domains["qimen"]["stdout_schema"]["properties"]["palaces"]["items"]["required"]).issubset(
        qimen_sample["palaces"][0]
    )
    assert set(domains["qimen"]["stdout_schema"]["properties"]["useful_gods"]["required"]).issubset(
        qimen_sample["useful_gods"]
    )
    assert qimen_sample["annual_timing"]
    assert set(domains["qimen"]["stdout_schema"]["properties"]["calculation_basis"]["required"]).issubset(
        qimen_sample["calculation_basis"]
    )
    assert len(qimen_sample["calculation_basis"]["rule_source_sha256"]) == 64

    astrology_sample = domains["astrology"]["sample_stdout"]
    assert len(astrology_sample["planets"]) >= 10
    assert len(astrology_sample["houses"]) == 12
    assert set(domains["astrology"]["stdout_schema"]["properties"]["planets"]["items"]["required"]).issubset(
        astrology_sample["planets"][0]
    )
    assert set(domains["astrology"]["stdout_schema"]["properties"]["houses"]["items"]["required"]).issubset(
        astrology_sample["houses"][0]
    )
    assert astrology_sample["annual_transits"]
    assert set(domains["astrology"]["stdout_schema"]["properties"]["ephemeris"]["required"]).issubset(
        astrology_sample["ephemeris"]
    )
    assert "julian_day_ut" in astrology_sample["ephemeris"]["calculation_time"]

    xuanze_sample = domains["xuanze"]["sample_stdout"]
    assert xuanze_sample["rows"]
    assert xuanze_sample["range"]["count"] == len(xuanze_sample["rows"])
    assert xuanze_sample["basis"]["provider_quality"]
    assert set(domains["xuanze"]["stdout_schema"]["properties"]["basis"]["required"]).issubset(
        xuanze_sample["basis"]
    )
    assert len(xuanze_sample["basis"]["rule_table_sha256"]) == 64
    assert set(domains["xuanze"]["stdout_schema"]["properties"]["rows"]["items"]["required"]).issubset(
        xuanze_sample["rows"][0]
    )
    assert set(domains["xuanze"]["stdout_schema"]["properties"]["summary"]["required"]).issubset(
        xuanze_sample["summary"]
    )


def test_provider_protocol_stdout_schemas_match_live_contract_expectations():
    domains = provider_protocol_document()["domains"]

    ziwei_required = set(domains["ziwei"]["stdout_schema"]["required"])
    assert {
        "ming_palace",
        "body_palace",
        "transformations",
        "palaces",
        "major_limits",
        "annual_activation",
        "calculation_basis",
    }.issubset(ziwei_required)
    assert domains["ziwei"]["stdout_schema"]["properties"]["palaces"]["minItems"] == 12
    ziwei_basis_required = set(domains["ziwei"]["stdout_schema"]["properties"]["calculation_basis"]["required"])
    assert {"rule_set", "rule_set_version", "rule_source", "license_or_review", "calculation_scope"}.issubset(
        ziwei_basis_required
    )

    qimen_required = set(domains["qimen"]["stdout_schema"]["required"])
    assert {
        "duty_door",
        "duty_star",
        "spirit",
        "palaces",
        "useful_gods",
        "annual_timing",
        "calculation_basis",
    }.issubset(qimen_required)
    assert domains["qimen"]["stdout_schema"]["properties"]["palaces"]["minItems"] == 9
    qimen_basis_required = set(domains["qimen"]["stdout_schema"]["properties"]["calculation_basis"]["required"])
    assert {"rule_set", "rule_set_version", "rule_source", "license_or_review", "calculation_scope"}.issubset(
        qimen_basis_required
    )

    astrology_required = set(domains["astrology"]["stdout_schema"]["required"])
    assert {"sun", "moon", "ascendant", "planets", "houses", "annual_transits", "ephemeris"}.issubset(astrology_required)
    assert domains["astrology"]["stdout_schema"]["properties"]["planets"]["minItems"] == 10
    assert domains["astrology"]["stdout_schema"]["properties"]["houses"]["minItems"] == 12
    ephemeris_required = set(domains["astrology"]["stdout_schema"]["properties"]["ephemeris"]["required"])
    assert {"source", "house_system", "time_scale", "calculation_time", "data_source", "license_or_review"}.issubset(
        ephemeris_required
    )

    xuanze_required = set(domains["xuanze"]["stdout_schema"]["required"])
    assert {"basis", "rows", "summary"}.issubset(xuanze_required)
    basis_required = set(domains["xuanze"]["stdout_schema"]["properties"]["basis"]["required"])
    assert {"rule_table_source", "rule_table_version", "license_or_review", "calculation_scope"}.issubset(
        basis_required
    )
    row_required = set(domains["xuanze"]["stdout_schema"]["properties"]["rows"]["items"]["required"])
    assert {"date", "weekday", "ganzhi", "solar_term", "recommended_hours", "risk_notes"}.issubset(row_required)
