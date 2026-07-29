---
date: 2026-07-14
tags: [mingli, methodology, evaluation, calibration]
sources:
  - "examples/mingli_5agents/case_studies/hour_calibration/cases/*.json"
related: [../exact_calendar_book_comparison.md]
---

# Rank Comparison Must Preserve Ties and Boundaries

Changing the calendar backend before comparing books is necessary because an
incorrect month command makes a book comparison meaningless. It is not
sufficient for validation: the available set has only 11 public reference
hours, heterogeneous source quality, and no frozen holdout. [source:
examples/mingli_5agents/case_studies/hour_calibration/cases/*.json]

Several profiles produce zero-margin winners. A nominal winner in that state is
an implementation tie-break, not a method preference. Any comparison must
therefore report margin and top-k coverage alongside Top-1 and mean rank.

## Related pages

- [Operational Note](../exact_calendar_book_comparison.md)
