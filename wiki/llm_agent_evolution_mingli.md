# Mingli Agent Evolution Wiki

Status: living methodology note  
Scope: SEMAS Mingli multi-agent evolution, provider governance, reproducible migration  
Rule: README/logs record operations; wiki records absorbed ideas, reasoning changes, and methodology lineage.

## One-Screen Thesis

The Mingli agent should not evolve as a single answer generator. It should evolve as an auditable computation graph:

- LLMs coordinate, critique, synthesize, and explain.
- Domain engines calculate.
- Provider contracts define what external engines must prove.
- Receipts bind inputs, outputs, protocol versions, and known gaps.
- Evolution optimizes evidence quality, governance completeness, reproducibility, and user-facing clarity before it claims predictive truth.

Karpathy's Software 2.0 framing is useful but incomplete for this project: learned programs are powerful, yet Mingli production use needs Software 1.0-style contracts around every learned or external component. The working pattern is therefore "Software 2.0 reasoning inside Software 1.0 governance rails."

## Version Lineage

### v0: Symbolic Scaffold

Initial posture: generate structured symbolic Mingli analysis with deterministic local scaffolds.

Lesson absorbed: symbolic output is useful for UX and integration tests, but not enough for professional calculation. It must clearly label fallback status and avoid pretending to be a verified domain engine.

### v1: Five-Agent SEMAS Topology

The framework moved to specialist agents: BaZi, Ziwei, Qimen, evidence/classics, and synthesis. This matches ReAct's separation of reasoning and acting: reasoning traces decide what is needed, while actions call tools/providers and gather external state.

Source: ReAct, "Synergizing Reasoning and Acting in Language Models", arXiv:2210.03629, https://arxiv.org/abs/2210.03629

### v2: Provider Boundary

The next step was to stop baking domain calculation into the LLM path. Each professional domain became a provider boundary with JSON-CLI protocols, sample stdin/stdout, normalized chart contracts, and production provenance requirements.

Absorbed idea: Toolformer-style tool use says a language model can benefit from external APIs/tools, but in this framework every tool call must become inspectable, typed, and certifiable rather than just convenient.

Source: Toolformer, "Language Models Can Teach Themselves to Use Tools", arXiv:2302.04761, https://arxiv.org/abs/2302.04761

### v3: Receipt Chain Governance

Provider governance then gained request receipts and raw contract receipts. The important change: a provider result is not valid merely because a JSON shape looks plausible. It must bind:

- birth profile hash
- stdin hash
- stdout hash
- protocol version/hash echo
- raw provider contract validity
- certification ledger record

This converts provider integration from "adapter exists" to "adapter output is attributable and replayable."

### v4: Source and Rights Governance

Classical text retrieval was made governance-aware. Source lists now need license, rights basis, review status, reviewer, and content scope. This prevents the evidence layer from becoming an untraceable pile of excerpts.

Methodological rule: source evidence is not just semantic retrieval; it is provenance plus usage permission plus review boundary.

### v5: Outcome Dataset Label Provenance

Empirical validation now requires record-level label provenance: source, collection time, whether labels were collected before analysis, reviewer/method, and special acknowledgment for life-event outcome labels.

Reasoning change: evaluation data is part of the program. This follows Karpathy's Software 2.0 point that datasets and labels are active programming artifacts, not passive files.

Source: Karpathy, "Software 2.0", 2017, https://karpathy.medium.com/software-2-0-a64152b37c35

### v6: Ziwei/Qimen Calculation-Basis Audit

Current iteration: Ziwei and Qimen JSON-CLI providers now must disclose `calculation_basis`:

- provider
- rule_set
- rule_set_version
- rule_source
- rule_source_sha256 or rule_receipt_sha256
- license_or_review
- calculation_scope

Reasoning change: Ziwei/Qimen outputs depend heavily on school/rule choices. Without a rule-source receipt or hash, two engines can disagree and still look equally "structured." The framework should preserve method lineage before synthesis.

### v7: Provider Lineage as a Production Gate

The `calculation_basis` contract is now part of production readiness and known-gap closure, not just a schema nicety. A professional Ziwei or Qimen provider is not considered closable unless the production plan includes the calculation-basis audit gate.

Reasoning change: agent evolution should promote important audit contracts into release gates once they become necessary for trust. This is a Reflexion-style feedback loop applied to architecture: once a weakness is identified, it becomes a persistent gate so future runs cannot forget the lesson.

Source: Reflexion, "Language Agents with Verbal Reinforcement Learning", arXiv:2303.11366, https://arxiv.org/abs/2303.11366

### v8: Pre-Registered Outcome Evaluation

The outcome dataset manifest now requires a pre-registered statistical plan: `pre_registered`, `registration_id`, `registered_at`, `analysis_freeze_date`, and either `plan_sha256` or `plan_receipt_sha256`. This turns empirical validation from "we have labels" into "we have a frozen analysis plan that existed before production validation."

Reasoning change: if SEMAS evolution will ever learn from outcome data, the data contract must defend against hindsight fitting. Open-science preregistration contributes the key pattern: freeze the study question, analysis plan, and decision rules before looking at validation outcomes. SEMAS adapts that pattern as a machine-checkable production gate.

Sources: Center for Open Science / OSF preregistration guidance, https://www.cos.io/initiatives/prereg; AsPredicted preregistration workflow, https://aspredicted.org/

### v9: Audit Contracts Must Become Release Gates

The astrology ephemeris contract and xuanze rule-table contract now join the Ziwei/Qimen calculation-basis contract as production readiness gates. A provider is not "production closeable" just because its runtime adapter can emit structured rows; the framework must also prove that its computational basis is recorded and release-gated.

Reasoning change: SEMAS evolution should treat provenance contracts as durable invariants. Once an audit contract is strong enough to protect a known gap, it should become a release gate and a known-gap closure condition. This prevents later optimization from keeping shape while dropping provenance.

Source: Reflexion feedback-memory pattern, arXiv:2303.11366, https://arxiv.org/abs/2303.11366

### v10: Audited Manifests Must Materialize Into Receipts

The external classical-source gap now requires a latest refresh receipt, not just a valid source-list audit. A source list proves that the intended sources are allowlisted, rights-reviewed, and hash-pinned; a refresh receipt proves that the local evidence corpus was actually materialized from that list.

Reasoning change: production evidence systems need two receipts: intent receipt and materialization receipt. The agent should not treat a reviewed manifest as equivalent to an available local corpus.

Source: ReAct's observation discipline maps here: an intended tool/source plan must produce an observed artifact before synthesis can rely on it. ReAct, arXiv:2210.03629, https://arxiv.org/abs/2210.03629

### v11: Readiness Gates Must Be Bound Into Release Evidence

The release manifest now has explicit binding checks for the newest governance gates: provider audit contracts, outcome statistical-plan preregistration, and latest classical-source refresh receipts. The check is not another copy of the same production decision. It proves that the readiness decision exists in the readiness receipt/blocker chain, and when a gate passes, that the corresponding receipt material is present.

Reasoning change: agent evolution needs a two-layer release proof. Readiness decides whether the system can run in production; release manifest proves that the readiness decision and its artifacts are exactly what CI/archive approval saw. This prevents a common failure mode where a subsystem grows stronger, but the top-level release evidence remains unaware of the new invariant.

Mapped pattern: `readiness gate -> readiness receipt/blocker -> release gate check -> release manifest receipt hash -> release ledger/drift`.

Sources: SLSA provenance and verification model, https://slsa.dev/spec/v1.0/; in-toto attestations/provenance idea, https://in-toto.io/

### v12: Implemented Ideas Must Become Audited Capabilities

The release-readiness binding itself is now a capability-audit requirement, not just code inside release manifest. The audit materializes runtime and schema evidence for each new release gate check, so the framework can detect if future edits remove the binding while leaving release code superficially functional.

Reasoning change: SEMAS evolution should treat every absorbed methodology as a contract lifecycle: idea -> implementation -> release gate -> capability-audit evidence -> regression test. This is a stricter version of Reflexion memory: lessons are not merely written down; they become executable checks that future genomes and framework edits must preserve.

Mapped pattern: `method lesson -> implemented requirement -> evidence list -> materialization probe -> capability flag -> receipt`.

Sources: Reflexion, arXiv:2303.11366, https://arxiv.org/abs/2303.11366; SLSA/in-toto provenance verification pattern, https://slsa.dev/spec/v1.0/ and https://in-toto.io/

### v13: False Capabilities Need Ownership

Capability audit now maps every false capability to either an open known gap or an explicit optional-configuration policy. Missing Ziwei, Qimen, ephemeris, and classical-source production configuration remain real blockers; optional LLM configuration remains non-blocking because deterministic offline synthesis is a valid fallback. The important change is that no false capability can silently float outside the gap model.

Reasoning change: advanced agent frameworks should not only report what is missing; they should prove that each missing capability has ownership, closure criteria, and a reason it is or is not production-blocking. This turns "known gap" from a narrative list into an accountability graph.

Mapped pattern: `false capability -> accounting entry -> known gap or optional policy -> owner/blocking scope -> receipt hash`.

Sources: SLSA/in-toto provenance verification pattern for accountable artifacts, https://slsa.dev/spec/v1.0/ and https://in-toto.io/; SWE-agent/SWE-bench patch-test accountability, https://github.com/SWE-agent/SWE-agent and https://arxiv.org/abs/2310.06770

### v14: Accountability Must Become a Release Gate

Blocked-capability coverage is now a production-readiness gate and a release-manifest gate check. The system does not merely explain false capabilities after the fact; production readiness verifies that the accounting is complete, and release evidence binds that verification.

Reasoning change: an accountability graph is only useful if the release process depends on it. Otherwise it can decay into a dashboard. SEMAS should promote important governance diagnostics into gates once they protect a production invariant.

Mapped pattern: `false capability accounting -> production gate -> release gate check -> release receipt -> drift detection`.

Sources: SLSA/in-toto release provenance pattern, https://slsa.dev/spec/v1.0/ and https://in-toto.io/; Reflexion memory-to-policy pattern, https://arxiv.org/abs/2303.11366

### v15: Runbooks Are Interfaces

Known-gap verification commands are now parsed and checked against the current CLI subcommands. The framework does not execute placeholder commands, but it does prove that each runbook points at real local interfaces. This catches a subtle decay mode: a gap can have "verification commands" that look plausible but no longer match the tool surface.

Reasoning change: reproducibility is not only data, hashes, and receipts. It also includes operational instructions that remain aligned with executable interfaces. Treat runbooks as lightweight API clients.

Mapped pattern: `known gap -> verification command -> CLI parser subcommand -> command coverage hash -> readiness/release receipt`.

Sources: SWE-agent/SWE-bench patch-test discipline, https://github.com/SWE-agent/SWE-agent and https://arxiv.org/abs/2310.06770; ReAct action grounding, https://arxiv.org/abs/2210.03629

### v16: Interfaces Include Options

Known-gap verification now validates not only CLI subcommands but also option names used by each runbook command. A runbook that points to `release-manifest` but uses a stale `--manfiest` option is no longer considered covered. The framework records observed options, valid options by subcommand, invalid options by gap, and a command-coverage hash.

Reasoning change: action grounding has two levels: verb and arguments. If the arguments drift, the action is no longer reproducible even when the verb still exists. SEMAS should treat both as part of the executable contract.

Mapped pattern: `runbook command -> subcommand + options -> CLI parser option surface -> command coverage receipt`.

Sources: ReAct action grounding, https://arxiv.org/abs/2210.03629; SWE-agent patch/test discipline, https://github.com/SWE-agent/SWE-agent

### v17: Runbook Coverage Must Gate Release

Known-gap command and option coverage is now an explicit release gate check. The release manifest does not merely carry runbook coverage in receipt material; it has a boolean gate proving the coverage is complete, command validation passed, invalid command/option maps are empty, and the command coverage hash exists.

Reasoning change: if runbooks are interfaces, then release approval must know whether those interfaces are intact. Receipt material is evidence; a release gate check is a decision. SEMAS needs both.

Mapped pattern: `runbook coverage receipt -> release gate check -> release manifest receipt -> release drift`.

Sources: SLSA/in-toto release provenance, https://slsa.dev/spec/v1.0/ and https://in-toto.io/; SWE-agent patch/test discipline, https://github.com/SWE-agent/SWE-agent

### v18: Gap Handoff Bundles Make Closure Portable

Known-gap closure is now packaged as a handoff bundle. Each open gap carries owner domain, blocking scope, closure condition, provider environment variables, provenance variables, verification commands, production gates, external candidate projects, blocked capabilities, a `handoff_ready` flag, and a stable bundle hash.

Reasoning change: a known-gap plan is useful for the current repo, but a handoff bundle is useful for the next runtime, team, or agent generation. It converts tacit integration knowledge into a portable interface, so future work can connect a real provider or dataset without rediscovering command names, env vars, provenance requirements, candidate projects, and closure gates.

Mapped pattern: `known gap -> closure plan -> handoff item -> provider/source/dataset integration -> certification/readiness/release gate`.

Sources: Voyager skill-library portability, https://arxiv.org/abs/2305.16291 and https://github.com/MineDojo/Voyager; SWE-agent patch/test handoff discipline, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent; SLSA/in-toto portable provenance, https://slsa.dev/spec/v1.0/ and https://in-toto.io/

### v19: Handoffs Become Release-Governed Interfaces

The known-gap handoff bundle is now a production-readiness gate and a release-manifest gate check. Readiness proves the bundle is ready, covers every known gap, has no missing handoff item, and carries a stable hash. Release manifest then binds that readiness decision and stores the handoff bundle in release receipt material so release drift can detect changed external-closure instructions.

Reasoning change: portability is not achieved when a handoff exists; portability is achieved when the release system refuses to forget it. For SEMAS, every durable lesson should eventually move from note -> audit field -> readiness gate -> release receipt when it protects future migration or reproduction.

Mapped pattern: `handoff bundle -> readiness gate -> release gate check -> release receipt material -> ledger/drift comparison`.

Sources: SLSA/in-toto provenance-as-release-evidence, https://slsa.dev/spec/v1.0/ and https://in-toto.io/; SWE-agent task handoff and regression discipline, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent; Voyager reusable skill library, https://arxiv.org/abs/2305.16291

### v20: Governed Artifacts Need Direct Export Surfaces

The known-gap handoff bundle now has a dedicated CLI command and HTTP endpoint. The export response carries the bundle, known gap IDs, audit receipt hash, and expected-audit drift fields, so another runtime or agent can consume the external-closure package without parsing the full capability audit.

Reasoning change: a governed artifact is not fully portable until it has a stable export surface. Release receipts prove that the artifact was present at approval time; direct export makes it operationally reusable by future agents, provider integrators, and deployment scripts.

Mapped pattern: `release-governed artifact -> direct CLI/API export -> audit receipt binding -> downstream integration`.

Sources: Toolformer tool/API-use framing, https://arxiv.org/abs/2302.04761; SWE-agent operational handoff pattern, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent; SLSA/in-toto provenance binding, https://slsa.dev/spec/v1.0/ and https://in-toto.io/

### v21: Export Surfaces Need Their Own Receipts

The known-gap handoff export now carries `handoff_export_receipt`, a stable hash over export identity, known gap IDs, bundle hash, audit receipt hash, and expected-audit drift status. This separates the hash of the bundle from the hash of the exported transfer object.

Reasoning change: when a downstream agent consumes an exported artifact, it needs to verify both the underlying governed object and the exact transfer wrapper. Bundle hash proves the handoff content; export receipt proves which repo/audit state and drift boundary delivered it.

Mapped pattern: `governed bundle hash -> export receipt material -> export receipt hash -> downstream verification`.

Sources: in-toto link metadata and artifact provenance, https://in-toto.io/; SLSA provenance model, https://slsa.dev/spec/v1.0/; Toolformer/API-use framing, https://arxiv.org/abs/2302.04761

### v22: Exported Artifacts Must Be Verifiable Downstream

The handoff export now has an offline verifier. `known-gap-handoff-verify` recomputes the bundle hash, export receipt material, export receipt hash, known-gap ID binding, and optional expected export receipt hash. It also accepts PowerShell UTF-16 redirected JSON, because transfer artifacts must survive the user's actual shell, not only ideal UTF-8 test fixtures.

Reasoning change: exportability is incomplete without downstream verification. SEMAS artifacts should be portable across runtimes and agents with enough embedded receipt structure that the receiver can detect tampering before trusting the content.

Mapped pattern: `export JSON -> offline verifier -> recomputed hashes -> accept/reject before integration`.

Sources: in-toto verification workflow, https://in-toto.io/; SLSA artifact verification model, https://slsa.dev/spec/v1.0/; SWE-agent patch/test discipline, https://arxiv.org/abs/2405.15793

### v23: Verified Handoffs Become Implementation Checklists

The verified handoff export can now be transformed into per-gap implementation checklists. Each checklist item carries environment variables, provenance variables, candidate projects, verification commands, production gates, blocked capabilities, closure conditions, and a checklist receipt.

Reasoning change: migration artifacts should move from "valid data" to "actionable work packets." Agents and operators should not repeatedly rediscover how to turn a verified handoff into implementation steps; the framework should generate the next executable layer.

Mapped pattern: `verified handoff export -> per-gap implementation checklist -> provider/source/dataset integration work`.

Sources: SWE-agent task-to-patch workflow, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent; Voyager skill-library reuse, https://arxiv.org/abs/2305.16291; ReAct action planning, https://arxiv.org/abs/2210.03629

### v24: Executable Handoffs Need CLI and API Surfaces

Handoff verification and checklist generation are now available through HTTP POST endpoints as well as CLI commands. Non-shell runtimes can submit a handoff export object and receive the same verification and checklist contracts.

Reasoning change: if the framework is meant for agent-to-agent and service-to-service migration, shell commands are not enough. Governance artifacts need both human/operator CLI surfaces and machine/service API surfaces that call the same core functions.

Mapped pattern: `core governance function -> CLI command -> HTTP endpoint -> shared schema contract`.

Sources: Toolformer/API-use framing, https://arxiv.org/abs/2302.04761; ReAct tool/action interface, https://arxiv.org/abs/2210.03629; SWE-agent operational automation, https://github.com/SWE-agent/SWE-agent

### v25: Implementation Checklists Need Drift Binding

The generated implementation checklist now accepts an expected checklist receipt SHA-256 through both CLI and HTTP API. The expected value is compared outside the checklist receipt material, so the act of checking a prior receipt does not mutate the artifact being checked.

Reasoning change: a handoff can be valid at transfer time and still drift at the action-plan layer. Once a verified handoff becomes a checklist, the checklist itself is an artifact that downstream agents may cache, sign, compare, or replay. Therefore the checklist needs its own expected-receipt comparison, separate from the export receipt and separate from the receipt material.

Mapped pattern: `verified handoff export -> checklist receipt -> expected checklist receipt -> drift decision -> safe implementation`.

Sources: SLSA provenance and verification model, https://slsa.dev/spec/v1.0/; in-toto artifact/link verification, https://in-toto.io/; SWE-agent handoff/test loop, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent; Toolformer/API-use framing, https://arxiv.org/abs/2302.04761

### v26: Safe Defaults Close Configuration Gaps, Not Evidence Gaps

Mingli capability audit now uses the bundled copyright-safe, hash-pinned classical source list when no explicit source list or environment variable is configured. This makes the framework auditable out of the box while preserving the production blocker that requires a latest classical-source refresh receipt.

Reasoning change: configuration readiness and evidence readiness are different layers. A default fixture can prove that the pipeline has a valid allowlist contract, source governance metadata, and stable source-list receipt. It cannot prove that an operator has refreshed and accepted a production corpus. Therefore the audit may close `classical_source_refresh_configured`, while production readiness still blocks on `classical_source_latest_refresh_receipt_present`.

Mapped pattern: `safe bundled fixture -> configuration capability closes -> refresh execution -> latest receipt -> production evidence closes`.

Sources: SLSA provenance and build-material separation, https://slsa.dev/spec/v1.0/; in-toto layout/link separation, https://in-toto.io/; SWE-agent reproducible test fixture discipline, https://arxiv.org/abs/2405.15793 and https://github.com/SWE-agent/SWE-agent

## Absorbed Agent Ideas

### ReAct: Interleave Thinking and Acting

Use for SEMAS dispatch. The agent should reason about which domain capability is needed, act through provider/tool calls, observe structured outputs, then update the analysis path.

Mapped pattern: `plan -> provider/tool action -> observation -> contract check -> synthesis`.

Source: https://arxiv.org/abs/2210.03629

### Reflexion: Feedback Memory Changes Future Attempts

Use for evolution archives and regression memories. Failed provider checks, missing evidence, and low-confidence synthesis should become written feedback for later generations rather than transient errors.

Mapped pattern: `failure -> verbal diagnosis -> archived lesson -> next genome/provider policy`.

Source: Reflexion, "Language Agents with Verbal Reinforcement Learning", arXiv:2303.11366, https://arxiv.org/abs/2303.11366

### Voyager: Skill Library and Open-Ended Growth

Use for persistent Mingli capability growth. Voyager's key transferable idea is not Minecraft; it is the combination of automatic curriculum, executable skill library, environment feedback, execution-error repair, and self-verification.

Mapped pattern: provider protocols, analysis modules, source governance checks, and report renderers are the local "skill library." The evolution system should add or improve skills only when they pass receipts and tests.

Sources: arXiv:2305.16291, https://arxiv.org/abs/2305.16291; GitHub MineDojo/Voyager, https://github.com/MineDojo/Voyager

### Generative Agents: Memory Enables Believable Long-Horizon Behavior

Use for long-horizon agent memory, but with stricter audit. Mingli analysis needs persistent memory for methodology, source decisions, and user preferences; it should not store unsupported claims as facts.

Mapped pattern: memory entries are typed as operation log, source evidence, methodology note, or unresolved gap.

Source: Generative Agents, arXiv:2304.03442, https://arxiv.org/abs/2304.03442

### SWE-agent and SWE-bench: Patch/Test Loop as Agent Discipline

Use for engineering workflow. The useful pattern is issue/task -> inspect code -> patch -> run tests -> record residual gaps. For this project, every architecture evolution should have a parallel method note in wiki and a verification path in tests/audits.

Sources: SWE-agent, arXiv:2405.15793, https://arxiv.org/abs/2405.15793; SWE-agent GitHub, https://github.com/SWE-agent/SWE-agent; SWE-bench, arXiv:2310.06770, https://arxiv.org/abs/2310.06770

## v27: Hierarchical Mingli Reasoning Before Narrative Output

User-facing Mingli reports should not be generated as a flat list of life
domains. A flat template easily produces absurd outputs, such as discussing
wealth, office politics, or marriage in early childhood. The report generator
must first infer the age stage and reasoning layer, then choose the right
domains for that life period.

The adopted reasoning order is five layers:

1. Pattern recognition: identify the chart type, life theme, constitutional
   strengths and weaknesses.
2. Macro trend: use ten-year luck cycles to set the dominant life-stage theme.
3. Annual event: read the annual stem/branch together with the luck cycle and
   natal chart, then map it to concrete event categories.
4. Cross-validation: compare BaZi, Zi Wei, and Qi Men signals before assigning
   confidence.
5. Fact calibration: compare the inference with known life events, revise the
   pattern when facts contradict theory.

Three modeling ideas should be promoted into provider contracts and report
renderers:

- Body-use-protection: the useful element alone does not determine outcome; the
  protection mechanism decides whether the energy chain can work.
- Five-element circulation map: the chart should expose circulation paths,
  breakpoints, and repair paths instead of only saying strong or weak.
- Ten-god duality matrix: each ten-god has constructive and destructive
  expressions depending on configuration, age stage, and protection state.

Implementation implication: every annual paragraph should be generated from an
age-aware domain policy. Childhood focuses on health, parents, household
rhythm, temperament, and study habits. Adult years can discuss career, wealth,
marriage, leadership, partnership, and children. The renderer should state
clear directional judgments, while still keeping confidence and evidence
boundaries visible.

Source: user-provided `bazi-hierarchical-analysis` methodology note in this
conversation, 2026-06-24. Related agent reasoning patterns: ReAct for layered
act/observe/synthesize loops, Reflexion for fact-calibration memory, and
Voyager for turning repeated reasoning procedures into a reusable skill
library.

## v28: Annual Reports Must Derive, Not Template

The previous age-aware renderer fixed an obvious category error, but it still
used too many repeated annual sentences. A Mingli annual report should not be a
topic template with the year number changed. It should derive each year from
the interaction graph among natal chart, major luck, annual pillar, and key
months.

The adopted annual derivation loop is:

1. Split the annual pillar into stem and branch.
2. Map stem and branch into ten-god roles relative to the day master.
3. Compare the annual branch against natal year, month, day, and hour branches.
4. Compare the annual branch against the active major-luck branch.
5. Mark branch relations as clash, punishment, harm, combination, or repeated
   activation.
6. Infer a small set of key month branches from their relation to the annual
   branch, natal day branch, and major-luck branch.
7. Translate the result through an age-stage policy before writing user-facing
   language.

This changes the report generator from "fill every domain every year" to
"derive the year's pressure points, then choose the right domains." It also
creates a clean insertion point for factual calibration: known real events
should be recorded separately and then used to revise pattern recognition,
major-luck framing, and annual wording.

Source: user feedback in this conversation, 2026-06-24: annual language must
reflect different yearly and monthly five-element relations, including
punishment, clash, combination, harm, generation, and control, rather than
fixed phrases. Related source: user-provided `bazi-hierarchical-analysis`
methodology note, especially Layer 3 annual event analysis and Layer 5 fact
calibration.

## v29: One Specialist Can Contain School Sub-Agents

The original five-agent topology was horizontal: BaZi, Zi Wei, Qi Men,
astrology, and a coordinator. User feedback clarified that BaZi itself contains
multiple schools that should not be collapsed into one voice. The BaZi agent
therefore gains an internal debate layer made of paper sub-agents:

1. Zi Ping pattern agent.
2. Strength/support agent.
3. Tiaohou climate-balancing agent.
4. Body-use circulation agent.
5. Blind-school image-symbol agent.
6. Shensha/Na Yin auxiliary agent.

Each sub-agent emits a claim, challenge, evidence fields, confidence, and vote
stance. The BaZi profile then stores a `school_debate` receipt containing
votes, conflicts, consensus, and a stable hash. The final BaZi judgment should
use high-confidence school consensus as the main line, preserve conflicts
explicitly, and ask for factual calibration when schools disagree.

This mirrors the outer SEMAS pattern at a smaller scale: specialist -> school
sub-agents -> debate -> vote -> conflict preservation -> synthesis. The same
pattern can later be applied to Zi Wei schools and Qi Men schools once
production providers expose their calculation-basis metadata.

Source: user feedback in this conversation, 2026-06-24: BaZi should branch into
school-specific paper agents that debate and vote, especially where judgments
conflict. Related framework idea: ReAct-style decomposition and Reflexion-style
calibration memory, already cited in this wiki.

## v30: Every Period Needs Its Own Computed Signature

User feedback exposed a failure mode in long-form destiny reports: even when the
underlying annual/monthly rows differ, the renderer can collapse them into
category templates such as "authority year", "wealth month", or "study month".
That produces readable but low-value repetition. The fix is to make prose
generation depend on a computed period signature before any sentence is written.

For each year or month, the Mingli renderer should derive:

1. The current stem-branch and its ten-god pair.
2. The five-element flow and whether the useful/protective chain is supported or challenged.
3. The branch interactions against natal branches, current annual branch, and major-luck branch.
4. A pressure score from clash, punishment, harm, break, combination, or repetition.
5. Age-aware domain scores, such as study, career preparation, career, resource/wealth, relationship, and family pressure.
6. A period-specific trigger sentence and a period-specific assertion.

