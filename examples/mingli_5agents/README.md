# Mingli Five-Agent SEMAS Demo

This example implements the architecture described in `plan_mingli5agents.md` as a runnable SEMAS application.

The system contains one coordinator agent and four specialist agents:

- `mingli_orchestrator`: input validation, dispatch, debate, voting, citation review, final synthesis.
- `bazi_analyst`: BaZi structure and luck-cycle analysis.
- `ziwei_analyst`: Zi Wei Dou Shu palace and star analysis.
- `qimen_analyst`: Qi Men Dun Jia situation analysis.
- `astrology_analyst`: Western astrology chart analysis.

The implementation is deliberately deterministic and offline-friendly. It is a framework scaffold for cultural research, entertainment, and algorithm demonstrations, not a claim that fortune-telling predictions are scientifically valid.

## Run

```bash
python examples/mingli_5agents/run_demo.py
```

The demo runs a baseline analysis, scores it with consistency, citation, and feedback metrics, then runs a population-based SEMAS evolution step. The accepted candidate is saved as the next `mingli_orchestrator` genome version and recorded in an archive.

## Persistent CLI

For repeated local use with persistent genomes, archive, and feedback memory:

```bash
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo init
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo analyze --input birth.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo evolve --input birth.json --feedback feedback.json --validate-on-input
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo benchmark --baseline-version 1
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo status
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo history
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo rollback --to-version 1 --reason "restore stable baseline"
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo audit --classical-source-list path/to/classical_sources.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo known-gap-handoff
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo known-gap-handoff-verify --input handoff.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo known-gap-handoff-checklist --input handoff.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo known-gap-handoff-checklist --input handoff.json --expected-checklist-receipt-sha256 <previous_checklist_receipt_sha256>
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo providers
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo providers --live
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo certify-provider ziwei
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo certify-provider ziwei --command "python path/to/ziwei_provider.py" --provenance "provider=reviewed; version=1.0; source=review; license_or_review=licensed"
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo certify-provider ziwei --expected-receipt-sha256 <previous_receipt_sha256>
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo certify-provider ziwei --record
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo provider-ledger
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo provider-drift
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo provider-drift --domain ziwei
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo provider-protocols
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo provider-protocols --domain ziwei
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo outcome-dataset --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo classical-sources --source-list path/to/classical_sources.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo classical-refresh --source-list path/to/classical_sources.json --cache-dir .semas_mingli_repo/classical_sources/cache --output-dir .semas_mingli_repo/classical_sources/corpus
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo production-readiness --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json --classical-source-list path/to/classical_sources.json --live
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-manifest --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json --classical-source-list path/to/classical_sources.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-manifest --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json --expected-release-manifest-receipt-sha256 <previous_release_manifest_receipt_sha256> --record
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-ledger
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-drift --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json --classical-source-list path/to/classical_sources.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo schema
```

`history` lists every coordinator genome version with its fingerprint, lineage
event, archive hash, and whether the source archive event is still present. It
also returns `history_integrity`, a pass/fail summary for contiguous versions,
lineage presence, fingerprint matches, archive-event presence, and archive
hash-chain status.
Rollback reasons are written into the archive event, genome lineage, rollback
response, and version history.
`certify-provider` focuses on one JSON-CLI provider domain, runs the live smoke
contract by default, checks structured provenance, and reports blockers before
the provider can count toward production readiness. `--command` and
`--provenance` run a one-off certification without mutating environment
variables. Each certification returns a stable `certification_receipt.sha256`
over the contract result, provenance fields, status, and blockers for deployment
audit records. `--expected-receipt-sha256` compares the current certification
with an archived receipt and reports `receipt_matches_expected` without changing
the receipt hash itself. `--record` appends a passing certification to
`providers/provider_certification_ledger.json` with a per-record hash chain for
deployment audit. `provider-ledger` reports `integrity_status`,
`coverage_status`, the ledger hash-chain status, and which provider domains
already have recorded certification receipts.
`provider-drift` re-certifies current configured provider commands and compares
their receipts with the latest ledger receipts without running the full
production-readiness gate. `--domain` narrows the check to one provider domain.
`provider-protocols` returns the machine-readable JSON-CLI contracts that real
professional engines must implement. `--domain` narrows the protocol document to
one provider domain. Each domain includes `sample_stdin`, `sample_stdout`, and a
`sample_stdout_contract` result for local adapter debugging. The protocol
document also exposes stable `protocol_version` and `protocol_hash` values that
provider certification receipts record for deployment audit. The provider
ledger reports whether the latest recorded receipt for each domain still matches
the current protocol hash, and production readiness blocks stale protocol
certifications.
`providers --live` reports the same protocol version/hash on JSON-CLI readiness
checks and live smoke results, so adapter debugging and certification receipts
can be compared against the same contract identity.
Provider integration-plan targets also list the protocol hashes for JSON-CLI
candidate checks.
`outcome-dataset` audits an external outcome manifest and returns both the
governance audit and the non-predictive SEMAS evolution-gate decision. Its
`data_split_record_coverage` section verifies that every `records[].case_id` is
assigned to exactly one frozen split, either `data_split.train_case_ids` or
`data_split.holdout_case_ids`, and reports unassigned, unknown, overlapping
case IDs plus a stable `split_fingerprint`.
`production-readiness` aggregates hard provider, provider-ledger hash-chain and
coverage, live receipt-drift, outcome-dataset, archive, lineage, capability,
known-gap resolution-plan coverage, classical-source refresh, and release-ledger integrity gates into one
production-ready/blocked response. A missing release ledger does not block
readiness before the first release, but an existing release ledger must pass
hash-chain and receipt-integrity checks. Production readiness also requires
`SEMAS_CLASSIC_SOURCE_LIST` to point at an allowlisted, SHA-256-pinned external
classical-source manifest list; seed-only evidence remains usable for local
demo analysis but is not enough for production claims. Outcome manifests must
also pass the `outcome_dataset_data_split_records_covered` gate before readiness
can pass.
`release-manifest` aggregates status, history, archive, capability-audit,
benchmark, production-readiness, provider-ledger, and outcome-dataset evidence
into one stable `release_manifest_receipt`. It accepts expected audit,
benchmark, readiness, and release-manifest receipt hashes so CI can detect
capability, benchmark, or release drift before publishing a build. Its receipt
uses the benchmark receipt already bound inside `production-readiness`, keeping
release evidence deterministic without running the current benchmark twice.
Release material also exposes readiness benchmark deliberation-receipt coverage,
claim counts, and receipt hashes so release audit can prove every benchmark case
had a bound final-report deliberation receipt. It also exposes external-payload
birth-match coverage and provider action-plan coverage derived from readiness
benchmark blockers, including unresolved cases and per-case blocker/action-plan
counts, so release drift catches provider-gap governance regressions before
publication. Classical source-list receipt coverage is surfaced in the same
release material, so source allowlist/hash-pin configuration drift is visible
without opening the readiness receipt. Known-gap resolution-plan coverage is
also bound into readiness and release receipts, so CI can prove every open
professional/source/dataset gap still has closure criteria, verification
commands, and production gate IDs. Those verification commands are parsed
against the current CLI subcommands and option surface, and readiness/release
receipts expose `command_validation_complete`, invalid command/option maps,
observed subcommands/options, and a stable command coverage hash. Capability
audit exposes `known_gap_command_coverage_release_binding`, and release gate
checks include `known_gap_command_coverage_bound`, so runbook interface coverage
is part of release approval. Capability audit also exposes
`known_gap_handoff_bundle`, a portable per-gap closure package that binds owner
domain, blocking scope, closure condition, provider environment variables,
provenance variables, verification commands, production gates, external
candidate projects, blocked capabilities, and a stable bundle hash. Production
readiness gates this as `known_gap_handoff_bundle_ready`; release manifests bind
the decision as `known_gap_handoff_bundle_bound` and carry the bundle in release
receipt material, so release drift can detect changed gap-handoff instructions.
Capability audit reports this release birth-match coverage as
`release_manifest_external_payload_birth_match_coverage`
with materialized evidence. The release `release_gate_checks` also includes
`provider_onboarding_receipt_current`, `provider_protocols_receipt_current`, and
`outcome_dataset_split_coverage_bound`, proving that the release evidence bound
the current real-provider onboarding checklist, current JSON-CLI protocol
document, and the same complete outcome split coverage before release approval.
It also includes `provider_audit_contract_gates_bound`,
`outcome_statistical_plan_preregistration_bound`, and
`classical_latest_refresh_receipt_bound`, proving that the provider provenance
contracts, pre-registered outcome statistical plan, and latest classical-source
refresh receipt are represented in the readiness receipt and its blocker chain
before release approval. Capability audit exposes this as
`release_manifest_readiness_gate_binding` with materialized runtime/schema
evidence, so the binding itself is regression-checked. Capability audit also
exposes `blocked_capability_coverage`, mapping every current false capability to
an open known gap or an explicit optional-configuration policy; this keeps
missing provider/source/LLM configuration visible without treating scaffolds as
production providers. Production readiness gates this as
`blocked_capability_coverage_complete`, and release manifests bind the decision
as `blocked_capability_coverage_bound`. The release
`provider_ledger` summary includes protocol, request-receipt, and
reference-contract status, plus reference-contract failures, so provider
certification drift is visible in the release receipt without opening the full
provider ledger. `--record`
appends a ready release manifest to `release/release_manifest_ledger.json` with
a per-record hash chain, but recording is blocked when an expected release
manifest receipt is provided and does not match the current receipt.
`release-ledger` reports release-ledger existence, hash-chain integrity, record
count, latest record hash, latest release receipt, and tamper failures.
`release-drift` compares the current release manifest receipt with the latest
recorded release-ledger receipt. If the release ledger is missing or fails
integrity checks, drift is reported as `not_checked` rather than returning a
misleading pass/fail comparison.

