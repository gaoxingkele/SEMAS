---
date: 2026-07-13
tags: [mingli, methodology, ahp, calibration, uncertainty]
sources:
  - "https://commons.wikimedia.org/wiki/File:NLC416-15jh007754-99036_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf"
related: [../mingli_book_profiles_hour_calibration.md]
---

# Keep Method Votes Separate From Calibration Evidence

Book-derived profiles are more useful when they preserve their own judgement
modules and weights. A single early aggregate hides whether disagreement came
from pattern assessment, seasonal adjustment, event mapping, or the evidence
set itself. [source: `examples/mingli_5agents/tools/mingli_book_ahp.py`]

The calibration design has two layers: deterministic method votes and structured
event-fit scoring. The resulting rank is conditional on supplied events and
profiles, so a narrow margin is reported as ambiguous rather than treated as a
factual identification. [source: `examples/mingli_5agents/case_studies/hour_calibration/hour_calibration.py`]

## Related pages

- [Operational Note](../mingli_book_profiles_hour_calibration.md)