The renderer can still use controlled phrasing, but only after the period
signature is computed. A sentence is valid when a reader can point back to the
period's own stem, branch, ten-god, flow, and interaction evidence. A sentence is
invalid when the same body could be copied to another month without changing
the reasoning. In practical validation, monthly bodies should remain unique
after removing only the date prefix.

For minors, the signature must be routed through an age policy before wording:
childhood years emphasize health, learning, parents, teachers, habits, and
environment; teen and early adult years emphasize study, exams, credentials,
skill-building, internships, and direction preparation; full adult wealth,
career, and marriage language is delayed until the age context supports it.

Source: user feedback in this conversation, 2026-06-25: each year and month
must be independently calculated and independently evaluated; repeated filler is
not acceptable. Related local implementation:
`examples/mingli_5agents/reports/generate_linfan_family_reports.py`.

## v31: Anti-Template Is A Global Report Rule

The anti-template rule is now global, not a one-off formatting preference.
Whenever the system writes a timeline report, it must assume that repeated
language is a reasoning failure unless the repeated phrase is a stable factual
label such as a birth date, a pillar name, or a section heading.

The practical rule is:

1. A report may share structure, but not conclusions.
2. Each year, month, or phase must carry its own evidence signature.
3. If two periods share the same category, the renderer must still explain what
   differs: stem, branch, active major luck, natal branch trigger, age stage,
   score, pressure, or real-world domain.
4. A generic phrase such as "suitable for steady progress" is not allowed as a
   repeated conclusion.
5. After date prefixes are removed, period bodies should remain unique unless
   two periods are deliberately marked as the same pattern and the reason is
   stated.

For child reports, the age-stage policy is also global. Childhood and teen
years emphasize health, study, parents, teachers, habits, and direction. Adult
wealth, career, and marriage language only enters when the age stage supports
it. Gender calibration must be treated as a factual update, not a stylistic
detail, because it changes how traditional systems frame major luck and
relationship emphasis.

Source: user feedback in this conversation, 2026-06-25: "千万记得不要用任何的重复性的套话，千万不要去套模板，你把这个规则记住，这是全局规则。"

## v32: Monthly Analysis Must Bind Wuxing To Yongshen

Monthly predictions are not complete when they only list branch interactions.
For exam-focused or study-focused reports, each flowing month must explain:

1. Which five elements appear in the monthly stem and branch.
2. What those elements mean for the specific chart and age-stage task.
3. Whether the month directly activates the useful/exam-use chain or only helps indirectly.
4. How the element movement changes the practical advice.

For the male child Gaokao report, the local exam-use mapping is:

1. Metal: output, answer presentation, expression, and problem-solving hand feel.
2. Wood: rules, targets, teacher requirements, and exam constraint.
3. Fire: resource star, comprehension, memory, teachers, and parent support.
4. Water: time/resource allocation, real pressure, and external pull.
5. Earth: self-bearing, stable execution, repetition, and persistence.

The renderer must avoid saying only "this month is good for study." It should
say what element moved, what exam-use function it touches, what it helps, what
it harms, and what action follows. This makes the monthly line falsifiable and
portable instead of decorative.

Source: user feedback in this conversation, 2026-06-25: flowing-month five
elements must be explained against the useful-god relationship.

## v33: Annual Context Must Precede Monthly Tables

For exam-timeline reports, monthly analysis should not stand alone. The reader
needs the annual container first because a month is judged inside an annual
flow, a major-luck stage, and the native four-pillar structure.

The report order becomes:

1. Basic birth and exam assumptions.
2. Annual analysis, including the annual pillar, approximate Gregorian Li Chun
   start/end dates, annual ten-god and five-element flow, and annual branch
   relationship to the native four pillars.
3. Special exam month relation, especially the exam month branch against the
   native chart and annual branch.
4. Monthly comparison table.

The monthly table should carry separate columns for:

1. Month.
2. Flowing month.
3. Benefit.
4. Risk.
5. Ten-god preference/avoidance.
6. Five-element flow.
7. Interaction situation, including combination, generation, control,
   punishment, harm, clash, or repetition.
8. Action.

This makes the report easier to audit: annual assumptions are visible before
month-level claims, and repeated prose is replaced by comparable independent
fields.

Source: user feedback in this conversation, 2026-06-25: monthly analysis should
use a comparison table and be preceded by annual analysis with Gregorian
start/end dates and June exam-month relationship to the native four pillars.

## v34: Famous Cases Are Weak Calibration Fixtures

Modern and contemporary famous-person charts can help test whether the Mingli
agent produces coherent, non-template reasoning, but they must not be treated as
proof of predictive validity. Public celebrity charts have three recurring
problems:

1. Birth time may be wrong, rounded, or disputed.
2. Biographical event years are selectively remembered.
3. Famous lives overrepresent unusual careers and public crises.

Therefore the system should use famous cases only as weak calibration fixtures:

1. Prefer sources with explicit birth-data ratings and provenance, such as
   Astro-Databank's Rodden-style ratings.
2. Keep source URL, source rating, birth fields, and event tags attached to the
   case record.
3. Compare school-agent hypotheses against broad topic/year tags, such as
   study, career, migration, public fame, relationship, family, or health risk.
4. Never count a symbolic sentence as validated just because it sounds similar
   to a biography.
5. Keep AA/A-rated cases separate from B-rated or unsourced internet charts.

The first local fixture set lives in
`examples/mingli_5agents/famous_case_validation.py`. It contains Bruce Lee,
Chiang Kai-Shek, Marilyn Monroe, and Albert Einstein, all recorded as sourced
calibration fixtures with source ratings and event tags.

Source: user request in this conversation, 2026-06-26: search contemporary and
modern historical famous charts for validation and use them to upgrade the
agents. External source family used for the first fixture set: Astro-Databank
public pages.

## v35: BaZi School Sub-Agents Need Method Rules

The earlier BaZi school debate layer preserved disagreement, but it still
behaved too much like a field-availability checker. The upgraded version gives
each school sub-agent its own method rules:

1. Zi Ping pattern agent: month command, stem exposure, pattern formation, and
   major-luck continuation or damage.
2. Strength/support agent: day-master state, useful element, avoid-overweight
   element, and whether useful support is protected.
3. Tiaohou agent: seasonal climate bias, cold/heat/dry/wet adjustment, and
   state-level effects such as sleep, endurance, and learning absorption.
4. Body-use circulation agent: body, use, support/protection chain, and
   breakpoints.
5. Blind-school image agent: pillar position, visible image, branch
   interactions, and concrete scene hypotheses.
6. Shensha/Na Yin agent: low-weight auxiliary markers only.

Each sub-agent now emits a claim, challenge, method rules, event hypotheses,
and calibration questions. This improves portability: future domains can copy
the same pattern when a specialist contains competing schools or traditions.

Source: user request in this conversation, 2026-06-26: enrich each BaZi school
sub-agent's judgment logic if necessary.

## v36: Sports, Film, And Music Cases Improve Event Diversity

Sports, film, and music celebrities are useful additions to the validation
fixture set because their public events are often dated and domain-specific:

1. Sports cases provide championship peaks, injury windows, retirement, and
   performance cycles.
2. Film and television cases provide breakout roles, awards, public image,
   relationship events, and career transitions.
3. Music cases provide album breakthroughs, tours, public fame, controversy,
   and health-risk windows.

This improves calibration coverage beyond political or intellectual biographies.
However, the same boundary applies: celebrity charts are only weak calibration
fixtures. The system should compare structured topic/year tags, not retrofit
dramatic biography language into destiny claims.

The local fixture set now includes twelve sourced cases:

1. Sports: Arthur Ashe, Mark Spitz, Roger Federer.
2. Film/television: Bruce Lee, Marilyn Monroe, Lucille Ball, Sean Penn.
3. Music: Aretha Franklin, Michael Jackson, Madonna.
4. Other comparison domains: Chiang Kai-Shek and Albert Einstein.

Source: user request in this conversation, 2026-06-26: find sports, film, and
music stars for validation. Source family used for the fixture links:
Astro-Databank public pages with source ratings.

## v37: Validation Fixtures Must Enter Capability Receipts

A validation dataset is not part of an agent's capability just because a file
exists in the repository. It becomes part of the executable architecture only
after the runtime audit exposes a stable receipt, schema, and hash.

The famous-person fixture set therefore moved from "available evidence" to
"audited capability evidence":

1. `famous_case_receipt()` produces the source-rated case count, domains,
   ratings, material summary, and sha256.
2. `capability_audit()` reports `famous_case_validation_receipt` as a capability
   flag only when the receipt hash is valid and the fixture count is at least
   twelve.
3. The API schema exposes `FamousCaseValidationReceiptSummary`.
4. The audit receipt material embeds the same famous-case summary, so downstream
   users can replay and compare drift.
5. Tests require sports, film, and music domains to remain present.

Reasoning change: the system should not say "I validated against celebrities"
unless the validation fixture set is part of the same reproducible audit chain
as providers, source lists, method lineage, and release checks. This follows
the SEMAS pattern that every evolved idea must cross from prose into a typed,
hashed, test-gated artifact before it is treated as architecture.

Source: user request in this conversation, 2026-06-26: use sports, film, and
music celebrities for validation and upgrade the agent code if necessary.

## v38: Case Fixtures Should Drive School-Level Calibration

After validation fixtures enter capability receipts, the next step is to make
them exercise the reasoning machinery. A famous-person case should not only be
counted; it should be pushed through the same BaZi chart and school-debate path
used for ordinary analysis.

The current implementation runs each sourced famous case through:

1. birth data normalization
2. `build_bazi_chart()`
3. BaZi deep analysis
4. school-agent debate
5. school-topic overlap scoring against public event tags
6. a stable calibration receipt

The score is deliberately weak: it measures whether a school-agent's topic
scope overlaps the case's event-tag categories. It does not check exact event
years, event severity, or factual causality. This boundary matters because
celebrity biographies are noisy and birth-time quality varies.

Reasoning change: the framework should first ask "which school has blind spots
for this type of life event?" before asking "did the school predict the exact
event?" For example, sports cases should reveal whether the flow can even talk
about peak performance, injury, retirement, and public fame; music and film
cases should reveal whether output, fame, controversy, relationship, and health
tags are represented. Exact-year calibration can only be added after this
topic-coverage layer is stable.

This follows the same incremental-evaluation idea used in agent benchmarks:
start with a clearly defined, reproducible proxy task before claiming broader
capability. In this project the proxy is not "truth"; it is a diagnostic for
school-agent coverage.

Source: user request in this conversation, 2026-06-26: use sports, film, and
music celebrities to validate and upgrade the BaZi sub-agent logic.

## v39: Annual Event Calibration Starts As Signal Coverage

Once school-level topic coverage exists, the next evaluation layer is annual
event-year coverage. The system should ask: when a sourced public event happens
in a given year, does the annual luck row expose a compatible symbolic signal?

The current layer maps public event tags to expected annual signals:

1. `sports_peak` expects expression or authority signals.
2. `public_fame` expects expression or high-visibility signals.
3. `health_risk` expects high-volatility or dominant-element pressure signals.
4. `study_exam` expects learning or authority signals.
5. `relationship` expects relationship/peer/wealth-family signals.
6. `public_controversy` expects expression-authority tension or volatility.

For every famous case, the framework now:

1. builds the BaZi chart
2. generates annual rows across known public event years
3. checks exact event-year signal coverage
4. checks +/-1-year window signal coverage
5. stores a stable annual-event calibration receipt

Reasoning boundary: this is not prediction accuracy. It is a diagnostic for
whether the annual row vocabulary is too narrow, too broad, or missing key
event types. A high window score may indicate that categories are broad enough
to cover many events; that is useful only as a first-stage smoke test. Stricter
future validation should add negative years, frozen rules, and event-specific
precision/recall before any predictive claim.

Source: user request in this conversation, 2026-06-26: use sports, film, and
music famous cases to validate and upgrade the agent.

## v40: High Recall Must Be Challenged By Negative Years

The annual event calibration initially showed high event-year coverage. That
looked encouraging, but it was not enough. A broad annual signal can match many
event years and still be useless because it also fires in many years where the
event did not happen.

The next evolution adds negative-year samples:

1. For each famous case, collect the known event years for every event topic.
2. Build annual rows across the public-event range.
3. For each topic, treat years without that topic as negative samples.
4. Count false positives when the annual row still emits the expected signal.
5. Report exact precision and false-positive rate alongside recall.

Current diagnostic result: event-year recall is high, but exact precision is
low. This is not a failure of the audit layer; it is the audit layer exposing
that the annual event-signal mapping is too broad.

Reasoning change: a Mingli model should not graduate from "symbolic language"
to "calibrated timing" merely because it can explain known event years. It must
also avoid explaining too many non-event years. In practice, each event topic
needs sharper evidence:

1. `health_risk` should require volatility plus health/body or pressure cues,
   not volatility alone.
2. `public_fame` should require expression/visibility plus supportive strength
   or major-luck context.
3. `relationship` should require relationship-domain signals, not any peer or
   wealth-family symbol.
4. `sports_peak` should require performance/output plus constructive intensity,
   not any active year.

Source: this session's annual famous-case calibration results, 2026-06-26:
high recall but low precision after adding non-event years.

## v41: Keep Loose And Strict Annual Matchers Side By Side

After adding negative years, the framework learned that a loose annual matcher
has high recall and high false positives. The answer is not to delete the loose
matcher. The better structure is to keep two layers:

1. Loose matcher: asks whether any plausible annual signal exists. This is a
   recall-oriented smoke test.
2. Strict matcher: asks whether the event type has a specific combination of
   signals. This is a precision-oriented diagnostic.

The strict matcher now requires different combinations by event type:

1. `health_risk`: volatility plus dominant-element pressure.
2. `public_fame`: expression plus constructive or activated support.
3. `public_controversy`: expression/authority plus volatility.
4. `relationship`: relationship-domain category plus volatility or activation.
5. `sports_peak`: expression/authority plus constructive intensity.
6. `study_exam`: learning/authority plus constructive or activated support.

Current diagnostic result: strict matching lowers false positives substantially,
but strict precision is still low. That is useful: it tells us the next
evolution should add stronger event-domain evidence rather than merely
tightening generic symbolic categories.

Reasoning change: calibrated Mingli analysis should expose both broad
interpretability and narrow event discipline. Broad interpretability helps a
human reader understand possible themes; narrow discipline prevents every year
from being retrofitted into every event.

Source: this session's strict annual famous-case calibration results,
2026-06-26.

## v42: Diagnose Annual Timing By Event Topic

Aggregate annual calibration metrics are not enough. A low global precision
score says the framework is overfiring, but it does not say where to improve.
The next evolution splits calibration by event topic.

The annual calibration receipt now reports each topic separately:

1. event count
2. negative-year count
3. loose recall and precision
4. loose false-positive rate
5. strict recall and precision
6. strict false-positive rate
7. supporting case ids

This reveals different rule-quality profiles. Health-risk rules currently look
more disciplined after strict matching. Sports-peak rules improve but still
overfire. Public-fame and career-project rules remain too broad, so they should
not be tightened by a generic threshold; they need domain-specific evidence.

Reasoning change: every event type should earn its own timing rule. "Important
year" is not enough. A fame year, health year, relationship year, exam year,
career-project year, and migration year need different evidence bundles.

Source: this session's topic-level annual famous-case calibration results,
2026-06-26.

## v43: Turn Diagnostics Into A Rule Refinement Queue

Topic-level diagnostics are useful only if they create the next executable
work item. The framework now converts annual calibration diagnostics into a
rule-refinement queue.

The queue ranks event topics by:

1. event count
2. strict precision
3. strict false-positive rate
4. whether there is enough evidence to act or only enough to watch

Each queue item also carries recommended evidence. This matters because the
next evolution should not blindly change thresholds. It should add the missing
evidence family for that event type:

1. Public fame needs expression ten-god, useful-element activation, and an
   output-to-public-image chain.
2. Career/project events need career-domain ten-god, major-luck continuation,
   and natal-pillar activation.
3. Relationship events need day-branch or relationship-palace activation,
   branch interaction, and relationship-domain ten-god.
4. Migration events need branch clash or movement signals and residence-axis
   activation.
5. Health events need volatility plus body-system or dominant-pressure evidence.

Reasoning change: an evolving agent should not merely report that it is weak.
It should produce a structured next-action queue that can be migrated, tested,
and audited. This keeps "automatic evolution" concrete instead of becoming
retrospective commentary.

Source: this session's annual event rule-refinement queue, 2026-06-26.

## v44: Attach Evidence Bundles To Annual Event Samples

The rule-refinement queue said that weak topics need stronger evidence. The
next evolution attaches an evidence bundle to every event-year and negative-year
sample.

The bundle currently records:

1. annual ten-gods
2. expression, authority, wealth, resource, and peer flags
3. active major-luck flag
4. natal-pillar activation flag and activated pillars
5. useful-state

This changes the calibration object from "year matched category X" to "year
matched category X with these supporting signals." That is important because
future rule changes can inspect what evidence was actually present instead of
guessing from summary scores.

Diagnostic result: adding major-luck and natal-activation support increased
strict recall, but also increased false positives. That is a useful warning.
Major-luck continuation and natal activation are real supporting signals, but
they are too broad to serve as standalone exact-year evidence.

Reasoning change: event evidence should be layered. A broad supporting signal
can raise confidence only after event-specific evidence is present. For example:

1. Fame should start with expression/public-output evidence, then use major-luck
   support as confirmation.
2. Relationship should start with relationship-domain or day-branch evidence,
   then use activation as confirmation.
3. Migration should start with movement/clash/residence-axis evidence, then use
   major-luck transition as confirmation.
4. Career-project events should start with career-domain ten-god and project
   launch evidence, then use major-luck continuation as confirmation.

Source: this session's annual event evidence-bundle calibration results,
2026-06-26.

## v45: Movement Events Need Movement Evidence

The evidence bundle showed that major-luck continuation and natal activation
are too broad for migration and transition timing. A person can be in a major
luck period every year, and many years can activate some natal signal. Those
signals cannot be the trigger for relocation or major transition.

The next evolution adds movement-specific evidence:

1. Parse the annual branch.
2. Compare it against natal branches.
3. Detect branch clashes as movement proxies.
4. Add `movement_signal` and `branch_clashes` to every event sample.
5. Require `movement_signal` for migration and transition strict matches.

Reasoning change: event-specific evidence must lead, broad support evidence
must confirm. For migration, the leading evidence should be movement/clash or
residence-axis activation. Major-luck continuation and natal activation can
raise confidence only after movement evidence appears.

This improved the migration diagnostic by lowering false positives. It also
keeps the framework honest: exact-year migration claims should not be made from
generic activity, useful-element support, or major-luck continuation alone.

Source: this session's migration movement-evidence tightening, 2026-06-26.

## v46: Career Events Need Strong Career Evidence

Career-project and career-power topics remained overbroad after adding annual
event evidence. The issue was similar to migration: broad supporting signals
were allowed to act as triggers. A career event should not fire because any one
career-adjacent ten-god appears.

The next evolution adds `career_signal_strength`:

1. expression signal
2. authority signal
3. wealth signal

Career-project strict matching now requires at least two career-domain signals
plus support or activation. Career-power requires authority evidence. Business
power requires wealth or authority plus major-luck or natal confirmation.

Diagnostic result: false positives dropped sharply, but recall also dropped.
This is acceptable for an intermediate calibration layer. It means the rule is
more disciplined but still missing project-launch evidence.

Reasoning change: career events are not one category. The framework should
separate:

1. project launch: output/expression plus support and a launch marker
2. role power: authority plus institutional or title marker
3. business power: wealth/operation plus structural support
4. generic busy year: insufficient for exact-year career claims

Source: this session's career-event strong-evidence tightening, 2026-06-26.

## v47: Split Project Launch From Role Power

After strengthening career evidence, career-project recall became too low. That
showed that "career evidence" still needs subtypes. A project launch and a role
power event are not the same signal.

The next evolution adds two evidence flags:

1. `career_launch_signal`: output, visibility, sales, teaching, public delivery,
   creative output, or career-entry wording in the annual row.
2. `role_power_signal`: rules, title, leadership, institutional pressure,
   managers, regulators, or role clarity wording in the annual row.

Career-project timing now requires project-launch evidence plus at least one
career-domain ten-god and support/activation. Career-power timing requires
authority plus role-power evidence.

Diagnostic result: career-project recall recovered, but precision remains low.
Career-power remains too sparse. This means the framework needs better
structured markers for actual project launches and title/institution changes,
not merely annual career prose.

Reasoning change: report-language themes can provide weak evidence, but they
are not enough. Future iterations should promote launch markers and role-power
markers into structured annual fields rather than mining text.

Source: this session's career launch and role-power evidence pass, 2026-06-26.

## v48: Promote Annual Event Markers Into Structured Fields

Career-launch and role-power evidence initially came from annual prose. That
was a useful bridge, but it was brittle: prose changes can silently change
calibration behavior.

The next evolution promotes event clues into structured annual row fields:

1. career launch
2. role power
3. business power
4. relationship
5. movement
6. study/exam
7. public visibility
8. health pressure
9. adult career stage
10. marker basis

The famous-case calibration now reads these structured markers first and uses
text extraction only as fallback.

Reasoning change: a report renderer can use prose, but calibration should use
typed features. Typed event markers make the analysis portable, testable, and
less dependent on wording. This is a step toward turning Mingli interpretation
from narrative-only output into auditable intermediate representations.

Source: this session's annual event-marker schema upgrade, 2026-06-26.

## v49: Compute Event Markers From Evidence, Not Labels Alone

Typed event markers are useful only if they are grounded in the same evidence
used by the chart engine. A marker that comes only from the annual category or
life-stage label is still a disguised template.

This iteration changes the annual marker layer to read these features before
setting career, relationship, movement, study, visibility, or health flags:

1. annual stem and branch ten-god pair
2. useful-god or dominant-element state
3. active major-luck overlap
4. natal pillar activation
5. annual intensity
6. age-stage boundary

The calibration result is intentionally mixed: the structure is now more
auditable, but the strict famous-case metrics did not yet improve. Overall
strict exact hit rate remains 0.138, strict precision remains 0.111, and strict
false-positive rate remains 0.102 in the current fixture set. This means the
upgrade is a representation improvement, not yet a predictive-quality claim.

Reasoning change: move from "typed markers exist" to "typed markers must be
computed from inspectable symbolic evidence." Future rule evolution should tune
the marker predicates against topic-level false positives instead of modifying
Chinese report prose.

Source: this session's evidence-driven annual marker pass, 2026-06-26.

## v50: Select Strict Rules With Variant Sweeps

After event markers became structured, the next failure was no longer missing
fields; it was over-permissive strict matching. Career-project and migration
signals fired too often in negative years.

This iteration adds a rule-variant sweep to the famous-case annual calibration.
For each high-risk topic, the framework compares candidate predicates against
event years and negative years, then records the selected rule in the receipt.

Observed changes in the current fixture set:

1. overall strict exact hit rate changed from 0.138 to 0.108
2. overall strict precision improved from 0.111 to 0.177
3. overall strict false-positive rate dropped from 0.102 to 0.046
4. career-project false-positive rate dropped from 0.222 to 0.021
5. migration false-positive rate dropped from 0.169 to 0.008

The selected migration rule requires a stronger movement signature: movement
signal, at least two core pillar branch clashes, and major-luck or natal
confirmation. The selected career-project rule accepts only structured career
launch markers with useful-state or natal activation, reducing broad output-year
overfires.

Reasoning change: strict exact-year claims should optimize for fewer false
positives, while loose/window matching preserves recall diagnostics. Rule
changes should be chosen through a recorded sweep rather than informal prose
edits.

Source: this session's annual rule-variant sweep and strict-rule tightening,
2026-06-26.

## v51: Record Rejected Rule Variants

After strict-rule tightening, the next temptation is to recover recall by
loosening low-hit topics. The candidate sweep showed why that is risky.

For career-power, broad authority-transition variants raised recall to 0.5, but
false-positive rate rose to 0.17 or 0.362. For study/exam, broad
resource-authority variants raised recall to 0.667, but false-positive rate rose
to 0.333. The selected strict variants therefore remain conservative even
though their current recall is zero.

Reasoning change: automatic evolution should record rejected candidates, not
only accepted upgrades. A rejected candidate is useful knowledge because it
prevents later agents from repeating a superficially attractive but noisy rule
change. The framework should treat "do not adopt this rule yet" as a first-class
method artifact when the evidence shows a worse precision/false-positive
tradeoff.

Source: this session's career-power and study-exam variant sweep, 2026-06-26.

## v52: Turn Diagnostics Into Executable Evolution Tasks

Rule diagnostics are useful, but future agents should not have to reread all
metrics to infer the next work item. This iteration adds an evolution task plan
to the annual famous-case calibration receipt.

Each task records:

1. event topic
2. priority
3. task type
4. selected rule variant
5. rejected variant metrics
6. next evidence fields to add
7. acceptance criteria

The first generated tasks target career-power and study/exam because they have
low strict recall and rejected broad variants with unacceptable false positives.
The task plan therefore says what evidence must be added before rules should be
relaxed: command/title-transition markers for career power, and formal
exam/certificate markers for study events.

Reasoning change: evolution should produce a work packet, not only a score. A
diagnostic receipt becomes more useful when it can directly drive the next
agent iteration with acceptance criteria.

Source: this session's annual evolution task-plan receipt, 2026-06-26.

## v53: Separate High-Recall Evidence From Strict Rules

The career-power task plan asked for a title-or-command-transition marker. This
iteration adds a structured role-transition marker to annual event rows and
annual evidence bundles.

The result is useful but noisy:

1. role-transition marker hit rate for career-power events is 1.0
2. strict precision is 0.129
3. false-positive rate is 0.574

Therefore the marker is retained as evidence but rejected as the selected strict
rule. This is a useful distinction: a high-recall marker can be a candidate
feature for later combinations, while still being too broad for exact-year
claims.

Reasoning change: evidence fields and decision rules are different layers. A
new field may improve observability even when it should not be adopted as a
strict predictor. Future evolution should combine role-transition with event
subtypes or stronger authority-axis evidence before using it for career-power
judgment.

Source: this session's role-transition marker pass, 2026-06-26.

## v54: Add Event Subtypes As Calibration Labels

Role-transition evidence was too broad. The next missing layer is event subtype:
career power is not one thing. It can mean command succession, military command,
national leadership consolidation, international recognition, or loss of
office.

This iteration adds event subtypes to sourced famous-case event years and
exports subtype summaries in the annual calibration receipt. Subtypes are labels
for diagnostics, not prediction inputs. Negative years do not receive subtypes.

Current coverage:

1. career-power subtype coverage is 1.0
2. study/exam subtype coverage is 1.0
3. career-project subtype coverage is 0.094

Reasoning change: before a broad symbolic marker can become a strict rule, the
fixture set needs event subtypes. Subtypes let future agents ask a sharper
question: "which kind of power event is this?" rather than tuning one generic
career-power predicate.

Source: this session's event-subtype calibration-label pass, 2026-06-26.

## v55: Expand Project-Event Subtype Coverage

Career-project was the largest event topic but had poor subtype coverage. A
single label like "project_or_work_event" hides very different cases: film
breakthrough, album release, major theory, sports title, television launch, or
business production launch.

This iteration adds explicit project-event subtypes for sports, film/TV, music,
martial arts, and science fixtures. Career-project subtype coverage improves
from 0.094 to 0.938 while strict prediction metrics remain unchanged.