Optional professional calendar backends can be installed with:

```bash
pip install -e ".[mingli]"
```

Optional OpenAI-compatible LLM synthesis can be installed with:

```bash
pip install -e ".[llm]"
```

Optional Swiss Ephemeris-backed Western astrology can be installed with:

```bash
pip install -e ".[astrology]"
```

Optional kinqimen-backed Qi Men provider can be installed with:

```bash
pip install -e ".[qimen]"
```

If local native dependencies cannot be installed, Qi Men can also be connected
through a JSON-speaking CLI command:

```bash
set SEMAS_QIMEN_CLI=python path\to\your_qimen_provider.py
```

Bundled protocol example:

```bash
set SEMAS_QIMEN_CLI=python examples\mingli_5agents\providers\qimen_json_cli_example.py
python examples\mingli_5agents\cli.py --repo .semas_mingli_repo providers --live
```

Optional Zi Wei professional engines can be connected through a JSON-speaking
CLI command:

```bash
set SEMAS_ZIWEI_CLI=python path\to\your_ziwei_provider.py
```

Bundled protocol example:

```bash
set SEMAS_ZIWEI_CLI=python examples\mingli_5agents\providers\ziwei_json_cli_example.py
python examples\mingli_5agents\cli.py --repo .semas_mingli_repo providers --live
```

Western astrology can also be connected through a JSON-speaking ephemeris CLI:

```bash
set SEMAS_ASTROLOGY_CLI=python path\to\your_astrology_provider.py
```

Bundled protocol example:

```bash
set SEMAS_ASTROLOGY_CLI=python examples\mingli_5agents\providers\astrology_json_cli_example.py
python examples\mingli_5agents\cli.py --repo .semas_mingli_repo providers --live
```

Tongshu/xuanze auspicious-day calculation can be connected through a JSON-speaking CLI:

```bash
set SEMAS_XUANZE_CLI=python path\to\your_xuanze_provider.py
```

Bundled protocol example:

```bash
set SEMAS_XUANZE_CLI=python examples\mingli_5agents\providers\xuanze_json_cli_example.py
python examples\mingli_5agents\cli.py --repo .semas_mingli_repo providers --live
```

`birth.json`:

```json
{
  "birth": {
    "name": "Demo Person",
    "birth_date": "1990-04-12",
    "birth_time": "09:20",
    "gender": "unspecified",
    "birthplace": "Hangzhou"
  },
  "annual_start_year": 2024,
  "annual_end_year": 2026,
  "monthly_years": [2025, 2026],
  "auspicious_start_date": "2026-06-21",
  "auspicious_end_date": "2026-06-27",
  "calendar_provider": "auto",
  "language": "zh",
  "llm_synthesis": {"enabled": false},
  "professional_charts": {
    "bazi": {
      "source": "your_verified_bazi_engine",
      "pillars": {
        "year": "GengWu",
        "month": "GengChen",
        "day": "DingWei",
        "hour": "YiSi"
      }
    },
    "ziwei": {
      "source": "your_verified_provider",
      "ming_palace": "Career",
      "body_palace": "Wealth"
    },
    "xuanze": {
      "source": "your_verified_tongshu",
      "rows": []
    }
  }
}
```

`birth_place` is also accepted as an alias for `birthplace`. If no annual range
is supplied, the structured annual-luck table runs from birth year through the
current local year. If no monthly years are supplied, the monthly refinement
table expands only the latest three years to keep default reports bounded.
If no auspicious-date range is supplied, the xuanze/huangdao scaffold emits a
bounded seven-day window from the current local date.
`calendar_provider` can be `approximate`, `auto`, or `professional`. The
default is `auto`: it uses an installed professional BaZi calendar backend when
available and otherwise falls back to the deterministic approximate provider.
Use `approximate` explicitly for fixed offline regression fixtures.
`language` can be `en` or `zh`; `zh` returns a Chinese Markdown report in the
top-level `output` while both languages remain available at
`final_report.rendered_reports`.
`professional_charts` can inject externally verified BaZi, Zi Wei, Qi Men,
Western astrology, or xuanze/tongshu payloads under `bazi`, `ziwei`, `qimen`,
`astrology`, or `xuanze`. The built-in engines remain deterministic symbolic
scaffolds, but injected payloads are marked with
`provider_quality: external_<domain>` and keep the same downstream schema.
Each request-scoped external payload gets an `external_payload_receipt` that
binds the normalized birth profile, payload hash, provenance hash, and optional
payload-declared `birth`/`birth_profile` audit. If a payload declares birth
data and it differs from the current request, `provider_summary` exposes
`external_payload_birth_match_status: mismatch`, lists the mismatched fields,
and keeps that domain out of `production_ready`. Payloads without declared
birth data remain compatible but are reported as `not_declared`. Capability
audit exposes this request-scoped path as
`request_scoped_external_payload_birth_match_audit`.
`provider_summary` also includes a `readiness_matrix` plus per-domain
`interpretation_mode`, `confidence_level`, and `blocking_reasons`, so report
consumers can distinguish production-grade provider output from symbolic
fallbacks or blocked external payloads. Capability audit exposes this guard as
`provider_interpretation_readiness_matrix`.
Each topic in `final_report.topic_synthesis` includes `synthesis_confidence`,
which counts timing evidence, cross-agent support, production-ready provider
coverage, fallback domains, blocked domains, and downgrade reasons. This score
is an evidence/readiness audit for report synthesis, not empirical proof of
prediction accuracy. Benchmark and empirical-validation runs project the same
summary into `report_features.topic_confidence_summary`, and production
readiness includes `benchmark_topic_confidence_boundaries` so releases cannot
drop topic confidence boundaries silently.
`providers --live` now checks configured JSON-CLI engines against the same
production contract expected by downstream reports: Zi Wei must return palace,
four-transformation, major-limit, annual-activation rows, and
`calculation_basis` rule-source metadata; Qi Men must return nine palace rows,
duty fields, useful-god mappings, annual timing, and `calculation_basis`
rule-source metadata; astrology must return planet, house, transit rows, and
auditable `ephemeris` metadata; xuanze must return full almanac rows, summary
fields, and auditable rule-table `basis` metadata. Partial smoke outputs are
treated as configured but not production-ready. Production readiness also checks
that the Ziwei/Qimen calculation-basis, astrology ephemeris, and xuanze
rule-table audit contracts remain registered as release gates.
The bundled scripts under `providers/*_json_cli_example.py` are protocol
templates for adapter wiring and live-smoke verification. They can make
`providers --profile production --live` pass at the adapter-contract layer when
configured through `SEMAS_*_CLI`, but they do not claim professional domain
calculation quality; replace them with verified engines before production use.
`llm_synthesis.enabled` can be set to `true` to request an optional LLM prose
synthesis. Without an external backend configured, the framework records a
stub/skipped status and keeps deterministic reports unchanged.
For API convenience, `llm_synthesis: false` is also accepted as a shorthand for
disabled synthesis.

