# Source Environment

## Code

- Primary system: `china_a_share_alpha/` on branch `china-a-share-alpha-evolver`
- Worktree: `C:\aicoding\semas_framework_china_alpha_worktree`
- Loop entry: `python -m china_a_share_alpha.scripts.run_factor_mining_loop china_a_share_alpha/examples/factor_mining_loop_config.yaml`
- Frozen data config: `china_a_share_alpha/examples/enhanced_loop_config_val_frozen.yaml`

## Planned new modules (Stage 1)

| Module | Direction |
|---|---|
| `evolution/ast_regularizer.py` | D2 AST similarity + complexity |
| `evolution/dag_neighborhood.py` | D3 expression DAG + parent sampling |
| `loop/synergy_objective.py` | D1 pool IC / ensemble hold helpers |
| `scripts/run_ablation_campaign.py` | E1–E4 orchestration |

## Baseline repos (read-only)

See `evidence/baselines/external_repos.txt`. Ignored by git via root `.gitignore` `external/` — keep local.

## Python

- Use `py -3` (Python 3.14 env with pandas) for loop runs in this worktree.
- Do not require live `TUSHARE_TOKEN` when `snapshot_dir` is set.

## Skills / tooling (mylib)

- Paper routing: `C:\aicoding\mylib\skills\paper-writing`
- Lit search: `C:\aicoding\mylib\skills\paper_search`
- Experiment design: `C:\aicoding\mylib\skills\experiment-design`
- ARA: Codex `ara-paper` + mylib ARA package
- Venue: KDD = CCF-A (`academic-search/references/venue-rankings.md`)