Reasoning change: improve calibration labels before tuning rules. Better
subtype coverage helps future agents design domain-specific evidence markers
without pretending the label itself is a predictive feature.

Source: this session's career-project subtype expansion, 2026-06-26.

## v56: Use Subtype Coverage To Schedule Evolution Tasks

Subtype coverage should not only be reported; it should change what the next
agent does. This iteration feeds subtype coverage into the annual evolution task
plan.

If a topic has enough events but subtype coverage below 0.5, the task type
becomes `expand_subtypes` before rule tuning. The current top tasks are now:

1. public-fame subtype expansion
2. relationship subtype expansion
3. public-controversy subtype expansion

Reasoning change: when labels are too coarse, rule tuning is premature. The
evolution scheduler should first improve dataset granularity, then revisit
symbolic predicates.

Source: this session's subtype-aware task scheduler pass, 2026-06-26.

## v57: Complete Public-Fame Subtype Expansion

The scheduler identified public-fame as the highest-priority subtype expansion
task. This iteration adds explicit public-fame subtypes across film/TV, sports,
music, martial arts cinema, and science fixtures.

Public-fame subtype coverage moved from 0.061 to 1.0. The task plan now changes
public-fame from `expand_subtypes` to `refine_precision`, while relationship and
public-controversy remain subtype-expansion tasks.

Reasoning change: the evolution loop should close tasks and move on. Once a
label-quality task is complete, the same topic can graduate to precision work,
and the scheduler should surface the next unresolved label-quality topics.

Source: this session's public-fame subtype expansion, 2026-06-26.

## v58: Complete Relationship Subtype Expansion

The next scheduled subtype task was relationship. This iteration adds explicit
relationship subtypes for marriage, celebrity marriage, early marriage, divorce,
relationship end, and marriage breakdown.

Relationship subtype coverage moved from 0.0 to 1.0. The task plan now changes
relationship from `expand_subtypes` to `refine_precision`, leaving
public-controversy and sports-peak as remaining subtype-expansion work.

Reasoning change: relationship events are not one symbolic outcome. Marriage,
divorce, public partnership, and relationship ending should be separated before
relationship rules are tuned.

Source: this session's relationship subtype expansion, 2026-06-26.

## v59: Complete Public-Controversy Subtype Expansion

The next subtype task was public controversy. This iteration separates media
legal controversy, political controversy, criminal allegation controversy, trial
controversy, religious-media controversy, and sexual-expression controversy.

Public-controversy subtype coverage moved from 0.0 to 1.0. The task now
graduates from `expand_subtypes` to `add_specific_evidence`, because the labels
are granular enough to design evidence fields.

Reasoning change: controversy is a very broad social outcome. Before symbolic
rules can be tuned, the fixture must distinguish legal pressure, media pressure,
religious/censorship pressure, and public-expression backlash.

Source: this session's public-controversy subtype expansion, 2026-06-26.

## v60: Complete Sports-Peak Subtype Expansion

Sports peak was still labeled as one generic competition peak. This iteration
adds explicit subtypes for grand-slam breakthrough titles, Olympic medal
breakthroughs, Olympic record peaks, world-number-one peaks, dominant multi-slam
seasons, record titles, late-career titles, and comeback titles.

Sports-peak subtype coverage moved from 0.0 to 1.0. The task now graduates from
`expand_subtypes` to `reduce_false_positive`, because sports peak already had
relatively higher hit rate but still overfired in negative years.

Reasoning change: sports achievements need subtype resolution before performance
rules can be tightened. A championship, record season, ranking peak, and
comeback title are related but not identical signals.

Source: this session's sports-peak subtype expansion, 2026-06-26.

## v61: Complete Health-Risk Subtype Expansion

Health-risk was the last major high-count subtype gap. This iteration separates
sudden death, acute drug-related death, mental-health or hospitalization crisis,
cardiac surgery/transfusion risk, chronic infectious disease diagnosis,
terminal illness disclosure, cancer diagnosis/treatment, terminal cancer death,
sports injury surgery, and injury recurrence.

Health-risk subtype coverage moved from 0.0 to 1.0. After this pass, no large
event topic remains scheduled as `expand_subtypes`. The remaining low-coverage
topics are small-sample or already above the subtype threshold.

Reasoning change: health-related labels need extra caution. Subtypes should
increase calibration precision, but they must not be used to produce stronger
medical claims in reports. The next stage should improve evidence fields and
strict-rule precision, not intensify health wording.

Source: this session's health-risk subtype expansion, 2026-06-26.

## v62: Domain-Stratified Celebrity Fixture Coverage

The famous-person fixture set already included sports, film, and music cases,
but the validation receipt only exposed a total domain list. This iteration adds
`domain_coverage` to the famous-case receipt, with per-domain case counts, event
counts, source names, source ratings, case ids, event topics, and topic counts.

The practical change is that sports, film, and music coverage is now an audited
contract instead of a prose claim. Current local coverage includes three sports
cases with 32 event labels, three film cases with 33 event labels, and three
music cases with 33 event labels; Bruce Lee remains a separate film-martial-arts
bridge case.

Reasoning change: celebrity validation can silently overfit to one public-life
domain if only aggregate event metrics are checked. Domain-stratified coverage
keeps sports, film, and music as separate calibration surfaces before annual
rules are changed.

Source: this session's domain-coverage receipt upgrade, 2026-06-26; source
family remains Astro-Databank public pages with attached ratings.

## v63: Domain-Topic Annual Calibration Slices

The annual famous-case receipt now includes `domain_topic_summary`, a
cross-table by public-life domain and event topic. Each slice records case
count, event count, negative-year count, loose and strict hit rates, precision,
false-positive rate, case ids, and an explicit small-sample boundary.

This creates a more useful diagnostic surface than aggregate topic metrics. For
example, sports `sports_peak` currently has visible strict signal but high
false positives; film `public_fame` and film `career_project` have zero strict
hits in the local sample; music `public_fame` and `career_project` show weak
but nonzero strict signals. These differences should drive separate evidence
design instead of one shared celebrity-fame rule.

Reasoning change: a topic such as fame, career launch, or peak achievement does
not mean the same thing across sports, film, and music. The framework should
learn and reject rules at the domain-topic level before promoting them to
general annual timing logic.

Source: this session's domain-topic annual calibration receipt upgrade,
2026-06-26; source family remains Astro-Databank public pages with attached
ratings.

## v64: Domain-Topic Refinement Queue Before Rule Changes

The domain-topic calibration table exposed weak slices, especially film
`public_fame` and film `career_project`. This iteration adds
`domain_topic_refinement_queue` to the annual famous-case receipt. The queue
turns weak slices into executable work packets with task type, current metrics,
case ids, next evidence to add, and acceptance criteria.

The important design choice is that the queue does not change strict annual
rules. Film fame currently needs film/television release, award, nomination,
ratings, box-office, or press-recognition evidence before public-visibility
signals can become a stricter timing rule. Music fame needs chart, album,
broadcast, tour, and media-peak evidence. Sports peak needs title, ranking,
record, medal, and comeback evidence with false-positive control.

Reasoning change: when a diagnostic slice is weak, the next action should be
evidence design, not prose confidence or broad rule relaxation. A rule can be
promoted only after the queue item has a candidate marker and acceptance
metrics.

Source: this session's domain-topic refinement queue upgrade, 2026-06-26.

## v65: Domain-Topic Candidate Sweep Without Rule Promotion

The annual famous-case receipt now includes `domain_topic_variant_sweep`. It
evaluates candidate predicates for film fame, film projects, music fame, music
projects, and sports peaks while keeping every candidate unselected. The sweep
is audit evidence, not a rule change.

The current result is instructive: film `public_fame` and film `career_project`
remain at zero strict hits even under visibility-oriented candidates. That
means the local symbolic evidence cannot yet distinguish film release,
industry recognition, ratings, box office, or press recognition from generic
expression years. Music and sports candidates show some signal but also show
false-positive tradeoffs, so they should not be promoted without domain facts.

Reasoning change: when candidate rules fail, the correct evolution is not a
looser symbolic predicate. It is a new evidence layer. For celebrity domains,
that layer should encode industry facts such as release, award, nomination,
chart, ranking, title, record, ratings, box office, broadcast, and tour markers.

Source: this session's domain-topic candidate sweep, 2026-06-26.

## v66: Industry-Event Evidence Layer for Celebrity Calibration

The candidate sweep showed that film fame and film project timing cannot be
improved by broad symbolic predicates alone. This iteration adds
`industry_event_evidence` to sourced famous-case event rows and
`industry_event_evidence_summary` to the annual calibration receipt.

The layer converts event subtypes into structured industry evidence: film or
television release, screen role, production launch, award, nomination, ratings,
box office, press recognition, music chart/album/broadcast/tour markers, and
sports title/ranking/record/medal/season/comeback markers. Current local
coverage reaches 1.0 for film project, film fame, music project, music fame,
and sports peak calibration slices.

Reasoning change: when symbolic rules cannot distinguish an industry outcome,
the framework should add a sourced outcome-evidence layer before changing
timing predicates. This keeps BaZi symbolic evidence separate from factual
industry outcomes and prevents the model from pretending that a broad
expression year knows about awards, releases, rankings, or box office.

Source: this session's industry-event evidence layer, 2026-06-26.

## v67: Industry-Evidence Upper-Bound Candidate Sweep

The domain-topic candidate sweep now includes fixture-industry variants such as
`fixture_industry_fame_marker`, `fixture_industry_project_marker`, and
`fixture_industry_peak_marker`. These variants combine the new industry-event
evidence with domain-topic slices, but they remain explicitly unselected.

The result is an upper-bound diagnostic: film fame, film projects, music fame,
music projects, and sports peak all reach strict hit rate 1.0 and false-positive
rate 0.0 when the sourced known-event industry labels are used. This proves the
industry evidence layer can represent known outcomes. It does not prove future
predictive timing, because negative years do not have equivalent industry-event
labels.

Reasoning change: outcome evidence and timing evidence must remain separate.
Industry labels can validate that the event ontology is expressive enough; they
cannot replace the symbolic annual rule. The next real rule work must connect
industry-evidence categories to independently observable pre-event or
same-year public data, then test false positives again.

Source: this session's industry-evidence upper-bound candidate sweep,
2026-06-26.

## v68: Industry Negative-Year Source Coverage Gate

The annual famous-case receipt now includes `industry_event_source_coverage`.
It records that positive event years have fixture-derived industry evidence,
but negative years do not yet have equivalent external industry labels. Current
local calibration has 130 positive events and 1418 negative-year samples; the
negative-year industry label coverage rate is 0.0.

This turns an implicit weakness into an explicit gate. Fixture-industry
candidate variants can show perfect hit rate and precision only because they
read known event-year labels. They cannot be promoted until non-event years are
also checked against reviewed external sources for releases, awards,
nominations, charts, rankings, titles, records, box office, broadcasts, and
explicit absence where available.

Reasoning change: false-positive control requires symmetric evidence. A
positive fixture label without negative-year industry coverage is enough to
test ontology expressiveness, but not enough to test predictive timing.

Source: this session's industry negative-year source coverage gate,
2026-06-26.

## v69: Industry-Event Source Provider Handoff Gap

The industry negative-year gate is now promoted into a global known gap:
`industry_event_source_provider`. It has owner domain `industry_events`,
blocking scope `externally_reviewed_industry_event_manifest`, verification
commands through the existing outcome-dataset, production-readiness, and
release-manifest paths, and handoff candidates for IMDb non-commercial
datasets, MusicBrainz, Wikidata Query Service, and Olympedia.

Reasoning change: once a calibration blocker affects rule promotion, it should
not live only inside a receipt. It needs a portable gap record, candidate source
list, closure condition, and runbook commands so another agent can close it
without rereading the whole evolution log.

Boundary: these sources are candidates, not accepted providers. Licensing,
coverage, identity matching, refresh cadence, statement references, and
negative-year semantics must be reviewed before any source closes the gap.

Source: this session's industry-event source provider handoff, 2026-06-26;
candidate source URLs are recorded in `EXTERNAL_INTEGRATION_CANDIDATES`.

## v70: Industry-Event Manifest Contract Before Provider Integration

The industry-event handoff now has a local manifest contract example at
`examples/mingli_5agents/providers/industry_event_source_manifest_example.json`.
It models how famous sports, film/television, and music cases should encode
both positive event years and explicit negative years. The capability audit now
hashes this file into `industry_event_source_manifest_example`, recording
record counts, positive/negative counts, source families, candidate source
names, content hash, and the fact that the file is not production evidence.

Reasoning change: before writing connectors for IMDb, MusicBrainz, Wikidata, or
Olympedia, define the receiving contract. Provider code should satisfy the
contract rather than allowing each source to introduce its own ad hoc event
shape. This follows the same architecture as provider stdout contracts and
outcome-dataset manifests: build the stable boundary first, then attach data.

This matters for celebrity validation because positive famous events are easy
to overfit. The manifest forces each domain-topic-year to carry source family,
source URL, review/licensing status, split role, and negative-year explanation.
That makes later rule debates distinguish factual industry evidence from
symbolic timing evidence.

Boundary: the current file is example-only. It demonstrates field shape and
handoff readiness, but does not close `industry_event_source_provider` because
it is not externally reviewed and is not accepted as production evidence.

Sources:

- IMDb Non-Commercial Datasets: https://developer.imdb.com/non-commercial-datasets/
- MusicBrainz Database: https://musicbrainz.org/doc/MusicBrainz_Database
- Wikidata Query Service: https://query.wikidata.org/
- Olympedia: https://www.olympedia.org/
- This session's industry-event manifest example contract, 2026-06-26.

## v71: Executable Industry-Event Manifest Audit

The industry-event source contract is now executable through
`examples/mingli_5agents/industry_event_manifest.py`, CLI command
`industry-events --manifest`, API core function `industry_event_manifest_status`,
and HTTP route `GET /industry-events?manifest=...`.

The audit requires both positive event years and explicit negative years. It
also checks record fields, source-family declarations, `https://` source URLs,
split roles, pre-rule-change collection flags, and negative-year explanations.
It emits `industry-event-manifest-audit-receipt-v1`, so later connectors for
IMDb, MusicBrainz, Wikidata, and Olympedia can prove they satisfy the same
contract.

Reasoning change: a source contract is not operational until a machine can
reject malformed data. For famous-case validation, this matters because
celebrity histories are especially prone to hindsight leakage. The system must
be able to say: this year has a reviewed event, this year has a reviewed
non-event label, and both were collected before rule tuning.

The production gate remains closed. The bundled manifest passes structure
review, but it is still `example_only_not_production_evidence`; production
evidence requires external review and an explicit `reviewed_production_evidence`
status.

Source: this session's industry-event manifest audit CLI/API implementation,
2026-06-26.

## v72: Query Plan Before Live Celebrity Event Collection

The industry-event layer now has a query-plan contract at
`examples/mingli_5agents/providers/industry_event_source_query_plan_example.json`
and an executable auditor at
`examples/mingli_5agents/industry_event_query_plan.py`. The example query plan
uses Wikidata Query Service as a cross-domain source and defines SPARQL
templates for film public-fame events, music public-fame events, and sports
career-peak events.

Reasoning change: a manifest contract controls how collected facts are stored;
a query-plan contract controls how facts are searched before they become
records. Both are needed to prevent hindsight leakage. Without a query plan,
future agents could hand-pick famous-event years and skip negative years. With
a query plan, every collector must declare source endpoint, placeholders,
domain template, result mapping, negative-year rule, identity review, statement
reference requirements, and live-collection approval status.

This iteration keeps live collection closed. The query plan is marked
`example_only_not_live_collection`, and the collection gate does not pass until
external review marks the plan as `reviewed_live_collection_plan`. This matches
the broader framework pattern: define the contract, audit it, then allow data
only after review.

Source: this session's industry-event source query-plan audit implementation,
2026-06-26; query source candidate is Wikidata Query Service:
https://query.wikidata.org/.

## v73: Offline Collection Request Bundle Before Live Fetch

The industry-event query layer now supports offline collection request bundles.
Given a query plan, case id, public name, Wikidata QID, year range, split role,
and optional domain, the system expands SPARQL templates, builds query URLs,
previews the manifest fields that successful results would fill, and emits
stable request and bundle hashes. The CLI entry point is
`industry-event-requests`.

Reasoning change: live fetching should not be the first concrete collection
artifact. A reproducible offline request bundle lets reviewers inspect exactly
what would be queried before any network call happens. This creates a third
boundary after query-plan audit and before manifest audit:

1. Query plan: what templates are allowed.
2. Offline request bundle: what this case/year window would query.
3. Manifest audit: what collected records are allowed to enter calibration.

For celebrity validation, this is important because source queries can encode
hindsight leakage just as easily as final labels. The request bundle records
the QID, year range, domain, template id, expanded SPARQL, query URL, negative
year rule, and manifest preview before the collector can see results.

Boundary: execution remains blocked. `execution_gate.passed` is false because
offline request bundles are not live collection authorization. External review
must still approve identity matching, source references, and collection policy.

Source: this session's industry-event offline collection request bundle
implementation, 2026-06-26.

## v74: Cached Response Import Before Evidence Promotion

The industry-event layer can now convert a cached Wikidata-like JSON response
into a draft manifest without making a network request. The importer maps
response bindings into positive industry-event records, then fills missing
years in the requested window as explicit negative records. The generated draft
is immediately passed through the same industry-event manifest audit used for
hand-authored manifests.

Reasoning change: evidence ingestion needs a no-network rehearsal layer between
request review and production evidence. This layer proves that a response can
be transformed into auditable records and that negative years are not forgotten.
It also binds the draft to the query-plan receipt, request-bundle receipt,
response hash, and manifest-audit receipt.

This matters for命理 calibration because public celebrity events are tempting
to cherry-pick. A cached-response importer forces every year in the requested
window to become either a sourced positive record or a documented negative
record. That makes later false-positive tests structurally possible.

Boundary: the draft is not production evidence. It still needs source review,
identity review, statement-reference review, and live-collection governance
before it can close the industry-event source provider gap.

Source: this session's cached-response to draft-manifest implementation,
2026-06-26.

## Current Strategy

1. Treat every domain calculation as a provider capability, not an LLM opinion.
2. Require provider stdout contracts before accepting professional status.
3. Bind each provider call to request receipts and raw contract receipts.
4. Promote critical provider lineage and provenance requirements into production gates.
5. Bind source evidence to rights/review metadata and latest refresh receipts.
6. Bind outcome evaluation to pre-analysis label provenance and pre-registered statistical plans.
7. Bind production-readiness decisions into release manifest checks and release receipts.
8. Promote implemented methodology changes into capability-audit evidence.
9. Map every false capability to a known gap or explicit optional policy.
10. Promote critical accountability checks into production and release gates.
11. Validate known-gap runbooks against current executable interfaces.
12. Validate both action names and option surfaces for runbook commands.
13. Promote runbook coverage into release gate checks.
14. Preserve known gaps as first-class release blockers.
15. Package every open external gap as a portable handoff bundle.
16. Gate the handoff bundle in production readiness and bind it into release receipts.
17. Expose release-governed artifacts through direct CLI/API export surfaces.
18. Attach stable export receipts to direct export surfaces.
19. Provide offline verification commands for exported governance artifacts.
20. Convert verified handoffs into implementation checklists.
21. Expose executable handoff operations through both CLI and HTTP API surfaces.
22. Add expected-receipt drift binding for generated implementation checklists.
23. Separate safe default configuration fixtures from production evidence receipts.
24. Let LLM synthesis operate only after structured contracts and evidence summaries exist.
25. Record methodology changes in wiki at the same time operational changes land in code/tests.
26. Run Mingli synthesis through five reasoning layers before report narration.
27. Apply age-aware domain policies before generating annual event language.
28. Treat user fact feedback as calibration data that can revise the recognized pattern.
29. Generate annual narratives from branch-relation evidence instead of fixed topic templates.
30. Keep factual event calibration as a separate input that can override theoretical framing.
31. Let a domain specialist contain school sub-agents when the tradition has competing methods.
32. Preserve intra-domain school conflicts as structured evidence, not prose-only caveats.
33. Require a computed period signature before generating annual or monthly prose.
34. Reject long-form reports whose monthly bodies repeat after only the date prefix changes.
35. Treat anti-template generation as a global report invariant, not a local style preference.
36. Recalibrate gender as factual input before rerendering child major-luck and relationship language.
37. Bind monthly wuxing movement to the chart's useful-god or exam-use chain before writing monthly advice.
38. Put annual context before monthly exam tables, including Gregorian annual boundaries and four-pillar relations.
39. Use famous-person charts only as weak, sourced calibration fixtures with explicit source ratings.
40. Give each school sub-agent method rules, event hypotheses, and calibration questions, not just a confidence vote.
41. Include sports, film, and music cases to diversify event tags before drawing calibration conclusions.
42. Promote validation fixtures into capability-audit receipts before claiming they are active system capabilities.
43. Run validation fixtures through the actual school-debate path and store weak calibration scores as diagnostic receipts.
44. Use annual event-year signal coverage as a smoke test before claiming exact-year predictive validation.
45. Pair every event-year recall metric with negative-year precision and false-positive diagnostics.
46. Keep loose and strict annual matchers side by side so recall and precision failures are both visible.
47. Diagnose annual timing failures by event topic before changing matching rules.
48. Convert calibration diagnostics into a prioritized rule-refinement queue with event-specific evidence requirements.
49. Attach evidence bundles to event-year samples so strict rules can be audited at feature level.
50. Require movement-specific evidence before accepting migration or transition timing signals.
51. Require strong career-domain evidence before accepting career-project or career-power timing signals.
52. Split career-project launch evidence from career-power role evidence.
53. Promote recurring event clues from prose into typed annual event markers.
54. Compute typed event markers from ten-god, useful-state, major-luck, and natal-activation evidence.
55. Choose strict event rules with recorded variant sweeps, not subjective prose edits.
56. Preserve rejected rule variants when they improve recall by creating unacceptable false positives.
57. Convert calibration diagnostics into executable evolution tasks with evidence requirements and acceptance criteria.
58. Keep high-recall evidence fields separate from strict decision rules until false positives are controlled.
59. Add event subtypes as calibration labels before tuning broad event-topic rules.
60. Increase subtype coverage for large event topics before learning finer symbolic rules.
61. Let subtype coverage drive evolution task scheduling before rule tuning.
62. Let completed subtype-expansion tasks graduate into precision-refinement tasks automatically.
63. Split relationship labels into marriage, divorce, and relationship-ending subtypes before tuning relationship rules.
64. Split public-controversy labels into legal, political, religious/media, and expression-conflict subtypes.
65. Split sports-peak labels into title, record, ranking, dominant-season, and comeback subtypes.
66. Split health-risk labels into medical-event subtypes while keeping report wording safety-bounded.
67. Audit famous-case coverage by public-life domain before changing event-timing rules.
68. Compare annual event timing by domain-topic slice before generalizing a rule across celebrity domains.
69. Convert weak domain-topic slices into evidence-design tasks before changing strict rules.
70. Run domain-topic candidate sweeps before promoting any domain-specific strict rule.
71. Add sourced industry-event evidence before asking symbolic rules to time celebrity outcomes.
72. Treat industry-label candidate sweeps as upper bounds unless negative-year labels exist.
73. Require negative-year industry-event coverage before using industry evidence for false-positive claims.
74. Promote rule-blocking source gaps into known-gap handoff bundles with candidate sources and runbooks.
75. Define source manifest contracts before building external connectors.
76. Make every external evidence contract executable through an audit command before accepting real data.
77. Define query-plan contracts before live collection so positive and negative celebrity-event data share one search protocol.
78. Generate offline request bundles before live fetch so reviewers can inspect exact source queries.
79. Import cached source responses into draft manifests before accepting live evidence.
80. Add a reviewed fetch/cache gate before collecting sports, film, or music celebrity events from public sources.
81. Audit celebrity candidate pools before collecting public events so sample selection is visible and reproducible.
82. Expand candidate pools into batch dry-run collection plans before any per-case live source work.
83. Batch-import cached celebrity source responses into draft positive/negative year manifests before calibration.
84. Merge per-candidate draft labels into one audited candidate-pool manifest before rule calibration.

## v75: Controlled Celebrity Event Fetch Cache Gate

The latest evolution answers whether sports, film, and music celebrities can be
used for validation: yes, but only through a governed evidence pipeline. The
framework now treats public event collection as a staged process:

1. Source family is declared in a reviewed manifest.
2. Query plan defines exact public-source search templates.
3. Offline request bundle expands person, year range, and domain.
4. Fetch/cache gate produces deterministic cache filenames and a receipt.
5. Cached response importer creates positive and negative annual records.
6. Manifest audit decides whether the evidence can enter calibration.

The important methodological change is that live data collection is no longer
an informal scraping step. It is a gated action with a receipt. By default the
system only creates a dry-run cache plan. A live fetch is blocked unless the
query plan is externally reviewed and marked collection-ready. This mirrors the
pre-registration idea from empirical research and supply-chain attestation from
SLSA/in-toto: define what will be collected before collecting it, bind it to a
hashable receipt, and make later calibration traceable.

For celebrity命理 validation this means:

- 体育明星: use public competition or award events, but preserve negative years.
- 影视明星: use award, nomination, or major work-release events with source
  family review.
- 歌手明星: use award, chart, release, or certification events with source
  family review.

The rule is now: do not let symbolic命理 rules learn from a celebrity case until
the factual event layer has positive-year and negative-year coverage.

## v76: Celebrity Candidate Pool Before Event Collection

The framework now separates "who should be tested" from "what happened in a
year." This is a small but important reasoning upgrade. If the system only
collects events for celebrities after seeing a convenient example, the validation
set can be biased before any命理 rule is tested. The new candidate-pool layer
therefore records candidate people first, before event extraction.

The bundled candidate pool covers three public-life domains:

- 体育: Roger Federer, Serena Williams, Michael Jordan.
- 影视: Jackie Chan, Meryl Streep, Tom Hanks.
- 音乐: Taylor Swift, Beyonce, Jay Chou.

Each candidate has a case id, public name, domain, industry, Wikidata QID,
Wikidata entity URL, split role, suggested event collection window, and
selection reason. The audit requires film/music/sports coverage, checks QID
shape and source URL shape, and emits a receipt. This means future validation
can say exactly which public figures were chosen before event labels were
collected.

Methodological change: sample selection becomes a first-class artifact. The
pipeline is now:

1. Candidate pool audit: decide which public figures are eligible.
2. Query-plan audit: decide how public events may be searched.
3. Request-bundle receipt: expand exact source queries.
4. Fetch/cache gate: cache source responses under deterministic names.
5. Draft manifest import: convert cached responses into positive and negative
   annual records.
6. Manifest audit: decide whether the event data may enter calibration.

This follows the same anti-leakage principle as pre-registration: choose the
sample and protocol before observing labels. It also makes later debate between
八字流派 more meaningful, because the schools will be evaluated against a
fixed public candidate set rather than a hand-picked anecdote.

## v77: Batch Candidate Collection Plans

The celebrity validation pipeline can now expand a reviewed candidate pool into
per-candidate dry-run fetch/cache plans. This turns the process from manual
case-by-case work into a reproducible batch operation:

1. Read the candidate manifest.
2. Optionally filter by domain or split role.
3. For each selected candidate, use their QID, event domain, split role, and
   collection window.
4. Generate a per-person source-query request bundle.
5. Generate deterministic cache paths.
6. Emit a batch receipt binding the candidate-pool receipt and all child plans.