`feedback.json`:

```json
{
  "feedback": {
    "satisfaction": 0.5,
    "corrections": ["too vague", "weak source labels", "needs uncertainty boundary"]
  }
}
```

The CLI prints JSON so it can be used by scripts, web services, or future UI layers.

## Optional LLM Backend

The deterministic report pipeline is the default and is fully testable without
API keys. For optional LLM prose synthesis, configure an OpenAI-compatible
backend through environment variables:

```bash
set SEMAS_LLM_API_KEY=...
set SEMAS_LLM_BASE_URL=https://your-openai-compatible-endpoint
set SEMAS_LLM_MODEL=kimi-2.7-or-compatible-model
```

`semas/utils/llm_client.py` also recognizes `OPENAI_API_KEY`, `KIMI_API_KEY`,
and `DEEPSEEK_API_KEY`, plus provider-specific `KIMI_MODEL`, `KIMI_BASE_URL`,
`DEEPSEEK_MODEL`, and `DEEPSEEK_BASE_URL` when generic `SEMAS_LLM_*` variables
are not set. `status` and `audit` include a non-secret `llm_backend` block that
reports whether the runtime is using the stub or an OpenAI-compatible backend.
The LLM layer never replaces structured fields; it only adds
`final_report.llm_synthesis`.

## HTTP API

The example also includes a stdlib HTTP server with no extra web dependency:

```bash
python examples/mingli_5agents/api_server.py --repo .semas_mingli_repo --host 127.0.0.1 --port 8765
```

Endpoints:

- `GET /health`
- `GET /status`
- `GET /history`
- `GET /audit`
- `GET /known-gap-handoff`
- `GET /providers`
- `GET /certify-provider`
- `GET /provider-ledger`
- `GET /provider-drift`
- `GET /provider-protocols`
- `GET /outcome-dataset`
- `GET /classical-sources`
- `GET /classical-refresh`
- `GET /production-readiness`
- `GET /release-manifest`
- `GET /release-ledger`
- `GET /release-drift`
- `GET /schema`
- `POST /analyze`
- `POST /evolve`
- `POST /known-gap-handoff-verify`
- `POST /known-gap-handoff-checklist`
- `POST /rollback`
- `POST /benchmark`

`POST /analyze` accepts the same JSON shape as `birth.json`. `POST /evolve`
accepts `{"input": <analyze request>, "feedback": <feedback object>,
"validate_on_input": true}` and returns an `EvolveResponse` with
`selection_decision`, named acceptance gates, validation-task count, and
rejection reasons. The server intentionally reuses `api_core.py`, the
same service layer used by the CLI, so CLI and HTTP behavior stay aligned.
`POST /known-gap-handoff-verify` and `POST /known-gap-handoff-checklist`
accept `{"handoff_export": <KnownGapHandoffExportResponse>}` and mirror the CLI
verification/checklist outputs for non-shell runtimes.
`GET /history` returns `VersionHistoryResponse`, a version-by-version lineage
view for the coordinator genome. `POST /rollback` accepts `RollbackRequest`
with `to_version` and optional `reason`, creates a new latest genome version
from a prior version, and writes an audited rollback archive event.
`GET /certify-provider?domain=ziwei&live=1&command=...&provenance=...&expected_receipt_sha256=...&record=1` returns
`ProviderCertificationResponse` for one JSON-CLI provider and is intended for
acceptance-testing real professional provider commands.
`GET /provider-ledger` returns the provider certification ledger integrity and
domain-coverage summary.
`GET /provider-drift?live=1&domain=ziwei` returns the current-provider receipt
drift check against the certification ledger, optionally narrowed to one domain.
`GET /provider-protocols?domain=ziwei` returns the JSON-CLI stdin/stdout
contracts, `sample_stdin`, `sample_stdout`, and `sample_stdout_contract` for all
external professional provider domains or one selected domain, plus stable
protocol version/hash metadata.
`GET /outcome-dataset?manifest=path-to-json` returns
`OutcomeDatasetAuditResponse`, including consent/privacy/statistical-plan
checks and a gate showing that only non-predictive quality labels may drive
validation. It also returns `data_split_record_coverage`, with record/train/
holdout counts, unassigned/unknown/overlap case IDs, `coverage_complete`, and a
`split_fingerprint`.
`GET /production-readiness?manifest=path-to-json&live=1` returns
`ProductionReadinessResponse`, a strict go-live gate that remains blocked until
professional providers, live provider smoke checks, provider certification
ledger hash-chain integrity and coverage for every JSON-CLI domain, outcome
governance, benchmark birthplace geocoding, benchmark deliberation-receipt
coverage, benchmark external-payload birth-profile matching, known-gap
resolution-plan coverage, archive integrity, and version-history integrity all
pass. The outcome split gate is exposed as
`outcome_dataset_data_split_records_covered`, and failed split coverage adds a
split-specific remediation step to `resolution_plan`. With
`live=1`, it also re-certifies the current provider commands and compares their
receipts with the latest ledger receipts to detect provider drift.
The response also includes `resolution_plan`, a priority-ordered remediation
plan with provider certification commands, provider-drift commands, ledger
coverage steps, outcome-manifest fixes, diagnostics, and deployment checklist
items derived from the failed gates. Provider-ledger remediation steps include
full `certify-provider <domain> --command ... --provenance ... --record`
templates for missing receipts, request-level receipt binding, and
reference-contract coverage failures. The readiness receipt binds a compact
`production_resolution_plan_summary` with step IDs, command counts, categories,
and a full resolution-plan hash; release receipts and release-ledger records
carry the same summary so CI can detect remediation-plan drift.
`GET /release-manifest?manifest=path-to-json&expected_release_manifest_receipt_sha256=...&record=1`
returns `ReleaseManifestResponse`, a release evidence bundle with the current
audit, benchmark, readiness, provider-ledger, outcome, and known-gap receipt
hashes. `record=1` appends the manifest to the release ledger only when the
manifest is ready and any supplied expected release-manifest receipt matches.
`release_approval_ready`, `release_approval_status`, and `release_blockers`
separate evidence-manifest generation from release approval; a manifest can be
generated and ledgered while still explicitly blocked for approval when
`production_ready` is false. These approval fields are also bound into the
release receipt material and release-ledger integrity checks, so approval-state
drift is detectable.
The release receipt material includes readiness deliberation-receipt coverage,
external-payload birth-match coverage, provider action-plan coverage,
classical source-list receipt coverage, known-gap resolution-plan coverage,
`provider_onboarding_receipt`, and `provider_protocols_receipt`, all hashed into
the release ledger record. `release_gate_checks` includes
`provider_onboarding_receipt_current`, `provider_protocols_receipt_current`, and
`outcome_dataset_split_coverage_bound`, so CI can reject a release whose provider
onboarding/protocol evidence or readiness split coverage is stale.
`GET /release-ledger` returns `ReleaseManifestLedgerResponse`, including
release-ledger hash-chain integrity and tamper failures.
`GET /release-drift?manifest=path-to-json` returns
`ReleaseManifestDriftResponse`, comparing the current release manifest receipt
with the latest recorded release-ledger receipt.

