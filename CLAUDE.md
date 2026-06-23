# Claude Code Instructions for SEMAS

> This file is read by Claude Code. For a tool-agnostic version, see
> `AGENTS.md`.

## Project

SEMAS — Self-Evolving Multi-Agent System Framework.
A minimal Python framework for building self-evolving multi-agent systems on
top of frozen-weight LLMs.

## Global Behavior Convention

For every non-trivial task, maintain TWO records:

1. **Operational record** — append to `OPERATION_LOG.md`; update `README.md`
   for user-facing changes.
2. **Thinking / ideation record** — write to `wiki/` in Karpathy-style notes
   with `[source: ...]` citations, and keep `wiki/references.md` current.

This split is mandatory. It makes the project auditable and portable across
agents.

## How to Use Claude Code Here

- Before large changes, use plan mode and get user approval.
- Use `CLAUDE.md` + `AGENTS.md` + `README.md` as context.
- For research tasks, always record absorbed papers/repos in `wiki/`.
- For code changes, always record steps in `OPERATION_LOG.md`.
- Run tests before finishing: `pytest tests/ semas/plugins/function_evolve/tests/`.
- Run the FunctionEvolve demo to verify plugin behavior:
  `python semas/plugins/function_evolve/demo.py`.

## Citation Rule

Every external idea must be tagged with a stable source, e.g.:

- `[source: arXiv:2605.27276]`
- `[source: https://github.com/hexo-ai/sia]`
- `[source: SEMAS_ARA_Architecture.md §5.7]`

## Style

- Python 3.10+, type hints, black line length 100.
- Minimal dependencies; standard library preferred for plugins.
- Do not break existing tests without explicit user approval.
