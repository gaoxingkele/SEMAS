---
date: 2026-07-07
tags: [meta, wiki, thinking-process, karpathy-style]
sources:
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
related:
  - index.md
  - log.md
---

# Thinking-Process Wiki (`wiki/think/`)

This directory is an **independent** Karpathy-style knowledge base dedicated to
the *process of thinking* behind the SEMAS project. It is separate from the
operational `wiki/` run notes and focuses on:

1. **Chain-of-thought** — why a decision was made, what alternatives were
   considered, and what was learned.
2. **Methodology evolution** — how the factor-mining loop, mutators, data
   pipeline, and evaluation framework evolved over iterations.
3. **Ideas from papers / articles / repos** — extracted core concepts, tagged
   with stable sources, and connected to local experiments.
4. **Simulation of human research evolution** — an append-only log of
   hypotheses, failed experiments, and updated mental models.

## Schema

Every atomic note is a markdown file with YAML frontmatter:

```yaml
---
date: YYYY-MM-DD
tags: [factor-mining, methodology, paper-idea, experiment]
sources:
  - ../path/to/source.md
  - arXiv:XXXX.XXXXX
related:
  - other_note.md
---
```

Special files:

- `index.md` — content-oriented catalog.
- `log.md` — chronological append-only record of thinking events.
- `references.md` — BibTeX-like entries for external sources.
- `paper_ideas_queue.md` — queue of papers/articles to ingest or already
  ingested.

## Maintenance rule

After every significant interaction or ingest:

1. Ask: *did this turn produce a valuable insight, failed hypothesis, or
   methodological change?*
2. If yes, create or update an atomic note in `wiki/think/`.
3. Append a one-line entry to `wiki/think/log.md`.
4. Update `wiki/think/index.md`.
5. Cite every external idea with `[source: ...]` and add it to
   `wiki/think/references.md`.