`GET /schema` returns compact JSON schemas for `AnalyzeRequest`,
`AnalyzeResponse`, `EvolveRequest`, `EvolveResponse`,
`EvolutionSelectionDecision`, `ProviderSummary`, `ProviderDomainStatus`,
`SpecialistReport`, `SpecialistLayer`, and `BenchmarkResult`. The response schemas explicitly expose
`final_report.provider_summary`, `provider_summary_status`, and
`provider_blocker_count` so clients can consume production-readiness signals
without scraping rendered text.
It also includes `provider_protocols`, a machine-readable contract for external
JSON-CLI engines. Each domain lists its environment variable, example command,
stdin schema, stdout schema used by `providers --live`, required provenance
fields, certification command template, drift-check command template, and
deployment checklist, so a real Zi Wei, Qi Men, astrology, or xuanze backend can
be implemented and certified without reverse-engineering the Python adapters.

`GET /audit` and the CLI `audit` command return a machine-readable capability
matrix. It separates implemented SEMAS orchestration/evolution/reporting
features from known professional-grade gaps, such as verified Zi Wei and Qi Men
calculation providers, ephemeris-backed astrology, external classical-text
retrieval, and empirical validation datasets.
When no `SEMAS_CLASSIC_SOURCE_LIST` or `--classical-source-list` is provided,
the Mingli capability audit uses the bundled
`providers/classical_source_list_example.json` as a copyright-safe, hash-pinned
demonstration source list. This closes the source-list configuration capability
without treating the bundled example as production evidence: production
readiness and release approval still require a latest classical-source refresh
receipt, so operators must run `classical-refresh` and bind the resulting
receipt before the external classical-text gap can close.
The audit also includes `plan_compliance`, a section-by-section matrix mapped
to `plan_mingli5agents.md`, with verified implemented requirement IDs and known
gap IDs for each plan section. `section_gap_resolution_coverage` then binds
those section-level gaps back to the known-gap remediation plan, including
planned gap IDs, command counts, and production gate IDs for each affected
section.
`known_gap_resolution_plan` turns every open known gap into a deterministic
remediation item with closure criteria, verification commands, owner domain,
blocking scope, and production gate IDs. Professional provider gaps explicitly
include both provider certification protocol gates and reference-contract
coverage gates, so a backend must be certified against the declared protocol and
the domain reference fixtures before the gap can close. The audit receipt binds
this plan with `known_gap_resolution_plan_hash` so release tooling can detect
drift in the gap-closure plan. `known_gap_handoff_bundle` then packages the
same open gaps for transfer to another runtime or team, adding required
`SEMAS_*_CLI` and provenance variables where applicable, GitHub candidate
projects such as iztro-family Zi Wei engines, `kinqimen`, and `pyswisseph`,
blocked capability mappings, `handoff_ready` flags, and `bundle_sha256`.
Production readiness and release manifests now bind this bundle, so a release
cannot silently drop the external-closure handoff package while still carrying
the older known-gap resolution plan. The CLI command `known-gap-handoff` and
HTTP endpoint `GET /known-gap-handoff` export the same bundle with
`audit_receipt_sha256`, optional expected-audit drift fields, and
`handoff_export_receipt`, allowing another runtime or agent to consume and verify
the closure package without parsing the full audit. `known-gap-handoff-verify`
recomputes the bundle hash, export receipt material, export receipt hash, and
known-gap ID binding for an exported JSON file; the CLI accepts UTF-8 and
PowerShell UTF-16 redirected JSON files. `known-gap-handoff-checklist` verifies
the export and turns it into per-gap implementation checklists with env vars,
provenance vars, candidate projects, verification commands, production gates,
blocked capabilities, closure conditions, and a checklist receipt. The checklist
command and `POST /known-gap-handoff-checklist` also accept an expected
checklist receipt SHA-256, allowing downstream agents to detect implementation
checklist drift before using the generated work packet.

The same audit output includes `state_of_art` and `github_comparison_matrix`.
The current verdict is intentionally conservative: the project is advanced for
SEMAS-style multi-agent orchestration, evolution gates, source governance,
Chinese reporting, and safety validation; it is not yet state-of-the-art for
specialized domain calculation until production providers such as an
iztro-family Zi Wei engine, `kinqimen`, `pyswisseph`, and a verified
tongshu/xuanze engine are configured and covered by reference fixtures.

Audit separates environment-installed provider readiness from request-scoped
professional payload readiness. `state_of_art.production_ready_for_professional_calculation`
refers to providers configured in the runtime environment, while
`state_of_art.request_scoped_production_ready_path` and
`request_scoped_provider_contract` report whether one analysis request can
reach `production_ready` by supplying verified `professional_charts` payloads
for all five domains. Request-scoped receipts also expose optional declared
birth-profile matching so production consumers can reject payloads generated for
the wrong person or time.

`GET /providers` and the CLI `providers` command return non-destructive
readiness checks for optional professional backends: `lunar_python`, `sxtwl`,
`SEMAS_ZIWEI_CLI`, `kinqimen`, `SEMAS_QIMEN_CLI`, `pyswisseph`,
`SEMAS_ASTROLOGY_CLI`, and `SEMAS_XUANZE_CLI`. These checks report what is
installed or configured without executing user-supplied JSON-CLI commands by
default, include install hints and native-build blocking details where known,
and include the fixed reference-chart contract status.

Use CLI `providers --live` or HTTP `GET /providers?live=1` to execute configured
JSON-CLI providers with a minimal smoke-test payload. Live checks verify that a
provider command starts, accepts JSON on stdin, returns JSON on stdout, and
includes required top-level fields.

Provider checks support two profiles:

- `development` is the default and allows symbolic fallbacks while showing
  optional gaps.
- `production` requires professional BaZi/calendar support plus ready Zi Wei,
  Qi Men, astrology/ephemeris, and xuanze/almanac providers. Use
  `providers --profile production --live` or
  `GET /providers?profile=production&live=1` to require live smoke checks for
  configured JSON-CLI providers.