Methodological change: a validation set is no longer merely "available"; it can
be operationalized as a batch plan before any network data is fetched. This is
important because manual per-case execution can silently change the sample:
some inconvenient candidates might be skipped, windows might be narrowed after
seeing data, or domains might be mixed inconsistently. The batch plan fixes
those choices in a receipt.

For命理智能体 evolution, this means famous-case validation can move toward a
more empirical workflow without pretending that the current evidence is already
production-grade:

- 候选池控制样本选择。
- 查询计划控制事件搜索方式。
- 批量 dry-run 控制执行范围。
- 缓存响应和清单审计控制事实标签。
- 八字流派辩论只在事实标签固定之后再参与判断。

This keeps the symbolic reasoning layer separate from the factual evidence
layer. The symbolic agents can debate timing rules later, but they cannot change
who was selected, what years were queried, or what source query was used.

## v78: Batch Cached Response To Draft Event Labels

The validation pipeline now has a batch import step after cached source
responses exist. It reads the candidate pool, regenerates the expected
fetch/cache plan, checks whether each planned cache file exists, and imports
available responses into draft manifests. Missing cache files are not ignored;
they become explicit failures.

The reasoning upgrade is that "we have data" now means:

1. The candidate was selected before event labels were observed.
2. The query plan was fixed before collection.
3. The expected cache path was derived from a receipt.
4. The cached response hash is recorded.
5. The response is converted into both positive years and negative years.
6. The generated draft remains audit-only until source review.

This matters because命理流年 validation is very sensitive to cherry-picking.
If only event years are recorded, almost any symbolic rule can appear useful.
Negative years are what make false-positive testing possible. The batch importer
therefore treats each requested year as a required label: either a positive
event is found in the cached response, or the year becomes an explicit negative
record with a reason.

The current implementation is still conservative. It does not claim real-world
truth merely because a cached response exists. It produces draft manifests and
receipts, then leaves production approval to source review. This keeps the
pipeline aligned with the larger agent-evolution strategy: LLM agents may
propose rules and debate interpretations, but factual labels must come from
reviewed, replayable evidence artifacts.

## v79: Candidate Pool Combined Draft Manifest

The batch importer now produces a single combined draft manifest for the selected
candidate pool. This is a structural change in the evidence layer: calibration
should not have to stitch together many per-person artifacts by hand. The
combined manifest gives downstream scoring one object that can be audited by the
same industry-event manifest contract used everywhere else.

The combined manifest contains:

- All imported positive and negative annual records.
- Deduplicated source-family declarations.
- A draft-only status that blocks production interpretation.
- Candidate-pool and query-plan provenance.
- A manifest audit receipt.

Reasoning change: validation needs a stable "fact table" boundary. Before this
step, the system could say each candidate produced a draft. Now it can say the
candidate pool produced one draft event-label table with record counts, source
families, split roles, and negative-year coverage. This makes the next stage
cleaner: 八字流派 and annual-timing rules can evaluate against a single reviewed
label table instead of reading ad hoc per-person outputs.

This also reduces a common failure mode in agentic research systems: evidence
fragmentation. If every agent keeps its own partial labels, later debate can
quietly compare different data. A combined manifest forces all agents to debate
against the same label set.

## v80: 事件清单先转成验证标签表

下一步演化，是把已经审计过的公开事件清单，先转换成统一的年度验证标签表，然后才允许八字、紫微、奇门或各流派子智能体去评分。事件清单负责保存证据来源，验证标签表负责给模型提供稳定的事实边界。

这对体育、影视、歌手三类名人尤其重要。体育样本常见的是冠军、排名、入选、伤病、复出和低谷年份；影视样本常见的是获奖、代表作品上映、票房、转型、争议和沉寂年份；歌手样本常见的是专辑、榜单突破、巡演、奖项、舆论风波和事业低点。三类事实形态不同，如果让命理智能体直接读传记，它很容易抓住传记措辞做事后解释。先转成标签表之后，各流派只能围绕同一个人物、年份、领域、事件主题、正负样本来辩论。

标签表记录这些内容：

- 公开人物是谁。
- 属于体育、影视还是歌手等哪个领域。
- 当前检验哪一年。
- 这一年是目标事件年份，还是明确的负样本年份。
- 检验的事件主题是什么。
- 证据来自哪个来源家族。
- 该记录属于训练、校准还是留出样本。
- 对应的确定性回执，方便后续智能体复现。

推理变化：命理流派智能体不能自己拥有评判自己的事实。它们可以争论格局、用神、十神、宫位、奇门象意和置信度，但事实标签必须来自独立的证据管线。这和机器学习评估里的基本纪律一致：模型输出和测试标签分离，才能发现误报和过拟合。

这也提高了移植性。另一个项目可以把来源采集器换成 Wikidata、IMDb、MusicBrainz、Olympedia，或者人工审核过的人物年谱，但仍然输出同一个标签表契约。符号推理层不需要知道证据怎么采集，只需要知道标签、来源回执和审核状态。

## v81: 名人验证必须标记跨领域覆盖

新增的覆盖门槛要求验证标签表明确说明是否同时覆盖体育、影视、歌手三类公开人物，并且每一类都至少有一个正样本年份和一个负样本年份。这样做不是为了阻止单领域实验，而是为了防止把单领域结果说成通用能力。

例如，只用体育样本测试网球或篮球明星，可以证明体育事件管线能跑通，也可以帮助改进运动成就的年份判定。但它不能证明影视、歌手样本也能判断准确，因为影视的作品爆发、奖项、票房、舆论和歌手的专辑、巡演、榜单、奖项，在事实结构和命理解释上都不完全相同。

推理变化：验证结论必须带上适用范围。标签表有效，不等于跨领域验证通过；单领域正负样本充足，不等于三领域泛化成立。后续各流派智能体投票时，应该读取覆盖门槛：通过时可以讨论跨领域规律，未通过时只能讨论当前领域的局部规律。

## v82: 事件标签必须先匹配出生资料

行业事件标签只说明某人在某一年是否发生了某类公开事件，它本身不是命盘。八字、紫微、奇门要做年度评分，至少还需要出生日期、时间、性别、地点和来源可信度。新的准备度层把这件事显式化：每一条事件标签都要先检查是否能匹配本地已审核的出生资料，能匹配才进入后续命理评分，不能匹配就保留为阻塞标签。

这一步解决一个常见误区：公开事件资料很容易找，出生资料却不一定可靠。如果只因为某个名人事件年份很多，就直接让命理智能体评分，系统会在事实层和命盘层之间偷换概念。准备度表把这种偷换挡住：事实标签有效，不等于命理评分可执行。

准备度表输出三类信息：

- 标签级：这一条年份标签是否可评分，缺什么。
- 案例级：这个人物有多少可评分标签，是否缺出生资料。
- 领域主题级：某个领域和事件主题是否有可评分的正负样本。

推理变化：命理评分的输入必须同时满足两个条件：一是事件标签可审计，二是出生资料可审计。只有事件、没有命盘，只能做事实数据准备；只有命盘、没有正负事件标签，只能做个案解释。两者都齐，才允许进入年度命理评分和流派辩论。

## v83: 可评分标签进入年度符号诊断

准备度层之后，新的年度符号诊断层开始真正读取可评分标签：先用出生资料排出命盘和年度行，再把正样本年份当作命中检验，把负样本年份当作误报检验。这样名人验证链条终于从“候选人和事实标签”推进到“命理年度信号是否在对应年份出现”。

这一层有一个重要的显式映射：行业标签里的 `career_peak` 不是传统命理事件主题。体育领域的 `career_peak` 会映射到 `sports_peak`，影视和音乐领域的 `career_peak` 会映射到 `career_project`。映射必须写进结果，不能悄悄替换，否则后续流派辩论会不知道自己到底在评什么。

当前示例给出一个清晰信号：宽松规则有命中，但也有误报；严格规则没有误报，但也没有命中。这说明系统不能为了好看的分数放松严格规则。正确的进化方向是补强事件证据，例如作品发布、奖项、排名、榜单、票房、冠军、角色权力、公众曝光等结构化标记，让严格规则有更真实的触发依据。

推理变化：命理规则演化要同时看命中和误报。只看正样本会鼓励事后解释；只看严格规则会过于保守。真正有价值的是把宽松规则、严格规则、正样本、负样本放在同一张诊断表里，然后决定下一步是补证据、扩样本、改主题映射，还是调整规则。

## v84: 评分结果必须产出证据任务

年度符号诊断如果只给出命中率和误报率，下一步仍然容易靠人工直觉决定。新的演化规则是：每一次行业名人评分，都必须同时输出证据补强队列和任务计划。分数回答“现在表现如何”，任务队列回答“下一步该补什么”。

当前队列的判断逻辑很朴素：如果某个领域主题的可评分正样本或负样本太少，优先扩样本和出生资料；如果严格误报高，优先收紧规则和负样本对照；如果严格命中低但样本基本够，优先补事件专属证据，而不是放松规则。这样可以避免为了让分数好看而把严格规则改宽。

对名人命理验证来说，证据任务应该尽量具体。例如：

- 影视和公众名声：补作品上映、奖项、票房、媒体曝光和负样本年份。
- 体育和高峰成就：补冠军、排名、奖牌、纪录、复出、退役和非高峰赛季。
- 歌手和公众名声：补专辑、榜单、巡演、奖项、认证和沉寂年份。
- 商业权力：补公司控制、制作人身份、职位变化和非权力年份。

推理变化：自动进化不是“看到低分就调规则”，而是“看到低分先判断缺数据、缺证据、误报高还是映射错”。只有当证据覆盖足够、正负样本充足、误报仍然可控时，才值得调整命理规则本身。

## v85: 证据任务必须落成工作包

任务队列仍然只是“应该做什么”。真正可复现的自动进化，还需要把任务落到候选池、查询计划、缓存目录和命令。新的工作包层会读取评分任务，找到对应领域的候选名人，然后生成下一步可执行但不触网的命令。

这一步把流程串起来：

1. 年度评分发现某个领域主题样本不足。
2. 任务队列生成 `expand_ready_labels`。
3. 工作包到候选池里找同领域候选人。
4. 工作包生成 dry-run fetch/cache 命令。
5. 等缓存响应存在后，再生成 draft-import 命令。
6. 后续再回到标签表、准备度、年度评分。

这让“自动进化”不再停留在建议层。未来智能体拿到工作包后，不需要重新理解整个项目，只要检查命令和来源边界，就能继续推进证据采集。

推理变化：进化闭环应该是“评分 -> 任务 -> 工作包 -> 证据 -> 再评分”。如果只有评分和任务，下一代智能体仍可能随意改规则；如果有工作包，下一步行动会被绑定到候选池、查询协议、缓存和回执。

## v86: 工作包要内嵌 dry-run 预览

只有命令文本的工作包还不够。命令告诉下一代智能体“可以怎么做”，但没有告诉它“这一步会产生多少请求、多少缓存文件、哪些候选人、哪些路径”。新的规则是：证据工作包必须内嵌 dry-run 计划摘要。

内嵌摘要至少包含：

- 候选人数。
- 请求数量。
- 计划缓存数量。
- 计划缓存路径。
- fetch/cache 回执。
- 失败原因。

这样未来执行前就能审查工作量和证据边界。比如一个工作包如果突然从 6 个请求变成 600 个请求，回执和摘要会立刻暴露范围变化。对于命理自动进化来说，这能防止证据扩充在无意中变成无边界抓取。

推理变化：可执行不等于可审计。真正适合迁移和复现的工作包，应该在执行前就能被审查；执行后再用缓存回执和标签回执复核。也就是先有计划回执，再有执行材料回执。

## v87: 区分计划证据和已落地证据

工作包知道缓存路径之后，还要知道这些缓存文件是否已经存在。计划路径表示“应该有这些证据”，本地文件表示“证据已经落地”。这两者不能混为一谈。

新的物化状态摘要会记录：

- 计划缓存数量。
- 已存在缓存数量。
- 缺失缓存数量。
- 已存在路径。
- 缺失路径。
- 是否全部缓存都已存在。

这让下一代智能体能先判断当前处于哪个阶段：如果缓存都缺失，就应该执行或审核采集；如果缓存已存在，就可以进入 draft-import；如果只存在一部分，就要补齐缺口，而不是用不完整数据评分。

推理变化：证据链至少有三层状态：计划、落地、审核。计划不能当事实，落地也不等于审核通过。命理规则评分只能使用审核后的标签；工作包阶段最多只能说明证据采集准备到哪里。

## v88: 缓存未齐不能进入草稿导入

有了缓存物化状态之后，还需要一个明确的闸门来回答“现在能不能导入”。如果只给出缺失数量，下一代智能体仍可能把导入命令拿去执行，最后生成不完整标签。

新的做法是：证据工作包必须有 `draft_import_readiness_gate`。这个闸门只看一件事：计划中的来源响应缓存是否全部存在。

闸门字段包括：

- 是否通过。
- 计划缓存数量。
- 已存在缓存数量。
- 缺失缓存数量。
- 阻断导入的缺失路径。
- 下一步动作。
- 阻断原因。

如果全部缓存存在，下一步才是 draft-import。如果缓存缺失，下一步必须回到 fetch/cache 审核与采集。这样体育、影视、歌手等名人案例可以继续扩展，但每一个案例都必须先经过“候选池 -> 查询计划 -> 缓存物化 -> 草稿导入 -> 标签审核 -> 年度评分”的链条。

推理变化：名人验证不能只问“找得到哪些人”。真正的问题是“每个案例的事实证据是否已经进入可评分状态”。闸门把这个判断从人工猜测变成可执行字段，避免把公开名人资料的搜索计划误当作已验证证据。

## v89: 被阻断的领域不能从工作包里消失

体育、影视、歌手三类候选人都可以找到，但“找到候选人”和“可以评分”不是一回事。一次检查发现：音乐标签已经在事件清单里，但因为 Bob Dylan 没有匹配的已审核出生资料，音乐切片没有进入年度象意评分，也没有生成事件采集工作项。这个状态如果不显式记录，下一代智能体会误以为音乐领域已经覆盖，或者误以为音乐不需要处理。

新的做法是把任务分成两层：

- 已可评分切片：生成事件标签扩展任务，比如影视、体育继续进入候选池取证和缓存计划。
- 被准备度阻断的切片：生成 deferred task，比如音乐先补“已审核出生资料”，暂时不进入事件缓存导入。

这样工作包里会同时出现：

- `work_items`：可以执行的事件来源缓存计划。
- `deferred_tasks`：还不能采集或评分的上游准备任务。

这条规则对命理验证很重要。命盘推演需要出生资料，流年验证需要事实事件标签，两者缺一不可。若只有事件没有出生盘，就不能评分；若只有出生盘没有事件，也不能验证。自动进化框架必须保留这种“不满足条件”的任务，而不是只展示已经能跑的部分。

推理变化：覆盖率不只看候选池有没有人，还要看“候选人、出生资料、事件标签、正负样本、缓存证据、审核状态”是否在同一条链上对齐。被阻断的领域要进入任务计划，否则系统会产生虚假的覆盖感。

## v90: 阻断任务要连接本地可补齐材料

只把音乐切片标成 deferred task 还不够。下一代智能体知道“缺出生资料”，但仍要自己翻仓库找有没有可用歌手样本。新的规则是：如果一个任务因为准备度不足被阻断，工作包应该给出本地可补齐材料建议。

这次音乐切片的情况是：

- 事件标签里有 Bob Dylan。
- Bob Dylan 没有匹配的本地已审核出生资料。
- 本地名人样本里已经有 Aretha Franklin、Madonna、Michael Jackson 三个歌手出生资料。
- 这三个样本都有 `career_project` 相关事件标签，可以作为音乐职业项目切片的候选补齐方向。

工作包因此新增 `local_birth_profile_suggestions`。它只做建议，不自动改标签。下一步可以有两种路径：

- 给 Bob Dylan 补已审核出生资料。
- 或者把已有歌手出生资料配套的音乐事件标签补进行业事件清单。

推理变化：自动进化不仅要指出缺口，还要指向可以补缺口的本地材料。但建议层不能直接改变事实表；事实表仍必须经过来源、标签、缓存、审核和回执链条。

## v91: 补齐建议要变成可审查工作单

本地材料建议只能回答“可能用什么补”。它还不能回答“下一步怎么补、补完后怎么验收”。新的规则是：deferred task 如果能找到本地补齐材料，就要附带 completion work order。

音乐切片现在有两条路线：

- 保留 Bob Dylan：给当前被阻断案例补已审核出生资料，不改事件标签。
- 使用本地歌手：给 Aretha Franklin、Madonna、Michael Jackson 补已审核音乐事件标签，让它们进入行业事件清单。

工作单必须明确：

- 当前状态。
- 可选策略。
- 每条策略需要的材料。
- 验收门槛是否通过。

当前验收门槛仍然是未通过，因为建议和工作单都不是证据。只有当出生资料或事件标签真的被加入，并生成新的准备度回执、标签表回执和评分回执，才算完成。

推理变化：自动进化的下一步不能停留在“可以考虑”。每个阻断任务都要被改写成可执行、可审查、可验收的工作单。但工作单仍然不能越权改变事实表；它只压缩下一步行动空间，让后续智能体少走弯路。

## v92: 本地年表只能生成草案标签队列

本地名人样本里有歌手的事件年表，例如 Aretha Franklin、Madonna、Michael Jackson 的 `career_project` 年份。它们对下一步很有帮助，但不能直接等同于行业事件验证标签。因为行业事件验证要求来源家族、来源链接、正负样本窗口、审核状态和回执。

新的规则是：本地年表可以生成 draft label plan，但不能直接写入 validation manifest。

草案标签计划包括：

- 每个本地歌手一个正样本年。
- 每个本地歌手一个相邻负样本年。
- 事件主题映射到 `career_project`。
- 来源状态标记为待行业事件来源审核。
- 验收门槛默认不通过。

这样做的价值是把“要补什么”进一步具体化：不再只是说“补音乐标签”，而是列出具体人物、具体年份、正负样本数量和需要审核的来源类型。后续智能体可以拿这个草案去找 MusicBrainz、Wikidata 或人工审核来源，而不是重新推断该从哪里开始。

推理变化：自动进化应该允许从本地弱证据生成待审查工作队列，但必须把弱证据和可评分证据分开。草案标签是行动线索，不是事实标签；只有通过来源审核并进入 manifest 后，才可以参与命理年度评分。

## v93: 草案队列也要有回执

草案标签虽然不能用于评分，但它仍然是自动进化链条里的重要中间产物。如果没有回执，下一代智能体无法判断草案队列是否被改过，也无法复现“为什么这次建议这 6 条音乐标签”。

新的规则是：只要草案队列会影响后续取证方向，就必须有稳定哈希和回执。

音乐草案标签计划现在包含：

- 草案记录哈希。
- 草案计划回执。
- 记录数量。
- 正负样本数量。
- 来源审核门槛。
- 草案记录明细。

这样后续执行来源审核时，可以先比对草案回执。如果回执变了，说明候选人物、年份选择、负样本规则或字段映射发生过变化，必须重新审查。

推理变化：不可评分不等于不可追踪。自动进化中很多关键决策发生在“还不能评分”的阶段，例如候选选择、草案年表、负样本规则和来源计划。这些中间产物如果没有回执，就会让后续评分看似可复现，实际输入已经漂移。

## v94: 回执要配自校验摘要

草案队列有回执之后，还要能证明“当前嵌套内容”和“回执材料”是一致的。否则后续智能体仍然要人工判断：这个回执是不是对应当前这组草案记录。

新的规则是：关键草案队列要带 `integrity_check`。

自校验至少检查两件事：

- 用当前 material 重算草案计划回执，是否等于存储回执。
- 用当前 draft records 重算记录哈希，是否等于存储哈希。

如果两者都通过，说明这个草案队列在当前输出里内部一致。它仍然不是事实证据，但至少可以作为稳定工作包交给下一步来源审核。

推理变化：回执不是装饰字段。回执必须可重算、可比对、可解释。对命理智能体进化来说，这能降低“提示词或中间草案被悄悄改动，但后续评分还沿用旧结论”的风险。

## v95: 草案标签要落到来源审核请求

草案标签列出了人物、年份、正负样本，但还不够。后续智能体还需要知道每一条草案应该到哪里核验、核验什么、现有查询模板是否匹配。

音乐草案现在暴露一个 `source_review_request_plan`：

- 每条草案标签对应一个审核请求。
- 正样本请求核验音乐发行、奖项、榜单、出版或公共职业项目标记。
- 负样本请求核验目标年份没有同类标记。
- 建议来源包括 MusicBrainz 和 Wikidata。
- 明确说明现有最近模板是 `wikidata_music_public_fame_events`。
- 明确说明没有精确的 music `career_project` 查询模板。

这一步很关键：不能因为“音乐 public_fame 模板看起来也能查音乐资料”，就把它悄悄用于 `career_project`。模板不匹配必须作为门槛暴露出来。后续要么新增 career_project 模板，要么人工确认 public_fame 模板足以覆盖当前草案；在此之前，门槛保持不通过。

推理变化：证据工作不是只有“找来源”。还要确认来源查询契约和要验证的事件主题一致。命理规则评分中的主题映射如果和事实采集模板错位，后续分数会变成模板偏差，而不是命理规则质量。

## v96: 模板缺口要给出可审查草案

发现 query template 不匹配之后，如果只写“需要新增模板”，后续智能体仍然要重新设计模板。新的规则是：当系统能安全推导模板形状时，要生成一个 query template draft，但保持门槛不通过。

音乐 `career_project` 草案模板现在包含：

- 模板编号。
- 领域和事件主题。
- 正样本事件类型。
- 负样本年份规则。
- 占位符。
- SPARQL 草案。
- 结果映射。
- manifest 默认字段。
- 模板哈希。
- 字段完整性检查。
- 审核门槛。

这让下一步从“想办法补模板”变成“审查这个模板草案是否可用”。如果模板草案通过审核，再进入 query-plan manifest；如果不通过，就记录拒绝原因并改模板。

推理变化：自动进化要减少下一步的自由度，但不能越过审核门槛。模板草案是可审查补丁，不是已安装能力。它把证据管线的设计意图变成结构化对象，便于复现和迁移。

## v97: 模板草案也要自校验

模板草案有哈希还不够。后续智能体需要知道当前模板内容是否真的等于这个哈希，以及模板是否仍然满足 query-plan 的必填字段契约。

新的模板草案自校验包括：

- 重算模板哈希。
- 比对重算哈希和存储哈希。
- 检查必填字段是否完整。
- 输出自校验状态。

这和草案标签队列的自校验类似，但模板多了一个字段完整性维度。因为模板即使哈希一致，也可能从一开始就缺字段；反过来，字段完整但哈希不匹配，说明内容漂移。

推理变化：证据管线的每个中间补丁都要能证明两件事：内容没漂移，契约没破。命理智能体的自动进化不是只改规则，也要保证采集事实的工具契约稳定。

## v98: 模板草案要附带补丁计划

模板草案自校验通过之后，下一步不是立即写入 manifest，而是生成补丁计划。补丁计划说明“如果要安装这个模板，应该怎么改”，但它本身不执行修改。

补丁计划至少包含：

- 目标文件。
- 操作类型。
- 插入位置。
- 预期模板数量变化。
- 模板编号和模板哈希。
- 需要人工审核的点。
- 补丁后验证命令。
- 审核门槛。

这样下一代智能体可以直接审查补丁计划：是否应该把模板放在这个位置，是否应该从 3 个模板变成 4 个模板，SPARQL 语义和来源许可是否可接受。未审查前，补丁门槛保持不通过。

推理变化：自动进化不是自动改所有文件。对影响证据采集能力的契约文件，应该先生成结构化补丁计划，再由审核或明确执行步骤推进。这样既提高连续性，又避免未审核采集能力悄悄上线。

## v99: 补丁计划也要可验证

补丁计划告诉后续智能体怎么修改文件，但它本身也可能漂移。例如目标文件、插入点、模板哈希或验证命令被改过。如果补丁计划没有回执，后续执行者无法判断自己看到的计划是不是原来的计划。

新的规则是：补丁计划必须有回执和自校验。

自校验至少包括：

- 回执是否由当前补丁计划 material 重算得到。
- 补丁计划哈希是否由当前 material 重算得到。
- 补丁计划引用的模板哈希是否等于模板草案哈希。

这样执行文件修改之前，可以先检查补丁计划本身是否稳定。只有补丁计划稳定，才值得继续审查是否执行。

推理变化：可执行计划也是证据链的一部分。自动进化不能只验证最终输出，还要验证中间行动计划，否则系统会在“准备修改能力契约”的阶段发生不可追踪漂移。

## v100: 补丁计划还要检查目标文件当前状态

补丁计划有回执和自校验，只能说明计划自身没有漂移。它不能证明目标文件仍然适合这个补丁。比如 query-plan manifest 可能已经新增模板、插入点可能被删掉、模板数量可能变化。此时即使补丁计划本身正确，也不应该直接执行。

新的规则是：补丁计划要有 applicability check。

适用性检查包括：

- 目标文件是否存在。
- 当前模板数量是否等于预期数量。
- 插入点模板是否存在。
- 草案模板是否尚未存在。
- 如果适用，也仍然保持执行门槛不通过，直到人工或上层审核明确允许修改。

推理变化：可执行计划的安全性由两部分组成：计划自身没漂移，目标环境也没漂移。命理智能体进化涉及能力契约、证据模板和评分规则，任何一边漂移都可能让后续结论失真。

## v101: 补丁执行前要有非写入预览

适用性检查只说明“当前目标文件可以套用这个补丁”。它还不能说明补丁套上之后文件会变成什么样。新的规则是：执行补丁前要生成非写入 patch preview。

补丁预览应该给出：

- 是否会写文件：必须为否。
- 补丁后的模板数量。
- 补丁后的模板顺序。
- 补丁后 query-plan 内容哈希。
- 预览本身的哈希。
- 执行门槛：仍然不通过。

这样审核者可以先看补丁结果是否符合预期，再决定是否真的修改文件。比如本轮音乐模板草案预览显示，新增模板会插在 `wikidata_music_public_fame_events` 后面，模板数量从 3 变 4。

推理变化：自动进化要把“将要发生什么”也结构化，而不是只给操作命令。对证据采集契约来说，非写入预览是执行前最后一道可复查边界。

## v102: 非写入预览也要可验证

patch preview 是执行前最后一道边界，因此它也要有回执和自校验。否则后续智能体只能看到一个“预览哈希”，但不能确认当前预览内容是否真的对应这个哈希。

预览自校验包括：

- 用当前 preview material 重算预览回执。
- 用当前 preview material 重算预览哈希。
- 检查预览 material 里的补丁后 query-plan 哈希是否等于外层暴露的哈希。

这样审核者可以先确认预览对象本身稳定，再决定是否执行文件修改。

推理变化：在自动进化链条中，越靠近“真实修改能力契约”的步骤，越需要强约束。预览虽然不写文件，但它直接影响下一步是否写文件，所以必须像正式证据一样可追踪、可重算。

## v103: 多层门槛要有顶层摘要

当一个 deferred task 发展出草案标签、来源审核计划、模板草案、补丁计划、适用性检查和补丁预览之后，门槛会分散在很多层级里。每一层都有 `acceptance_gate`、`execution_gate` 或 `integrity_check`。如果没有顶层摘要，后续智能体容易漏掉某个阻断条件。

新的规则是：复杂 deferred task 要输出 `gate_summary`。

摘要至少包含：

- 总门槛数量。
- 阻断门槛数量。
- 完整性检查数量。
- 失败完整性检查数量。
- 阻断门槛列表。
- 失败完整性检查列表。
- 下一步动作。

