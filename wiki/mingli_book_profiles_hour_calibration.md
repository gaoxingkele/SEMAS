---
date: 2026-07-13
tags: [mingli, bazi, ahp, hour-calibration, case-study]
sources:
  - "https://commons.wikimedia.org/wiki/File:NLC416-15jh007754-99036_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf"
  - "https://ctext.org/datawiki.pl?if=gb&res=24146"
related: [llm_agent_evolution_mingli.md, think/mingli_book_profiles_hour_calibration.md]
---

# Mingli Book Profiles and Hour Calibration

The Mingli example represents classical material as independent, deterministic
AHP profiles. Each profile owns named sub-agent votes, so disagreement remains
inspectable instead of being flattened into one score. [source: `examples/mingli_5agents/tools/mingli_book_ahp.py`]

The hour-calibration harness compares all twelve candidate hours against
source-labelled public events. Its output is an evidence- and profile-dependent
ranking, not a claim to recover an unknown historical birth hour. Small winning
margins remain ambiguous. [source: `examples/mingli_5agents/case_studies/hour_calibration/hour_calibration.py`]

Local scans and text captures are research inputs rather than repository
assets. Stable public source links are retained for verification. [source: Wikimedia Commons NLC scan]

## Related pages

- [Mingli Agent Evolution](llm_agent_evolution_mingli.md)
- [Thinking Note](think/mingli_book_profiles_hour_calibration.md)
