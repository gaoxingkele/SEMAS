---
date: 2026-07-07
tags: [papers, queue, external-ideas]
related: [references.md, README.md]
---

# Paper Ideas Queue

This page tracks papers, articles, and repos that contain ideas relevant to
the project. When a new source is downloaded or searched, extract the core
value and create an atomic note, then add a BibTeX-like entry to
`references.md`.

## Extraction template

For each source, answer:

1. **Core claim**: What is the main result or idea?
2. **Method**: What technique enables it?
3. **Relevance to SEMAS**: How can we apply or test it here?
4. **Limitations / caveats**: When does it fail?

## Queue

| Status | Source | Topic | Notes page |
|---|---|---|---|
| baseline | [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | Personal knowledge base for LLM-aided research | [README.md](README.md) |

## Candidate topics

- Genetic programming for alpha factors (Koza's work, Arnold et al.).
- Non-overlapping backtests in quantitative finance (Lopez de Prado).
- Factor momentum and horizon dependency (Ehsani, Linnainmaa, Roberts).
- Large-language-model critiquing for code/scientific reasoning.

## Rule

When a paper is ingested, create `wiki/think/papers/<short_name>.md` and add
an entry here.
