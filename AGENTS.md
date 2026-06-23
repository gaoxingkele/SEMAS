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

This split keeps **doing** (logs/readme) separate from **thinking** (wiki),
making the project portable and auditable.

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
