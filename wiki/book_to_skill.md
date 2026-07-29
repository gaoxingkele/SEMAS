---
date: 2026-07-27
tags: [skills, book-to-skill, agent-skills, tooling]
---

# book-to-skill in SEMAS

Installed the most popular open-source book→skill converter into this repo so
agents can distill owned books/docs into on-demand `SKILL.md` toolkits instead
of dumping full PDFs into context.

[source: https://github.com/virgiliojr94/book-to-skill]

## Why this one

- Highest-visibility public `book-to-skill` repo (~10k GitHub stars; Trendshift
  #10 Python / #25 overall on 2026-05-23).
- Open [Agent Skills](https://github.com/agentskills/agentskills) `SKILL.md`
  format — works across Cursor, Claude Code, Copilot CLI, Amp.
- Claims 24×–51× fewer tokens vs dumping the book for one question
  (measured on real books in upstream `docs/PERFORMANCE.md`).

## Install layout here

| Location | Role |
|----------|------|
| `.cursor/skills/book-to-skill/` | Canonical vendored skill (Cursor project skill) |
| `.agents/skills/book-to-skill` | Junction → same tree (cross-agent discovery) |

Pinned upstream commit at install time: `92b248fa`
(`feat(security): scan generated skills`).

## Relation to mingli book skills

SEMAS already has a domain-specific distillation path in
`examples/mingli_5agents/tools/build_mingli_book_skills.py` that follows the
same “structure not summary” idea for classical BaZi books. Upstream
`book-to-skill` is the general converter; the mingli builder remains the
school-specific, evidence-bounded pipeline for 渊海子平 / 三命通会 / 横门断 etc.

## Usage

1. Point the skill at a book you own (local PDF/EPUB/DOCX/…).
2. It writes a generated skill under the agent skills root.
3. Query by topic/chapter via the generated skill slug.

Do not redistribute generated skills of copyrighted third-party books
(upstream fair-use guidance).