The provider response also includes `integration_plan`, a machine-readable
production checklist. It groups required provider targets, accepted checks,
blocked checks, contract names, relevant environment variables, next actions,
the exact live smoke command needed before claiming production readiness,
per-domain certification command templates, provider-ledger recording steps,
drift-check commands, required provenance fields, and a bundled-example policy.
Bundled `*_json_cli_example.py` scripts are protocol fixtures for smoke tests;
they are explicitly blocked from production certification receipts.
`provider-onboarding` emits a stable `provider_onboarding_receipt` with
`missing_evidence_by_domain` and `missing_evidence_counts`, so release and audit
logs can show both per-domain blockers and aggregate provider-certification gaps
without expanding every provider row.
`certify-provider` responses and receipts now include
`reference_contract_coverage`, a domain-level summary of covered reference
cases, observed/missing method names, provenance coverage, and a stable coverage
hash. Provider-ledger status exposes `reference_contract_status` and per-domain
`reference_contract_covered` fields so production readiness can distinguish a
provider that merely runs from a provider whose certification is tied to fixed
reference-chart contracts.
Each provider readiness check also includes `install_diagnostics`, which reports
the Python version, platform, dependency module, native-build risk, suggested
install command, and remediation path. On Windows/Python versions without
prebuilt wheels, native packages such as `pyswisseph`, `sxtwl`, or `kinqimen`
may require Microsoft C++ Build Tools; JSON-CLI providers remain the preferred
deployment boundary when native packages are hard to install in-process.

## Benchmarking

`benchmark.py` defines built-in regression/leaderboard cases covering feedback,
citation, workflow, safety boundaries, report schema, Chinese rendering,
topic synthesis, auto/professional calendar-provider behavior, and a five-domain
external-provider production-readiness case. It reports:

- per-case pass/fail and metric breakdown,
- aggregate average score,
- pass rate,
- mean metrics,
- version-to-version deltas,
- report features such as topic count, Chinese renderer availability, provider
  quality, output language, request-provenance coverage, deliberation-receipt
  coverage, external-payload receipt coverage, and provider action-plan
  coverage for production blockers,
- `reference_charts`, a provider-contract check suite that verifies external
  BaZi, Zi Wei, Qi Men, Western astrology, and xuanze/almanac fixture behavior,
  baseline BaZi and xuanze timing contracts, and required method-matrix
  coverage for every production domain,
- `empirical_validation`, a non-predictive validation harness with explicit
  label policy and zero predictive-truth cases by default.

Use the CLI `benchmark` command after evolution to confirm that a new genome improves the benchmark and does not regress source grounding, safety, or workflow quality.

`reference_charts.py` contains fixed provider-contract fixtures. These checks do
not claim predictive validity; they verify that professional/external provider
payloads, core BaZi structures, xuanze/almanac timing rows, and all domain
method matrices keep their expected schema and key fields as the SEMAS system
evolves. `benchmark.reference_charts.method_coverage` reports required,
observed, and missing methods per domain.

`empirical_validation.py` separates objectively checkable report-quality labels
from unavailable predictive-truth labels. Current cases validate safety,
structure, evidence provenance, provider contracts, Chinese rendering, and
timing-table coverage. Predictive optimization remains disabled until an
ethically usable outcome dataset, baselines, label definitions, and statistical
tests exist.

`outcome_dataset.py` defines that future dataset boundary. If
`SEMAS_OUTCOME_DATASET_MANIFEST` points at a JSON manifest, `capability_audit`
will check consent, deidentification, direct-identifier removal, label
definitions, baselines, statistical plan, duplicate case IDs, record-label
references, label-type consistency, and a declared integer minimum sample size
of at least 30. A valid manifest is reported as `ready_for_review`; it still keeps
`predictive_optimization_enabled: false` until an external review explicitly
approves the dataset and study design.
The audit output includes `governance_gates`, `label_inventory`, and
`optimization_policy`. Record labels whose IDs are undefined, whose type differs
from the label definition, or whose manifest fails deidentification/statistical
gates are rejected before any validation task is created. Only `report_quality`
and `schema_quality` labels can become SEMAS validation tasks; `life_event_outcome`
labels remain audit-only.
The public `/schema` document exposes the same manifest shape as
`OutcomeDatasetManifest`, including consent, privacy, label definitions,
baselines, statistical plans, deidentified records, record labels, and frozen
`data_split` membership. Every case in `records` must appear in exactly one of
`data_split.train_case_ids` or `data_split.holdout_case_ids`; IDs listed in the
split but absent from `records`, IDs listed in both splits, and records missing
from both splits block the dataset gate. `/schema` also exposes
`OutcomeDataSplitRecordCoverage` and `ReleaseManifestGateChecks`, including the
release-level `outcome_dataset_split_coverage_bound` check.
The `statistical_plan` must also be pre-registered and frozen with
`pre_registered`, `registration_id`, `registered_at`, `analysis_freeze_date`,
and either `plan_sha256` or `plan_receipt_sha256`; production readiness exposes
`outcome_dataset_statistical_plan_preregistered` so releases cannot use a
mutable post-hoc analysis plan.
Projected quality-task fingerprints include a `split_role` field. By default,
`empirical_validation_tasks()` imports only `holdout` manifest quality labels as
SEMAS validation tasks, so train-split records cannot silently leak into the
validation gate. Operators can explicitly request `train` or `any` split roles
for offline inspection, but the production evolution path remains holdout-first.
An executable example lives at
`providers/outcome_dataset_manifest_example.json`:

```bash
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo outcome-dataset --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json

SEMAS_OUTCOME_DATASET_MANIFEST=examples/mingli_5agents/providers/outcome_dataset_manifest_example.json \
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo audit

SEMAS_OUTCOME_DATASET_MANIFEST=examples/mingli_5agents/providers/outcome_dataset_manifest_example.json \
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo benchmark
```

The example intentionally contains both `life_event_outcome` and
`report_quality` labels. Only `report_quality` and `schema_quality` records are
converted into validation tasks; `life_event_outcome` remains audit-only.

## Evolution Surface

SEMAS can evolve these editable artifacts:

- System prompts in `genomes/*.yaml`
- Few-shot examples in agent genomes
- Tool functions under `tools/`
- Discussion and voting topology encoded by `MingliFiveAgentSystem`
- Evaluation metrics under `evaluators/`
- Local source registry in `knowledge_base.py`
- Local evidence retrieval in `evidence.py`
- Allowlisted classical-source manifest audit, refresh, cache, and JSONL ingestion
  in `classical_corpus_refresh.py`, surfaced through `classical-sources`,
  `classical-refresh`, `GET /classical-sources`, and `GET /classical-refresh`.
- Safety and scope-boundary rules in `safety_evaluator.py`
- Shared calendar and chart context in `tools/calendar_core.py`
- Structured BaZi ten-god, hidden-stem, Na Yin, growth-stage, and major-luck details in `tools/bazi_deep_analysis.py`
- BaZi eight-school method matrix in `tools/bazi_deep_analysis.py`, covering
  Ziping pattern, strength/support, blind-school workflow, shensha/nayin,
  tiaohou, image-symbol reading, simplified polarity, and governed
  data-validation boundaries.
- Shared production method surfaces in `method_surface.py`; reference charts
  and provider production contracts both consume this module so method coverage
  cannot drift silently.
