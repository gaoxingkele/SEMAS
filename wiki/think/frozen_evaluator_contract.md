---
date: 2026-07-13
tags: [methodology, evaluator, frozen_data, promotion, failure_analysis]
sources:
  - china_a_share_alpha/scripts/run_multihizon_audit.py
  - china_a_share_alpha/scripts/run_frozen_promotion_audit.py
related:
  - methodology_evolution_factor_mining.md
  - multi_horizon_design.md
---

# A Metric Is a Contract, Not a Scalar

The same label, such as "hold Sharpe", is not comparable unless strategy mode,
horizon, costs, smoothing, factor coverage, universe, dates, and data content
are identical [source: local promotion audit]. A persisted scalar without that
contract can silently compare simple hold against dynamic trim or one data
revision against another.

The durable state should therefore store a structured promotion baseline:
metric values, evaluation parameters, library hash, snapshot ID, coverage, and
observation count. Candidate and baseline must be recomputed on the same panel
before selection [source: local implementation].

Another methodological correction is that invalid evaluation is not a zero
score. Zero is a valid numerical outcome; empty factor intersections and parse
failures are missing evidence. Representing both as zero hides evaluator faults
inside apparently conservative results.

The failed complete-case approach also shows why ensemble coverage must be an
explicit gate. Requiring every factor on every row lets one sparse expression
erase otherwise valid evidence. A minimum available-factor fraction preserves
the ensemble while making the relaxation auditable.

## Related pages

- [Factor Mining Methodology Evolution](methodology_evolution_factor_mining.md)
- [Multi-Horizon Design](multi_horizon_design.md)