本轮音乐任务的状态很清楚：所有审核/执行门槛仍然阻断，但完整性检查全部通过。这表示结构化工作包是健康的，问题不在内部一致性，而在来源审核、模板审核和人工确认还没有完成。

推理变化：自动进化不只是增加更多门槛，也要让门槛可读。顶层摘要让系统能区分“结构坏了”和“审核还没过”这两种完全不同的问题。

## v104: 顶层门槛摘要也要有回执

门槛摘要让阻断状态可读，但摘要本身也可能漂移。比如某个嵌套门槛新增、删除或状态变化，顶层摘要就应该产生不同回执。

新的规则是：复杂 deferred task 的 `gate_summary` 要有回执、哈希和自校验。

这让后续智能体可以快速判断：

- 阻断栈是否和上次一致。
- 完整性失败数量是否变化。
- 阻断门槛数量是否变化。
- 摘要是否由当前 material 重算得到。

如果摘要回执变化，下一步就应该重新审查 blocker 栈，而不是沿用旧判断。

推理变化：顶层摘要不是普通展示文本，而是一个可迁移的状态快照。只要它影响后续执行顺序，就应该进入回执体系。

## Migration Recipe

To transplant this framework into another vertical:

1. Define domain specialists and the final synthesis boundary.
2. List claims that must come from deterministic engines, databases, or reviewed corpora.
3. Create JSON/tool provider protocols for each external capability.
4. Add raw output contracts and normalized public schema contracts.
5. Add request receipts, raw contract receipts, and protocol hash governance.
6. Add source/license/review governance for external text.
7. Add dataset label provenance before empirical validation claims.
8. Add capability audit entries and evaluator gates.
9. Add evidence-materialization probes for every implemented governance invariant.
10. Add blocked-capability coverage so every false capability has ownership.
11. Promote accountability coverage into production-readiness and release checks.
12. Validate runbook commands against local CLI/API surfaces.
13. Validate runbook options against current parser contracts.
14. Bind runbook coverage into release manifest gates.
15. Keep known gaps explicit until an installed provider or dataset closes them.
16. Export a per-gap handoff bundle with env vars, provenance vars, candidate projects, blocked capabilities, commands, gates, and hash.
17. Promote the handoff bundle into readiness/release gates before relying on it for migration.
18. Add direct export commands/endpoints for portable governance artifacts.
19. Add export receipts so downstream consumers can verify the transfer wrapper.
20. Add verifier commands that recompute hashes after transfer.
21. Generate implementation checklists from verified transfer artifacts.
22. Mirror executable handoff operations in both CLI and API contracts.
23. Add expected checklist receipt comparison so generated work packets can be replayed and drift-checked.
24. Provide safe default fixture configuration only when it cannot be mistaken for production evidence.
25. Keep production gates tied to executed receipts, not merely configured examples.
26. Append a wiki note for every imported method idea with source URL.
27. Define age-stage domain policies so generated annual narratives do not apply adult domains to children.
28. Store user-supplied domain reasoning frameworks as cited methodology notes before reusing them.
29. Implement branch-relation derivation before prose rendering.
30. Add a known-event calibration input and keep reports marked uncalibrated until facts are loaded.
31. Add a school-debate layer for domains where multiple interpretive schools exist.
32. Bind school-debate outputs with stable receipts so schema, audit, and reports can track them.
33. For every repeated timeline report, build a period-signature function before prose templates.
34. Add a uniqueness/hygiene check for generated reports: no mojibake, no stray English, no code blocks, and no repeated monthly bodies after date-prefix removal.
35. For every timeline renderer, add a uniqueness check after stripping only date or period prefixes.
36. When a user corrects a factual input such as gender, regenerate from source data rather than patching prose by hand.
37. For monthly reports, add a domain-specific element-to-function map and include it in each period signature.
38. For exam timelines, render monthly periods as comparison tables after an annual-context section.
39. Build a sourced case-fixture module before using public biographies for validation.
40. For any multi-school specialist, encode school-specific rules and calibration questions inside the sub-agent definition.
41. Segment validation fixtures by domain so model upgrades do not overfit to political or intellectual biographies.
42. Bind fixture receipts into capability audits and public schemas so downstream migrations can verify dataset presence and drift.
43. Add a school-level calibration receipt before attempting exact-year predictive scoring.
44. Add annual event-signal mappings and +/-1-year window coverage before introducing strict exact-year prediction metrics.
45. Add negative-year samples and precision metrics before tightening event-specific timing rules.
46. Add strict event-type matchers as a parallel diagnostic rather than replacing broad recall checks.
47. Add topic-level calibration summaries so migrations can prioritize which event rules need domain evidence.
48. Export a rule-refinement queue so future agents can reproduce the next evolution step without reading prose logs.
49. Treat broad supporting signals such as major-luck continuation as confirmation, not standalone exact-year evidence.
50. For movement events, add branch interaction or residence-axis evidence before using broad support signals.
51. Split career timing into project launch, role power, business power, and generic busy-year evidence.
52. Promote launch and role-power markers into structured fields after validating text-derived proxies.
53. Prefer typed event markers over text-mined evidence in all calibration paths.
54. Generate typed markers from structured evidence before using them in calibration or report synthesis.
55. Add rule-variant sweep receipts before tightening or relaxing exact-year event predicates.
56. Store rejected variants and their metrics so future migrations do not repeat noisy rule changes.
57. Export evolution task plans from calibration receipts so the next agent can continue from explicit work packets.
58. Add new evidence markers as observable features first, then promote them to strict rules only after precision checks.
59. Keep subtype labels out of prediction features; use them to guide evidence design and fixture expansion.
60. Track subtype coverage as a dataset-quality metric before accepting event-topic rule changes.
61. Promote low subtype coverage into explicit expand-subtypes tasks in downstream migrations.
62. After subtype coverage reaches threshold, remove the label-quality blocker and schedule rule-quality work.
63. Treat relationship-event subtype coverage as a prerequisite for relationship timing calibration.
64. Treat controversy subtype coverage as a prerequisite for authority-expression conflict rules.
65. Treat sports-achievement subtype coverage as a prerequisite for performance timing calibration.
66. Use health-risk subtypes for calibration only; do not convert them into stronger medical claims.
67. Preserve per-domain fixture counts, event counts, source ratings, and event-topic counts in portable receipts.
68. Export domain-topic annual metrics so migrations can decide whether to split or share event-timing rules.
69. Export domain-topic refinement queues with evidence requirements and acceptance criteria.
70. Keep candidate sweeps unselected until a new evidence layer passes false-positive checks.
71. Keep factual industry evidence separate from symbolic timing evidence in portable receipts.
72. Do not promote fixture-industry variants without an external event-source provider and negative-year coverage.
73. Export industry-event source coverage gates with provider fields and required domain-topic slices.
74. Record candidate source families as candidates only until licensing, coverage, and negative-year semantics pass review.
75. Ship an example-only manifest contract for each external evidence provider family before treating provider work as implementation-ready.
76. Add CLI/API audit surfaces for each manifest contract so downstream teams can validate data before integration.
77. Add query-plan audit surfaces before writing source collectors or accepting sourced event manifests.
78. Add request-bundle receipts between query-plan review and live collection.
79. Add cached-response importers that create both positive and negative records before production evidence review.
80. Add a dry-run-first fetch/cache gate so public celebrity data collection remains reviewable, repeatable, and blocked until source governance is ready.
81. Add candidate-pool manifests before event collection so sampling bias can be audited separately from timing-rule quality.
82. Add batch candidate-pool expansion so future validators can reproduce the same planned source queries from one manifest.
83. Add batch cached-response import so candidate pools can produce auditable positive and negative annual labels without manual per-case work.
84. Add a combined draft manifest after batch import so all downstream timing-rule agents score against the same fact table.
85. Convert audited event manifests into stable validation label tables before symbolic rule scoring.
86. Add cross-domain positive/negative coverage gates before claiming celebrity validation generalizes across sports, film, and music.
87. Add a birth-profile readiness gate before sending public event labels into symbolic annual scoring.
88. Score only readiness-approved event labels, and report both hit rate and false-positive rate before changing symbolic rules.
89. Generate evidence-refinement tasks from score receipts before tuning symbolic rules.
90. Convert evidence-refinement tasks into executable, receipt-bound workplans before collecting more labels.
91. Embed dry-run request/cache summaries inside evidence workplans before live collection.
92. Track cache materialization separately from planned evidence before draft import.
93. Add a draft-import readiness gate after cache materialization and before label import.
94. Preserve blocked domain-topic slices as deferred tasks instead of dropping them from executable workplans.
95. Attach local evidence suggestions to deferred tasks without silently rewriting validation labels.
96. Convert local suggestions into explicit completion work orders with failed gates until reviewed artifacts are added.
97. Convert local event timelines into draft label plans only, with failed source-review gates until evidence is audited.
98. Add receipts and stable hashes to draft queues that influence later evidence collection.
99. Add self-integrity summaries that recompute draft queue receipts and record hashes from current content.
100. Convert draft labels into source-review requests and expose query-template mismatches as failed gates.
101. When a query-template mismatch is detected, emit a reviewed-required template draft instead of prose-only guidance.
102. Add integrity checks to query-template drafts: recomputed hash match plus required-field completeness.
103. Emit non-mutating patch plans for reviewed-required template drafts before editing provider manifests.
104. Add receipts and integrity checks to non-mutating patch plans before execution.
105. Add applicability checks against the current target file before executing patch plans.
106. Generate non-mutating patch previews with expected post-patch hashes before file edits.
107. Add receipts and integrity checks to non-mutating patch previews before file edits.
108. Add top-level gate summaries for complex deferred tasks with nested gates and integrity checks.
109. Add receipts and integrity checks to top-level gate summaries that guide downstream execution.
110. Add whole-workplan readiness summaries that combine cache, deferred review, validation, and integrity blockers.
111. Before claiming sports, film, and music validation coverage, run an offline cross-domain fixture import that produces positive and negative labels for every domain.
112. Promote successful fixture loops into capability-audit receipts so future agents can discover and verify them without reading tests.
113. Bind new capability-audit artifacts into the public schema before treating them as portable integration surfaces.
114. Validate real runtime artifacts against the public schema after adding a schema contract; static `$ref` checks are not enough.
115. Validate public HTTP artifacts against the same schema used for internal runtime objects.
116. Validate CLI artifacts against the same schema because release scripts and future agents often use CLI surfaces.
117. Promote mature validation loops into implemented requirements with materialized evidence, not only capability flags.
118. Split celebrity validation into event-label coverage and birth-profile readiness before allowing symbolic BaZi scoring.
119. Convert readiness blockers into explicit evidence-completion task plans with case ids and acceptance criteria.
120. Link evidence-completion tasks to workplan summaries with local suggestions and blocked review gates.
121. Add a reviewed-birth-profile manifest contract before importing celebrity birth data into fixtures.
122. Expose critical review manifests through direct API/CLI surfaces, not only full capability audit.
123. Before importing reviewed data, build a non-mutating preview with a failed gate until evidence is complete.
124. Bind standalone review/import tools back into capability audit so future agents can discover the full evidence chain.
125. Put blocked safety previews into production-readiness gates so "must not import yet" is tested as a release invariant.
126. After adding a blocked import preview, add a reviewed-manifest contract path that proves the next state still remains non-mutating.
127. Before reviewed external data enters a core fixture, render a non-mutating patch preview with target-file hash, patch hash, and review gate.
128. Bind every new evidence-chain stage back into capability audit; direct tools alone are not enough for migration.
129. Put core-fixture patch previews into production readiness so default non-write behavior is a release invariant.
130. Convert blocked source-review needs into explicit human review work items before attempting live collection or fixture edits.
131. Give human review workplans their own API/CLI/HTTP surface so reviewers do not have to mine full capability audits.
132. Put human review workplans into production readiness so source-review tasks cannot disappear from the release path.

## v105: 工作包也要有整体就绪摘要

命理智能体进化到名人案例验证阶段后，问题不再只是“某个子任务有没有证据”，而是“整个验证工作包现在能不能推进”。影视、体育任务可能已经能生成抓取计划，但缓存还没有落地；音乐任务可能因为出生资料和来源审核不足而只能作为延期任务存在。如果执行器只看局部门槛，很容易误以为已有部分任务可进入导入阶段。

这次吸纳的规则是：复杂工作包必须有一个顶层就绪摘要。它不替代底层明细，而是把缓存缺口、延期审核门槛、校验失败、完整性失败合并成一个状态。状态为 blocked 时，执行器先看顶层 next_action；需要追溯时，再进入具体的 work item 或 deferred task。

这个模式来自前面已经建立的“门槛、回执、完整性检查”链条，但进一步强调控制面和证据面的分离。控制面回答是否可以执行下一步；证据面保存为什么。这样后续迁移到其他命理流派子智能体时，也可以让八字、紫微、奇门、名人验证、流月报告等模块都暴露统一的就绪摘要，而不是让调用者解析各自内部结构。

## v106: 明星验证要先跑通三域离线闭环

用户问“能不能找到体育、影视歌明星来验证”，这不是只列出名字就够。对命理规则进化来说，名人案例的价值在于能形成可复验的事实标签：候选人、来源查询、缓存响应、草案 manifest、正负样本、覆盖门槛都要连起来。

这次新增的做法是：在不能 live 抓取、来源尚未生产审核时，先用仓库内的离线 fixture 跑通三域闭环。体育、影视、音乐各自使用对应的 Wikidata 形状响应样例，候选池 9 人全部导入，生成 9 条正样本和 273 条负样本，跨域覆盖门槛通过。

这里的关键边界是：离线 fixture 只能证明管线能跑通，不能证明事实标签已经真实可靠。真实验证仍需要来源审核、身份核验、负样本窗口核验和生产来源许可。但这个闭环让后续规则进化不再停留在“能不能找明星”，而是进入“事实标签如何进入评分器、如何度量误报”的阶段。

推理变化：命理智能体的案例验证必须区分三层证据。第一层是候选覆盖，说明样本面够不够；第二层是离线管线覆盖，说明数据形状和导入逻辑能不能复现；第三层是生产事实覆盖，说明来源和事件标签是否可信。只有第三层通过，才能把结果用于更强的断言。

## v107: 测试跑通的能力要进入能力审计

三域离线明星验证闭环跑通后，如果只停留在测试文件里，后续智能体仍然可能不知道这个能力已经存在。测试证明“代码能跑”，但能力审计证明“系统知道自己具备这个能力，并且能把它交给下游迁移”。

这次新增的规则是：凡是影响方法演化的证据闭环，都要有能力审计回执。回执至少保存候选数量、草案数量、正负样本数量、覆盖门槛、标签表回执和边界说明。这样下一代智能体不用重新读测试，也能知道当前明星验证能力处于什么层级。

对命理系统来说，这个区别很重要。一个规则能在本地测试中通过，不代表它已经可以用于用户报告；但如果它进入能力审计，就可以作为“可复现的中间能力”被其他智能体发现、复查和继续推进。审计回执因此成为自动进化的目录，而不仅是质量报告。

推理变化：自动进化需要两套证据。测试证据证明实现没有坏；能力审计证据证明系统能自我描述。只有两者同时存在，能力才算真正可移植。

## v108: 能力审计产物也要进入公开契约

能力审计能说明系统知道自己有什么能力，但如果公开 schema 没有描述这个字段，外部调用者仍然不知道它是否稳定。尤其是三域明星验证这种中间能力，后续可能被前端、CLI、迁移脚本或其他智能体读取；如果没有 schema，字段名和结构就容易漂移。

这次新增的规则是：进入能力审计的关键产物，还要进入公开 schema。响应本体和审计回执材料都要引用同一个 schema，这样“实时返回值”和“可追溯回执”不会各讲各话。schema 至少要约束版本、哈希、候选数量、正负样本数量、覆盖门槛、标签表回执和非生产边界。

推理变化：自动进化不是只让内部更聪明，还要让能力成为可调用接口。测试证明可运行，能力审计证明可发现，schema 契约证明可集成。三者同时存在，后续智能体才能放心复用，而不是重新猜测对象结构。

## v109: 公开契约要用真实运行对象验证

给三域明星验证能力补了 schema 之后，静态检查能证明 `$ref` 写对了，但不能证明真实返回值符合 schema。本轮运行时校验发现一个具体问题：顶层响应是完整回执，审计回执 material 里却是摘要；schema 要求二者都是同一种回执对象。

新的规则是：每次新增公开契约，都要至少拿一个真实运行对象做 schema 校验。对关键审计产物，还要同时校验两个位置：顶层响应对象，以及审计回执 material 中保存的同一对象。二者的 sha256 必须一致。

推理变化：schema 契约不是文档装饰。它要约束真实数据流。命理智能体以后会有很多中间产物：命盘、流年、流月、子智能体投票、名人验证、来源审核。只要某个产物要被后续智能体复用，就必须通过“静态契约 + 运行时对象”双重校验。

## v110: 内部能过不等于接口能过

内部 Python 对象通过 schema 校验，只能说明模块之间的直接调用是稳定的。外部系统、前端和其他智能体通常不会直接 import 函数，而是走 HTTP `/audit` 和 `/schema`。所以关键能力还要经过公开接口验证。

这次新增的规则是：对要迁移的能力产物，至少验证三种形态：内部顶层对象、内部审计回执 material、HTTP 顶层对象。HTTP 校验要使用同一个 `/schema` 返回，而不是测试里另起一套局部 schema。

推理变化：命理智能体的能力如果要真正可移植，不能只在内部稳定。它必须在公开接口上也稳定。以后八字流派辩论、流年评分、名人校验、来源审核这些能力，只要进入 API，就要走“内部对象 + HTTP 对象 + schema”三点闭环。

## v111: CLI 也是迁移接口

HTTP 接口适合服务调用，但很多自动化脚本、发布流程和后续智能体会直接调用 CLI。一个能力如果只在 Python 内部和 HTTP 上稳定，仍然可能在命令行输出里漂移，导致迁移脚本读错字段。

这次新增的规则是：进入能力审计和公开 schema 的关键产物，也要通过 CLI `audit` 和 CLI `schema` 做同样校验。顶层对象和审计回执 material 中的对象都要通过 CLI schema，且回执 sha256 必须一致。

推理变化：可移植能力至少有四个面：内部对象、能力审计、HTTP 接口、CLI 接口。命理智能体以后输出命盘、流年、流月、子智能体辩论、名人验证等能力时，只要需要被复用，就不能只保证其中一个入口正确。

## v112: 能力要进入实施矩阵

能力标志说明系统现在能做某件事，但实施矩阵说明这件事是一个被承认的工程交付物。三域明星验证闭环已经具备内部对象、审计回执、schema、HTTP 和 CLI 校验后，还需要进入 implemented requirements，才方便后续智能体按工程能力继续追踪。

这次新增的规则是：成熟的验证闭环要同时进入能力标志和实施矩阵。实施矩阵中的 evidence 必须能被机器物化，不能只写自然语言描述。比如这次绑定了回执构造函数、公开 schema 字段、fixture 文件和 Python/HTTP/CLI 测试。

推理变化：自动进化不仅要增加能力，还要让能力处在可治理的位置。能力标志回答“现在能不能用”，实施矩阵回答“这是不是正式交付过”，证据物化回答“交付证据是否仍然存在”。三者结合，后续迁移和复现才不容易丢失上下文。

## v113: 名人验证要分清事件标签和出生盘就绪

用户提出可以找体育、影视、歌手明星来验证命理规则。系统此前已经能把三域明星事件导入为年度标签：体育、影视、音乐各有正负样本，候选覆盖和管线形状都成立。但这还不能直接进入八字规则校准，因为八字评分还需要可信的出生日期、出生时间和出生地。事件标签回答“哪一年发生了什么”，出生盘资料回答“能不能把那一年和命盘流年对应起来”。这两件事必须分开。

这次新增的规则是：名人案例验证必须先过事件标签门槛，再过出生盘就绪门槛。三域 fixture 当前有 282 条年度事件标签，其中 25 条可以进入符号评分，257 条被阻塞。可评分案例只有 Roger Federer；Beyonce、Jackie Chan、Jay Chou、Meryl Streep、Michael Jordan、Serena Williams、Taylor Swift、Tom Hanks 都因为本地 reviewed birth profile 缺失而不能用于八字年度评分。影视和音乐不是没有事件标签，而是缺少可审计出生盘。

方法论上的变化是：验证闭环从“找到明星事实”进化为“事实标签和命盘资料双重对齐”。如果只看事件标签，系统会误以为三域都可以用于校准；如果只看出生盘库，系统又不知道有没有对应事件。新的 readiness summary 把两者相交：只有同时拥有事件标签和出生盘的样本，才能进入符号评分；其余样本必须进入补资料队列。

这个设计吸收了前面建立的 gate、receipt、schema、runtime validation 思路，也和 Karpathy 风格的 LLM Wiki 一致：知识不是写成一次性结论，而是沉淀为可迁移的操作规则。未来迁移到紫微、奇门或流派辩论子智能体时，也应先问两个问题：外部事实标签是否可审计，命理计算输入是否完整。只有两者都通过，才能讨论规则命中率、误报率或流派投票。

推理变化：名人验证不再用“样本很多”作为能力证明，而用“可评分交集”作为能力证明。事件覆盖是外部事实能力，出生盘覆盖是命理输入能力，年度评分才是规则检验能力。三层分离后，系统可以更诚实地回答用户：能找到体育、影视、歌手明星；能导入三域事件；但当前真正可用于八字评分的只有已有出生盘的子集。

## v114: 缺口必须变成可执行任务

上一版已经把明星验证拆成事件标签和出生盘就绪两道门槛，但只说“哪些案例缺出生盘”还不够。自动进化系统不能把缺口留给后续智能体重新猜。一个 readiness gate 失败后，必须输出下一步任务：补什么、补哪些案例、验收标准是什么、补完后用哪张回执验证。

这次新增的规则是：把缺出生盘的明星样本转换为 `add_reviewed_birth_profiles` 任务计划。当前三域明星样本产生 3 个高优先级任务：影视 public_fame 需要 Jackie Chan、Meryl Streep、Tom Hanks；音乐 public_fame 需要 Beyonce、Jay Chou、Taylor Swift；体育 sports_peak 需要 Michael Jordan、Serena Williams。三个任务合计覆盖 257 条阻塞标签。

方法论上的变化是：阻塞项不再只是失败信息，而是工作包。每个工作包都要有 task_id、领域、事件主题、阻塞标签数、阻塞案例、要补的证据、验收标准和边界说明。这样下一代智能体可以直接执行补资料、重新跑 readiness receipt、再进入评分，而不是回到“为什么不能评分”的诊断阶段。

这个模式来自 ReAct 和 SWE-agent 类工程代理的执行循环，也继承了本项目前面建立的 receipt-gate 思路：观察到失败，形成动作；动作必须有可验证结果；结果再进入下一轮推理。对命理智能体来说，尤其要避免“讲得很像完成了”的幻觉。只要出生盘没有补齐，任务计划就必须保持显式存在。

推理变化：自动进化的基本单位从“发现一个能力缺口”升级为“发现缺口并生成可验收的补证据任务”。这会让未来的八字流派子智能体、紫微子智能体、奇门子智能体都能按同样方式处理资料缺口：先阻塞，再排队，再验收，再评分。

## v115: 任务计划还要连接审核门槛

把缺出生盘样本变成任务计划后，还存在一个问题：任务计划告诉后续智能体“补什么”，但没有告诉它“能不能执行、有什么替代建议、哪些审核门槛还没过”。如果只给 task_id 和 case_id，后续智能体仍可能直接把本地建议当成已审核资料，或者跳过人工审核。

这次新增的规则是：证据补全任务必须连接 workplan summary。workplan summary 不展开全部草案，但要保留关键执行面：deferred task 数量、本地出生盘建议、completion work order 状态、gate summary 状态、blocked gate 数量、workplan receipt。当前跨域明星验证中，影视、音乐、体育三条补资料任务都有本地建议，但 gate 全部保持 blocked，这说明系统知道下一步怎么做，也知道现在不能越权评分。

方法论上的变化是：自动进化的“下一步”不只是自然语言建议，而是有状态的工作包。它同时包含候选路径和禁止越界的门槛。比如影视缺 Jackie Chan、Meryl Streep、Tom Hanks 的出生盘，系统可以建议先复用 Bruce Lee、Lucille Ball、Marilyn Monroe 这些已有本地影视盘做替代验证，但不能把建议等同于补齐原案例。音乐和体育同理。

这个规则延续了 SLSA/in-toto 式的供应链思路：每个可迁移能力不仅要有产物，还要有来源、回执、门槛和状态。命理智能体的资料链条也要这样处理。出生盘、事件标签、流派结论、年度评分都不能只靠“看起来合理”；它们必须处在可追溯、可阻塞、可复验的工作流里。

推理变化：任务计划是行动，workplan 是治理。行动告诉系统下一步补什么；治理告诉系统补之前不能声称什么。以后流派子智能体辩论、名人验证、用户案例校准都应采用同样结构：候选建议可以出现，但必须带审核门槛；门槛未过时只能作为待办，不能作为结论。

## v116: 出生盘导入前要先有审核清单

明星出生盘是高风险数据。它看起来只是生日、时间、地点，但一旦进入八字评分，就会影响规则校准、流派投票和后续用户报告。如果直接把网上查到的出生时间写入本地 fixture，系统会失去区分“已审核资料”和“待核资料”的能力。

这次新增的规则是：补明星出生盘之前，先建立 reviewed-birth-profile manifest。manifest 不保存未核验出生时间，而是保存审核任务：case_id、身份锚点、需要补齐的字段、建议查询语句、阻塞的命理事件主题、阻塞标签数量、来源政策、审核状态。当前清单覆盖 8 个缺口：影视 3 个、音乐 3 个、体育 2 个，合计 257 条阻塞标签。它的状态是 ready_for_review，但 ready_for_import 是 false。

方法论上的变化是：出生盘不再是“找到就填”的资料，而是一个供应链对象。它必须先进入清单，再通过外部来源审核，再生成回执，最后才允许导入 famous-case fixture。这样可以避免两类错误：一是把不可靠出生时间用于评分；二是让后续智能体误以为阻塞已经解除。

这个规则吸收了前面 SLSA/in-toto 和 preregistration 的思想。对命理系统而言，出生盘相当于模型输入源；输入源不受控，后续再复杂的八字、紫微、奇门推理都会变成不可追溯的幻觉链。审核清单把“想补资料”和“已经有资料”分开，保证系统可以继续进化但不越过证据边界。

推理变化：资料补全的第一步不是写数据，而是定义可审核的资料入口。以后任何会影响命盘计算的外部输入，都应走同样流程：审核清单、来源政策、回执、导入门槛、评分解锁。未过门槛时，它只能是任务，不能是命理证据。

## v117: 审核清单要有独立调用面

出生盘审核清单进入能力审计后，系统已经能在全量 audit 中看到它。但这还不够。后续智能体或人工操作者如果只是想检查出生盘补资料清单，不应该被迫运行完整能力审计，也不应该从大对象里手动翻字段。关键资料链路需要独立 API/CLI surface。

这次新增的规则是：凡是会影响命盘计算输入的审核清单，都要有直接接口。出生盘审核清单现在可以通过 CLI `birth-profile-review`、HTTP `/birth-profile-review` 和公开 schema `BirthProfileReviewStatusResponse` 单独审计。接口返回审核结果、回执、生产 gate、配置提示和明确边界：它是 collection worklist，不是出生盘导入。

