---
date: 2026-07-14
tags: [mingli, hengmen, calibration, books, evaluation]
sources:
  - "examples/mingli_5agents/case_studies/hour_calibration/cases/*.json"
  - "lunar_python 1.4.8"
related: [exact_four_pillar_linfan.md, hengmen_rule_engine_v2.md, think/exact_calendar_book_comparison.md]
---

# Exact-Calendar Public-Case Book Comparison

All 12 public hour-calibration cases were rerun with the exact calendar backend
available. Of the 11 cases that include a public reference hour, independent
Hengmen reached Top-1 3/11, Top-3 3/11, and Top-5 6/11; its mean reference rank
was 5.545. The book-level Hengmen profile retained Top-1 3/11 and had a mean
reference rank of 5.455. [source:
examples/mingli_5agents/case_studies/hour_calibration/cases/*.json]

In this sample, Xingping Huihai had the lowest mean reference rank (5.091) and
Top-5 coverage 7/11. Mingli Jicheng and Ziping Zhenquan also reached Top-5
coverage 7/11. Multiple other profiles emit tied candidates, often with a zero
winner margin, so this is a descriptive rank comparison rather than a reliable
accuracy ordering. [source:
examples/mingli_5agents/case_studies/hour_calibration/cases/*.json]

No scoring weights were fitted during this run. The event timelines generally
lack exact months and declared counterexample years, so flow-month and
falsification modules remain neutral in this comparison. [source:
examples/mingli_5agents/case_studies/hour_calibration/cases/*.json]

## Related pages

- [Exact Four-Pillar Boundary and Lin Fan Fixture](exact_four_pillar_linfan.md)
- [Hengmen Rule Engine V2](hengmen_rule_engine_v2.md)
- [Thinking Note](think/exact_calendar_book_comparison.md)