- Structured Zi Wei twelve-palace, four-transformation, major-limit, and annual activation rows in `tools/ziwei_deep_analysis.py`
- Structured Qi Men nine-palace, door-star-spirit, useful-god, and annual timing rows in `tools/qimen_deep_analysis.py`
- Structured Western astrology natal planets, houses, aspects, and annual transit rows in `tools/astrology_deep_analysis.py`
- Structured annual luck-cycle rows in `tools/annual_luck.py`
- Selected-year monthly luck-cycle rows in `tools/monthly_luck.py`
- Replaceable calendar providers in `tools/calendar_provider.py`
- Workflow topology genes in `workflow.py`; the default coordinator genome now
  uses two discussion rounds, cross-agent challenge, reconciliation, conflict
  preservation, and a 0.75 vote threshold.
- Claim-level vote audit records in `final_report.votes._claims` and
  `final_report.votes._audit`; these bind each accepted synthesis claim to
  supporters, preserved challenges, source IDs, thresholds, and pass/fail
  decisions.
- Deliberation receipts in `final_report.deliberation_receipt`; these hash the
  discussion transcript, vote record, source review, conflict list, and workflow
  settings, and their receipt hash is included in request provenance.
- Long-term feedback memory in `memory.py`
- CLI and HTTP service functions in `api_core.py` and `api_server.py`
- Optional LLM synthesis in `llm_synthesis.py` through `semas/utils/llm_client.py`

## Population Evolution

`evolution.py` adds a domain-specific population layer on top of the generic SEMAS orchestrator:

- Generates candidate coordinator genomes for feedback adaptation, citation precision, debate depth, safety guardrails, and synthesis calibration.
- Evolves workflow genes such as discussion depth, cross-checks, reconciliation, source-review strictness, conflict preservation, and vote threshold.
- Scores candidates across training tasks with the same SEMAS evaluator used by runtime execution.
- Applies metric floors for citation, safety, consistency, workflow quality, report schema, provider-contract regressions, evidence provenance, and Chinese rendering before accepting a genome.
- Selects from the Pareto front across citation, safety, consistency, workflow, report schema, provider contracts, evidence provenance, Chinese rendering, feedback, and memory-adjusted score.
- Runs the registered regression suite before committing a candidate.
- Optionally validates the best candidate on holdout tasks.
- Writes an append-only archive to `<repo>/archives/mingli_evolution.json`, including the selected candidate, Pareto front, metric floors, validation result, and a `selection_decision` object with named gates and rejection reasons.
- Records `reproducibility_manifest.cost_governance` for every evolution and benchmark run. It lists candidate count, training/validation task counts, total candidate-task evaluations, LLM and remote-provider call budgets, and the manual/feedback-triggered iteration policy, so SEMAS evolution cost and frequency are auditable before production automation.
- Uses `memory.py` to convert recurring corrections and accepted strategies into bounded strategy priors.

## Long-Term Memory

`memory.py` stores normalized feedback and accepted evolution events as JSON. It summarizes:

- recurring correction phrases,
- unsafe correction phrases that request deterministic or high-stakes advice,
- strategy priors inferred from corrections such as vague output, weak citations, missing uncertainty, and debate/conflict issues,
- accepted strategies and observed score deltas.

Unsafe corrections are quarantined from ordinary correction counts and only reinforce `safety_guardrails`. The population evolver uses this profile as a bounded selection bonus, so historical feedback can influence future candidate selection without bypassing regression, validation, citation, safety, or workflow gates.

## Multi-Objective Selection

Candidate selection is not based on a single average score alone. `evolution.py` records each candidate's mean metrics, rejection reasons, Pareto-front membership, validation task count, and named acceptance gates. A candidate must satisfy metric floors before it can be accepted:

- citation >= 0.95
- safety >= 1.0
- consistency >= 0.8
- workflow >= 0.8
- report_schema >= 0.9
- provider_contracts >= 1.0
- evidence_provenance >= 1.0
- chinese_render >= 1.0
- capability_audit >= 1.0
- schema_contract >= 1.0

The selected candidate must also pass regression tests and validation checks. This prevents a candidate from improving user feedback while degrading source grounding, evidence provenance, safety boundaries, collaboration topology, report structure, Chinese report readability, professional-provider contracts, capability-audit transparency, or public API schema contracts.

## Evidence And Safety Gates

The current evaluator combines these dimensions:

- `consistency`: every specialist must produce macro, micro, yearly, monthly,
  and uncertainty sections both as flat fields and as machine-readable
  `layers` entries with registry-backed `source_ids`.
- `citation`: source IDs must exist in `knowledge_base.py`, cover BaZi, Zi Wei, Qi Men, and Western astrology traditions, and pass source review.
- `feedback`: user satisfaction and corrections become a reward signal.
- `safety`: output must preserve cultural-research/entertainment framing and high-stakes decision boundaries.
- `workflow`: collaboration topology must include a valid voting flow, claim-level vote audit, and stronger variants are rewarded for cross-checks, reconciliation, strict source review, and calibrated vote thresholds.
- `report_schema`: final output must preserve structured summary, boundaries, source review, claim-level voting, topic synthesis, BaZi/Zi Wei/Qi Men/Western astrology deep-analysis details, annual rows, annual timeline rows, monthly rows, and auspicious-day rows.
- `provider_contracts`: fixed reference-chart checks in `reference_charts.py` must pass, including external structured BaZi/Zi Wei/Qi Men/astrology/xuanze payloads, professional BaZi pillar/deep-analysis contracts, and xuanze/almanac timing-row contracts.
- `evidence_provenance`: source-review snippets must carry corpus provenance, citation policy, snippet ID, and paraphrase/excerpt boundary metadata.
- `chinese_render`: Chinese Markdown output must contain readable Chinese section headings, topic headings, safety boundaries, and no known mojibake markers.
- `capability_audit`: `capability_audit.py` must keep core SEMAS capabilities, GitHub/open-source comparison dimensions, state-of-art verdicts, and known professional-provider gaps visible to downstream users.
- `schema_contract`: `/schema` must expose stable contracts for analyze, benchmark, version history, provider readiness, capability audit, plan compliance, and JSON-CLI provider protocols.

Runtime output includes both rendered `output` text and a structured
`final_report` artifact with boundaries, source review, claim-level votes, conflicts, topic
synthesis, annual/monthly luck-cycle rows, API-facing annual timeline rows,
auspicious-day rows, and strategy notes. Each specialist artifact under
`specialists.<domain>` also carries
machine-readable `layers.macro`, `layers.micro`, `layers.yearly`,
`layers.monthly`, and `layers.uncertainty` entries for downstream auditing.
Each layer includes `source_ids`, `evidence_required`, and `boundary_type` so
layer-level claims can be checked against the source registry and evidence
retrieval pipeline.

The vote record keeps backward-compatible per-specialist stances while adding
`_claims` and `_audit`. `_claims` records synthesis claims such as yearly
timing, relationship/family boundaries, and career/finance boundaries with
supporters, preserved challenges, source IDs, support ratios, thresholds, and
decisions. `_audit` summarizes claim count, pass rate, evidence binding, and
whether minority or cautionary positions were preserved.

`final_report.deliberation_receipt` binds that vote record to the actual
discussion rounds, source-review result, conflict list, and workflow topology
with stable SHA-256 hashes. `final_report.request_provenance.report_material`
records the deliberation receipt hash and claim count, so an analysis response
can be checked for input, provider, report, and collaboration-chain drift.

`final_report.rendered_reports.zh` is a Chinese Markdown report with usage
boundaries, four-system summary, topic synthesis, and structured-data overview.
The English compact renderer remains available at `final_report.rendered_reports.en`.

