# Smart_SkillandAgent Topic

## 2026-07-04 - One Upstream Repo Per Evolvable Subproject

Decision: create `Smart_SkillandAgent/` as a topic workspace where each
subproject maps to exactly one GitHub-origin skill or agent repository.
[source: SEMAS Smart_SkillandAgent Topic]

Why:

- Skills and agents evolve at different speeds; a per-repository boundary keeps
  provenance, license notes, patches, evaluation receipts, and run artifacts
  together.
- SEMAS evolution is selection-based over editable artifacts such as prompts,
  tools, topology, examples, memory, and evaluators. The same pattern can be
  applied to imported skills and agents without changing model weights.
  [source: SEMAS Framework]
- A local wiki per subproject prevents project-level reasoning from being lost
  in global logs and makes each evolved artifact portable.

Absorbed into:

- `Smart_SkillandAgent/README.md`
- `Smart_SkillandAgent/registry.yaml`
- `Smart_SkillandAgent/projects/_template_skill_or_agent/`

Required trace:

- `source/SOURCE.md` records upstream URL, license, revision, and import method.
- `evolution/` records iteration plans, metrics, and selection decisions.
- `evaluations/` records baseline and post-change receipts.
- `wiki/` records durable reasoning and citations using `[source: ...]` tags.

Open question:

- For each real project, choose the import mode case by case: direct clone,
  submodule, source snapshot, or patch mirror. The choice should preserve
  upstream attribution and keep evaluation reproducible.

---

## 2026-07-04 - First Two Imported Subprojects

Imported two GitHub-origin repositories as independent Smart_SkillandAgent
subprojects:

- `cobusgreyling_loop-engineering`: loop-engineering patterns and tooling for
  stateful agent loops. [source: https://github.com/cobusgreyling/loop-engineering]
- `handsomestWei_patent-disclosure-skill`: AgentSkills-style Chinese patent
  disclosure writing workflow. [source: https://github.com/handsomestWei/patent-disclosure-skill]

Design implication:

- `loop-engineering` should drive loop-level SEMAS evaluators: cadence, durable
  state, audit, budget, and human-gate checks.
- `patent-disclosure-skill` should drive skill-level SEMAS evaluators:
  project-evidence traceability, prior-art citation discipline, disclosure
  completeness, and iterative correction preservation.

Evidence boundary:

- Both imports are source/provenance baselines only.
- Runtime dependency installation and upstream test execution are deferred to
  the first improvement iteration inside each subproject.

---

## 2026-07-04 - Evolution Space Assessment

Assessment: both imported projects are evolvable, but the first mutation should
not be applied until each has a stronger evaluator.

Loop Engineering:

- Best evolution target: semantic loop-readiness and SEMAS loop-genome adapter.
- Reason: upstream already has structural file-signal scoring, so additional
  value should come from evidence quality, action boundary clarity, verifier
  reproducibility, budget specificity, rollback path, and actual run-log
  analysis. [source: https://github.com/cobusgreyling/loop-engineering]

Patent Disclosure Skill:

- Best evolution target: offline patent-disclosure benchmark before prompt
  mutation.
- Reason: upstream has rich staged prompts and tool tests, but needs an
  end-to-end quality evaluator for patent-point coverage, prior-art
  traceability, section completeness, formula consistency, claim support, and
  revision integrity. [source: https://github.com/handsomestWei/patent-disclosure-skill]

Planning artifacts:

- `Smart_SkillandAgent/evolution_plan.md`
- `Smart_SkillandAgent/projects/cobusgreyling_loop-engineering/evolution/evolution_plan_0001.md`
- `Smart_SkillandAgent/projects/handsomestWei_patent-disclosure-skill/evolution/evolution_plan_0001.md`

---

## 2026-07-04 - Skill-MAS Imported As Third Subproject

Imported `linhh29_Skill_MAS` as the third Smart_SkillandAgent subproject.
[source: arXiv:2606.18837]

Why it matters:

- Skill-MAS is almost a direct external realization of the SEMAS principle:
  frozen frontier LLM, editable orchestration artifact, rollout-based evidence,
  reflection-based mutation, and validation-based selection.
- Its Meta-Skill document is equivalent to a high-level genome over task
  decomposition, agent engineering, and workflow orchestration.
- Its multi-trajectory rollout and selective reflection loop can inform SEMAS
  mutator/evaluator design. [source: https://github.com/linhh29/Skill-MAS]

Evolution judgment:

- Do not start by running expensive benchmark evolution.
- First build a SEMAS-side Meta-Skill adapter and structural evaluator that can
  parse, diff, score, and rollback Skill-MAS skill snapshots.
- Then run a low-cost local mini benchmark before spending API budget on full
  official benchmark rollouts.

Planning artifact:

- `Smart_SkillandAgent/projects/linhh29_Skill_MAS/evolution/evolution_plan_0001.md`

---

## 2026-07-04 - First Evolution Iteration For The First Two Subprojects

Completed evaluator-first evolution for:

- `cobusgreyling_loop-engineering`
- `handsomestWei_patent-disclosure-skill`

Loop Engineering:

- Added a SEMAS-side semantic readiness evaluator.
- Result: the upstream reference repo scored `100/100`, `semantic-L3`.
- Interpretation: this project is a strong positive control; the next useful
  evolution is applying the evaluator to weaker target projects and exporting a
  loop genome. [source: https://github.com/cobusgreyling/loop-engineering]

Patent Disclosure Skill:

- Added a deterministic offline benchmark evaluator for patent disclosure
  drafts.
- Result: the batch-job-scheduler fixture had `9/10` evidence-anchor coverage;
  no candidate disclosure was scored yet.
- Interpretation: the skill now has selection pressure for future prompt/tool
  mutations without needing live CNIPA or paid LLM calls.
  [source: https://github.com/handsomestWei/patent-disclosure-skill]

Boundary:

- Both upstream `repo/` checkouts remained unchanged.
- This was a wrapper/evaluator evolution pass, not an upstream code patch.

---

## 2026-07-04 - Skill-MAS First Evolution Iteration

Completed evaluator-first evolution for `linhh29_Skill_MAS`.
[source: arXiv:2606.18837]

What changed:

- Added a SEMAS-side Meta-Skill adapter that parses Skill-MAS markdown skill
  files into explicit module fields.
- Compared `init_skill/SKILL.md` with `optimized_skill/*.md`.
- Generated a structural diff report and core compile receipt.
  [source: https://github.com/linhh29/Skill-MAS]

Result:

- Parsed skill files: `5`.
- Structurally valid skill files: `5/5`.
- Highest generality diffs: `bcp.md`, `drb.md`, and `vitabench.md` scored
  `1.0`; `hlemath.md` scored `0.9`.
- Selected upstream Python core files passed `py_compile`.

Interpretation:

- Skill-MAS optimized skills are complementary:
  - BCP: constraint linking, retrieval, merge-node re-execution.
  - DRB: synthesis/report topology and memory.
  - HLEMath: interpretation, verification, calibration, answer formatting.
  - VitaBench: real-world action gating and context integrity.

Boundary:

- No upstream Skill-MAS code was modified.
- No paid rollout or benchmark evolution was run.

---

## 2026-07-04 - Skill-MAS Installed For Local Codex

Installed Skill-MAS as a local Codex skill:

`C:\Users\xmupt\.codex\skills\skill-mas`

The skill uses progressive disclosure:

- `SKILL.md` is a short routing and workflow guide.
- `references/bcp.md` supports constraint-heavy retrieval and entity-linking.
- `references/drb.md` supports research/report synthesis.
- `references/hlemath.md` supports math, logic, verification, and formatting.
- `references/vitabench.md` supports real-world action workflows and safety
  gates.
- `references/initial-meta-skill.md` preserves the baseline three-stage
  Meta-Skill. [source: https://github.com/linhh29/Skill-MAS]

This makes Skill-MAS usable directly from local Codex with `$skill-mas` or by
asking for Skill-MAS / Meta-Skill / MAS workflow design.

Follow-up fix:

- Added a dedicated local validation venv for Codex skills at
  `C:\Users\xmupt\.codex\skill-venv`.
- Installed `PyYAML` there and verified `skill-mas` with official
  `quick_validate.py`.
- Updated local Codex to `0.142.5` through WinGet and added a user shim so
  `codex` resolves to the new executable.
- `codex doctor` now reports `0 warn` and `0 fail`.

---

## 2026-07-06 - Skill-MAS Installed For Local Kimi

Installed Skill-MAS as a Kimi Code skill in two places:

- Project-level: `.kimi\skills\skill-mas`
- User-level: `C:\Users\xmupt\.kimi-code\skills\skill-mas`

The skill mirrors the local Codex Skill-MAS layout:

- `SKILL.md` routes tasks to the right optimized Meta-Skill reference.
- `references/bcp.md`
- `references/drb.md`
- `references/hlemath.md`
- `references/vitabench.md`
- `references/initial-meta-skill.md`

Validation:

- `kimi doctor` reports valid Kimi config files.
- `kimi --skills-dir .kimi\skills -p ...` successfully loaded `skill-mas` and
  recognized the four output sections.