方法论上的变化是：能力审计负责全局自我描述，直接接口负责可操作性。两者不能互相替代。全局审计可以告诉系统“这条链路存在”；直接接口让后续执行者能单独验证“这份清单现在能不能导入”。这降低了后续迁移成本，也避免为了一个小资料清单跑完整系统检查。

这个规则来自工程接口治理：重要中间产物必须是可调用、可校验、可脚本化的。对命理智能体而言，出生盘清单、事件标签清单、流派规则清单、用户反馈清单都属于关键中间产物。只要它会影响推理输入或规则演化，就应该有 API/CLI/schema 三面闭环。

推理变化：资料审核从“审计内部字段”升级为“独立工具面”。以后补资料、复核资料、迁移资料时，可以先调用专门接口验证边界和 gate，再决定是否进入导入流程。这让命理能力演化更像可维护系统，而不是一次性脚本。

## v118: 导入前必须先做非破坏性预览

审核清单解决了“资料从哪里来”的问题，独立接口解决了“怎么单独检查”的问题，但还缺一层：审核通过后到底会不会写入 fixture、写到哪里、现在为什么不能写。没有导入预览，后续智能体可能在资料尚未完整时直接修改名人样本库。

这次新增的规则是：任何会进入命盘计算输入的数据，在真正导入前必须先生成 non-mutating import preview。预览必须明确目标 fixture、是否会写文件、是否允许导入、候选 case、阻塞原因、导入 gate、回执和完整性检查。当前出生盘清单的预览状态是 blocked_not_ready_for_import，would_write_file 为 false，import_allowed 为 false。

方法论上的变化是：导入不再是动作，而是先成为可审计对象。即使未来清单通过外部审核，也应先通过预览生成明确的 patch 或 import plan，再由人工或发布流程批准写入。预览阶段的失败不是错误，而是安全状态：它告诉系统“现在还不能把待审核资料变成命理证据”。

这个规则来自前面 query-template patch preview 的经验，也符合 agentic workflow 的基本要求：先观察，后计划，再预览，最后才执行。对命理系统尤其重要，因为出生盘一旦写入，会影响后续评分、流派辩论和用户报告。没有预览 gate，就很难追溯某个命理结论到底用了什么输入。

推理变化：资料链路从“审核清单”升级为“审核清单 + 导入预览 + 阻塞 gate”。以后任何外部资料，包括经典文献、名人事件、出生盘、用户反馈，只要要进入推理输入，都应先经过非破坏性预览。预览通过之前，不允许写入核心 fixture。

## v119: 独立工具要回流到能力审计

出生盘审核清单和导入预览已经有独立 API/CLI，这提高了可操作性。但如果它们只存在于独立工具面，未来智能体从全量能力审计看系统时，仍然看不到完整链条。自动进化需要两种入口同时存在：独立工具用于执行，能力审计用于发现和迁移。

这次新增的规则是：凡是关键资料链路新增了独立工具，都要把摘要和回执哈希回流到 capability audit。跨域明星验证现在在同一个 readiness summary 中暴露：事件标签覆盖、出生盘任务计划、workplan、review manifest、import preview。后续智能体不用重新猜“出生盘链路走到哪一步”，只读能力审计就能知道导入预览仍然 blocked、不会写文件、不能解锁评分。

方法论上的变化是：能力审计从“列出已有能力”升级为“串起证据链状态”。它不替代独立 API/CLI，但要保存每个关键中间产物的状态和回执。这样迁移到新项目时，可以先看能力审计了解整体成熟度，再调用具体工具执行局部任务。

这个规则来自 agent memory 和 reproducibility 的结合：记忆不能只记最终结论，也要记工具面的当前状态。命理智能体尤其需要这样做，因为很多能力会长期处于“可计划、不可生产”的中间状态。把这些中间状态显式写入能力审计，可以防止下一代智能体把 blocked 工具误当成 completed 能力。

推理变化：独立工具面负责局部动作，能力审计负责全局可发现性。以后新增经典文献刷新、流派规则导入、名人事件导入、出生盘导入等工具，都必须回流一个精简摘要到能力审计：状态、gate、回执、边界。否则能力不可迁移。

## v120: 阻塞型安全预览也要进入生产门禁

上一版把出生盘导入预览回流到了能力审计，但这还只是“看得见”。如果生产就绪检查不验证它，未来发布时仍可能出现一种危险情况：能力审计里显示 blocked，实际发布门禁却没有拦住导入路径。对自动进化系统来说，安全状态也必须被测试，而不能只写在说明里。

这次新增的规则是：凡是用于保护证据边界的阻塞型预览，都必须进入 production readiness gate。出生盘导入预览现在有独立生产门禁 `birth_profile_import_preview_blocked`。它只有在以下条件同时成立时才通过：预览有效、不写文件、不允许导入、导入 gate 被阻塞、完整性检查通过、有阻塞请求、没有可导入请求。也就是说，当前“不能导入”本身就是一个被证明过的生产状态。

方法论上的变化是：门禁不只验证“功能能做什么”，也验证“功能不能越过什么边界”。这对命理智能体尤其重要。明星出生盘还没有审核完成时，系统的正确行为不是尝试评分，而是保持阻塞、保持非破坏性、保持可追溯。生产门禁把这个正确行为固定下来，避免后续迭代为了追求覆盖率而误开资料入口。

这个规则吸收了 SLSA/in-toto 的供应链防护思想，也延续了 SWE-agent 和 ReAct 的可验证动作循环：观察到资料缺口，生成任务和预览，但只要证据未完成，执行层必须被 gate 拦住。对 Karpathy 风格的 LLM Wiki 来说，这是一条重要的工程化经验：智能体的“进化”不只是学会更多判断，也包括学会更稳定地拒绝不合格输入进入推理核心。

推理变化：安全边界从文档约定升级为生产断言。以后任何非破坏性预览，只要它负责阻止未审核资料进入命盘计算、流派规则、名人事件库或用户校准库，都必须有对应生产门禁。门禁通过表示边界被守住，不表示资料已经可用。

## v121: 审核通过态也要先做契约预演

前一版证明了“未审核出生盘不能导入”，但系统还缺另一半：如果未来真的补齐了审核资料，下一步应该长什么样。只有阻塞态，没有审核通过态，会让后续智能体在资料补齐后重新发明导入流程，甚至可能直接写 fixture。

这次新增的规则是：阻塞型导入预览之后，要补一个 reviewed-manifest contract path。它不是导入真实明星资料，而是用合成契约样本证明状态机：当清单标记为 `reviewed_ready_for_import`、总审核为通过、每条请求都有完整出生日期、出生时间、性别、出生地、来源名称、来源地址、来源评级和来源说明时，系统可以生成 `candidate_profiles`。但即便此时，预览仍然保持 `would_write_file = false`，只说明“可以进入下一步 patch 审核”，不直接写入名人样本库。

方法论上的变化是：安全流程不能只测试失败路径，也要测试成功前一刻。未审核态要被拦住；审核通过态要能产生清晰、结构化、可回执的导入计划；真正写入仍应是下一步显式补丁。这样可以避免两种偏差：一是永远停在 blocked，无法推进；二是一旦审核通过就越过预览直接修改核心资料。

这个规则来自 agent workflow 和供应链发布的共同经验：发布前不仅要有 deny gate，还要有 promote plan。对命理智能体来说，出生盘、名人事件、流派规则、用户校准事实都应遵守同样节奏：未审核时阻塞，审核后生成非破坏性计划，计划再进入人工或发布补丁，最后才成为可评分证据。

推理变化：资料链路从单态门禁升级为双态状态机。第一态证明“不合格资料不能进入命盘计算”；第二态证明“合格资料也只能先形成可审计导入计划”。这让未来补齐真实明星出生盘时可以直接复用流程，而不是靠临场判断。

## v122: 核心样本库写入前还要有补丁预览

审核通过态可以生成 `candidate_profiles`，但这还不能直接进入 `FAMOUS_CASES`。核心样本库一旦改变，后续八字评分、流派辩论、名人验证和用户报告都会受到影响。如果没有补丁预览，资料链路仍然会在最后一步变成“有人直接改了文件”。

这次新增的规则是：外部资料进入核心 fixture 前，必须生成 non-mutating fixture patch preview。这个预览要保存目标文件路径、目标文件哈希、候选 case、补丁文本、补丁文本哈希、补丁门槛、回执和完整性检查。默认未审核清单仍然输出 `blocked_not_ready_for_patch_preview`；只有已审核清单通过前置导入预览时，才会生成 `ready_for_patch_review`，但仍保持 `would_write_file = false`。

方法论上的变化是：资料进入命理系统的链路被拆成三段。第一段是 review manifest，回答“资料是否被审核”；第二段是 import preview，回答“审核资料能否变成候选结构”；第三段是 fixture patch preview，回答“如果要改核心样本库，具体补丁是什么、目标文件是否漂移”。每一段都有哈希和 gate，任何一段失败都不能跳到下一段。

这个规则延续了 SLSA/in-toto 的供应链思想，也吸收了软件发布中的 patch review 模式。对命理智能体来说，核心问题不是能不能找到资料，而是资料能否以可追溯、可复核、可回滚的方式进入推理输入。出生盘、名人事件、经典文献、用户校准事实都应使用同样的三段式入口。

推理变化：资料导入不再是单个动作，而是可审计发布流程。未来补齐真实明星出生盘时，系统应该先看目标文件哈希是否匹配，再看补丁文本和候选资料是否符合预期，最后才允许人工或发布流程应用补丁。这样命理规则的演化不会被不可追溯的数据写入污染。

## v123: 证据链每加一段都要回流到能力审计

补丁预览已经有 API、CLI、HTTP 和 schema，但如果它只存在于独立接口里，后续智能体从能力审计看系统时仍然会漏掉最后一段资料链路。这样迁移到新项目时，很容易只复刻“审核清单”和“导入预览”，却忘记“核心样本库写入前的补丁预览”。

这次新增的规则是：证据链每增加一个阶段，都要把摘要和回执哈希回流到 capability audit。出生盘链路现在在 cross-domain symbolic scoring readiness 中同时暴露三段：review manifest、import preview、fixture patch preview。patch preview 摘要包含状态、是否写文件、是否可进入补丁审查、候选数量、候选 case、目标文件哈希、补丁文本哈希、门槛状态、阻塞原因和完整性检查。

方法论上的变化是：独立工具负责局部执行，能力审计负责全局发现。两者缺一不可。API/CLI/HTTP 让人可以直接运行某一步；capability audit 让后续智能体知道这一步存在、当前处于什么状态、是否能迁移、有没有回执。没有审计回流，工具会变成隐藏能力。

这个规则来自 agent memory 和 reproducibility 的结合，也继承了 in-toto 式的链路证明思想。对命理智能体而言，很多能力不是一次完成的，而是长期停在“计划、阻塞、预览、待审核”的中间态。能力审计必须保存这些中间态，否则下一代智能体会把系统误判为缺能力，或者误判为已经完成。

推理变化：能力审计从“能力列表”继续升级为“证据链目录”。以后经典文献刷新、名人事件导入、出生盘导入、用户反馈校准、流派规则补丁，只要增加一个可执行阶段，就必须同步一个精简摘要和回执哈希到能力审计。迁移时先看审计目录，再调用独立工具。

## v124: 核心补丁预览的阻塞态也要进生产门禁

补丁预览已经回流到能力审计后，系统能“看见”它，但还不能证明发布时一定会守住默认不可写边界。能力审计是发现面，production readiness 是发布门槛。只进入审计、不进入生产门禁，仍然可能让未来改动把补丁预览提前放行。

这次新增的规则是：凡是会影响核心 fixture 的 patch preview，都要有生产门禁验证默认阻塞态。出生盘链路现在新增 `birth_profile_fixture_patch_preview_blocked`。它要求补丁预览状态为 blocked、有效、不写文件、不可进入补丁审查、候选数为零、patch gate 未通过、目标文件哈希存在、补丁文本哈希存在、完整性检查通过。

方法论上的变化是：生产门禁不只验证“已有能力能运行”，还要验证“危险能力默认不能运行”。对命理智能体来说，核心样本库是规则校准的输入源。默认状态下，未审核资料不能写入；即使未来有审核资料，也必须先通过显式补丁审查。生产门禁把这个边界变成发布断言。

这个规则延续了 SLSA/in-toto 的供应链防护，也吸收了软件发布中的 release gate 思想。资料链路中的每一个安全停靠点，都应有两类证明：能力审计证明它存在并可追溯，生产门禁证明它不会在未满足条件时越界。

推理变化：资料链路的安全性从“工具有边界”升级为“发布必须证明边界仍然存在”。以后名人事件、经典文献、流派规则、用户事实校准只要会改核心 fixture 或规则表，都要建立类似门禁：默认不写、哈希可查、门槛未过、完整性通过。

## v125: 阻塞资料要变成来源审核工作项

前面已经把出生盘资料链路拆成审核清单、导入预览、补丁预览和生产门禁。但真实推进时还有一个空档：系统知道 8 个明星缺出生盘，却没有把“谁去查什么、填什么、达到什么标准”变成可执行工作项。只记录缺口，后续智能体仍要重新解释任务。

这次新增的规则是：阻塞的来源审核需求必须转换成 human source-review workplan。每个明星生成一个工作项，包含身份锚点、建议查询语句、缺失字段、允许来源类型、禁止来源、必需证据、待填的 reviewed-profile 草案、验收标准和边界。工作包本身不联网、不写清单、不解锁评分，只负责把人工审核任务结构化。

方法论上的变化是：资料缺口从“失败原因”升级为“可执行审核单”。这和 ReAct 的观察-行动循环一致，也和 in-toto 的供应链思想一致：每一步都要有输入、动作、产物、门槛和回执。命理智能体不能把“去查资料”留成一句自然语言，因为这会让下一轮执行重新发散。

对命理系统来说，这尤其重要。出生时间、出生地、来源评级这些字段一旦进入命盘计算，就会影响后续八字评分、流派辩论和规则校准。来源审核工作项把每个字段的责任明确下来：身份要匹配，时辰要有来源，地点不能靠国籍推断，来源评级要说明可靠性。

推理变化：自动进化从“我知道缺什么”继续升级为“我知道下一步谁要审什么、怎么验收、审完后跑哪条门槛”。以后经典文献、名人事件、用户反馈事实、流派规则补丁，只要阻塞在来源审核阶段，都应该先生成这种人审工作包，再谈 live collection 或 fixture edit。

## v126: 人审工作包要有独立调用面

来源审核工作包已经进入能力审计，但如果只有能力审计能看到它，实际审核人员和后续智能体仍然要从一个很大的 audit 对象里找字段。这不利于执行，也不利于迁移。能力审计适合全局发现，直接接口适合局部执行。

这次新增的规则是：human source-review workplan 必须有独立 API/CLI/HTTP surface。出生盘来源审核现在可以通过 `birth-profile-source-review-workplan` 和 `/birth-profile-source-review-workplan` 单独调用，返回 8 个明星的审核工作项、来源政策、待填草案、验收标准、回执和完整性检查。这个接口仍然不联网、不写清单、不认证资料。

方法论上的变化是：人审工作包从“审计里的一个摘要”变成“可直接执行的工具入口”。审核者不需要理解完整命理系统，也不需要知道 cross-domain fixture import 的内部结构，只需要拿到工作包，逐项补证据，再回到导入预览和补丁预览链路。

这个规则来自工程化工作流中的 task surface 思想：计划要能被直接领取和验证。对命理智能体来说，很多关键进化卡在人工资料审核、经典文献审核、用户事实校准审核上。只把它们写在审计里，会降低执行效率；给它们独立接口，才能形成稳定的人机协作边界。

推理变化：能力审计负责“发现有这个任务”，工作包接口负责“执行这个任务”。以后任何会交给人审的工作包，都应该同时满足两点：进入能力审计，保证可迁移；提供独立接口，保证可执行。

## v127: 人审工作包也要进生产门禁

来源审核工作包已经有独立工具面，也进入了能力审计。但发布前还需要证明它没有消失、没有开始私自联网、没有写审核清单、没有提前通过 gate。否则资料链路会在最前端断掉：后续 import preview 和 patch preview 再安全，也没有明确的人审入口。

这次新增的规则是：human source-review workplan 要进入 production readiness。出生盘链路新增 `birth_profile_source_review_workplan_available`，验证工作包状态为 ready、有效、不抓取 live source、不写 reviewed manifest、有请求、有工作项、source-review gate 未通过、完整性检查通过。

方法论上的变化是：生产门禁不仅保护危险写入点，也保护关键待办入口。一个系统如果只能证明“不能写”，但不能证明“待审核任务还在”，后续进化会停在无人可执行的阻塞状态。生产门禁要同时保证安全边界和推进入口。

这个规则延续了前面的能力审计和 release gate 思路：能力审计保存证据链目录，独立接口让任务可执行，生产门禁保证发布时目录和接口仍处在正确状态。对于命理智能体，来源审核工作包是资料进入推理核心的第一道门，不能是可有可无的辅助说明。

推理变化：资料链路现在同时固定了四类状态：人审任务存在、导入预览阻塞、补丁预览阻塞、生产门禁注册完整。以后经典文献、名人事件、流派规则、用户事实校准也应采用同样结构：先保证待办入口存在，再保证未审核资料不会越界。

## v128: 人审工作包要自报进度和缺口

来源审核工作包能列出每个明星任务后，仍然缺一个管理视角：系统能回答“有哪些任务”，但不能一眼回答“现在整体卡在哪里”。对于用户提出的体育、影视、歌明星验证，这个问题会马上出现。候选人多了以后，只看逐条任务会淹没关键事实：哪些领域最多、哪些字段全部缺、当前有没有任何资料已经审核完成。

这次新增的规则是：human source-review workplan 必须有顶层进度摘要和字段缺口摘要。出生盘来源审核现在直接暴露影视、音乐、体育三个领域的任务数、阻塞标签数、审核状态分布、可导入数量，以及出生日期、出生时间、出生地、性别、来源名称、来源评级、来源链接等字段缺口。摘要从 work items 派生，不另起一套口径。

方法论上的变化是：工作包不能只服务执行者，也要服务调度者。执行者需要逐条任务；调度者需要知道先补哪个领域、哪个字段、有没有进入下一阶段的可能。这个设计吸收了 SWE-agent 的任务可追踪思想，也延续 in-toto/SLSA 的链路可证明思想：每个中间产物不仅要有回执，还要有能指导下一步行动的状态摘要。

对命理系统来说，这条规则很关键。名人命盘验证的难点不是“能不能想到一些明星”，而是出生资料质量参差不齐。没有进度和缺口摘要，系统容易把未审核资料误认为可评分样本，或者在大量候选中反复做无效搜索。有了摘要，后续可以明确先补出生时间、出生地和来源评级，再谈八字流派辩论和历史事件校验。

推理变化：来源审核从“任务列表”升级为“任务列表加调度仪表盘”。以后经典文献、名人事件、用户事实校准、流派规则补丁，只要生成工作包，就必须同步生成顶层进度和缺口统计。这样迁移到新项目时，不只知道要做什么，也知道当前最短板在哪里。

## v129: 来源审核之后要生成干运行检索计划

人审工作包已经能列出任务和缺口，但它还没有把“去查资料”拆成可执行单元。对于体育、影视、音乐名人验证，这会让后续执行停在一句泛泛的搜索建议上。真正可迁移的智能体不能只说“去查 Astro-Databank 或官方传记”，而要说明每条查询服务哪个字段、结果应缓存在哪里、哪些动作仍然禁止。

这次新增的规则是：source-review workplan 后面要接 dry-run source lookup plan。出生盘来源审核现在会把 8 个名人扩展成 16 条查询计划，按影视、音乐、体育分组，每条计划带 query id、优先级、目标字段、计划缓存路径、身份锚点、不联网不写入标记、验收条件和回执。这个计划仍然不抓网页、不写缓存、不认证资料，只把人工或未来受控抓取的动作边界清楚地摆出来。

方法论上的变化是：智能体的行动不应从“自然语言建议”直接跳到“外部执行”。中间必须有一层可审计的干运行计划。这个思想吸收了 ReAct 的观察-行动拆分，也延续 SWE-agent 的任务可复现思想和 in-toto/SLSA 的链路证明思想：每个外部动作在执行前就应有输入、目标、产物位置、边界和回执。

对命理系统来说，这能避免两个常见错误。第一，名人出生资料还没有审核时，系统不能为了完成验证而直接把搜索结果当命盘输入。第二，候选很多时，系统不能重复发散搜索，而要稳定复用同一套查询计划和字段缺口。干运行检索计划让“找体育、影视、歌星来验证”从一句目标变成可逐项执行、可审计、可中断续跑的流程。

推理变化：资料链路现在多了一层“准备外部动作但不执行”的状态。未来经典文献抓取、名人事件采集、用户事实校准、流派规则出处核验，都应先生成 dry-run lookup/fetch plan，再由人工或受控 provider 执行。只有执行结果经过审核，才允许进入 import preview 和 fixture patch preview。

## v130: 干运行检索计划也要进入生产门禁

干运行检索计划解决了“外部动作之前要先有可审计计划”的问题，但它本身也会变成新的风险点。如果未来某次迭代把 dry-run 计划改成真的联网、写缓存或写审核清单，而生产门禁没有覆盖这一步，资料链路就会在审核前端越界。也就是说，危险不只在 fixture 写入，也可能出现在“看似只是检索”的准备阶段。

这次新增的规则是：任何会组织外部资料动作的 dry-run plan，都必须有 production gate 证明它仍然是 dry-run。出生盘来源检索现在新增 `birth_profile_source_lookup_plan_dry_run`，要求状态为可人工检索、有效、不抓取 live source、不写缓存、不写 reviewed manifest、有 lookup items、有 query count、lookup gate 未通过、完整性检查通过。

方法论上的变化是：生产门禁不只管最终写入，也管外部动作的前置计划。这个规则吸收了 SLSA/in-toto 的供应链防护思想：链路中每一段都要能证明自己的边界。对智能体工程来说，越接近外部世界，越不能只靠注释和约定，而要靠可测试的 gate。

对命理系统来说，这一点尤其重要。名人出生资料、经典文献、行业事件、用户校准事实都可能来自外部来源。系统可以计划检索，但不能在未审核状态下把外部文本、网页片段或缓存直接变成命盘输入。生产门禁把“计划可以存在，但执行必须受控”固定成发布条件。

推理变化：资料链路现在覆盖五个安全状态：人审任务存在、检索计划保持干运行、导入预览保持阻塞、补丁预览保持阻塞、生产门禁注册完整。以后任何新增的 collection/fetch/lookup/cache plan，都要同时满足能力审计可见、独立接口可调用、生产门禁可证明 dry-run 边界。

## v131: 人工检索结果要先进入缓存审计

干运行检索计划能说明“应该查什么”，但还不能说明“查完以后怎么接住结果”。如果人工或受控 provider 把来源结果随手写进某个文件，下一轮智能体仍然要猜：这个缓存对应哪条查询，是否匹配同一个名人，来源字段是否完整，是否真的填到了目标出生字段。缺少缓存审计，资料链路会在“检索结果”这一段重新变成口头交接。

这次新增的规则是：lookup plan 后面必须有 source cache audit。出生盘来源链路现在会读取计划缓存路径，检查每个 JSON 是否存在，是否匹配 planned `query_id` 和 `case_id`，是否填写 source_name、source_url、source_rating、reviewer_note、review_status，是否至少填到一个计划目标字段。默认没有缓存时，状态是等待人工缓存；即使有一条缓存被标记为 source_reviewed，也只算“可审计来源证据”，不能直接成为出生资料。

方法论上的变化是：外部资料的执行结果不能直接进入推理核心，必须先变成可审计缓存，再进入 reviewed manifest draft。这个设计延续 ReAct 的观察-行动-观察循环，也延续 SLSA/in-toto 的供应链证据思想：每一步的产物都要能证明自己来自哪一步计划、服务哪个目标、是否被审核。

对命理系统来说，这防止了一个关键污染源。名人出生时间和出生地一旦被错导入，后续八字流派辩论、紫微斗数交叉验证、奇门辅助判断都会建立在错误输入上。缓存审计不尝试判断命理，只判断证据包装是否合格：身份是否对应、来源字段是否完整、目标字段是否被填、审核状态是否明确。

推理变化：资料链路从“计划检索”推进到“审计检索结果”，但仍然不进入命盘计算。以后经典文献、名人事件、用户事实校准、流派规则出处核验，也应采用同样结构：dry-run plan 生成计划，cache audit 接住结果，reviewed manifest draft 汇总证据，import preview 再决定能否进入核心样本或规则库。

## v132: 缓存审计也要进入生产门禁

缓存审计比干运行检索计划更接近外部资料。检索计划只是说明要查什么；缓存审计会读取人工或 provider 准备好的 JSON 文件。如果这一层未来被改成写缓存、写审核清单或直接导入资料，那么未审核来源就可能绕过 reviewed manifest。只把缓存审计放在 API 和能力审计里还不够，发布前必须证明它仍然只读。

这次新增的规则是：source cache audit 必须有 production gate。出生盘来源链路新增 `birth_profile_source_cache_audit_read_only`，要求缓存审计状态可接受、有效、不抓 live source、不写缓存、不写 reviewed manifest、不导入 profiles、有 expected cache count、cache audit gate 未通过、完整性检查通过。

方法论上的变化是：生产门禁要覆盖所有“接触外部资料”的阶段，而不只是最终导入阶段。这个规则继续吸收 SLSA/in-toto 的供应链思想：越接近外部输入，越要证明动作边界。对智能体系统来说，读缓存也不是无风险动作，因为缓存内容可能被下一步误认为已审核事实。

对命理系统来说，这条规则防止名人出生资料链路被缓存污染。即使某个缓存文件已经包含出生时间或出生地，系统也只能把它当作待审核来源证据，不能直接进入八字、紫微、奇门推理。只有 reviewed manifest draft 和后续 import preview 才能决定资料是否可进入样本库。

推理变化：资料链路的安全门禁继续前移。现在出生资料链路的生产断言包括：人审任务存在、检索计划干运行、缓存审计只读、导入预览阻塞、补丁预览阻塞、gate registry 完整。以后任何读取外部缓存、抓取结果、用户上传事实、论文摘录或规则出处的阶段，都要有对应 read-only gate。

## v133: 已接受缓存证据要先生成审核清单草案

缓存审计能判断某条来源缓存是否形状合格、是否对应计划查询、是否填到了目标字段。但即使缓存证据被接受，也不能直接进入 import preview。原因很简单：命盘输入不是零散证据，而是一份完整、统一、经过批准的 reviewed manifest。缺少草案预览时，后续智能体可能手工拼 manifest，跳过缺失字段、混淆 case，或者把部分证据误当完整出生资料。

这次新增的规则是：source cache audit 后面要接 reviewed manifest draft preview。出生盘来源链路现在会按 case 聚合已接受缓存证据，生成一份非破坏性的 reviewed manifest 草案 JSON 和文本预览，统计完整行和不完整行，并绑定 hash 与回执。草案 gate 始终要求人工批准；默认缓存不全时状态保持阻塞，即使某个 case 的缓存已完整，也不会让整个清单直接进入导入。

方法论上的变化是：资料链路从“证据审计”进入“清单草案”，但仍然不是“资料可用”。这个步骤把零散来源证据转成统一 manifest 结构，让人工可以审核整份清单，而不是审核散落的缓存文件。它延续 in-toto/SLSA 的供应链思想：证据可以被接受，但 promotion 到下一层必须通过一个显式、可审计、可 hash 的中间产物。

