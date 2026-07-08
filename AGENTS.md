# Agent Instructions for SEMAS

> Cross-tool behavior conventions for any coding agent (Kimi Code, Claude Code,
> GitHub Copilot / Codex, Cursor, etc.) working on this repository.

## Project Identity

- **Name**: SEMAS — Self-Evolving Multi-Agent System Framework
- **Language**: Python 3.10+
- **Core principle**: frozen-weight LLM + selection-based evolution over
  prompts, tools, topologies, few-shot examples, and memory.
- **Key docs**: `README.md`, `SEMAS_ARA_Architecture.md`,
  `SEMAS_SIA_Integration_Design.md`, `OPERATION_LOG.md`, `wiki/`.

## Global Behavior Convention

For every non-trivial task (feature, bug fix, research, architecture change,
plugin addition), the agent MUST maintain two separate records:

1. **Operational record** — what was done, step by step.
   - Append to `OPERATION_LOG.md`.
   - Update `README.md` if the change is user-facing.
   - Include: date, motivation, actions taken, files changed, verification
     commands, and results.

2. **Thinking / ideation record** — why it was done, what ideas were absorbed.
   - Write to `wiki/` using Karpathy-style atomic notes.
   - Every borrowed idea, paper, or GitHub repo MUST be tagged with
     `[source: ...]`.
   - Keep `wiki/references.md` up to date with a BibTeX-like entry.

## Wiki Schema (Karpathy-style)

The `wiki/` directory is a persistent, compounding knowledge base following
[Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

- **Raw sources** are immutable and live in `external/`, papers, or URLs.
- **Wiki pages** are LLM-maintained markdown files with YAML frontmatter
  (`date`, `tags`, `sources`, `related`).
- **Special files**:
  - `wiki/index.md` — content-oriented catalog, updated after each ingest/run.
  - `wiki/log.md` — chronological append-only record of ingests and runs.
- **Conventions**:
  - One atomic note per run/ingest/idea.
  - Cross-link related pages.
  - Update `index.md` and `log.md` whenever a new wiki page is added or a
    major result changes.
  - Use `## Related pages` sections at the bottom of atomic notes.

This split keeps **doing** (logs/readme) separate from **thinking** (wiki),
making the project portable and auditable.

## Independent Thinking-Process Wiki (`wiki/think/`)

In addition to operational `wiki/` run notes, maintain a separate
thinking-process wiki at `wiki/think/`:

- **Purpose**: chain-of-thought, methodology evolution, failed hypotheses,
  absorbed paper/article ideas, and simulated research evolution.
- **Schema**: same Karpathy-style atomic notes with YAML frontmatter
  (`date`, `tags`, `sources`, `related`).
- **Special files**:
  - `wiki/think/index.md` — content catalog.
  - `wiki/think/log.md` — chronological thinking log.
  - `wiki/think/paper_ideas_queue.md` — papers/repos to ingest or already
    ingested.
  - `wiki/think/references.md` — BibTeX-like source list.

### Automatic maintenance rules

1. **After every significant interaction**, ask: *did this turn produce a
   valuable insight, methodological change, or failed hypothesis?* If yes,
   create/update an atomic note in `wiki/think/`, append one line to
   `wiki/think/log.md`, and update `wiki/think/index.md`.
2. **When downloading or searching papers/articles/repos**, extract the core
   value (claim, method, relevance, caveats) and write it to a new
   `wiki/think/papers/<short_name>.md`. Add a BibTeX entry to
   `wiki/think/references.md` and update `wiki/think/paper_ideas_queue.md`.
3. **Cite every external idea** with `[source: ...]` inside thinking notes.

## Source Citation Rule

- Always cite external ideas with a stable identifier:
  - Papers: `[source: arXiv:XXXX.XXXXX]` or `[source: Paper Title, Venue Year]`.
  - Code / repos: `[source: https://github.com/org/repo]`.
  - Local design: `[source: SEMAS_ARA_Architecture.md §X.Y]`.
- When in doubt, add the citation. Future maintainers (and other agents) must
  be able to trace every non-obvious decision.

## Workflow

1. **Understand**: read `README.md`, relevant code, and existing `wiki/` notes.
2. **Plan**: for multi-file or architectural changes, use the tool's plan mode
   or explicitly ask the user before writing code.
3. **Track progress**: maintain a TODO list if the tool supports it.
4. **Make minimal changes**: preserve existing behavior and tests.
5. **Verify**: run the relevant tests and the demo scripts. Record results.
6. **Document**: update operational logs and wiki as described above.

## Code Style

- Follow PEP 8 with `black` line length 100.
- Use type hints where reasonable.
- Keep dependencies minimal; prefer standard library for plugins.
- Do not break existing tests unless explicitly instructed.

## Safety Defaults

- Do not run `git commit`, `git push`, `git reset`, or `git rebase` unless the
  user explicitly asks.
- Do not install system-wide packages; use virtual environments.
- Sandbox all generated code before committing a genome version.