## Topic Synthesis

`final_report.topic_synthesis` provides a cross-agent view for the topics most
often requested by users: finance, official/career pressure, career, study,
relationship, friends, leadership, and children/family.

Each topic contains a headline, annual focus, monthly focus, four-agent evidence
items, and a risk boundary. This lets API clients render user-facing report
sections without reverse-engineering raw BaZi, Zi Wei, Qi Men, and astrology
structures.

## BaZi Deep Analysis

`tools/bazi_deep_analysis.py` enriches the BaZi chart with structured fields for
ten gods, hidden stems, Na Yin, growth stage, Xun Kong, Ming Gong, Shen Gong,
Tai Yuan, Tai Xi, luck-start timing, and major-luck cycles. With `lunar_python`
available, these fields come from the professional backend. Without it, the
system still returns an explicitly marked approximate fallback so agent and UI
contracts remain stable.

The normalized BaZi deep-analysis contract now also exposes
`ten_god_distribution`, `hidden_stem_profile`, `nayin_growth_profile`,
`strength_analysis`, `pattern_analysis`, `useful_god_analysis`,
`tiaohou_analysis`, and a five-entry `method_matrix` covering Ziping pattern,
strength/support, blind-school workflow hints, Shensha/Na Yin, and Tiaohou
balancing. These fields make method coverage auditable without claiming that
symbolic interpretation is empirically predictive.

The BaZi specialist now references the day master, month-stem ten god, and
current major-luck range in its micro/yearly analysis, and the Chinese rendered
report includes a compact BaZi method-coverage line. The `report_schema` and
provider-contract metrics check this structure so SEMAS evolution cannot drop
it silently.

## Zi Wei Deep Analysis

`tools/ziwei_deep_analysis.py` expands the Zi Wei chart into twelve palace rows,
four-transformation placement, major-limit cycles, and selected annual palace
activation rows. The current implementation is deterministic symbolic structure
that keeps the downstream contract stable while leaving a clear adapter point
for a professional Zi Wei pan-calculation provider.

The normalized Zi Wei contract also includes `life_focus`,
`triad_analysis`, `transformation_analysis`, `limit_activation_analysis`, and a
five-entry `method_matrix` covering the Ming/body axis, twelve-palace topic
themes, triad/opposition review, four transformations, and major-limit plus
annual activation linkage.

The Zi Wei specialist now references twelve-palace coverage and current
major-limit focus in its micro/yearly analysis. The `report_schema` and
normalized provider-contract metrics check these method layers so SEMAS
evolution cannot drop them silently.

## Qi Men Deep Analysis

`tools/qimen_deep_analysis.py` expands the Qi Men chart into a nine-palace plate.
Each palace row includes direction, element, door, star, spirit, heaven stem,
earth stem, theme, and symbolic judgment. The structure also records duty
door/star placement, useful-god palace selections for career, wealth,
relationship, study, and health, pattern flags, and selected annual timing rows.

The normalized Qi Men contract also includes `door_star_spirit_analysis`,
`stem_relation_analysis`, `useful_god_analysis`, `pattern_risk_analysis`,
`timing_activation_analysis`, and a five-entry `method_matrix` covering
door-star-spirit combinations, heaven/earth stem relations, useful-god topic
mapping, pattern-risk review, and annual timing activation.

The Qi Men specialist now references nine-palace coverage, duty-door palace, and
career useful-god placement. The `report_schema` and normalized
provider-contract metrics check these method layers so evolution cannot
silently drop the structured Qi Men plate.

## Western Astrology Deep Analysis

`tools/astrology_deep_analysis.py` expands the Western astrology chart into ten
natal planet rows, twelve house rows, major aspect rows, and selected annual
transit rows. The current implementation is deterministic and symbolic, but the
schema matches the adapter boundary needed for a future astronomical ephemeris
such as Swiss Ephemeris.

The normalized Western astrology contract also includes `ephemeris_quality`,
`core_identity_analysis`, `house_emphasis_analysis`, `aspect_pattern_analysis`,
`transit_activation_analysis`, and a five-entry `method_matrix` covering
ephemeris quality, Sun/Moon/Ascendant synthesis, house emphasis, aspect
patterns, and annual transit activation.

The Western astrology specialist now references natal planet count, aspect
coverage, activated houses, and annual transit focus. The `report_schema` and
normalized provider-contract metrics check these method layers so SEMAS
evolution cannot silently regress this agent. Production readiness includes
`astrology_ephemeris_audit_contract`, so closing the astronomical-ephemeris gap
requires ephemeris provenance, time scale, calculation time, data source, and
license/review metadata to remain audited.

## Annual Luck Rows

`tools/annual_luck.py` creates a year-by-year symbolic table from the BaZi chart
context. Each row includes:

- year, age, annual stem-branch, life phase, element focus, and intensity,
- finance, official/career, career, study, relationship, friends, leadership,
  and children/family themes,
- risk notes that keep high-stakes decisions outside the system boundary.

The annual table is available at `final_report.annual_luck.rows`. It is a
deterministic trend scaffold for agent discussion, UI rendering, and benchmark
coverage, not an authoritative professional luck-cycle calculation.

`final_report.annual_timeline` exposes the same yearly data as a stable
API/UI-facing list. Each row carries year, age, stem-branch, phase, category,
intensity, element focus, eight topic entries, risk notes, and a source pointer
back to `annual_luck.rows`.

`tools/monthly_luck.py` expands selected years into twelve monthly rows at
`final_report.monthly_luck.rows`. Monthly rows use the same field family as the
annual table so downstream consumers can render year and month views with one
schema.

## Auspicious-Day Rows

`tools/auspicious_calendar.py` creates a bounded xuanze/huangdao scaffold at
`final_report.auspicious_calendar.rows`. Each row includes the day stem-branch,
solar term, twelve officer, twenty-eight mansion, huangdao rating, suitable and
avoid lists, recommended hour branches, and risk notes. This is an auditable
offline rule baseline, not a verified professional tongshu calculation.

The normalized xuanze contract also includes `twelve_officer_analysis`,
`mansion_analysis`, `huangdao_analysis`, `hour_selection_analysis`,
`risk_boundary_analysis`, `provider_quality_analysis`, and a six-entry
`method_matrix` covering twelve officers, twenty-eight mansions, huangdao
rating, recommended hours, risk boundaries, and provider quality.
Production readiness includes `xuanze_rule_table_audit_contract`, so closing
the huangdao/tongshu gap requires rule-table source, version, hash or receipt
hash, calculation scope, and license/review metadata to remain audited.

When `SEMAS_XUANZE_CLI` is set, `tools/xuanze_cli_provider.py` can replace the
offline rows with a JSON-speaking professional tongshu/xuanze service while
preserving the same `final_report.auspicious_calendar` schema.

For request-scoped integrations, `birth.professional_charts.xuanze` can inject a
verified xuanze/tongshu payload with `rows`, optional `basis`, `summary`, and
`range` fields. This uses the same schema as the JSON-CLI provider and marks the
calendar as `provider_quality: external_xuanze`.
`report_schema` and normalized provider-contract metrics require the xuanze
method layers after provider output is adapted, so SEMAS evolution cannot drop
the coordinator's auspicious-day audit surface silently.

## Evidence Retrieval