对命理系统来说，这一步把资料治理和命理推理继续分开。八字、紫微、奇门流派智能体只应该看最终被批准的出生资料，不应该直接看缓存证据或草案。草案预览的职责是发现缺口、合并来源、让人批准，而不是计算命盘。

推理变化：外部出生资料进入样本库前，现在有完整的预发布链路：人审任务、干运行检索计划、只读缓存审计、审核清单草案预览、导入预览、补丁预览。以后经典文献、名人事件、用户事实校准和流派规则出处也应采用同样结构：先把证据聚合成 reviewed manifest draft，再进入 import preview。

## v134: 审核清单草案也要进入生产门禁

reviewed manifest draft preview 是导入前的最后一道人工审核材料。它比缓存审计更接近“可导入资料”，因此风险更高。如果未来某次改动让草案预览直接写 reviewed manifest 或导入 profiles，那么前面的人审、缓存审计和导入预览都会被绕过。仅有 API 和能力审计还不够，生产发布前必须证明草案预览仍然非破坏性。

这次新增的规则是：reviewed manifest draft preview 必须有 production gate。出生盘来源链路新增 `birth_profile_reviewed_manifest_draft_preview_non_mutating`，要求草案预览状态可接受、有效、不写 reviewed manifest、不导入 profiles、有 review request、draft gate 未通过、完整性检查通过。

方法论上的变化是：越接近 promotion 的中间产物，越要用门禁固定它的边界。草案预览可以把证据整理成接近最终形态的 manifest，但它不是批准本身。这个规则延续了软件发布里的 release candidate 思想：候选物可以生成、可以审查、可以 hash，但不能自我发布。

对命理系统来说，这保证了出生资料不会因为“已经整理成清单草案”就被八字、紫微、奇门智能体使用。推理层只能看批准后的正式资料；草案层只服务人工审核和缺口发现。

推理变化：资料链路的生产断言现在覆盖了从任务到导入前的所有关键中间态。以后任何能生成“接近可导入清单”的步骤，都必须有 non-mutating gate，证明它不会自己写入、不会自己发布、不会自己解锁评分。

## v135: 审核清单落盘前要有文件级预览

reviewed manifest draft preview 能让人看到一份审核清单草案，但它还没有回答最后一个工程问题：如果人工批准，系统到底准备写到哪个 JSON 文件？目标文件现在是否存在？旧文件哈希是什么？新文本哈希是什么？这些信息不明确时，人工批准仍然可能变成口头批准，未来复现时也难以判断当时批准的是哪一份文本。

这次新增的规则是：草案预览之后、真正写 reviewed manifest 之前，必须生成 file-write preview。出生盘来源链路现在会给出目标文件路径、目标文件是否存在、目标文件哈希、草案文本哈希、草案回执哈希、阻塞原因和人工批准边界。默认状态仍然不写文件、不导入 profiles、不解锁评分。体育、影视、音乐名人验证因此可以先把查源任务推进到文件级审查，而不会把未审核出生资料混入样本库。

方法论上的变化是：智能体的“将要写入”也要成为一个可审计对象。这个思想继续吸收 SLSA/in-toto 的供应链证明，也贴近软件发布里的 diff/patch review：在真正修改文件前，人应该看到目标、内容、哈希和边界。对 LLM 智能体来说，这能把“我准备写”从一句承诺变成一个可测试、可复现、可比较的产物。

对命理系统来说，这一步尤其关键。名人出生时间、出生地、性别一旦进入正式样本，就会影响八字流派辩论、紫微斗数交叉验证、奇门辅助判断和年度事件校准。file-write preview 保证资料晋升到正式 reviewed manifest 前，还有最后一层文件级确认。只有缓存证据完整、草案完整、人工批准明确之后，才允许进入后续 import preview。

推理变化：资料链路现在从“证据计划”推进到“文件级晋升预览”，但仍不进入命盘推理。以后经典文献语料、名人事件标签、用户事实校准和流派规则出处也应采用同样规则：任何正式 JSON、JSONL、Markdown 规则库、fixture 或报告写入前，都先生成 file-write preview，绑定目标路径、旧哈希、新哈希、预览文本和人工批准条件。

## v136: 名人来源要按证据用途分层

“可以找体育、影视、歌手明星来验证”不能只理解成扩大样本数量。名人验证最容易出错的地方，是把“能确认这个人是谁”的资料误当成“能确认出生时辰”的资料。Wikidata、IMDb、MusicBrainz、Olympedia 这类来源对身份、职业、作品、赛事、出生日期或出生地有帮助，但通常不能单独证明出生时辰。出生时辰必须来自有评级或明确出处的出生资料来源，例如 Astro-Databank 或同等级的出生资料库。

这次新增的规则是：source lookup plan 必须携带 source-family catalog。当前目录把来源分成五类：出生时辰评级来源、Wikidata 身份锚点、影视身份和作品锚点、音乐身份和作品锚点、体育身份和成绩锚点。每条查询都会标注推荐来源家族、能服务哪些字段、是否要求 rated birth-time source、以及禁止把 identity-only/domain-only metadata 晋升为 birth_time 的规则。

方法论上的变化是：外部来源不再只有“可信/不可信”二分，而是按“证据用途”分层。这个思想吸收了数据集治理里的 provenance 思路和 SLSA/in-toto 的供应链思想：同一个来源可能适合做身份锚点，却不适合做关键字段证据。对命理验证来说，出生时辰是高敏感字段，它的证据门槛必须高于姓名、职业、出生日期和事件标签。

对命理系统来说，这直接改进了名人样本验证质量。体育、影视、音乐名人可以作为跨领域验证样本，但每个样本进入八字、紫微、奇门推理前，必须先证明四个输入字段的证据用途正确：出生日期、出生时辰、性别、出生地。尤其是出生时辰，不能由领域数据库、百科条目或搜索摘要推断。

推理变化：资料链路现在不仅知道“要查什么”，还知道“查到的东西最多能证明什么”。以后经典文献、近现代名人案例、用户事实校准、行业事件标签也应采用同样规则：每个来源必须声明 source_family_id、usable_for_fields、minimum_use、trust_tier 和 disallowed_use。智能体只能在来源用途覆盖目标字段时，才允许进入下一层审核。

## v137: 来源用途分层必须进入生产门禁

source-family catalog 解决了“来源能证明什么”的问题，但如果它只存在于 lookup plan 里，未来某次改动仍然可能把目录删掉、把 birth_time 查询降级成普通身份查询，或者让 Wikidata/IMDb/MusicBrainz/Olympedia 这类身份锚点意外满足出生时辰字段。对高敏感输入字段来说，规则写在计划里还不够，必须写进生产门禁。

这次新增的规则是：名人出生资料查源计划必须通过 `birth_profile_source_family_catalog_bound`。这个 gate 要求来源目录至少包含五类来源家族，出生时辰查询必须绑定 rated birth-time source，身份锚点和领域锚点必须明确禁止满足 birth_time，同时 lookup plan 的完整性检查必须通过。

方法论上的变化是：证据用途分层从“解释性元数据”升级为“发布前不变量”。这继续吸收 SLSA/in-toto 的思想：供应链里不只是文件哈希要受保护，证据用途也要受保护。对智能体来说，最危险的回归往往不是代码崩溃，而是证据边界悄悄变宽。生产门禁把这种边界固定下来。

对命理系统来说，这保护了八字、紫微、奇门三套推理的共同输入。出生时辰一旦被低等级来源污染，后续流派辩论再充分也只是围绕错误输入精细化。因此，出生资料链路必须先证明来源用途没有越权，再进入缓存审计、审核清单草案、导入预览和补丁预览。

推理变化：以后凡是会影响命盘核心计算的字段，都要有“来源用途门禁”。出生时辰、出生地、历法换算、时区、真太阳时、重大事件年份、经典文献规则出处，都不能只记录来源名称；还要记录该来源可服务的字段，并在生产门禁中证明没有越权晋升。

## v138: 人工来源缓存也要模板化

source lookup plan 说明了要查什么，source cache audit 说明了什么样的缓存合格，但两者之间还有一个容易出错的人工环节：人要创建 JSON 文件。如果没有模板，人可能漏填 query_id、case_id、source_rating、reviewer_note，或者把 review_status 写成系统不认识的词。这样不是命理判断错，而是资料管道在人工入口处发生漂移。

这次新增的规则是：lookup plan 后面要接 source cache template preview。模板预览会为每条 planned query 生成一份 JSON 骨架，包含 planned cache path、query_id、case_id、query、必填来源字段、出生字段占位、review_status 可选值、目标字段、推荐来源家族、来源用途规则和模板哈希。它仍然不写文件，只告诉人工或未来受控 provider 应该如何填写缓存。

方法论上的变化是：可复现系统不能只约束机器步骤，也要约束人工步骤。这个思想延续 in-toto/SLSA 的供应链证明，也贴近表单化数据采集：人工可以判断来源质量，但人工不应该重新发明文件格式。格式由系统给出，事实由人工审核填入，之后再由 cache audit 读取验证。

对命理系统来说，这一步减少了名人出生资料进入样本库前的结构性噪声。体育、影视、音乐名人的来源查找可能需要人工判断，但缓存格式、必填字段、状态枚举和目标字段必须统一。只有这样，后续 reviewed manifest draft 才能可靠聚合证据，八字、紫微、奇门智能体才不会读到形状不稳定的输入。

推理变化：资料链路现在多了一层“人工填写模板”。以后经典文献摘录、用户事实校准、重大年份事件、流派规则出处、外部 provider 回执，只要需要人工填 JSON 或 Markdown，都应先生成 template preview，再允许人工填写，再由 audit 读取。

## v139: 人工模板也要进入生产门禁

template preview 解决了人工填写格式漂移的问题，但它仍然是一个靠近外部资料入口的步骤。如果未来某次改动让模板预览顺手创建缓存文件、抓取网页、或把模板内容当成已审核证据，资料链路就会在人工入口处越界。因此，模板不仅要存在，还要被生产门禁证明为非破坏性。

这次新增的规则是：source cache template preview 必须通过 `birth_profile_source_cache_template_preview_non_mutating`。这个 gate 要求模板预览状态为可人工填写、有效、不抓 live source、不写 cache、不导入 profiles、有 template_count、template gate 未通过、完整性检查通过。

方法论上的变化是：所有“人机交接产物”都要被门禁化。计划、模板、缓存、草案、落盘预览分别代表不同阶段，不能因为它们看起来只是辅助文件就缺少发布前断言。这个规则继续延续供应链治理思路：真正可复现的系统不仅保护最终数据，也保护中间交接格式。

对命理系统来说，这保护了名人出生资料的人工入口。体育、影视、音乐样本的查源可能需要人工判断，但模板层不能自动写证据，也不能把占位字段当事实。模板只负责规范输入形状，事实是否可用必须交给缓存审计和后续审核清单。

推理变化：资料链路现在形成更完整的晋升序列：source-review workplan、source lookup plan、source family catalog gate、source cache template preview、source cache audit、reviewed manifest draft preview、file-write preview、import preview、fixture patch preview。以后任何新增的人机交接步骤，都要同时有模板、审计和生产门禁。

## v140: 来源用途规则必须在证据审计层再执行

source family catalog 和生产门禁能证明“计划层”知道不同来源能证明什么，但真正进入资料链路的是人工填写的 cache JSON。如果 cache JSON 不声明 source_family_id，或者声明了身份锚点却填入 birth_time，系统仍然可能在证据层被污染。因此，来源用途规则不能只停留在计划和模板里，还必须在 cache audit 里重新执行。

这次新增的规则是：每个来源缓存必须填写 source_family_id。cache audit 会检查这个 source_family_id 是否属于该查询推荐的来源家族；如果 payload 填了 birth_time，则 source_family_id 必须是 rated_birth_time_source；如果 payload 填了某个目标字段，则该来源家族的 usable_for_fields 必须覆盖这个字段。Wikidata、IMDb、MusicBrainz、Olympedia 这类身份或领域锚点即使被人工标成 source_reviewed，也不能满足出生时辰。

方法论上的变化是：约束要在每个晋升边界重复执行，而不能只在上游声明一次。这个思路类似类型系统和运行时校验的组合：计划层提供“静态规则”，缓存审计层提供“运行时规则”。对 LLM 智能体来说，这能防止计划正确但人工填写或外部 provider 输出越权。

对命理系统来说，这一步直接保护核心命盘输入。出生时辰是八字、紫微、奇门共同依赖的高敏感字段；只要它被身份锚点污染，后面所有流派辩论都会建立在错误输入上。cache audit 现在会拒绝这种污染，而不是等到导入预览才发现资料不可靠。

推理变化：以后所有关键事实字段都要在证据审计层做用途校验。出生时辰、出生地、时区、真太阳时、重大事件年份、经典文献规则出处，都要有 source_family_id 或等价字段，并且 audit 必须证明来源用途覆盖目标字段。

## v141: 关键约束要用最小反例探针证明

单元测试能证明开发时的行为，但生产门禁需要证明当前运行时仍然执行同一条关键约束。来源用途规则尤其如此：如果某次改动绕过了 cache audit 或改变了失败条件，测试可能没被运行，但 production readiness 应该能直接发现。最稳妥的方法是让门禁执行一个最小反例。

这次新增的规则是：source-family cache enforcement 要有运行时 probe。探针在临时目录里写入一条错误缓存：source_family_id 是 wikidata_identity_anchor，却填写 birth_time 并标记 source_reviewed。然后运行真实的 source cache audit，要求这条缓存被拒绝，accepted_cache_count 为 0，并且失败原因包含 birth_time 必须来自 rated_birth_time_source。

方法论上的变化是：门禁不只检查“有没有规则”，还检查“规则能不能挡住一个具体坏样本”。这和安全工程里的负例测试、供应链治理里的可验证断言一致。对智能体系统来说，越关键的边界越应该有最小反例：不是只证明好路径通，而是证明坏路径被挡住。

对命理系统来说，这种负例探针很重要。出生时辰、历法换算、时区、真太阳时、重大年份事件、经典文献出处，任何一个核心输入被错误来源污染，后面多智能体辩论都会变成错误输入上的精细推演。最小反例探针能让系统在进入推理前先证明污染被拦住。

推理变化：以后新增高风险规则时，同时要问两个问题：正例如何通过，反例如何失败。生产门禁应优先绑定最小反例，尤其是“身份来源伪装出生时辰”“未审核事实伪装历史事件”“普通文本伪装经典规则出处”“非专业 provider 伪装精确排盘”等场景。

## v142: 来源元数据不能替代事实证据

source cache audit 之前把 target_fields 当成一个整体，只要其中任一字段被填，就可能让 source_reviewed 通过。但 target_fields 里既有事实字段，也有来源元数据字段。source_name、source_url、source_rating 能说明“来源是谁”，不能说明“这个人的出生事实是什么”。如果只填来源元数据就通过，后续 reviewed manifest draft 会把空事实包装成已审核证据。

这次新增的规则是：source_reviewed 必须填入至少一个实质出生字段。当前实质字段限定为 birth_date、birth_time、gender、birthplace。source_name、source_url、source_rating、reviewer_note 仍然必填，但它们只证明来源包装完整，不证明出生事实成立。

方法论上的变化是：证据结构要区分“事实内容”和“来源元数据”。这类似数据建模里的 payload/provenance 分离：payload 回答发生了什么，provenance 回答这个说法来自哪里。两个都重要，但不能互相替代。对 LLM 智能体来说，这是防止“看起来引用很完整，但其实没有事实”的关键规则。

对命理系统来说，这一步继续保护命盘输入。出生日期、出生时辰、性别、出生地是进入八字、紫微、奇门计算的事实字段；来源名称和链接只是出处。只有出处、没有事实，不能让样本进入审核清单。

推理变化：以后所有证据缓存、经典文献摘录、用户事实校准、重大年份事件标签，都要区分 substantive fields 和 metadata fields。审核通过必须至少填入一个实质字段；元数据完整只能说明“可追溯”，不能说明“可用于推理”。

## v143: 实质证据规则也要用反例探针证明

上一版把事实字段和来源元数据分开了，但规则只存在于 cache audit 代码和单元测试里还不够。生产系统真正需要的是：每次发布前都现场跑一个坏样本，证明坏样本进不来。否则未来某次重构可能绕过这条规则，而生产门禁仍然只看“流程存在”。

这次新增的规则是：实质出生证据必须有运行时负例探针。探针在临时目录里写一条看起来很完整的 reviewed cache：有 source_name、source_url、source_rating，也声明 source_family_id 为 rated_birth_time_source，但故意不填 birth_date、birth_time、gender、birthplace。然后运行真实的 source cache audit，要求它被拒绝，accepted_cache_count 等于 0，失败原因必须包含“没有填入任何实质出生字段”。

方法论上的变化是：出处完整不等于事实成立，这条规则必须由生产门禁证明。以前的门禁证明“身份锚点不能冒充出生时辰”，这次证明“来源元数据不能冒充出生事实”。两者合起来形成事实入口的双重防线：来源用途要对，事实内容也要有。

对命理系统来说，这直接保护体育、影视、音乐名人样本验证链。名人案例会被用来校验八字流派、紫微流派、奇门流派和多智能体辩论机制，如果出生资料只是链接和来源评级，没有实质出生信息，后面的流年验证就是空转。现在系统在进入 reviewed manifest 之前会先挡住这种空证据。

推理变化：以后所有高风险事实字段都要同时有正例路径和反例探针。正例证明“合格资料能晋升”，反例证明“不合格资料不能混进去”。适用范围包括出生资料、真太阳时换算、重大年份事件、经典文献规则、外部 provider 排盘结果、用户事实校准记录。尤其是任何看起来“引用很多”的材料，都要检查它到底提供了事实，还是只提供了元数据。

## v144: 中文报告质量要用硬门槛保护

用户已经明确指出：命理研判报告里不应该出现英文、不应该出现 Python 代码，也不应该有问号乱码。这个要求不能只靠提示词提醒，因为报告是多层结构化数据、provider 状态、排盘符号、命令建议和最终渲染共同生成的。只要某个上游字段仍是英文，最终报告就可能混入英文。

这次新增的规则是：中文报告必须通过硬质量门槛。最终 Markdown 会先经过中文化清洗，把干支、五行、宫位、奇门门名、西占星座、provider 状态、择日活动和示例案例名转成中文；命令行接入说明不再直接出现在报告里，而是改写成通俗中文说明。评估器进一步要求：中文报告中不能有 ASCII 问号、不能有代码块、不能有 `python -m` 命令、不能有 `SEMAS_` 环境变量、不能有任何英文字母。

方法论上的变化是：用户可读性也是生产不变量。过去系统更重视 schema、receipt、source audit 和 provider contract，这些保护“机器可复现”；现在中文报告质量门槛保护“人能读懂”。命理智能体面向用户时，不能把内部工程术语、命令、英文符号和未翻译状态直接暴露给用户。

对命理系统来说，这一步直接影响林凡案例、小孩学业案例、名人样本验证报告和未来 PDF 输出。八字、紫微、奇门、多流派辩论可以在内部保留结构化英文键，但最终报告必须是中文、顺畅、少模板味、无乱码、无代码。内部数据和外部表达要分层：内部追求可审计，外部追求可读和可判断。

推理变化：以后所有面向用户的报告都要经过“表达质量审计”。结构化字段可以是英文键，provider 命令可以留在日志或 README，wiki 可以记录方法论，但中文报告不能泄漏这些内部实现。报告层的质量门槛应当包括：中文覆盖、无乱码、无代码、无重复套话、每年每月独立评价、关键断言清楚、低置信内容明确标注。

## v145: 每年每月都要绑定独立证据，不能只换标题

用户反复指出年度和月度内容不能大量重复。这个问题不是简单的文风问题，而是推理链的可审计问题：如果每一年、每个月都只输出同一批话术，读者无法看出系统到底有没有按该年的干支、十神、大运、用神状态和原局关系重新判断。

这次新增的规则是：年度、月度报告的每条主题判断都要绑定当前行证据。财运、官运、事业、学业、婚恋、朋友、领导、子女家庭这些句子，现在都会带上本年或本月、干支、天干十神、地支十神、所在大运、用神状态、原局同柱情况。主轴行和八字依据行也写入当前年/月和干支，避免同类结构被读成复制粘贴。

方法论上的变化是：反重复不能只靠“换几种说法”，而要靠“证据入句”。真正有价值的变化不是同义词替换，而是每一句判断都能指向不同的计算依据。这个思路和可复现推理一致：报告层的每一条结论，都应该能回到结构化行数据，而不是只回到模板库。

对命理系统来说，这直接服务林凡报告、小孩高考前二十四个月分析、名人样本验证和未来 PDF 输出。尤其是流月分析，很多月份可能主题相近，但仍要说明它们为什么相近、差异在哪里：干支不同、十神不同、是否引动用神不同、是否接大运不同、是否触发原局同柱不同。

推理变化：以后生成年度/月度报告时，先计算，再表达。表达层必须展示计算痕迹；评估层必须检测重复率。若重复率升高，说明报告没有把独立行证据充分写出来，不能只靠语言模型润色解决。

## v146: 不重复还不够，主题判断必须有证据锚点

上一版解决了年度、月度句子重复的问题，但还留下一个更细的风险：句子可以不重复，却仍然只是换了说法，没有把当前年或当前月的证据写出来。这样的报告看起来丰富，实际上仍然不方便复核。

这次新增的规则是：年度、月度每条主题判断必须有证据锚点。财运、官运、事业、学业、婚恋、朋友、领导、子女家庭这些行，都必须写出本年或本月、天干十神、地支十神、大运、用神状态、原局同柱状态。评估器会计算年度/月度尾部章节的证据锚点覆盖率，覆盖率低于一百个百分点，中文渲染直接不合格。

方法论上的变化是：报告质量不能只看语言表面，还要看每条判断是否可回溯。重复率解决“像不像复制粘贴”，证据锚点覆盖率解决“有没有真实计算依据”。两者合在一起，才比较接近用户说的“每个年份、每个月份都要独立计算独立评价”。

对命理系统来说，这条规则会影响所有流年、流月报告。即使两个年份判断同属财务主题，也必须告诉读者：它们是因为同一个大运、不同干支，还是因为不同十神、不同用神状态而表现相似或不同。读者才能看到判断来源，而不是只看到结论。

推理变化：以后新增任何命理主题行，都要问两个问题：这一句有没有独立证据锚点？这个锚点能不能回到结构化数据？如果答案是否定的，就不能进入正式报告，只能作为草稿或内部提示。

## v147: 质量门槛要变成 benchmark 可观测指标

证据锚点覆盖率、重复率、英文泄漏、代码泄漏这些规则，如果只藏在评估器里，调试时仍然不够直接。一个报告失败时，系统应该告诉我们是重复率高、证据锚点不足，还是英文和命令泄漏，而不是只给一个总分。

这次新增的规则是：中文报告质量诊断进入 benchmark report_features。每个 benchmark case 都会记录年度/月度重复率、年度/月度证据锚点覆盖率、英文字母数量、是否有 ASCII 问号、是否有代码或环境变量标记。这样生产 readiness、CLI schema、benchmark 回执都能观察到具体质量问题。

方法论上的变化是：指标要可诊断，不只是可打分。总分适合门禁，细分字段适合演化。智能体自动进化需要知道“哪里坏了”，才能决定下一步是修渲染、修证据入句、修中文化映射，还是修命理计算本身。

对命理系统来说，这让林凡报告、小孩流月报告、名人样本报告的质量问题更容易定位。比如用户说“还有英文”，可以看英文字母数量；用户说“每个月都一样”，可以看重复率；用户说“没有推理依据”，可以看证据锚点覆盖率。

推理变化：以后新增任何质量门槛，都要同时进入三个位置：评估器负责判定，benchmark 负责暴露诊断字段，wiki 记录方法论。只有这样，能力进化才不是黑箱打分，而是可复现、可迁移、可解释的工程过程。

## v148: 关键质量诊断要进入生产门禁

上一版把中文报告质量诊断放进 benchmark，但还缺最后一层保护：生产就绪检查必须明确读取这些诊断字段，并把它们变成发布前不变量。否则某次回归可能只在 benchmark 细节里出现，没有被 release gate 强制阻断。

这次新增的规则是：中文报告质量诊断必须通过生产门禁。`benchmark_chinese_render_quality_diagnostics` 会检查 benchmark 中文报告是否有年度/月度重复、证据锚点覆盖不足、英文字母泄漏、ASCII 问号、代码或 provider 命令泄漏。任何一项失败，production readiness 都会给出具体 blocker。

方法论上的变化是：评估器、benchmark、生产门禁形成三级链路。评估器负责判断，benchmark 负责暴露诊断，production readiness 负责发布阻断。这个链路让“中文报告是否可读、是否有独立依据”从用户反馈变成工程不变量。

对命理系统来说，这保护所有正式交付报告。林凡报告、小孩高考前流月分析、名人案例验证、PDF 输出，只要走生产路径，就不能退回到英文混杂、代码泄漏、重复套话或无证据锚点的状态。

推理变化：以后任何被用户反复指出的质量要求，都不要停在“我记住了”。要依次落到评估器、benchmark 诊断字段、生产门禁、日志和 wiki。只有这样，全局规则才是真正可执行的规则。

## v149: 名人验证要分成候选池、出生源、事件源和留出集

用户问能不能找体育、影视、歌星来验证。答案是可以，但方法上不能把“找到名人”直接等同于“可以升级规则”。名人样本最容易出现两个问题：出生时辰流传版本很多，成功年份过于显眼，模型容易事后贴合。因此验证链路必须分层。

这次明确的规则是：先建候选池，再复核出生源，再收集事件源，再划分训练集和留出集。候选池只说明这个人适合未来采样；出生源说明这个人的年月日时和地点是否可信；事件源说明某年是否真的发生了可标注事件；留出集用来防止规则只记住已知样本。没有外部复核之前，候选池和示例事件清单都不能叫生产证据。

本地已经有三类样本基础：体育包括阿瑟阿什、马克施皮茨、罗杰费德勒；影视包括玛丽莲梦露、露西尔鲍尔、西恩潘，并额外有李小龙作为影视武术样本；歌手包括艾瑞莎富兰克林、迈克尔杰克逊、麦当娜。候选池还覆盖费德勒、小威廉姆斯、迈克尔乔丹、成龙、梅丽尔斯特里普、汤姆汉克斯、泰勒斯威夫特、碧昂丝、周杰伦等人。

方法论上的变化是：命理智能体不能只追求“名人案例越多越好”，而要追求“每个案例的来源等级、事件标签、负样本年份、训练/留出角色都可审计”。尤其体育样本要记录冠军、排名、伤病、退役等事件；影视样本要记录作品、奖项、票房、制片权力变化；歌手样本要记录专辑、榜单、奖项、争议、健康等事件。这样才能让不同流派智能体围绕同一组事实辩论，而不是围绕传闻辩论。

这次还修正了一个数据层错误：阿瑟阿什的出生时间从错误的 `18:40` 改为来源检索一致的 `12:55`。这个修正提醒我们，命理验证的第一步不是判断格局，而是防止错时辰污染时柱。只要时辰错了，后面的十神、宫位、流年触发都会被带偏。

推理变化：以后用名人案例升级规则时，必须先问四个问题：这个人的出生时辰有没有来源等级？事件年份有没有正负样本？这个案例是训练用还是留出检验用？规则变化是否在看到留出结果之前冻结？如果答案不完整，只能作为探索样本，不能作为升级判断代码的证据。

## v150: 面向用户的命理报告要先给判断，再给依据

