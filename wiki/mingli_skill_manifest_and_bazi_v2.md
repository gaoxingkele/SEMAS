---
date: 2026-08-08
tags: [mingli, skills, agent-genome, provenance, reproducibility]
---

# Skill identity must be bound separately from agent behavior

The Mingli branch had three different notions of an agent: installed Codex
skills, versioned SEMAS AgentGenomes, and deterministic Python sub-agents. The
knowledge layer had evolved to full-text-backed skills while the persisted BaZi
genome remained v1 and did not name those skills. Treating those layers as if
they were automatically synchronized made the execution lineage ambiguous.
[source: SEMAS_ARA_Architecture.md §5.3]

The first repair is to bind content identity before changing inference logic.
`skill_manifest.json` records the 12 installed skill IDs, versions, maturity
boundaries, source references, file counts, directory hashes, and `SKILL.md`
hashes. `skill_registry.py` recomputes the hashes and fails on absence or drift.
This makes the current external installation auditable without claiming that it
is already portable. [source: examples/mingli_5agents/skill_manifest.json]

`bazi_analyst` v2 names seven primary school skills, one auxiliary skill, and
one side-validation skill. Its runtime receipt binds the genome version to the
exact manifest hash. A changed manifest therefore becomes visible as
`manifest_drift` instead of silently changing the agent's knowledge contract.
[source: examples/mingli_5agents/genomes/bazi_v2.yaml]

The order matters: first stabilize skill identity, then bind it to an agent,
then evaluate behavior. Changing skill content, orchestration, and AHP weights
in the same selection event would make improvements impossible to attribute.
[source: SEMAS_ARA_Architecture.md §6]

The remaining limitation is deliberate and explicit: skill payloads still live
outside Git under the Codex skills directory. Hash pinning detects drift but
cannot reconstruct missing files. A reviewed repository snapshot or a
deterministic distillation package is still required for full offline
reproducibility. [source: examples/mingli_5agents/skill_manifest.json]