`classical_text_index.py` provides a provenance-bearing index of short,
copyright-safe paraphrased evidence notes tied to source IDs. `evidence.py`
queries this index, and `SEMAS_CLASSIC_CORPUS_DIR` can point at local JSONL
files that extend the built-in seed corpus without changing report contracts.
`classical_corpus_ingest.py` converts curated external-source manifests into
that JSONL format while requiring source URL, license, citation policy, and
retrieval metadata. It rejects full-text fields such as `full_text`,
`verbatim_text`, and `raw_text`; use summaries or explicitly licensed short
metadata records instead.

`classical_corpus_refresh.py` adds the network/cache boundary for those
manifests. `classical-sources` and `GET /classical-sources` audit a source-list
without downloading. `classical-refresh` and `GET /classical-refresh` read the
same source-list JSON file, check `allowed_hosts` or the
`SEMAS_CLASSIC_ALLOWLIST_HOSTS` environment variable, download each manifest to
a cache directory, verify `sha256` when present, and then call the same safe
ingester.
File URLs are disabled unless a test or local maintenance source list sets
`allow_file_urls: true`. `/audit.classical_source_refresh` performs the same
source-list checks without downloading: unconfigured deployments are reported
explicitly, and remote manifests must be host-allowlisted and pinned with a
64-character SHA-256 before the source list is considered ready.
Every source-list audit includes a stable `source_list_receipt`; capability
audit and production-readiness receipts bind its SHA-256 so CI can detect
classical-source configuration drift without downloading source text.
Production readiness also requires `classical_source_latest_refresh_receipt_present`:
after configuring a ready source list, run `classical-refresh` so
`<repo>/classical_sources/corpus/refresh_receipt.json` exists, matches the
current `source_list_receipt`, and records at least one ingested evidence row.

Source-list example:

```json
{
  "allowed_hosts": ["example.org"],
  "sources": [
    {
      "name": "open-mingli-notes",
      "url": "https://example.org/mingli_manifest.json",
      "sha256": "64-character-hex-digest"
    }
  ]
}
```

A manifest can be a JSON list or an object with a `records` list. Each record
must include:

- `source_id`, `passage_id`, `title`, `tradition`, `keywords`, `summary`, and `caution`,
- `source_url`, `license`, and `citation_policy`,
- an allowed `citation_policy`: `paraphrase_only`,
  `public_domain_short_excerpt`, or `open_license_short_excerpt`.

The source review stage now checks:

- source ID exists in the registry,
- all four traditions are covered,
- every covered source can retrieve at least one evidence snippet,
- snippets include corpus provenance and citation-policy metadata,
- strict review can require the full nine-source coverage.

`source_review.evidence_index` includes a compact audit manifest with record
counts, source IDs, traditions, content hash, corpus directory, and copyright
policy. `final_report.evidence_summary` includes one snippet per covered source
so downstream UIs, logs, and audits can inspect the basis for symbolic claims.

## Calendar Core

`tools/calendar_core.py` gives all four specialist tools one shared substrate:

- Gregorian input validation and normalized birth records.
- Approximate year, month, day, and hour stem-branch labels.
- Traditional two-hour branch, zodiac animal, five-element counts, dominant/useful element, season, and approximate solar term.
- Western Sun sign date boundaries for the astrology helper.

These calculations are deterministic offline approximations. They are designed as replaceable interfaces for later integration with a full astronomical calendar or professional pan-calculation library.

`tools/calendar_provider.py` defines the adapter boundary:

- `CalendarProvider`: protocol for professional calendar/pan providers.
- `ApproximateCalendarProvider`: default offline implementation in `calendar_core.py`.
- `ProfessionalCalendarProvider`: optional adapter for installed `lunar_python` or `sxtwl` backends.
- `AutoCalendarProvider`: uses a professional backend when available and otherwise marks fallback explicitly.
- `ExternalCalendarProvider`: test/integration adapter for externally supplied authoritative contexts.
- `register_calendar_provider(...)`: runtime registration hook.

Downstream BaZi, Zi Wei, Qi Men, and astrology tools consume `build_chart_context(...)`, so replacing the calendar provider does not require rewriting specialist agents.

`tools/professional_chart_provider.py` defines the domain-specific provider
boundary for Zi Wei, Qi Men, and Western astrology. It currently registers an
`external_structured` provider for each domain, allowing verified outputs from a
future professional library, GitHub-derived adapter, or UI service to overlay
the symbolic scaffold without changing final-report consumers. The `status`
and `audit` commands expose these domain provider capabilities.

When `pyswisseph` is installed, `tools/swiss_ephemeris_provider.py` registers a
`swiss_ephemeris` provider for Western astrology. It calculates planetary
longitudes through Swiss Ephemeris and marks the astrology deep analysis as
`zodiac: tropical_ephemeris`. Without `pyswisseph`, the symbolic fallback remains
active.

For environments where Swiss Ephemeris cannot be installed or should run as a
separate service, `tools/astrology_cli_provider.py` registers an
`astrology_json_cli` provider when `SEMAS_ASTROLOGY_CLI` is set. The command
receives JSON on stdin and returns a JSON object with fields such as `sun`,
`moon`, `ascendant`, `planets`, `houses`, `aspects`, and `annual_transits`.
`providers/astrology_json_cli_example.py` is a deterministic protocol template.

When `kinqimen` is installed, `tools/kinqimen_provider.py` registers a
`kinqimen` provider for Qi Men. The adapter preserves the upstream raw plate at
`raw_provider_output` and maps stable high-level fields when the package output
can be identified safely. Without `kinqimen`, the symbolic Qi Men scaffold
remains active.

For environments where `kinqimen` cannot be installed because of native
dependencies, `tools/qimen_cli_provider.py` registers a `qimen_json_cli`
provider when `SEMAS_QIMEN_CLI` is set. The command receives JSON on stdin and
returns a JSON object with fields such as `duty_door`, `duty_star`, `spirit`,
`pattern`, `palaces`, `useful_gods`, `annual_timing`, and
`calculation_basis`.
`providers/qimen_json_cli_example.py` is a deterministic protocol template.

For Zi Wei, `tools/ziwei_cli_provider.py` registers a `ziwei_json_cli` provider
when `SEMAS_ZIWEI_CLI` is set. The command receives JSON on stdin and returns a
JSON object with fields such as `ming_palace`, `body_palace`, `major_stars`,
`transformations`, `palaces`, `major_limits`, `annual_activation`, and
`calculation_basis`. This is the adapter point for an iztro/Node/Dart/server
wrapper without coupling the SEMAS runtime to one JavaScript or Dart
environment.
`providers/ziwei_json_cli_example.py` is a deterministic protocol template.

The `status` CLI command includes `calendar_providers`, showing registered
providers, default provider, and whether an optional professional backend is
available. `lunar_python` is preferred because it directly exposes eight-character
BaZi APIs; `sxtwl` is supported as a fallback because it exposes astronomical
stem-branch and lunar-calendar primitives.

Current verification:

```bash
pytest tests examples/mingli_5agents/tests -q
python examples/mingli_5agents/run_demo.py
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo benchmark --baseline-version 1
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo status
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo schema
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo outcome-dataset --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-manifest --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-ledger
python examples/mingli_5agents/cli.py --repo .semas_mingli_repo release-drift --manifest examples/mingli_5agents/providers/outcome_dataset_manifest_example.json
```

When `lunar_python` is installed, `status` should report
`default: "auto"` and `professional_backend: "lunar_python"`. Ordinary inputs
then use the professional BaZi backend automatically; inputs can still use
`"calendar_provider": "professional"` to require the backend or
`"calendar_provider": "approximate"` to force deterministic offline fixtures.