前几版已经解决了两个问题：年度和月度不能重复套话，每条主题判断都要绑定独立证据。但用户仍然指出，语言要更通顺、指向性更强，最好有一些断言。这里的关键不是把证据再堆多一点，而是调整表达顺序。

这次新增的规则是：每一条年度、月度主题行都要写成“判断：……；依据：……”。判断部分先告诉读者这件事大致怎么走，依据部分再说明本年或本月的干支、天干十神、地支十神、大运、用神状态、原局同柱关系。这样读者先得到结论，再看到为什么，而不是先被一串字段打断。

方法论上的变化是：证据锚点和阅读顺序要分开管理。证据锚点保证可复核，判断先行保证可阅读。一个命理报告如果只有证据，没有清楚判断，会像数据库导出；如果只有判断，没有证据，会像玄学套话。两者必须同时存在。

工程上的变化是：新增“判断结构比例”。中文渲染评估、benchmark 诊断、生产门禁都会检查年度/月度主题行是否同时包含“判断”和“依据”。这让“语言要有断言、又不能脱离证据”变成可执行规则，而不是一次性的写作偏好。

推理变化：以后任何面向用户的流年、流月、名人验证、亲子对照报告，都应该遵循同一个表达顺序：先结论，后证据；先方向，后结构；先让人读懂，再让人复核。内部智能体可以保留复杂推理链，但交付报告必须把复杂性折叠成清楚的判断和可追溯的依据。

## v151: 名人样本先看出生源质量，再谈规则升级

名人案例很适合做命理智能体的反向校准，因为事件年份公开、跨领域样本多、体育影视歌手都有清晰的高峰和低谷。但名人样本也最容易误导系统：一个错误时辰会改掉时柱，一个低评级来源会把“传闻出生时间”包装成事实，一个只看成功年份的样本会让规则过拟合。

这次新增的规则是：famous case receipt 必须显式给出出生源质量摘要。摘要包括来源数量、评级数量、高置信样本、谨慎样本、出生时间格式异常、可用于时柱敏感验证的样本。这样后续自动进化在看名人验证结果时，不会只看“样本多少”，还会看“哪些样本可以参与小时柱相关判断”。

当前快照是：十二个名人样本都来自 Astro-Databank；评级为甲甲七个、甲四个、乙一个；高置信样本十一个；蒋介石因为乙级来源进入谨慎样本；所有样本出生时间格式都合格；阿瑟阿什在修正为十二点五十五分后进入时柱评分可用集合。

方法论上的变化是：命理验证要把“案例覆盖”和“输入可信度”拆开。覆盖回答有没有体育、影视、歌手这些领域；输入可信度回答这个人的年月日时能不能进入排盘验证。两者都满足，才能把样本用于规则升级。只满足覆盖、不满足出生源质量，只能用于探索，不应用于强化判断代码。

推理变化：以后任何基于名人样本的规则改动，都要先读取 birth_source_quality。若样本不在高置信或时柱可用集合，不能用它来调整时柱、子女宫、晚年、流时或任何对出生小时敏感的判断。若只是年柱、月柱、行业事件粗校准，也要在报告中标注来源谨慎。

## v152: 输入质量标签必须跟着校准结果一起传播

上一版把名人样本的出生源质量写进 famous case receipt，但这还不够。真正发生规则演化的位置不是原始样本清单，而是年度事件校准结果、主题诊断、规则优化队列。如果质量标签只停在输入层，下游仍然可能只看到事件命中率和误报率，而忘记这些数字来自高置信时辰还是谨慎时辰。

这次新增的规则是：年度事件校准的每个 case score 都要携带自己的 birth_source_quality，并明确 hour_pillar_scoring_eligible。年度校准整体也要给出 birth_source_quality_summary，统计可用于时柱评分的样本数、谨慎样本数、高置信事件标签数、谨慎事件标签数和高置信事件占比。

当前快照是：十二个年度校准样本里，十一个可用于时柱敏感校准，一个为谨慎样本；一百二十个事件标签来自高置信样本，十个事件标签来自谨慎样本，高置信事件占比约为九成二。这样未来规则演化可以选择：时柱敏感规则只看高置信集合，宽泛年度主题可以保留谨慎样本但必须带 caveat。

方法论上的变化是：质量元数据不能只在入口处检查一次，而要随数据产品继续流动。输入清单、校准结果、诊断摘要、规则队列都应该保留质量标签。否则系统会在后续阶段丢失“这个样本能不能用于某类判断”的上下文。

推理变化：以后任何自动进化指标都要问两个问题：这个分数是多少？这个分数来自什么质量等级的数据？如果无法回答第二个问题，就不能把分数直接用于升级判断代码。尤其是命理中的时柱、宫位、子女、晚年、小时触发、流月细断，必须由高置信出生时间样本驱动。

## v153: 低质量来源主题先补证据，不先调规则

上一版把出生源质量传到年度校准结果，但规则优化队列仍然可能只看命中率、精确率和误报率。如果某个主题的事件主要来自谨慎出生源，直接调规则会把来源不确定性误当成模型误差，最终形成过拟合。

这次新增的规则是：主题摘要、领域主题摘要、全局规则优化队列、领域主题优化队列，都要带上高置信事件数、谨慎事件数和高置信事件占比。如果一个主题至少有三个事件，但高置信事件占比低于一半，队列优先级不是 high 或 medium，而是 source_review_first。

当前快照显示，career_power 和 war_pressure 的高置信事件占比为零，因此进入 source_review_first；study_exam 的高置信事件占比为一，因此可以继续作为普通规则优化对象。这比单纯看精确率更稳，因为它先判断“数据是否值得调规则”，再判断“规则是否要调”。

方法论上的变化是：自动进化队列不能只按模型表现排序，还要按证据质量排序。低质量来源对应的失败，不一定说明推理规则错了，可能说明样本输入不可靠。先补来源，再调规则，才能避免在错误或低置信资料上优化。

推理变化：以后所有规则队列都应分成三类：可以直接调规则的高质量样本问题；需要补事件标签的样本问题；需要先补出生源或事实源的证据问题。只有第一类适合进入判断代码修改，后两类应该进入数据和来源工作流。

## v154: 质量门控必须进入最终执行计划

上一版把低质量来源主题标成 source_review_first，但这还只是规则队列层面的判断。如果最终 evolution_task_plan 仍然把它转成 add_specific_evidence、reduce_false_positive 或 refine_precision，系统还是会在下一层走错：表面上知道要先补来源，实际计划却继续调规则。

这次新增的规则是：source_review_first 必须在最终执行计划中变成 review_birth_sources。这个任务不要求新增命理判断证据，而是要求收集高评级出生时辰来源、暂时排除谨慎样本参与小时柱敏感规则选择、复核后再重新运行年度校准。

当前快照显示，career_power 和 war_pressure 已经从普通规则优化任务改成 review_birth_sources；study_exam、career_project、public_controversy 这些高置信事件占比为一的主题，才继续进入 add_specific_evidence。这样自动进化的动作和质量判断保持一致。

方法论上的变化是：诊断层、队列层、执行计划层必须保持同一条决策链。只在诊断里写“来源不足”没有意义，除非最终任务真的去补来源。对智能体框架来说，质量门控必须贯穿到 action plan，否则它只是报告字段，不是行为约束。

推理变化：以后任何门控判断都要问：它是否改变了最终行动？如果没有改变最终行动，这个门控就只是观测指标。真正的自动进化必须让指标进入队列，让队列进入计划，让计划决定下一步改数据、改证据、改规则，还是暂时不改。

## v155: 领域切片不能绕过来源质量门控

上一版让全局年度任务计划继承 source_review_first，但还有一个更细的漏洞：领域主题队列也会生成任务。比如“近代政治的 career_power”这种切片，如果高置信事件占比为零，却仍然被标成 add_domain_specific_evidence，就等于从局部队列绕过了来源质量门控。

这次新增的规则是：领域主题切片也要检查高置信事件占比。只要事件数不少于三个、高置信事件占比低于一半，就生成 review_birth_sources，而不是普通的领域证据任务。这样全局主题、领域主题、最终计划三层都对低来源质量保持一致处理。

当前快照显示，影视 public_fame、影视 career_project、体育 career_project 等高置信占比为一的切片，继续进入领域证据增强；近代政治 career_power 高置信占比为零，进入 review_birth_sources。这个行为符合命理验证逻辑：先确认出生资料，再讨论该领域规则是否失灵。

方法论上的变化是：门控必须覆盖所有进入行动的路径。全局队列、领域队列、流派队列、多智能体辩论队列，只要会产生规则修改任务，都不能绕过来源质量检查。否则系统会在某个细分入口继续优化低质量样本。

推理变化：以后新增任何子队列，都要继承同一组质量字段：高置信事件数、谨慎事件数、高置信占比、来源复核任务类型。队列越细，越需要质量门控，因为局部样本更小，更容易被低质量来源支配。

## v156: 门控还需要路由总览，证明没有漏网

上一版让全局队列、领域队列、最终执行计划都继承来源质量门控。但自动进化系统还需要一个更高层的自检摘要：不是让人分别翻三个列表，而是直接回答“低来源质量主题有没有全部进入来源复核，有没有绕过门控”。

这次新增的规则是：年度校准 receipt 要输出 source_review_routing_summary。它同时记录全局来源复核主题、领域来源复核切片、最终执行计划中的来源复核任务，以及三个层面是否存在低质量样本绕过。只有 routing_complete 为真，才能说明来源门控在当前年度校准链路里闭环。

当前快照是：全局来源复核主题为 career_power 和 war_pressure；领域来源复核切片为近代政治 career_power 和近代政治 war_pressure；最终计划来源复核任务也是 career_power 和 war_pressure；三个绕过列表全为空。这个摘要把“质量门控是否真的生效”变成了可直接读取的证据。

方法论上的变化是：门控不只要存在、不只要改变行动，还要有闭环证明。对智能体自动进化来说，诊断、队列、计划、路由摘要是一条链。路由摘要负责证明该链没有断在某个中间层。

推理变化：以后新增任何关键门控，都应该配一个 routing summary 或 equivalent receipt。它要列出被门控拦截的对象、被转向的任务、漏网对象和是否闭环。没有路由总览，复杂系统很容易在某个子流程绕过规则。

## v157: 路由闭环要进入生产门禁

上一版新增了 source_review_routing_summary，可以证明低来源质量主题没有漏过来源复核。但如果这个摘要只停在 receipt 里，生产 readiness 不检查它，系统仍然可能带着坏路由继续发布。关键门控必须从可观测字段升级为发布前不变量。

这次新增的规则是：famous_case_source_review_routing_complete 成为生产门禁。它检查 routing_complete 是否为真，三个 bypass 列表是否为空，全局来源复核主题、领域来源复核切片、最终执行计划来源复核任务是否都存在。任何一项失败，production readiness 会产生 blocker。

当前快照是：新 gate 通过，details 为空，没有 blocker；career_power 和 war_pressure 在全局、领域和最终计划三个层面都进入来源复核；三个漏网列表全为空。这说明来源质量门控从“看得到”变成“发布前必须成立”。

方法论上的变化是：重要质量规则应当走四级链路：诊断字段、路由摘要、能力审计、生产门禁。诊断字段告诉系统发生了什么；路由摘要证明是否闭环；能力审计把它纳入能力面；生产门禁决定能不能发布。

推理变化：以后用户反复强调的全局规则，不能只写进提示词或 wiki。要优先转成 gateable invariant：能计算、能审计、能在 benchmark 或 readiness 中失败。只有进入门禁的规则，才真正会约束自动进化。

## v158: 生产门禁必须有反例探针

上一版把来源复核路由闭环接入生产门禁，但正向通过只能说明当前样本没有问题，不能证明门禁真的会拦住坏路径。对自动进化系统来说，门禁如果没有反例探针，就可能只是一个“永远显示通过”的装饰字段。

这次新增的规则是：关键门禁必须同时保存正例和反例。正例证明当前生产快照能通过；反例证明如果 source_review_routing_summary 缺失、routing_complete 为假，或者全局主题、领域切片、最终进化任务中出现低质量来源漏网项，门禁会明确失败并返回失败原因。

当前新增的反例测试构造了一个假审计结果：career_power 正常进入来源复核，但 war_pressure 同时出现在三个 bypass 列表里。系统必须判定来源复核路由不完整，并分别指出全局、领域、进化计划三个层面的漏网项。这样来源质量门控从“当前闭环”升级为“坏闭环会被拦住”。

方法论上的变化是：门禁的可靠性不能只靠绿色样本证明。每一个重要不变量都应该有最小坏例：缺字段、假布尔值、非空漏网列表、空任务列表等。正例负责防止误杀，反例负责防止漏杀。两者合在一起，门禁才真正有约束力。

推理变化：以后新增任何命理智能体进化规则，尤其是用户反复强调的全局规则，都要问两个问题：当前好样本是否通过？刻意构造的坏样本是否失败？如果只有前者，这条规则还只是演示；如果两者都有，它才算进入可迁移、可复现的工程框架。

## v159: 上游队列和最终计划不能说两套话

上一版证明了来源复核路由门禁能拦住坏样本，但系统内部还有一个表达层面的漏洞：最终 evolution_task_plan 已经把低来源质量主题转成 review_birth_sources，上游 rule_refinement_queue 却仍然建议补十神证据、补地支关系、调严格规则。这样虽然最终计划正确，早期队列仍然可能误导后续智能体去优化规则。

这次新增的规则是：只要主题被标记为 source_review_first，所有会驱动后续行动的队列都必须使用来源复核语言，而不是普通规则优化语言。career_power 和 war_pressure 现在在 rule_refinement_queue 中直接要求收集评级出生时辰来源、暂时排除谨慎样本、复跑年度校准。

方法论上的变化是：门控不能只在最后一步修正方向。自动进化链路中，诊断、规则队列、领域队列、最终计划、生产门禁都可能被后续智能体读取并执行。任何一层说错话，都会给系统留下歧义。因此关键质量判断必须从上游开始统一，而不是只在最后生成一个正确结论。

推理变化：以后新增门控时，不仅检查最终 action plan 是否正确，还要检查所有中间产物的措辞和任务类型是否一致。对于命理系统尤其重要：低质量出生资料、未审核经典文献、未复核历史事件，都不能在某个队列里被包装成“可调规则”的普通任务。

## v160: 队列语义一致性也要进入生产门禁

上一版把 rule_refinement_queue 的来源复核项改成了正确语言，但它还只是代码行为和单元测试约束。对自动进化系统来说，只靠单元测试还不够，因为发布前如果不检查，未来某次重构仍可能让 source_review_first 项重新出现“补十神证据、补地支关系”这类规则优化建议。

这次新增的规则是：famous_case_source_review_queue_aligned 成为生产门禁。它检查所有 source_review_first 队列项是否包含“评级出生时辰来源”行动，并拒绝混入 branch interaction evidence、ten-god evidence、strict-rule predicate 等规则调参语言。也就是说，来源问题不能在队列层被包装成规则问题。

方法论上的变化是：生产门禁不只保护数据边界，也保护任务语义。自动进化系统的很多错误不是文件写错，而是任务被错误命名：资料不足被叫成规则优化、样本不足被叫成精度不足、未审核文献被叫成经典依据。任务语义一旦错了，后续智能体就会沿着错误方向努力。

推理变化：以后所有“先复核、后调参”的规则，都要有语义门禁。低质量出生资料、未审名人事件、未审经典文献、未认证排盘 provider，都必须在队列、计划和门禁里保持同一个动作：先补证据，不改规则。只有证据入口合格，才允许进入流派辩论、规则变体选择和预测语言优化。

## v161: 生产门禁失败必须能回到修复计划

上一版把来源复核队列语义做成了生产门禁，但门禁如果只会阻断，不会给出修复路径，后续智能体仍然要重新理解为什么失败、该改哪里。自动进化不是只判断通过或失败，还要把失败转成下一轮可执行动作。

这次新增的规则是：famous_case_source_review_routing_complete 和 famous_case_source_review_queue_aligned 的失败，都要进入 production resolution plan。前者生成“修复名人案例来源复核路由”的步骤，后者生成“修复来源复核队列语义”的步骤，并保留原始 blocker 诊断。

方法论上的变化是：门禁、诊断、修复计划必须形成闭环。门禁负责阻断，诊断负责指出具体坏点，修复计划负责把坏点转成下一步动作。没有修复计划的门禁只是刹车；有修复计划的门禁才是自动进化系统的一部分。

推理变化：以后新增任何生产门禁时，都要同时检查三件事：能否在好样本通过，能否在坏样本失败，失败后能否生成明确修复步骤。对命理系统来说，来源复核、经典文献、流派辩论、年度事件标签、中文报告质量，都应该遵守这个三段式闭环。

## v162: 用户反馈形成的质量门禁也要可修复

前面已经把中文报告质量做成 benchmark_chinese_render_quality_diagnostics：检查年度、月度文字是否重复，是否有证据锚点，是否有“判断、依据”结构，是否泄漏英文、问号、代码痕迹。但它和名人案例来源门禁一样，还需要进入修复计划，否则失败后只会告诉系统“报告不好”，不会告诉下一轮该修哪一类问题。

这次新增的规则是：中文报告质量门禁失败时，production resolution plan 生成 repair_benchmark_chinese_render_quality。它保留重复率、证据锚点比例、判断结构比例、英文或代码泄漏等诊断，并把验证命令指向 benchmark。

方法论上的变化是：用户反馈不能只变成写作偏好，也不能只变成静态测试。高频反馈应该经历四步：转成可计算诊断，进入生产门禁，绑定反例或失败诊断，进入修复计划。这样“不要重复、不要英文、要通顺、有断言、有依据”才会成为系统行为。

推理变化：以后中文报告、命理推断、月度分析、流年分析中的任何质量要求，都要能回答三个问题：怎么量化？失败时怎么阻断？失败后谁来修、修什么？这比单纯提示“请写得更好”可靠得多。

## v163: 可读文本必须显式带出年度、月度干支

上一版让中文报告质量门禁失败后可以回到修复计划，但质量诊断仍然偏向文本层面：是否重复、是否有判断和依据、是否有英文或代码泄漏。它能证明文字不像模板，却还不能证明每个主题焦点真的把本年、本月的干支依据写出来。

这次新增的规则是：benchmark report_features 增加 annual_pillar_anchor_ratio 和 monthly_pillar_anchor_ratio。系统从 topic_synthesis 中取年度焦点、月度焦点的八字干支，把拼音式干支转换成中文干支，然后检查中文报告里是否逐主题出现。生产门禁要求两个比例都为一。

工程上还修正了一个细节：月柱可能出现 WuChou 这样的“天干拼音加地支拼音”组合，不一定在标准六十甲子整表里。因此干支转换不能只查六十甲子表，还要能拆分天干和地支，分别转换成“戊”和“丑”。这对月运分析尤其重要。

方法论上的变化是：结构化证据不能只留在 JSON 里，也要出现在用户可读文本里。命理报告如果只在内部有 annual_ten_gods、monthly_ten_gods，而外部文字没有“丙午、戊丑”这样的锚点，用户就无法判断这段话是不是独立推导出来的。

推理变化：以后年度、月度、流派辩论、三术交叉验证的关键证据，都应该有“结构化字段存在”和“中文文本显式锚定”两层检查。前者防止模型胡写，后者防止报告读起来像套话。

## v164: 干支锚点之后还要有十神锚点

上一版要求中文报告显式写出年度、月度干支，例如丙午、戊丑。这能证明报告没有完全脱离本年、本月，但还不够。命理推理真正起作用的是“这个干支对日主形成什么十神关系”，也就是为什么同一个干支会落到财、官、印、食伤、比劫等不同主题上。

这次新增的规则是：benchmark report_features 增加 annual_ten_god_anchor_ratio 和 monthly_ten_god_anchor_ratio。系统从 topic_synthesis 的 timing_evidence 里取年度、月度十神，把内部英文枚举转换成中文术语：同类、财星、官杀、印星、食伤，然后检查中文报告是否显式带出。

方法论上的变化是：干支是时间锚点，十神是解释锚点。只有干支，没有十神，用户知道“是哪一年哪一月”；有了十神，用户才知道“为什么判断成财、官、学业、感情、朋友或子女家庭”。这一步把报告从“列出时间”推进到“展示推理骨架”。

推理变化：以后年度/月度质量门禁至少要覆盖三层：本期干支、本期十神、本期用神或流通状态。干支说明时间，十神说明主题，用神和刑冲合害说明利弊方向。只有三层都出现在文本里，才更接近用户要求的独立推演。

## v165: 用神状态锚点补上利弊方向

上一版补了十神锚点，让中文报告不仅写出本年、本月干支，也写出它对日主触发的是同类、财星、官杀、印星还是食伤。但十神只回答“主题是什么”，还没有充分回答“这件事偏利还是偏弊”。

这次新增的规则是：benchmark report_features 增加 annual_useful_state_anchor_ratio 和 monthly_useful_state_anchor_ratio。系统从年度、月度 timing_evidence 里取 useful_state，并映射成中文报告里的用神状态：用神状态有利、用神状态忌偏重、用神状态中性或间接。生产门禁要求这两个比例都为一。

方法论上的变化是：年度/月度推理至少要有三层锚点。第一层是干支，说明“哪一年、哪一月”；第二层是十神，说明“触发什么主题”；第三层是用神状态，说明“偏利、偏弊还是中性”。这三层都进入中文文本，报告才不只是列主题，而是在展示判断路径。

推理变化：以后再推进五行流通、刑冲合害、合化、害破、子女家庭、学业月份等细粒度判断时，也要沿用同样结构：先有结构化字段，再有中文显式锚点，再进生产门禁。这样才能把“每年每月独立计算”从口头要求变成工程约束。

## v166: 地支关系从口头要求进入结构化证据

上一版把年度、月度推理固定成三层锚点：干支、十神、用神状态。但用户要求的每年每月独立推理，还包含更细的地支关系：冲、合、刑、害、破等。如果系统只在文字里说“注意冲突”而没有结构化字段，就仍然可能退回套话。

这次新增的规则是：年度和月度 BaZi evidence 都要计算 branch_interactions。系统把当前年/月地支和原局四柱地支比较，记录冲、合、刑、害、破。月度证据会把字段规范成 monthly_branch，年度证据保留 annual_branch。topic_synthesis 也要携带这些关系，保证最终主题综合能读到。

渲染层同步输出“地支关系”，例如当前地支与原局某柱形成刑、合、害等关系。benchmark 再增加 annual_branch_interaction_anchor_ratio 和 monthly_branch_interaction_anchor_ratio：如果结构化证据里存在关系，中文报告必须显式写出；如果没有关系，则不强行扣分。

方法论上的变化是：刑冲合害不能只当成流派辩论里的术语，它必须成为数据结构。只有进入结构化证据、中文渲染、benchmark 诊断和生产门禁，才能真正服务“每一年、每一月独立计算独立评价”。

推理变化：年度/月度推理链现在至少有四层：干支说明时间，十神说明主题，用神状态说明利弊方向，地支关系说明结构性牵动。后续再补五行流通、合化成败、宫位落点时，也应沿用同样的证据链。

## v167: 结构化证据需要单元测试，不只靠渲染门禁

上一版把地支关系接入年度/月度证据、主题综合、中文渲染和 benchmark 门禁。但如果只靠渲染门禁，仍然可能出现一种假稳定：文字里还有“地支关系”几个字，底层冲合刑害计算却悄悄坏了。

这次新增的规则是：关键结构化证据必须有专门单元测试。年度测试固定 2024 甲辰对原局的辰刑辰、辰害卯；月度测试固定 2025 年 2 月丙卯对原局的卯破午、卯害辰。系统集成测试还要求最终报告带出 branch_interactions，并在中文报告中出现“地支关系”。

方法论上的变化是：质量门禁保护输出，单元测试保护计算。两者缺一不可。门禁告诉我们用户能不能看到证据，单元测试告诉我们证据是不是按规则算出来的。

推理变化：以后每新增一类命理证据，都要有三层保护：计算层例子、结构化 schema、中文渲染锚点。比如五行流通、合化、三合三会、空亡、神煞、宫位落点，都不能只出现在最终文字里。

## v168: 名人样本可以扩展，但只能作为弱校准和回归测试

用户问是否可以找体育、影视、歌手明星来验证。当前系统已经有一条名人案例验证链路：本地固定样本覆盖体育、影视、歌手，并记录出生资料来源、来源评级、公开事件年份、行业事件标签、年度信号命中率和误报率。代表样本包括阿瑟阿什、马克施皮茨、罗杰费德勒，玛丽莲梦露、露西尔鲍尔、西恩潘，艾瑞莎富兰克林、迈克尔杰克逊、麦当娜。

方法论上的关键点是：名人案例不是“证明命理有效”的证据，而是系统进化的压力测试。它能检查系统是否在体育高峰、作品发布、公众成名、关系事件、健康风险、争议事件等不同事件类型上给出一致的结构化信号，也能暴露误报过高、行业证据不足、出生时辰来源不稳等问题。

因此新增名人案例必须分两层处理。第一层是出生资料复核：只有高评级、可追溯的出生时辰，才进入时柱敏感的校准。第二层是事件标签复核：公开事件年份可以来自百科、作品库、赛事库、唱片资料库等，但必须标注来源，且只能用于验证“某类事件是否在该年被系统触发”，不能反过来修正出生时辰。

推理变化：以后扩展名人样本时，优先补齐三个方向。体育侧重比赛峰值、伤病、退役和排名；影视侧重作品上映、奖项、公众形象和关系事件；歌手侧重专辑、榜单、演唱会、争议和健康事件。每个方向都需要正例年份和负例年份，否则只会提高回忆率，无法降低误报。

## Open Method Questions

- How to score conflicting Ziwei/Qimen schools without collapsing differences into one averaged answer?
- How to represent provider disagreement as useful user-facing uncertainty?
- What minimum empirical dataset size is enough to graduate from audit-only validation to predictive calibration?
- How to separate culturally meaningful interpretive tradition from claims that require outcome evidence?

## References

- Andrej Karpathy, "Software 2.0", 2017: https://karpathy.medium.com/software-2-0-a64152b37c35
- ReAct, arXiv:2210.03629: https://arxiv.org/abs/2210.03629
- Reflexion, arXiv:2303.11366: https://arxiv.org/abs/2303.11366
- Toolformer, arXiv:2302.04761: https://arxiv.org/abs/2302.04761
- Voyager, arXiv:2305.16291: https://arxiv.org/abs/2305.16291
- Voyager GitHub: https://github.com/MineDojo/Voyager
- Generative Agents, arXiv:2304.03442: https://arxiv.org/abs/2304.03442
- SWE-agent, arXiv:2405.15793: https://arxiv.org/abs/2405.15793
- SWE-agent GitHub: https://github.com/SWE-agent/SWE-agent
- SWE-bench, arXiv:2310.06770: https://arxiv.org/abs/2310.06770
- Center for Open Science preregistration initiative: https://www.cos.io/initiatives/prereg
- AsPredicted preregistration workflow: https://aspredicted.org/
- SLSA specification v1.0: https://slsa.dev/spec/v1.0/
- in-toto: https://in-toto.io/
- Wikidata Query Service: https://query.wikidata.org/
- Wikidata Query Service user manual: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Wikidata_Query_Help
- Wikidata API wbsearchentities: https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
- Astro-Databank: https://www.astro.com/astro-databank/Main_Page
- IMDb non-commercial datasets: https://developer.imdb.com/non-commercial-datasets/
- MusicBrainz API documentation: https://musicbrainz.org/doc/MusicBrainz_API
- MusicBrainz Database: https://musicbrainz.org/doc/MusicBrainz_Database
- Olympedia: https://www.olympedia.org/
