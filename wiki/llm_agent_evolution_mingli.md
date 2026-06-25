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
