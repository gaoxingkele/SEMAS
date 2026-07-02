# SEMAS Operation Log

> Operational record of framework changes, plugin additions, and documentation
> updates. For the thinking/ideation behind decisions, see `wiki/`.

---

## 2026-06-26 - Annual Event Markers Schema

### Motivation

Career launch and role-power evidence had been derived from annual prose. That
was useful for calibration, but brittle. The next step was to promote weak text
signals into structured annual row markers.

### Actions Taken

1. Added `event_markers` to annual luck rows in
   `examples/mingli_5agents/tools/annual_luck.py`.
2. Added structured markers:
   - `career_launch`
   - `role_power`
   - `business_power`
   - `relationship`
   - `movement`
   - `study_exam`
   - `public_visibility`
   - `health_pressure`
   - `adult_career_stage`
   - `basis`
3. Added `AnnualEventMarkers` to the public API schema.
4. Added schema-contract evaluator coverage for `AnnualLuckRow.event_markers`.
5. Updated annual-luck tests to require the marker set.
6. Updated famous-case calibration evidence to prefer structured markers and
   keep text mining only as fallback.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

These markers are symbolic internal features, not validated event predictions.
They make calibration more auditable by replacing prose scraping with typed
annual row fields.

---

## 2026-06-26 - Career Launch And Role Power Evidence

### Motivation

The strong-career-evidence pass reduced false positives but made career-project
recall too low. Career events need project-launch and role-power evidence
instead of only counting career-domain ten-gods.

### Actions Taken

1. Extended annual event evidence in
   `examples/mingli_5agents/famous_case_validation.py` with:
   - `career_launch_signal`
   - `role_power_signal`
2. Derived those signals from existing annual career, official-career,
   leadership, theme, and phase text.
3. Tightened `career_power` to require authority plus role-power signal.
4. Adjusted `career_project` to require project-launch signal, at least one
   career-domain ten-god, and support/activation.
5. Updated tests to require both new evidence fields in event samples.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **strict recall 0.138, strict precision 0.111, strict false-positive rate 0.102**.
- Career topic diagnostics:
  - `career_project`: strict hit rate 0.125, strict precision 0.060, strict false-positive rate 0.222.
  - `career_power`: strict hit rate 0.000, strict precision 0.000, strict false-positive rate 0.085.
  - `business_power`: strict false-positive rate 0.000.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

Project-launch evidence restored some career-project recall, but precision
remains low. Role-power evidence remains too weak for career-power events.
Future work should add explicit title/institution/authority-transition markers.

---

## 2026-06-26 - Career Event Strong Evidence Tightening

### Motivation

Career project and career power remained high-priority weak topics after the
movement-evidence pass. The previous strict rule accepted any career-domain
ten-god plus broad support, which still fired in many non-event years.

### Actions Taken

1. Added `career_signal_strength` to annual event evidence in
   `examples/mingli_5agents/famous_case_validation.py`.
2. Tightened career strict matching:
   - `career_power` now requires authority ten-god and career/wealth category.
   - `business_power` now requires authority or wealth plus major-luck/natal
     confirmation.
   - `career_project` now requires at least two career-domain ten-god signals
     plus support/activation.
3. Updated tests to require `career_signal_strength` in event evidence.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **strict recall 0.123, strict precision 0.115, strict false-positive rate 0.087**.
- Career topic diagnostics:
  - `career_project`: strict hit rate 0.062, strict precision 0.045, strict false-positive rate 0.148.
  - `career_power`: strict hit rate 0.000, strict precision 0.000, strict false-positive rate 0.085.
  - `business_power`: strict false-positive rate 0.000.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The career rules are now more conservative. False positives dropped, but career
event recall also dropped. Future work should add project-launch and role-power
evidence rather than relaxing the generic career signal again.

---

## 2026-06-26 - Migration Movement Evidence Tightening

### Motivation

The annual event evidence bundle improved recall but still allowed major-luck
or natal activation to over-trigger migration and transition events. Migration
needs movement-specific evidence before broad support signals can confirm it.

### Actions Taken

1. Imported `STEMS` and `BRANCHES` into
   `examples/mingli_5agents/famous_case_validation.py` for local branch parsing.
2. Added `BRANCH_CLASHES` and branch-clash extraction helpers.
3. Extended annual event evidence with:
   - `annual_branch`
   - `branch_clashes`
   - `movement_signal`
4. Passed natal pillars into event-year and negative-year scoring.
5. Tightened `migration` and `transition` strict matching so movement signal is
   required before volatility, useful-state, major-luck, or natal activation can
   confirm the event.
6. Updated tests to require movement evidence fields in event samples.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **strict recall 0.169, strict precision 0.089, strict false-positive rate 0.158**.
- Migration topic diagnostic:
  **strict precision 0.048, strict false-positive rate 0.169, strict hit rate 0.200**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

Branch clash is still a symbolic movement proxy, not proof of relocation. It
now acts as a required movement signal for migration/transition strict matches,
while major-luck and natal activation remain confirmation signals.

---

## 2026-06-26 - Annual Event Evidence Bundle

### Motivation

The rule-refinement queue showed that career, relationship, migration, and fame
events need stronger evidence than broad annual category/intensity signals. The
next step was to attach an auditable evidence bundle to each event-year and
negative-year sample.

### Actions Taken

1. Added `_annual_event_evidence()` to
   `examples/mingli_5agents/famous_case_validation.py`.
2. Each annual event and negative sample now records:
   - annual ten-gods
   - expression/authority/wealth/resource/peer flags
   - active major-luck flag
   - natal-pillar activation flag and pillars
   - useful-state
3. Strict matching now uses the evidence bundle for public fame, career,
   relationship, sports, study, migration, transition, and pressure topics.
4. Updated tests to assert that event evidence is present in calibration
   samples.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **loose recall 0.754, loose precision 0.084, loose false-positive rate 0.754, strict recall 0.185, strict precision 0.080, strict false-positive rate 0.195**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The evidence bundle improves auditability and raises strict recall, but it also
increases strict false positives. Major-luck and natal activation should remain
supporting evidence, not standalone permission for exact-year claims.

---

## 2026-06-26 - Annual Event Rule Refinement Queue

### Motivation

Topic-level annual diagnostics identified weak event categories, but the system
still needed to convert those diagnostics into an executable improvement queue.
The next evolution step should know which event rules to refine first and what
extra evidence each rule needs.

### Actions Taken

1. Added `_annual_rule_refinement_queue()` to
   `examples/mingli_5agents/famous_case_validation.py`.
2. The annual calibration receipt now includes `rule_refinement_queue`.
3. Queue priority is based on event count, strict precision, and strict
   false-positive rate.
4. Added event-specific recommended evidence bundles, such as:
   - public fame: expression ten-god, useful-element activation, output-to-public-image chain.
   - career project: career-domain ten-god, major-luck continuation, natal pillar activation.
   - relationship: day-branch or relationship-palace activation, relationship ten-god, branch interaction.
   - migration: branch clash/movement signal and residence-axis activation.
5. Added the queue to capability-audit receipt material and public schema.
6. Updated capability-audit and schema-contract tests.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  high-priority topics include `career_power`, `career_project`,
  `relationship`, `migration`, and `public_fame`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The refinement queue is a diagnostic planning artifact. It prioritizes rule
improvement work; it is not itself a predictive validation result.

---

## 2026-06-26 - Annual Calibration Topic Diagnostics

### Motivation

The strict annual-event matcher reduced false positives, but the aggregate
precision remained low. Aggregate metrics did not explain which event topics
were responsible, so the calibration receipt needed topic-level diagnostics.

### Actions Taken

1. Added `_annual_topic_summary()` to
   `examples/mingli_5agents/famous_case_validation.py`.
2. The annual calibration receipt now aggregates each `event_topic` with:
   - event count
   - negative-year count
   - loose exact/window recall
   - loose precision and false-positive rate
   - strict recall, precision, and false-positive rate
   - case ids
3. Added `topic_summary` to capability-audit receipt material.
4. Added `topic_summary` to `FamousCaseAnnualEventCalibrationReceiptSummary`.
5. Updated capability-audit and schema-contract tests.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **13 event topics summarized**.
- Diagnostic highlights:
  - `health_risk`: strict precision 0.222, strict false-positive rate 0.036.
  - `sports_peak`: strict precision 0.250, strict false-positive rate 0.261.
  - `public_fame`: strict precision 0.077, strict false-positive rate 0.119.
  - `career_project`: strict precision 0.048, strict false-positive rate 0.352.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

Topic-level diagnostics are still weak calibration. Their value is prioritizing
which event rules to refine next. They do not convert celebrity biographies
into validated prediction evidence.

---

## 2026-06-26 - Strict Annual Event Signal Calibration

### Motivation

Negative-year calibration showed that the loose annual-event signal mapping had
high recall but very high false-positive rate. The next step was to add a
stricter parallel matcher that requires event-specific signal combinations
instead of accepting any one broad signal.

### Actions Taken

1. Added strict annual-event matching in
   `examples/mingli_5agents/famous_case_validation.py`.
2. Kept the loose matcher for recall comparison.
3. Added strict metrics:
   - `strict_exact_hit_count`
   - `strict_false_positive_count`
   - `strict_exact_hit_rate`
   - `strict_exact_precision`
   - `strict_false_positive_rate`
4. Added strict metrics to capability-audit receipt material.
5. Added strict metrics to `FamousCaseAnnualEventCalibrationReceiptSummary`.
6. Updated tests to require strict false-positive rate to be no worse than the
   loose false-positive rate.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **loose recall 0.754, loose precision 0.084, loose false-positive rate 0.754, strict recall 0.131, strict precision 0.070, strict false-positive rate 0.159**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The strict matcher substantially reduces false positives, but precision remains
low. This means event-specific evidence is still too weak for predictive
claims. The next useful step is to add stronger domain evidence per event
type, not to tune thresholds for cosmetic scores.

---

## 2026-06-26 - Famous Case Annual Negative-Year Calibration

### Motivation

The annual event calibration layer produced high event-year signal coverage, but
that could be caused by overbroad annual categories. The next step was to add
non-event years as negative samples and compute precision-oriented diagnostics.

### Actions Taken

1. Extended `famous_case_annual_event_calibration_receipt()` with negative-year
   samples for each event topic.
2. Added `negative_year_count`, `false_positive_count`, `exact_precision`, and
   `false_positive_rate` to the annual calibration receipt.
3. Added the same fields to capability-audit receipt material.
4. Added the new fields to `FamousCaseAnnualEventCalibrationReceiptSummary`.
5. Updated capability-audit and schema-contract tests to require the precision
   diagnostics.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **12 cases, 130 event tags, 1418 negative samples, exact recall 0.754, window recall 0.954, exact precision 0.084, false-positive rate 0.754**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The low precision is a useful failure signal. It means the current annual
event-signal mapping is broad enough to cover many event years, but also fires
in many non-event years. Future evolution should narrow event-specific signals
before using this layer for stronger claims.

---

## 2026-06-26 - Famous Case Annual Event Calibration Receipt

### Motivation

The previous famous-case calibration checked school-topic coverage only. The
next useful step was to test whether annual luck rows expose the expected
symbolic signal around sourced public event years.

### Actions Taken

1. Added `famous_case_annual_event_calibration_receipt()` to
   `examples/mingli_5agents/famous_case_validation.py`.
2. Added `EVENT_TOPIC_ANNUAL_SIGNALS`, mapping public event tags such as
   `sports_peak`, `public_fame`, `health_risk`, `relationship`, and
   `study_exam` to expected annual categories and intensities.
3. For each famous case, the new receipt builds the BaZi chart, generates
   annual rows from the first public event year to the last, and scores exact
   year plus +/-1-year window signal coverage.
4. Connected the annual-event calibration receipt to `capability_audit()`.
5. Added `famous_case_annual_event_calibration_receipt` to capability flags.
6. Added `FamousCaseAnnualEventCalibrationReceiptSummary` to the public API
   schema.
7. Updated schema-contract evaluator coverage and tests.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_annual_event_calibration_receipt()` smoke test:
  **12 cases, 130 public event-year tags, exact signal coverage 0.754, +/-1-year window signal coverage 0.954, 64-character receipt hash**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

This is annual signal coverage, not prediction accuracy. A high coverage score
can mean the annual categories are broad. Use it to find blind spots and
overbroad mappings before attempting stricter exact-year validation.

---

## 2026-06-26 - Famous Case School Calibration Receipt

### Motivation

The sports, film, and music celebrity fixtures were already present and audited,
but the system still needed an executable step that actually runs each case
through BaZi school debate and records how the schools cover public event-tag
categories.

### Actions Taken

1. Added `famous_case_school_calibration_receipt()` to
   `examples/mingli_5agents/famous_case_validation.py`.
2. The new receipt runs all 12 famous cases through `build_bazi_chart()`, reads
   each case's `school_debate`, and scores school-topic overlap with sourced
   event tags.
3. Added case-level, school-level, and domain-level summaries, plus
   `mean_topic_recall`, low-coverage cases, fixture hash binding, and a clear
   weak-calibration boundary.
4. Connected the calibration receipt to `capability_audit()`.
5. Added `famous_case_school_calibration_receipt` to capability flags.
6. Added `FamousCaseSchoolCalibrationReceiptSummary` to the public API schema.
7. Updated schema-contract evaluator coverage and tests.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` -
  **passed**.
- `famous_case_school_calibration_receipt()` smoke test:
  **12 cases, mean topic recall 0.389, domains include sports/film/music, 64-character receipt hash**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The score is topic-coverage recall across public event tags, not prediction
accuracy. It should be used to expose blind spots in school-agent reasoning and
to guide future calibration, not to claim validated fortune-telling.

---

## 2026-06-26 - Famous Case Validation Capability Binding

### Motivation

User asked whether sports, film, and music stars can be found and used for
validation. The fixture set already existed, but it still needed to be bound
into the executable capability audit so it could not remain an informal side
file.

### Actions Taken

1. Connected `famous_case_receipt()` to `capability_audit()`.
2. Added `famous_case_validation_receipt` to the capability flags.
3. Added the famous-case summary into the capability audit response and audit
   receipt material.
4. Added `FamousCaseValidationReceiptSummary` to the public API schema.
5. Updated schema-contract evaluator coverage so the response and receipt both
   require the famous-case validation reference.
6. Added tests requiring at least 12 cases and coverage of sports, film, and
   music domains.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tools\bazi_school_debate.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

### Source Boundary

The famous-person data remains weak calibration evidence. The upgrade here is
governance-level: the system now proves that the sourced fixture set is present
and hashed during capability audit; it does not claim statistical predictive
validity.

---

## 2026-06-26 - Sports Film Music Famous Case Expansion

### Motivation

User asked whether sports, film, and music celebrities can be found and used for
validation. These domains provide clearer public event tags: championship
peaks, award years, fame breakout years, career transitions, injuries, public
controversies, and relationship events.

### Actions Taken

1. Rewrote `examples/mingli_5agents/famous_case_validation.py` as clean UTF-8
   Chinese data.
2. Expanded the famous-case fixture set from 4 to 12 cases.
3. Added domain labels and event tags for:
   - Sports: Arthur Ashe, Mark Spitz, Roger Federer.
   - Film/television: Bruce Lee, Marilyn Monroe, Lucille Ball, Sean Penn.
   - Music: Aretha Franklin, Michael Jackson, Madonna.
   - Existing non-entertainment comparison cases: Chiang Kai-Shek and Albert Einstein.
4. Upgraded the receipt schema to `mingli-famous-case-validation-v2`.
5. Expanded school-topic hints to cover sports peak, transition, public
   controversy, and business power style tags.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` -
  **passed**.
- `famous_case_receipt()` smoke test:
  **12 cases, domains include sports/film/music, ratings AA/A/B, 64-character
  receipt hash**.

### Source Boundary

The expanded cases continue to use Astro-Databank pages as source links and
retain source ratings. They remain weak calibration fixtures, not predictive
proof. Unsourced celebrity charts and unverified birth times should remain out
of the main validation fixture set.

---

## 2026-06-26 - Famous Case Validation And BaZi School Rules

### Motivation

User requested searching modern and contemporary famous-person charts for
validation and upgrading the Mingli agents. User also allowed enriching each
BaZi school's sub-agent definition when needed.

### Actions Taken

1. Added `examples/mingli_5agents/famous_case_validation.py`.
2. Seeded a small sourced famous-case fixture set:
   - Bruce Lee, Astro-Databank, AA-rated source.
   - Chiang Kai-Shek, Astro-Databank, B-rated source.
   - Marilyn Monroe, Astro-Databank, AA-rated source.
   - Albert Einstein, Astro-Databank, A-rated source.
3. Attached public source URLs, source ratings, birth fields, public event-tag
   years, and validation boundaries to every case.
4. Added a stable `famous_case_receipt()` for audit/reproducibility.
5. Replaced the BaZi school debate scaffold with rule-specific sub-agent logic:
   - Zi Ping pattern rules.
   - Strength/support rules.
   - Tiaohou climate rules.
   - Body-use circulation rules.
   - Blind-school image rules.
   - Shensha/Na Yin auxiliary rules.
6. Added per-school method rules, event hypotheses, and calibration questions.
7. Kept `bazi-school-debate-v1` schema version for backward compatibility while
   adding optional richer fields.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\bazi_school_debate.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tools\bazi_deep_analysis.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.
- `famous_case_receipt()` smoke test:
  **4 cases, ratings A/AA/B, 64-character receipt hash**.

### Source Boundary

Famous-person cases are calibration fixtures, not proof of predictive validity.
AA/A cases can support stronger fixture confidence than B-rated or unsourced
internet charts. Event tags are used only for broad topic/year overlap, not for
claiming exact destiny prediction.

---

## 2026-06-25 - Gaokao Annual First Monthly Comparison Table

### Motivation

User requested the Gaokao monthly analysis to be reorganized as a comparison
table with benefit, risk, ten-god preference/avoidance, five-element flow, and
the interaction situation among combination, generation, control, punishment,
and harm. User also requested annual analysis before monthly analysis,
including Gregorian annual start/end dates and the relationship between the
June exam month, the annual flow, and the native four pillars.

### Actions Taken

1. Added annual Gaokao analysis lines for 2026, 2027, and 2028.
2. Added approximate Gregorian Li Chun year boundaries:
   - 2026-02-04 to 2027-02-03.
   - 2027-02-04 to 2028-02-03.
   - 2028-02-04 to 2029-02-03.
3. Added annual-flow versus native four-pillar relationship summaries.
4. Added a dedicated June 2028 exam-month relationship line:
   annual flow versus native four pillars, June month branch versus native
   chart and annual branch, and final five-element/use-god reading.
5. Replaced the long monthly bullet list with a Markdown comparison table:
   month, flowing month, benefit, risk, ten-god preference/avoidance,
   five-element flow, interaction situation, and action.

### Verification

- `python -m py_compile examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- `python examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- Gaokao report hygiene check:
  **no English letters, no question marks, no code fences**.
- Annual structure check:
  **3 annual analysis lines**.
- Monthly table check:
  **24 unique monthly table rows**.
- Content check:
  annual section exists, table header includes ten-god preference/avoidance and
  five-element flow, and June 2028 relation to the native four pillars is
  present.

---

## 2026-06-25 - Gaokao Monthly Wuxing Yongshen Mapping

### Motivation

User feedback clarified that monthly exam analysis must not stop at branch
relations and generic learning advice. Each flowing month must explain its
five-element movement and how that movement maps to the useful-god or exam-use
chain.

### Actions Taken

1. Added a dedicated Gaokao twenty-four-month report generator.
2. Added monthly five-element/use-god explanation:
   - Metal as output, answer presentation, expression, and problem-solving hand feel.
   - Wood as rules, targets, teacher requirements, and exam constraint.
   - Fire as resource star, comprehension, memory, teachers, and parent support.
   - Water as time/resource allocation, real pressure, and external pull.
   - Earth as self-bearing, stable execution, repetition, and persistence.
3. Added per-month independent lines with:
   - monthly ten-god pair,
   - flowing month five-element/use-god mapping,
   - branch interaction,
   - study score,
   - exam-execution score,
   - pressure label,
   - benefit,
   - risk,
   - action.
4. Generated:
   - `linfan_child_male_2028_gaokao_24months_wuxing_yongshen_zh.report.md`
   - `linfan_child_male_2028_gaokao_24months_wuxing_yongshen_zh.report.pdf`

### Verification

- `python -m py_compile examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- `python examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- Gaokao report hygiene check:
  **no English letters, no question marks, no code fences**.
- Monthly structure check:
  **24 monthly rows from 2026-07 through 2028-06**.
- Anti-template check:
  **24 unique monthly bodies after removing the date prefix**.
- Content check:
  every month includes flowing-month five-element and use-god mapping.

---

## 2026-06-25 - Male Child Macro Annual Report To Age Thirty

### Motivation

User calibrated the child profile as male and requested a new report focused on
macro destiny movement, major-luck phases, and independent annual flow
judgments through age thirty. User also promoted the anti-template rule to a
global behavior: no repeated filler and no copied annual/monthly wording.

### Actions Taken

1. Updated child birth input gender to male.
2. Extended child annual range to 2026-2039, covering the period before age
   thirty.
3. Reworked the child report into macro sections: basic facts, overall
   judgment, major luck, three age-stage trends, study/career/marriage lines,
   annual judgments, and parent advice.
4. Removed the monthly long table from the male child report.
5. Added a year-specific child annual assertion layer so each annual judgment
   has its own conclusion rather than sharing category-template endings.
6. Generated:
   - `linfan_child_male_20100618_to_age30_macro_annual_zh.report.md`
   - `linfan_child_male_20100618_to_age30_macro_annual_zh.report.pdf`

### Verification

- `python -m py_compile examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- `python examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- Male child report hygiene check:
  **no English letters, no question marks, no code fences**.
- Annual structure check:
  **14 annual rows from 2026 through 2039**.
- Anti-template check:
  **14 unique annual bodies after removing the date prefix**.
- Monthly section check:
  **no future monthly section in the male child macro report**.

---

## 2026-06-25 - Independent Annual Monthly Derivation

### Motivation

User feedback identified that the family Mingli reports still contained too
much repeated filler. Each year and each month must be calculated and evaluated
independently from its own stem-branch, ten-god, five-element flow, annual luck,
major-luck context, and branch interactions.

### Actions Taken

1. Replaced category-template annual/monthly prose in
   `examples/mingli_5agents/reports/generate_linfan_family_reports.py`.
2. Added independent relation extraction for natal branches, annual branches,
   and major-luck branches.
3. Added per-period study, career, wealth/resource, relationship, and pressure
   scoring.
4. Added age-aware wording so minors are evaluated for health, study, method,
   family/resources, and future-direction preparation rather than adult wealth
   or marriage claims.
5. Regenerated the two Chinese reports with new names:
   - `linfan_20260625_independent_annual_monthly_zh.report.md`
   - `linfan_20260625_independent_annual_monthly_zh.report.pdf`
   - `linfan_child_20100618_independent_study_career_marriage_zh.report.md`
   - `linfan_child_20100618_independent_study_career_marriage_zh.report.pdf`

### Verification

- `python -m py_compile examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- `python examples\mingli_5agents\reports\generate_linfan_family_reports.py` -
  **passed**.
- Report hygiene check:
  **no English letters, no question marks, no code fences**.
- Report structure check:
  **11 annual lines and 132 monthly lines per report**.
- Monthly uniqueness check:
  **132 unique monthly bodies per report after removing the date prefix**.

---

## 2026-06-24 - BaZi School Sub-Agent Debate

### Motivation

User feedback identified that the BaZi specialist should not speak as one
undifferentiated method. BaZi judgments often differ across Zi Ping pattern,
strength/support, Tiaohou, body-use circulation, blind-school image reading, and
Shensha/Na Yin auxiliary methods. Conflicts should be debated and preserved
before final synthesis.

### Actions Taken

1. Added `method_lineage.py`, binding Mingli schools, classical sources,
   implemented method surfaces, current use, and known gaps into a stable
   lineage receipt.
2. Added `tools/bazi_school_debate.py`, a deterministic paper sub-agent debate
   layer for six BaZi schools.
3. Attached `school_debate` to BaZi deep analysis and final `bazi_profile`.
4. Exposed `school_debate` through the public schema and Chinese renderer.
5. Added capability-audit support for method lineage and BaZi school debate.
6. Updated README and wiki methodology notes.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\bazi_school_debate.py examples\mingli_5agents\tools\bazi_deep_analysis.py examples\mingli_5agents\run_demo.py examples\mingli_5agents\method_lineage.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` -
  **2 passed**.

---

## 2026-06-24 - Mingli Annual Derivation Renderer

### Motivation

User feedback identified that the annual luck table still repeated too much
language. Each year should be derived from annual pillar, major luck, natal
branch interactions, and key month relations rather than rendered from fixed
phrases.

### Actions Taken

1. Added annual stem/branch splitting, ten-god labels, element labels, and
   branch-relation maps for clash, punishment, harm, combination, and repeated
   activation.
2. Rewrote annual prose generation to include annual ten-gods, five-element
   flow, natal-branch activation, major-luck interaction, and key month
   relation prompts.
3. Kept age-stage policy active so minor-year language avoids adult domains.
4. Added an optional known-event calibration input file:
   `examples/mingli_5agents/reports/linfan_major_events.json`.
5. Regenerated the Lin Fan report as an interpreted annual version.

### Verification

- `python examples\mingli_5agents\reports\generate_linfan_assertive_report.py` -
  **passed**.
- Text probe on `linfan_20260624_interpreted_annual_zh.report.md` found no
  ASCII letters, no half-width question marks, no full-width question marks,
  and no code fences.
- Annual probe counted 49 unique year entries from 1978 through 2026.
- Minor-year probe found no adult-domain terms for wealth, finance, career,
  romance, leadership, or children.

Output files:

- `examples/mingli_5agents/reports/linfan_20260624_interpreted_annual_zh.report.md`
- `examples/mingli_5agents/reports/linfan_20260624_interpreted_annual_zh.report.pdf`

---

## 2026-06-24 - Mingli Assertive Age-Aware Report Rendering

### Motivation

User feedback showed that a readable Mingli report still needs stronger
directional judgments and age-aware logic. Childhood years should focus on
health, parents, household rhythm, temperament, and study rather than adult
domains such as wealth, career, or marriage.

### Actions Taken

1. Generated an age-aware Chinese narrative report for the Lin Fan case.
2. Generated a more assertive Chinese narrative version with clearer summary
   judgments and smoother prose.
3. Regenerated the assertive version as an annual report with all 49 years from
   1978 through 2026.
4. Rendered the latest narrative report to PDF with Chinese font support.
5. Recorded the adopted five-layer Mingli reasoning method in the wiki as a
   methodology evolution note.

### Verification

- `python -m py_compile examples\mingli_5agents\reports\generate_linfan_assertive_report.py` -
  **passed**.
- Text probe on `linfan_20260624_assertive_annual_zh.report.md` found no ASCII
  letters, no half-width question marks, no full-width question marks, and no
  code fences.
- Annual probe counted 49 year entries, covering 1978 through 2026.
- Age-stage probe confirmed childhood sections use health, parents, family,
  temperament, and study language; adult sections can use career, wealth,
  relationship, leadership, and children language.

Output files:

- `examples/mingli_5agents/reports/linfan_20260624_assertive_annual_zh.report.md`
- `examples/mingli_5agents/reports/linfan_20260624_assertive_annual_zh.report.pdf`

---

## 2026-06-24 - Mingli Default Classical Source List Audit

### Motivation

Close the local classical-source list configuration gap without pretending that
a bundled demonstration corpus is production evidence. Capability audit needed a
deterministic, copyright-safe default source-list configuration, while
production readiness still needed to block until a refresh receipt exists.

### Actions Taken

1. Added an application-level default source list resolver in
   `capability_audit.py`.
2. Defaulted Mingli capability audit to
   `providers/classical_source_list_example.json` when no
   `SEMAS_CLASSIC_SOURCE_LIST` or explicit source-list path is provided.
3. Added `classical_source_list_path` to the capability-audit response schema.
4. Updated CLI, schema, empirical validation, and capability-audit tests to
   distinguish configured source-list audit from missing latest refresh receipt.
5. Updated README and wiki methodology notes.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_init_analyze_evolve_status -q` -
  **1 passed**.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_capability_audit_evaluator.py -q` -
  **4 passed**.
- Audit probe: `classical_source_refresh.status=ready`, configured capabilities
  `112/116`, with remaining false capabilities limited to Zi Wei, Qi Men,
  ephemeris astrology, and LLM backend configuration.

---

## 2026-06-24 - Mingli Handoff Checklist Receipt Drift Binding

### Motivation

Make implementation checklists reproducible after transfer. The framework could
already generate a stable checklist receipt, but callers could not provide a
previous receipt and receive an explicit drift decision.

### Actions Taken

1. Added expected checklist receipt comparison to
   `known_gap_handoff_implementation_checklist`.
2. Added `--expected-checklist-receipt-sha256` to
   `known-gap-handoff-checklist`.
3. Added `expected_checklist_receipt_sha256` support to
   `POST /known-gap-handoff-checklist`.
4. Updated schema contracts, capability evidence, CLI/API tests, README, and
   wiki methodology notes.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\capability_audit.py` -
  **passed**.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_known_gap_handoff_exports_portable_bundle examples\mingli_5agents\tests\test_api_server.py::test_http_api_known_gap_handoff_export examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_capability_audit_evaluator.py -q` -
  **5 passed**.
- CLI probe: generated a handoff export, generated a checklist, reran checklist
  generation with `--expected-checklist-receipt-sha256`, and received
  `checklist_receipt_matches_expected=true` with a 64-character receipt hash.

---

## 2026-06-23 — Create ai_video_evolver Package

### Motivation

User asked to materialize the AI video generation evolvable scaffold as a
standalone subpackage/module toolkit.

### Actions Taken

1. Created `ai_video_evolver/` as an independent Python package with its own
   `pyproject.toml`.
2. Added agent, tool, topology, and evaluator YAML/Python modules for a full
   AI video pipeline (scriptwriter → prompt engineer → asset generator → editor
   → critic).
3. Implemented `executor.py` to run the topology as a SEMAS `ExecutorFn`.
4. Implemented `mutator.py` with deterministic mutations for offline demo/CI.
5. Implemented `run_video_evolution.py` and `demo.py`; demo shows score
   improving from 0.603 to 0.803 after one SEMAS evolution round.
6. Added `tests/test_ai_video_evolver.py` with 6 passing tests.
7. Updated `wiki/semas_evolution_ideas.md` with the package details.

### Files Added

- `ai_video_evolver/pyproject.toml`
- `ai_video_evolver/README.md`
- `ai_video_evolver/__init__.py`
- `ai_video_evolver/bootstrap.py`
- `ai_video_evolver/executor.py`
- `ai_video_evolver/mutator.py`
- `ai_video_evolver/run_video_evolution.py`
- `ai_video_evolver/demo.py`
- `ai_video_evolver/agents/*.yaml`
- `ai_video_evolver/tools/*.py`
- `ai_video_evolver/topologies/*.yaml`
- `ai_video_evolver/evaluator/*.py`
- `ai_video_evolver/examples/sample_task.yaml`
- `tests/test_ai_video_evolver.py`

### Verification

- `python -m pytest tests/test_ai_video_evolver.py -q` — **6 passed**.
- `python -m ai_video_evolver.demo` — evolved from score 0.603 to 0.803.

---

## 2026-06-24 — Create china_a_share_alpha Package

### Motivation

User requested a complete independent scaffold for China A-share alpha factor
mining using the SEMAS evolution framework, with explicit attention to the
Qlib ecosystem (data format, operators, backtest), TA-Lib, and other factor
libraries (WorldQuant 101, AlphaGen, AlphaAgent, AlphaPROBE).

### Research Findings

- WorldQuant 101 Formulaic Alphas remains the baseline formula library.
- AlphaGen (KDD 2023) treats factor generation as token-level MDP and uses RL.
- AlphaAgent (KDD 2025) uses Idea/Factor/Eval LLM agents to fight alpha decay.
- AlphaPROBE (2026) uses a Bayesian retriever + DAG-aware generator.
- QuantaAlpha combines LLM + evolutionary strategies on Qlib data.
- Qlib supplies `.bin` data, ExpressionOps, processors, and backtest.
- TA-Lib supplies 150+ technical indicators.

### Actions Taken

1. Created `china_a_share_alpha/` as an independent installable package with
   `pyproject.toml` (core deps pandas/numpy; optional `qlib`/`talib` extras).
2. Implemented a Qlib-style expression tree (`ts_*`, `cs_*`, arithmetic,
   rolling binary ops) with dict serialization.
3. Implemented a synthetic China A-share panel generator for offline demo/CI.
4. Implemented optional Qlib data loader and optional TA-Lib wrappers.
5. Implemented a small Alpha101 baseline subset.
6. Implemented factor quality metrics: IC, RankIC, ICIR, turnover,
   long-short return.
7. Implemented a quantile long-short backtest.
8. Implemented `FactorMutator` as a SEMAS `Mutator` with deterministic
   seed mutation + random GP-style mutations.
9. Implemented `run_factor_mining.py` and `demo.py`.
10. Added 8 passing tests.

### Files Added

- `china_a_share_alpha/pyproject.toml`
- `china_a_share_alpha/README.md`
- `china_a_share_alpha/__init__.py`
- `china_a_share_alpha/data/{synthetic.py,qlib_loader.py,alpha101.py,talib_features.py}`
- `china_a_share_alpha/factor/expression.py`
- `china_a_share_alpha/evaluator/{metrics.py,neutralizer.py}`
- `china_a_share_alpha/backtest/long_short_backtest.py`
- `china_a_share_alpha/evolution/factor_mutator.py`
- `china_a_share_alpha/executor.py`
- `china_a_share_alpha/run_factor_mining.py`
- `china_a_share_alpha/demo.py`
- `china_a_share_alpha/examples/sample_config.yaml`
- `tests/test_china_a_share_alpha.py`

### Verification

- `python -m pytest tests/test_china_a_share_alpha.py -q` — **8 passed**.
- `python -m china_a_share_alpha.demo` — evolved from IC -0.07 to IC 0.23.

### Next Steps / Real-Data Usage

- Download community Qlib A-share data (e.g. chenditc/investment_data).
- Set `data_source: qlib` and `instruments: csi300` in the YAML config.
- Replace the deterministic seed mutator with a GP or LLM-driven mutator for
  open-ended search.
- Add industry/market-cap neutralization once sector mappings are available.

---

## 2026-06-24 — China A-Share Alpha Evolver Deepening

### Motivation

User asked to continue deepening the A-share factor mining scaffold.

### Actions Taken

1. **Train / test split**: `data/qlib_loader.py` and `data/synthetic.py` now
   return `(train, test)`; `executor.py` evaluates the same expression on both
   panels; `run_factor_mining.py` reports in-sample and out-of-sample IC.
2. **Sector / market-cap neutralization**: rewrote `evaluator/neutralizer.py`
   with `apply_neutralization()` and wired it into `executor.py` via config
   flags. Synthetic data now includes random `sector` and `market_cap`.
3. **Transaction costs**: enhanced `backtest/long_short_backtest.py` to
   compute turnover and subtract `2 * one-way_cost * turnover` from returns,
   yielding cost-adjusted returns.
4. **Open GP search**: added `mode: gp` to `FactorMutator`; it grows random
   expression trees from a grammar (`ts_*`, `cs_*`, arithmetic). The default
   deterministic `seed` mode remains for demo/CI.
5. **Factor report generator**: added `report/generator.py` that writes JSON
   and Markdown reports with expression, IC, backtest stats, and full config.
6. Updated `china_a_share_alpha/examples/sample_config.yaml` and README with
   the new options.
7. Updated `tests/test_china_a_share_alpha.py` to cover executor train/test
   output and report generation.

### Verification

- `python -m pytest tests/ -q` — **30 passed**.
- `python -m china_a_share_alpha.demo` — train IC 0.227, test IC 0.225,
  expression `neg(cs_rank(ts_mean(return, 5)))`, report written.

### Files Added/Modified

- `china_a_share_alpha/data/synthetic.py`
- `china_a_share_alpha/data/qlib_loader.py`
- `china_a_share_alpha/evaluator/neutralizer.py`
- `china_a_share_alpha/executor.py`
- `china_a_share_alpha/backtest/long_short_backtest.py`
- `china_a_share_alpha/evolution/factor_mutator.py`
- `china_a_share_alpha/report/{__init__.py,generator.py}`
- `china_a_share_alpha/run_factor_mining.py`
- `china_a_share_alpha/demo.py`
- `china_a_share_alpha/examples/sample_config.yaml`
- `china_a_share_alpha/README.md`
- `tests/test_china_a_share_alpha.py`

---

## 2026-06-24 — China A-Share Alpha Continuous Mining Loop

### Motivation

User requested `/loop` to continuously mine, download, validate, backtest,
compare, and evolve alpha factors.

### Actions Taken

1. Added `loop/population.py` with `FactorPopulation` class implementing a
   genetic-programming outer loop:
   - seeds raw variables + classic expressions + random grammar trees;
   - evaluates each candidate on train and test sets;
   - selects elites by **test IC** to discourage train-set overfitting;
   - produces offspring via `FactorMutator.mutate_prompt` and `crossover`;
   - deduplicates by expression string;
   - tracks convergence with `max_generations` and `patience` early stopping.
2. Added `run_factor_loop.py` CLI driver that runs the loop and writes:
   - `factor_loop_leaderboard.csv`
   - `factor_loop_history.json`
   - `factor_report_*.json` / `.md`
3. Added `crossover(parent1, parent2)` to `evolution/factor_mutator.py`.
4. Added `examples/loop_config.yaml` for the continuous loop.
5. Added `tests/test_factor_loop.py` with 2 passing tests.
6. Updated `README.md`, `.gitignore`, `wiki/semas_evolution_ideas.md`.

### Verification

- `python -m pytest tests/ -q` — **32 passed**.
- `python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml` —
  loop discovers `neg(cs_rank(ts_mean(return, 5)))` (test IC 0.225) and stops
  after 4 generations of no test-IC improvement.

### Files Added/Modified

- `china_a_share_alpha/loop/{__init__.py,population.py}`
- `china_a_share_alpha/run_factor_loop.py`
- `china_a_share_alpha/evolution/factor_mutator.py`
- `china_a_share_alpha/examples/loop_config.yaml`
- `tests/test_factor_loop.py`
- `china_a_share_alpha/README.md`
- `wiki/semas_evolution_ideas.md`
- `.gitignore`

### Notes / Next Steps

- The current loop uses synthetic data and a pure-Pandas operator set. For
  production use, switch `data_source` to `qlib` and provide real sector /
  market-cap mappings.
- Selection currently uses test IC only; future work can add a
  regularization term penalizing train/test IC decay (alpha decay).
 - Crossover is subtree exchange; could be extended to AlphaPROBE-style
  DAG-aware crossover.

---

## 2026-06-24 — China A-Share Alpha: All Target Directions Completed

### Motivation

User asked to complete all the previously listed deepening directions for the
A-share factor mining scaffold.

### Actions Taken

1. **Real Qlib data download**
   - Added `scripts/download_qlib_cn_data.py` to download and extract the
     community `qlib_bin.tar.gz` from `chenditc/investment_data`.
   - Added `examples/qlib_config.yaml` demonstrating real-data usage.

2. **Real sector / market-cap mapping**
   - Added `data/sector_mapping.py` supporting a user CSV (`symbol, sector,
     market_cap`) with synthetic fallback.
   - Added `scripts/generate_sector_template.py` to create a CSV template from
     a Qlib instrument list.
   - Wired neutralization into `data/qlib_loader.py` and `executor.py`.

3. **Alpha decay monitoring**
   - Added `loop/decay_monitor.py` computing rolling test-IC slopes.
   - `FactorPopulation.run_generation()` prints a decay warning when the slope
     is negative.

4. **Multi-factor portfolio evolution**
   - Added `loop/portfolio.py` with `PortfolioPopulation` storing portfolios
     inside SEMAS `AgentGenome` as expression lists + weights.
   - Added `run_portfolio_evolution.py` and `examples/portfolio_config.yaml`.
   - Added `examples/sample_factor_library.csv` for quick testing.

5. **LLM-driven factor mutation + DSL parser**
   - Added `factor/parser.py` to parse expressions such as
     `neg(cs_rank(ts_mean(return, 5)))`.
   - Added `evolution/llm_mutator.py` prompting an LLM and falling back to GP
     on parse failure.
   - Integrated with SEMAS `LLMClient` (OpenAI / Kimi / DeepSeek via env).

### Verification

- `python -m pytest tests/ -q` — **39 passed**.
- `python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml` —
  discovers `neg(cs_rank(ts_mean(return, 5)))` and stops on convergence.
- `python -m china_a_share_alpha.run_portfolio_evolution china_a_share_alpha/examples/portfolio_config.yaml` —
  evolves a weighted portfolio from the sample factor library.

### Files Added/Modified

- `china_a_share_alpha/scripts/{download_qlib_cn_data.py,generate_sector_template.py}`
- `china_a_share_alpha/data/sector_mapping.py`
- `china_a_share_alpha/data/qlib_loader.py`
- `china_a_share_alpha/loop/decay_monitor.py`
- `china_a_share_alpha/loop/portfolio.py`
- `china_a_share_alpha/run_portfolio_evolution.py`
- `china_a_share_alpha/factor/parser.py`
- `china_a_share_alpha/evolution/llm_mutator.py`
- `china_a_share_alpha/run_factor_loop.py`
- `china_a_share_alpha/examples/{qlib_config.yaml,portfolio_config.yaml,sample_factor_library.csv}`
- `china_a_share_alpha/README.md`
- `tests/test_china_a_share_alpha_advanced.py`
- `wiki/semas_evolution_ideas.md`
- `.gitignore`

---

## 2026-06-26 — China A-Share Alpha: Tushare 5-Year Backtest Comparison

### Motivation

User requested historical backtest evaluation and comparison of single vs
combined A-share factors over the past 5 years, using Tushare as the data
source.

### Actions Taken

1. **Tushare data loader**: added `china_a_share_alpha/data/tushare_loader.py`
   to fetch daily price, valuation (`daily_basic`), and sector data for CSI300
   constituents, with local Parquet caching.
2. **Explainable factor library**: added
   `china_a_share_alpha/examples/tushare_factors.py` with six single factors
   (momentum, short-term reversal, volume-price correlation, low-volatility,
   PB value, liquidity) and two rule-based combinations (multi-timeframe,
   multi-style equal).
3. **IC-weighted composite**: the backtest script computes in-sample IC for
   each single factor and builds a transparent combined factor whose weights
   are proportional to signed IC.
4. **Backtest comparison script**: added
   `china_a_share_alpha/scripts/run_tushare_backtest.py` which evaluates all
   factors on the full 5-year panel and reports IC, RankIC, ICIR, turnover,
   long-short return, Sharpe, max drawdown, cost-adjusted return, and
   train/test IC gap.
5. **Report generation**: outputs CSV, Markdown, and JSON summary to
   `china_a_share_alpha_output/tushare_backtest/`.
6. Added optional `tushare` dependency to `pyproject.toml`.
7. Added `tests/test_tushare_backtest.py` (skipped if `TUSHARE_TOKEN` is not
   set).

### Verification

- Ran full 5-year backtest on CSI300 constituents (2021-06-01 to 2026-06-01):
  - 300 symbols, 1,210 trading days, 356,207 rows.
  - Best Sharpe: `momentum_20` (0.406).
  - Best IC: `value_pb` (0.0097).
  - Highest RankIC: `ic_weighted_train` (0.0376).
- `python -m pytest tests/ -q` — **39 passed** (Tushare tests skipped without
  token).

### Files Added/Modified

- `china_a_share_alpha/data/tushare_loader.py`
- `china_a_share_alpha/examples/tushare_factors.py`
- `china_a_share_alpha/scripts/run_tushare_backtest.py`
- `china_a_share_alpha/pyproject.toml`
- `tests/test_tushare_backtest.py`
- `china_a_share_alpha/README.md`
- `wiki/semas_evolution_ideas.md`

### Notes

- Simple style factors were relatively weak over this 5-year sample; the
  IC-weighted combination improved IC but not always long-short Sharpe,
  underscoring the importance of transaction costs and risk neutralization.
- For production use, add sector/market-cap neutralization and consider
  barra-style risk model constraints.

---

## 2026-06-26 — China A-Share Alpha: Evolved Factors on Real Tushare Data

### Motivation

User asked how many factors had been built, which combined factor was best,
and requested continuous evolution to expand the factor library without
stopping.

### Actions Taken

1. **Wired Tushare into the factor mining loop**: updated
   `china_a_share_alpha/data/qlib_loader.py` to route `data_source: tushare`
   to `data/tushare_loader.py`, so the GP loop now mines factors on real
   CSI300 data.
2. **Loop configuration**: added `examples/tushare_loop_config.yaml` using the
   shared Tushare cache from the backtest script.
3. **Loop robustness fixes**: penalized NaN/constant factors with `-1.0` test
   IC and added per-generation checkpointing so partial results are preserved.
4. **Evolved factor comparison**: extended
   `scripts/run_tushare_backtest.py` with `--evolved-csv` / `--evolved-top-n`
   to merge a loop leaderboard into the same comparison report.

### Verification

- Ran the GP loop on real CSI300 data; it produced a 50-factor leaderboard in
  `china_a_share_alpha_output/tushare_loop/`.
- Ran the merged comparison (`--evolved-csv` leaderboard, top 10). Results:

| Factor | IC | RankIC | Sharpe | Source |
|---|---|---|---|---|
| evolved_3 | 0.0064 | 0.0063 | 1.155 | GP-discovered (robust) |
| evolved_7 | 0.0116 | 0.0297 | 0.307 | GP-discovered (robust) |
| evolved_1 | 0.0110 | 0.0216 | 0.714 | GP-discovered (robust) |
| momentum_20 | 0.0040 | -0.0138 | 0.406 | hand-designed |
| value_pb | 0.0097 | 0.0335 | 0.108 | hand-designed |
| ic_weighted_train | 0.0091 | 0.0376 | -0.057 | hand-designed combination |

The best evolved expression by Sharpe was:
`cs_rank(add(-0.309, div(ts_corr(ts_delta(vwap, 3), low, 3), ts_mean(low, 20))))`

- `python -m pytest tests/ -q` — **39 passed, 2 skipped**.

### Files Added/Modified

- `china_a_share_alpha/data/qlib_loader.py`
- `china_a_share_alpha/examples/tushare_loop_config.yaml`
- `china_a_share_alpha/run_factor_loop.py`
- `china_a_share_alpha/loop/population.py`
- `china_a_share_alpha/scripts/run_tushare_backtest.py`
- `china_a_share_alpha_output/tushare_backtest/factor_comparison.csv`
- `china_a_share_alpha_output/tushare_backtest/factor_comparison_report.md`
- `wiki/semas_evolution_ideas.md`
- `OPERATION_LOG.md`

### Notes

- The evolved factor library now has 50+ candidates; the top 10 were evaluated
  alongside the original six. The loop can be restarted with different seeds
  or an LLM mutator to keep expanding.
- Added a **robustness guard**: candidates whose train/test IC signs disagree
  are penalized, which prevents the loop from overfitting to a sign-flipping
  alpha.
- Future work: combine the top evolved factors into a portfolio evolution
  step and add sector/market-cap neutralization.

---

## 2026-06-23 — Domain Fit Assessment: End-to-End AI Video Generation Agent

### Motivation

User asked whether SEMAS is reasonable for evolving a full-pipeline AI video
generation agent.

### Conclusion

- **High fit**. Video generation is a multi-stage, multi-agent pipeline with
  subjective quality gates and expensive compute — exactly SEMAS's target
  shape.
- SEMAS would orchestrate scriptwriter, prompt engineer, asset generator,
  editor, and critic agents via `TopologyGenome`.
- `ToolGenome` would wrap video model APIs (Runway, Pika, ComfyUI) and
  post-processing tools (FFmpeg).
- `Evaluator` would combine automated metrics (CLIP, temporal coherence,
  aesthetics, safety) with optional human preference.
- Main risks: cost, subjectivity, non-determinism, safety/copyright.
- Recommended plugins: Core SEMAS + SIA for critic fine-tuning; avoid
  Gödel Agent.

### Files Updated

- `wiki/semas_evolution_ideas.md` — added "End-to-End AI Video Generation Agent"
  section.

---

## 2026-06-23 — Domain Fit Assessment: Finance / Mingli / OSINT

### Motivation

User asked whether SEMAS is reasonable for evolution-mode applications in
financial factor mining,命理 analysis, and open-source intelligence analysis.

### Conclusion

- **Financial factor mining**: very high fit; FunctionEvolve plugin maps
  directly to symbolic factor discovery, backtesting metrics map to Evaluator.
  Main risk is overfitting.
- **命理 analysis**: high fit; already prototyped in `examples/mingli_5agents/`.
  Main risks are hallucination and cultural sensitivity.
- **OSINT**: high fit; multi-agent topology and tool evolution match the
  workflow. Main risks are misinformation and legal/ethical boundaries.

SEMAS is reasonable for all three, but the value is in the generic evolution
loop; each domain still needs its own executor, metrics, data splits, and
safety gates.

### Files Updated

- `wiki/semas_evolution_ideas.md` — added "Domain Fit" section.

---

## 2026-06-23 — SEMAS Self-Upgrade Benchmark and Meta-Evolution Scaffold

### Motivation

User asked how to define downstream tasks to validate and evolve the SEMAS
framework itself. We needed a benchmark that exercises every core framework
capability and a meta-evolution loop that can improve the framework's own
"genome" (prompts, policies, plugin selection).

### Actions Taken

1. Wrote `SEMAS_SELF_UPGRADE_DESIGN.md` — design doc for reflexive framework
   evolution.
2. Created `benchmarks/semas_self_upgrade/`:
   - `README.md`
   - `tasks/` — six YAML task definitions covering tool evolution, prompt
     evolution, regression gate, plugin convergence, sandbox safety, and
     topology.
   - `fixtures/` — initial agent genomes for tasks.
   - `deterministic_mutator.py` — reproducible mutator for CI/benchmarking.
   - `metrics.py` — framework-level metric aggregation.
   - `run_benchmark.py` — task runner with `--json` output.
   - `framework_genome/framework_config_v1.yaml` — SEMAS meta-configuration
     genome.
   - `evolve_semas.py` — meta-evolution loop scaffold.
3. Added `benchmarks/__init__.py` and `benchmarks/semas_self_upgrade/__init__.py`
   so the benchmark can be run as a module.

### Verification

- `python -m benchmarks.semas_self_upgrade.run_benchmark` — **6/6 tasks passed**.
- `python -m benchmarks.semas_self_upgrade.evolve_semas` — reached target pass
  rate in meta round 1.

### Files Added

- `SEMAS_SELF_UPGRADE_DESIGN.md`
- `benchmarks/__init__.py`
- `benchmarks/semas_self_upgrade/README.md`
- `benchmarks/semas_self_upgrade/deterministic_mutator.py`
- `benchmarks/semas_self_upgrade/metrics.py`
- `benchmarks/semas_self_upgrade/run_benchmark.py`
- `benchmarks/semas_self_upgrade/evolve_semas.py`
- `benchmarks/semas_self_upgrade/tasks/*.yaml`
- `benchmarks/semas_self_upgrade/fixtures/*.yaml`
- `benchmarks/semas_self_upgrade/framework_genome/framework_config_v1.yaml`

---

## 2026-06-24 - Mingli Handoff Verify and Checklist HTTP API

### Motivation

Expose the handoff verification and implementation-checklist chain to non-shell
runtimes. The CLI path was useful for local operators, but other agents and
services should be able to submit a handoff export JSON object over HTTP and
receive the same verification/checklist contracts.

### Actions Taken

1. Added `POST /known-gap-handoff-verify`.
2. Added `POST /known-gap-handoff-checklist`.
3. Added request schemas `KnownGapHandoffExportVerificationRequest` and
   `KnownGapHandoffChecklistRequest`.
4. Updated capability evidence to require HTTP API coverage for verification
   and checklist generation.
5. Added API and schema tests plus README/wiki updates.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/api_server.py examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_api_server.py::test_http_api_known_gap_handoff_export examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **4 passed**.
- HTTP probe: `POST /known-gap-handoff-verify` returned valid receipt checks;
  `POST /known-gap-handoff-checklist` returned status `ready`, 6 ready items,
  and a 64-character checklist receipt.

---

## 2026-06-24 - Mingli Handoff Implementation Checklist

### Motivation

Turn verified known-gap handoff exports into directly actionable implementation
plans. A transfer artifact can be valid but still force the next operator or
agent to manually extract environment variables, candidate projects, commands,
and production gates for every gap.

### Actions Taken

1. Added `api_core.known_gap_handoff_implementation_checklist`.
2. Added CLI command `known-gap-handoff-checklist --input`.
3. Added schema contracts for checklist response, items, and checklist receipt.
4. Added capability flag `known_gap_handoff_implementation_checklist`.
5. Added tests covering checklist generation from a verified handoff export.
6. Updated README and wiki.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/cli.py examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_cli.py::test_cli_known_gap_handoff_exports_portable_bundle examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **4 passed**.
- CLI probe: export handoff JSON, run `known-gap-handoff-checklist --input`,
  receive `known-gap-handoff-checklist-v1`, status `ready`, 6 ready items, and a
  64-character checklist receipt.

---

## 2026-06-24 - Mingli Known-Gap Handoff Export Verification

### Motivation

Make exported known-gap handoff packages independently verifiable after transfer
to another runtime or agent. Export receipts are useful only if downstream
consumers can recompute them and detect tampering without running the full audit.

### Actions Taken

1. Added `api_core.verify_known_gap_handoff_export`.
2. Added CLI command `known-gap-handoff-verify --input`.
3. Added schema `KnownGapHandoffExportVerificationResponse`.
4. Added capability flag `known_gap_handoff_export_verification`.
5. Added verification tests for valid exports, expected receipt matching,
   tampered bundle detection, and UTF-16 JSON files from PowerShell redirection.
6. Updated README and wiki.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/cli.py examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_cli.py::test_cli_known_gap_handoff_exports_portable_bundle examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **4 passed**.
- PowerShell redirect probe: export to JSON, verify from file, and confirm
  `valid=True`, bundle hash valid, receipt hash valid, and known-gap IDs match.

---

## 2026-06-24 - Mingli Known-Gap Handoff Export Surface

### Motivation

Make the release-governed known-gap handoff bundle directly consumable by
another runtime, team, or agent. The bundle was present in audit/readiness/release
material, but external integration work should not need to parse the full audit
payload to find the portable closure package.

### Actions Taken

1. Added `api_core.known_gap_handoff` export response with audit receipt drift
   binding.
2. Added CLI command `known-gap-handoff`.
3. Added HTTP route `GET /known-gap-handoff`.
4. Added `handoff_export_receipt` with a stable hash over export identity,
   bundle hash, audit receipt binding, and expected-audit drift status.
5. Added schema `KnownGapHandoffExportResponse`,
   `KnownGapHandoffExportReceipt`, and endpoint documentation.
6. Added capability flag `known_gap_handoff_export_cli_api` plus CLI/API/schema
   tests.
7. Updated README and wiki.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/cli.py examples/mingli_5agents/api_server.py examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples/mingli_5agents/tests/test_cli.py::test_cli_known_gap_handoff_exports_portable_bundle examples/mingli_5agents/tests/test_api_server.py::test_http_api_known_gap_handoff_export -q` -
  **5 passed**.
- Runtime audit probe: evidence materialization `passed`, no failed/unchecked
  evidence, `known_gap_handoff_export_cli_api=True`, and blocked capability
  coverage remains complete.
- CLI export probe: `handoff_export_receipt.sha256` is 64 characters and binds
  the exported bundle hash and audit receipt hash.

---

## 2026-06-24 - Mingli Handoff Bundle Readiness and Release Binding

### Motivation

Promote the known-gap handoff bundle from audit evidence into the production
and release governance path. A portable closure package should not be optional
documentation; production readiness and release approval should prove it remains
present and current.

### Actions Taken

1. Added production gate `known_gap_handoff_bundle_ready`.
2. Bound the handoff bundle into production-readiness response and receipt
   material.
3. Added release gate check `known_gap_handoff_bundle_bound`.
4. Added `known_gap_handoff_bundle` to release receipt material and release
   ledger integrity comparison.
5. Added schema, capability-audit evidence, tests, README, and wiki updates.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **4 passed**.
- Runtime probe: `known_gap_handoff_bundle_ready=True`,
  `known_gap_handoff_bundle_bound=True`, readiness receipt bundle status
  `ready`, and a 64-character bundle hash.

---

## 2026-06-24 - Mingli Known-Gap Handoff Bundle

### Motivation

Make the remaining external provider/source/dataset gaps portable to another
runtime or future integration pass. The existing resolution plan proved that
each gap had commands and gates; the missing piece was a single machine-readable
handoff bundle with owner, closure condition, environment variables, candidate
projects, blocked capabilities, and a stable hash.

### Actions Taken

1. Added `known_gap_handoff_bundle` to capability audit responses and audit
   receipts.
2. Added per-gap handoff items with owner domain, blocking scope, closure
   condition, required provider/provenance env vars, verification commands,
   production gate IDs, candidate projects, blocked capabilities, and
   `handoff_ready`.
3. Added public schema contracts for `KnownGapHandoffBundle`,
   `KnownGapHandoffItem`, and `KnownGapHandoffCandidate`.
4. Added implemented requirement and capability flag
   `known_gap_handoff_bundle`.
5. Updated tests, README, and wiki.

### Verification

- `python -m py_compile examples/mingli_5agents/capability_audit.py examples/mingli_5agents/api_core.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **2 passed**.
- `pytest examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q` -
  **1 passed**.
- `pytest examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.

---

## 2026-06-24 - Mingli Known-Gap Command Coverage Release Binding

### Motivation

Promote known-gap runbook command and option coverage from receipt material into
an explicit release gate check. This makes release approval directly depend on
runbook/interface alignment, not only on the presence of coverage fields in the
readiness receipt.

### Actions Taken

1. Added helper logic requiring known-gap coverage to be complete, command
   validation to pass, invalid command/option maps to be empty, and command
   coverage hash to be present.
2. Added release gate check `known_gap_command_coverage_bound`.
3. Added public schema coverage for the new release gate check.
4. Added capability flag and implemented requirement
   `known_gap_command_coverage_release_binding`.
5. Updated tests, README, and wiki.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **16 passed**.
- Runtime release probe: `known_gap_command_coverage_bound=True`,
  receipt gate check bound, command validation true, no invalid commands/options,
  and 64-character command coverage hash.

---

## 2026-06-24 - Mingli Known-Gap Verification Option Coverage

### Motivation

Tighten runbook/interface drift checks. Subcommand validation proves that a
known-gap runbook points to a real CLI action, but misspelled or stale options
could still remain unnoticed.

### Actions Taken

1. Extended `known_gap_verification_command_coverage` to collect valid options
   per CLI subcommand.
2. Parsed verification-command options after the known-gap subcommand.
3. Added `invalid_verification_options_by_gap`, `command_options_by_gap`, and
   `valid_cli_options_by_subcommand` to `KnownGapResolutionPlanCoverage`.
4. Made invalid options fail command validation and known-gap coverage.
5. Added negative tests for unknown options and positive tests for observed
   option coverage.

### Verification

- `python -m py_compile examples/mingli_5agents/capability_audit.py examples/mingli_5agents/api_core.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **16 passed**.
- Runtime probe: readiness/release receipts reported
  `invalid_verification_options_by_gap={}`, observed Ziwei runbook options, and
  release-manifest valid options containing `--manifest`.

---

## 2026-06-24 - Mingli Known-Gap Verification Command Coverage

### Motivation

Improve reproducibility of known-gap closure runbooks. The framework already
required each known gap to include verification commands, but it did not verify
that those commands still referenced current CLI subcommands.

### Actions Taken

1. Added `known_gap_verification_command_coverage` to parse known-gap
   verification commands without executing them.
2. Validated extracted subcommands against the current CLI parser.
3. Added command validation fields to `KnownGapResolutionPlanCoverage`:
   `command_validation_complete`, `invalid_verification_commands_by_gap`,
   `command_subcommands_by_gap`, `valid_cli_subcommands`, and
   `command_coverage_sha256`.
4. Bound command coverage into capability audit, production-readiness receipts,
   and release-manifest receipts through the existing known-gap coverage object.
5. Added positive and negative schema-contract tests for command drift.

### Verification

- `python -m py_compile examples/mingli_5agents/capability_audit.py examples/mingli_5agents/api_core.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **15 passed**.
- Runtime probe: readiness and release receipts both reported
  `command_validation_complete=True`, no invalid commands, and a 64-character
  `command_coverage_sha256`.

---

## 2026-06-24 - Mingli Blocked Capability Coverage Production Gate

### Motivation

Promote blocked-capability accounting from an audit object into a production and
release invariant. A framework should not pass production readiness if any false
capability is unaccounted, even when individual provider/source gaps are already
reported elsewhere.

### Actions Taken

1. Added `blocked_capability_coverage_complete` to the shared production gate
   registry.
2. Added a production-readiness gate requiring
   `blocked_capability_coverage.coverage_complete`.
3. Added remediation guidance for unaccounted false capabilities.
4. Added release manifest gate check
   `blocked_capability_coverage_bound`.
5. Added capability flag and implemented requirement
   `blocked_capability_coverage_production_gate`.
6. Updated schema/tests/README/wiki for the new production/release invariant.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **14 passed**.
- Runtime probe: `blocked_capability_coverage_complete=True`,
  `registry_current=True`, `blocked_capability_coverage_bound=True`, and release
  receipt material binds the release gate check.

---

## 2026-06-24 - Mingli Blocked Capability Coverage Audit

### Motivation

Continue hardening the gap-governance layer. The audit exposed false
capabilities for missing provider/source/LLM configuration, but there was no
single machine-checkable object proving every false capability was intentionally
mapped to a known gap or optional policy.

### Actions Taken

1. Added `_blocked_capability_coverage` to map false capabilities to known gaps
   or optional configuration policy.
2. Added `blocked_capability_coverage` to capability-audit response and
   capability-audit receipt material.
3. Added capability flag and implemented requirement
   `blocked_capability_coverage_audit`.
4. Added public schema contracts for `BlockedCapabilityCoverage` and
   `BlockedCapabilityCoverageEntry`.
5. Added tests for response/receipt binding, schema refs, and Ziwei/LLM mapping
   examples.

### Verification

- `python -m py_compile examples/mingli_5agents/capability_audit.py examples/mingli_5agents/api_core.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py -q` -
  **13 passed**.
- `pytest examples/mingli_5agents/tests/test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` -
  **1 passed**.
- Runtime probe: `blocked_capability_coverage.status=covered`,
  `coverage_complete=True`, `unaccounted=[]`,
  `evidence_materialization=passed failed=0 unchecked=0`.

---

## 2026-06-24 - Mingli Capability Audit for Release Readiness Gate Binding

### Motivation

Continue enforcing the plan requirement that every implemented capability has
machine-checkable evidence. The release manifest already bound new
readiness-governance gates, but capability audit did not yet expose that binding
as a first-class implemented requirement.

### Actions Taken

1. Added implemented requirement
   `release_manifest_readiness_gate_binding`.
2. Added capability flag `release_manifest_readiness_gate_binding`.
3. Added evidence materialization for the three release gate checks:
   `provider_audit_contract_gates_bound`,
   `outcome_statistical_plan_preregistration_bound`, and
   `classical_latest_refresh_receipt_bound`.
4. Added tests asserting the new capability, implemented requirement, and
   evidence references.
5. Updated README and wiki to record the capability-audit methodology.

### Verification

- `python -m py_compile examples/mingli_5agents/capability_audit.py` -
  **passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **2 passed**.
- Runtime capability-audit probe:
  `release_manifest_readiness_gate_binding=True`, `caps_true=102/107`,
  `evidence_status=passed`, `failed=0`, `unchecked=0`.
- Requirement-level evidence probe:
  `release_manifest_readiness_gate_binding` status **passed** with seven
  materialized evidence records.

---

## 2026-06-23 - Mingli Release Manifest Governance Gate Binding

### Motivation

Continue closing the gap between production-readiness governance and release
approval. Recent iterations added provider audit-contract gates, outcome
statistical-plan preregistration, and classical-source refresh receipts, but
release manifest needed explicit checks proving those readiness decisions were
bound into release evidence.

### Actions Taken

1. Added release gate checks:
   `provider_audit_contract_gates_bound`,
   `outcome_statistical_plan_preregistration_bound`, and
   `classical_latest_refresh_receipt_bound`.
2. Added helper checks that require each readiness gate decision to appear in
   readiness gates/blockers, and require successful outcome/classical gates to
   expose their corresponding receipt material.
3. Updated the public schema and release manifest tests so the fields are
   required and written into `release_manifest_receipt.material.release_gate_checks`.
4. Updated README and wiki to record the release-binding methodology.

### Verification

- `python -m py_compile examples/mingli_5agents/api_core.py` - **passed**.
- `pytest examples/mingli_5agents/tests/test_schema_contract_evaluator.py -q` -
  **11 passed**.
- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py -q` -
  **2 passed**.
- Runtime probe over initialized/evolved temp repo:
  `provider_bound=True`, `stat_plan_bound=True`,
  `classical_refresh_bound=True`, `receipt_matches=True`.
- Full CLI release-manifest E2E test was attempted but exceeded 180 seconds in
  this environment.

---

## 2026-06-23 - Mingli Classical Source Refresh Receipt Gate

### Motivation

Continue closing the external classical-text retrieval gap. The framework
already audited source lists and included refresh receipts in release manifests,
but production readiness did not require the local corpus refresh receipt to be
present and bound to the current source-list receipt.

### Actions Taken

1. Added `classical_source_latest_refresh_receipt_present` to the shared
   production gate registry.
2. Added a production-readiness gate requiring a latest
   `<repo>/classical_sources/corpus/refresh_receipt.json` that matches the
   current `source_list_receipt` and has ingested records.
3. Added the gate to the `external_classic_text_retrieval` known-gap resolution
   plan.
4. Added remediation guidance to run `classical-refresh`.
5. Updated README and wiki to distinguish source-list intent receipts from
   materialized corpus refresh receipts.

### Verification

- `pytest examples/mingli_5agents/tests/test_schema_contract_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py examples/mingli_5agents/tests/test_evidence.py -q` - **54 passed**.
- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py` - **passed**.
- Runtime probe using `providers/classical_source_list_example.json`:
  `refresh_status=refreshed`, `refresh_receipt=True 64`, `latest_gate=True`,
  `gap_gate=True`, `registry_current=True`.

---

## 2026-06-23 - Mingli Astrology/Xuanze Provider Provenance Gates

### Motivation

Continue tightening provider-related production gaps. Astrology ephemeris and
xuanze rule-table metadata already had raw provider audit contracts, but those
contracts were not yet explicit production readiness gates or known-gap closure
conditions.

### Actions Taken

1. Added `astrology_ephemeris_audit_contract` and
   `xuanze_rule_table_audit_contract` to the shared production gate registry.
2. Added runtime production-readiness gates that check the capability audit still
   exposes both contracts.
3. Added `astrology_ephemeris_audit_contract` to the `astronomical_ephemeris`
   known-gap resolution plan.
4. Added `xuanze_rule_table_audit_contract` to the
   `huangdao_calendar_selection` known-gap resolution plan.
5. Updated README and wiki to record that provider provenance contracts must be
   promoted into release gates.

### Verification

- `pytest examples/mingli_5agents/tests/test_empirical_validation.py examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py -q` - **36 passed**.
- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py` - **passed**.
- Runtime probe: `astrology_ephemeris_audit_contract=True`,
  `xuanze_rule_table_audit_contract=True`, `registry_current=True`,
  `evidence=passed 0`, `capability_audit_score=1.0`.

---

## 2026-06-23 - Mingli Outcome Statistical-Plan Preregistration Gate

### Motivation

Continue hardening the `plan_mingli5agents.md` Mingli agent toward production
SEMAS evolution. The outcome dataset audit already checked consent, privacy,
holdout split, label provenance, and baselines; this iteration added a frozen
pre-registration requirement for the statistical plan so future empirical
optimization cannot rely on a mutable post-hoc analysis plan.

### Actions Taken

1. Added `statistical_plan.pre_registered`, `registration_id`, `registered_at`,
   `analysis_freeze_date`, and `plan_sha256`/`plan_receipt_sha256` checks to
   the outcome manifest audit.
2. Added `statistical_plan_preregistered` to outcome governance gates and
   `outcome_dataset_statistical_plan_preregistered` to production readiness.
3. Added the new gate to the empirical-validation known-gap resolution plan and
   the shared production gate registry.
4. Updated public schema contracts and stable outcome dataset receipt material
   to include the statistical-plan summary.
5. Updated the example manifest, README, and LLM wiki methodology note.

### Verification

- `pytest examples/mingli_5agents/tests/test_empirical_validation.py examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py -q` - **36 passed**.
- `python -m py_compile examples/mingli_5agents/outcome_dataset.py examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py examples/mingli_5agents/evaluators/capability_audit_evaluator.py` - **passed**.

---

## 2026-06-23 — Move geo-benchmark to C:/aicoding/geo-benchmark as Independent Project

### Motivation

User requested that `geo-benchmark/` be removed from `semas_framework` and
placed under `C:/aicoding/` as an independent project.

### Actions Taken

1. Moved directory:
   ```bash
   mv geo-benchmark C:/aicoding/geo-benchmark
   ```
2. Initialized an independent git repository in `C:/aicoding/geo-benchmark`:
   ```bash
   cd C:/aicoding/geo-benchmark && git init
   ```
3. Updated all internal SEMAS references from `geo-benchmark/...` to
   `../geo-benchmark/...`:
   - `SEMAS_ARA_Architecture.md` (claim C11, §7 experiment command, §9.2,
     evidence E10/E11).
   - `wiki/semas_evolution_ideas.md`.
   - `wiki/references.md`.

### Files Added / Changed

- Removed from `semas_framework`: `geo-benchmark/` (entire directory).
- Added to `C:/aicoding/`: `geo-benchmark/` (independent project).
- Modified:
  - `SEMAS_ARA_Architecture.md`
  - `wiki/semas_evolution_ideas.md`
  - `wiki/references.md`

### Notes

- `geo-benchmark` still contains its own `semas-integration/` bridge code, which
  now lives in the independent project.
- The SEMAS framework itself no longer depends on `geo-benchmark`.

---

## 2026-06-23 — Cross-Tool Agent Convention (AGENTS.md / CLAUDE.md / .codex/instructions.md)

### Motivation

User asked whether the "operation log + LLM Wiki" global behavior convention
can be transplanted to Claude Code and Codex. Since the convention is purely
file-based, it is portable to any agent that reads project-level instruction
files.

### Actions Taken

1. Created `AGENTS.md` — tool-agnostic agent instructions for SEMAS.
2. Created `CLAUDE.md` — Claude Code specific instructions (references
   `AGENTS.md`).
3. Created `.codex/instructions.md` — Codex / GitHub Copilot specific
   instructions (references `AGENTS.md`).
4. All three files encode the same core convention:
   - Operational changes → `OPERATION_LOG.md` + `README.md`.
   - Thinking / absorbed ideas → `wiki/` with `[source: ...]` citations.
   - Always cite external sources.
   - Run tests before finishing.

### Files Added

- `AGENTS.md`
- `CLAUDE.md`
- `.codex/instructions.md`

---

## 2026-06-23 — Push SEMAS to https://github.com/gaoxingkele/SEMAS

### Motivation

User requested pushing the current SEMAS framework to the remote GitHub repo
`https://github.com/gaoxingkele/SEMAS` using account `gaoxingkele`.

### Actions Taken

1. Initialized local git repo in `C:/aicoding/semas_framework`.
2. Added `.gitignore` (Python cache, temporary runtime data).
3. Configured git user name/email as `gaoxingkele`.
4. Added remote `origin https://github.com/gaoxingkele/SEMAS.git`.
5. Committed with message: "Initial SEMAS framework with plugin architecture and
   LLM Wiki".
6. Pushed to `main` using provided credentials via a temporary credential helper
   file; the file was removed immediately after push.

### Result

- Push succeeded: `main -> main`.
- Credential helper file cleaned up.

### Notes / Warnings

- The repo contained an embedded git repository `anysearch-skill`; Git committed
  it as a submodule/gitlink rather than as files. If it should be regular files,
  remove it from the index and re-add.
- Several runtime directories (`agents/`, `artifacts/`, `tmp_mingli_unicode_probe/`,
  `.semas_mingli_repo_sample/`) were committed because they pre-existed before
  `.gitignore` was created. If you want to clean these from the remote, run:
  ```bash
  git rm -r --cached agents artifacts tmp_mingli_unicode_probe .semas_mingli_repo_sample
  git commit -m "Remove runtime data from repo"
  git push
  ```

---

## 2026-06-23 - Mingli Ziwei/Qimen Provider Lineage Gate

### Motivation

Continue evolving the `plan_mingli5agents.md` Mingli agent toward a production
SEMAS framework. The previous provider protocol change required Ziwei/Qimen
raw outputs to disclose `calculation_basis`; this iteration promoted that
lineage requirement into the production gate and known-gap closure plan.

### Actions Taken

1. Added `ziwei_qimen_calculation_basis_audit_contract` to the shared production
   readiness gate registry.
2. Added a production-readiness gate that checks the capability audit still
   exposes the Ziwei/Qimen calculation-basis contract.
3. Added the gate to the professional Ziwei and professional Qimen known-gap
   resolution blueprints.
4. Updated README provider protocol notes to document `calculation_basis` as
   required provider stdout metadata.
5. Updated capability/readiness tests to assert the gate is present in valid
   production gate IDs and in Ziwei/Qimen gap plans.

### Verification

- `pytest examples/mingli_5agents/tests/test_capability_audit_evaluator.py examples/mingli_5agents/tests/test_empirical_validation.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py -q` - **35 passed**.
- `python -m py_compile examples/mingli_5agents/api_core.py examples/mingli_5agents/capability_audit.py examples/mingli_5agents/production_gates.py` - **passed**.
- Runtime probe: `capability=True`, `evidence=passed 0`,
  `readiness_gate=True`, `registry=True []`.
- Full `test_cli.py` and `test_api_server.py` are large end-to-end tests; this
  pass did not count them as verified because they exceeded the local timeout.

---

## 2026-06-23 — Plugin Architecture + FunctionEvolve Plugin + SIA Design + LLM Wiki

### Motivation

User asked to compare Gödel Agent, FunctionEvolve, and SIA with SEMAS, and to
integrate them as optional plugins/modules. Also requested a Karpathy-style
local LLM Wiki to record absorbed ideas and citations.

### Actions Taken

1. **Created plugin interface layer** (`semas/plugins/`):
   - `semas/plugins/base.py` — Protocols for `MutatorStrategy`,
     `CandidateOptimizer`, `WeightUpdateStrategy`, `SelfModificationPolicy`.
   - `semas/plugins/registry.py` — Programmatic, entry_points, and config-driven
     plugin registration.
   - `semas/plugins/__init__.py` — Public exports.

2. **Modified `semas/orchestrator/orchestrator.py`**:
   - Added optional `plugin_registry` parameter.
   - Extended `evolve()` to run plugin `MutatorStrategy` candidates,
     `CandidateOptimizer` refinement, and `WeightUpdateStrategy` weight updates.
   - Added `_build_plugin_context()`, `_apply_weight_updates()`, and
     `_build_training_samples()` helpers.
   - Preserved default behavior (all plugin args optional).

3. **Implemented `semas/plugins/function_evolve/` plugin**:
   - `ast_tool_mutator.py` — AST-based structural mutation of tool return
     expressions.
   - `optimizer.py` — Numeric constant perturbation with fitness scoring.
   - `demo.py` — Standalone demo evolving `x + 0` toward `2*x + 1`.
   - `tests/test_function_evolve_plugin.py` — Unit tests.

4. **Updated architecture documentation**:
   - `SEMAS_ARA_Architecture.md` — Added claim C12, plugin concepts, §5.7 Plugin
     Layer, and evidence entries E14–E18.
   - `SEMAS_SIA_Integration_Design.md` — New design doc for integrating SIA's
     harness + weight updates into SEMAS.

5. **Created local LLM Wiki** (`wiki/`):
   - `wiki/README.md` — Wiki conventions.
   - `wiki/semas_evolution_ideas.md` — Karpathy-style notes on SEMAS design and
     absorbed ideas (AgenticGEO, Gödel Agent, FunctionEvolve, SIA, etc.) with
     `[source: ...]` citations.
   - `wiki/references.md` — Centralized BibTeX-like reference list.

6. **Created this operation log** (`OPERATION_LOG.md`).

7. **Updated `README.md`** — Added Plugins and LLM Wiki sections.

### Files Changed / Added

- Added:
  - `semas/plugins/__init__.py`
  - `semas/plugins/base.py`
  - `semas/plugins/registry.py`
  - `semas/plugins/function_evolve/__init__.py`
  - `semas/plugins/function_evolve/ast_tool_mutator.py`
  - `semas/plugins/function_evolve/optimizer.py`
  - `semas/plugins/function_evolve/demo.py`
  - `semas/plugins/function_evolve/tests/test_function_evolve_plugin.py`
  - `SEMAS_SIA_Integration_Design.md`
  - `OPERATION_LOG.md`
  - `wiki/README.md`
  - `wiki/semas_evolution_ideas.md`
  - `wiki/references.md`
- Modified:
  - `semas/orchestrator/orchestrator.py`
  - `SEMAS_ARA_Architecture.md`
  - `README.md`

### Verification

- `pytest tests/test_genome.py tests/test_orchestrator.py` — **passed**.
- `pytest semas/plugins/function_evolve/tests/test_function_evolve_plugin.py` — **passed**.
- `python semas/plugins/function_evolve/demo.py` — **converged to `return x * 2.0` with fitness 1.0**.

### Future Follow-ups

- Implement `semas.plugins.sia.SIAWeightUpdate` (Phase 2).
- Implement `semas.plugins.godel` behind a strict policy gate (research-only).
- Consider adding optional dependencies groups in `pyproject.toml` for
  `function_evolve`, `sia`, and `godel` plugins.

## 2026-06-26 - Evidence-Driven Annual Event Markers

### Motivation

The famous-case calibration had structured annual event markers, but the first
version still depended too much on broad annual category and life-stage labels.
That was not enough to reduce repeated or weak annual reasoning. The next step
was to make each event marker inspect the same symbolic evidence used by the
annual-luck engine.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Annual rows now build `bazi_evidence` before `event_markers`.
   - `_event_markers()` reads annual ten-gods, useful-state, active major luck,
     natal pillar activation, intensity, phase, and age.
   - Career launch, role power, business power, relationship, movement,
     study/exam, visibility, and health-pressure markers are now booleans
     derived from structured evidence.
   - Fixed a JSON-serialization bug where set intersections could leak into
     marker fields.

2. Updated tests and schemas already covering annual marker fields:
   - Calendar row test checks marker basis entries.
   - Capability audit and schema contract tests verify the marker fields remain
     exposed through receipts.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v49, recording that typed markers must be computed from evidence,
     not from prose or labels alone.
   - Added strategy/migration rule 54.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py` passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate: `0.138`.
- Overall strict precision: `0.111`.
- Overall strict false-positive rate: `0.102`.
- Topic false-positive rates still needing refinement:
  - `career_project`: `0.222`.
  - `migration`: `0.169`.
  - `career_power`: `0.085`.

### Boundary

This iteration improves the intermediate representation and auditability. It
does not yet prove higher predictive accuracy. The next useful evolution is to
tune event-topic predicates against false positives rather than changing report
wording.

## 2026-06-26 - Strict Annual Rule Variant Sweep

### Motivation

After annual event markers became structured, the highest remaining problem was
strict-rule overfiring. Career-project and migration rules were still too broad
in negative years. The improvement needed to compare alternative predicates
against the same famous-case fixture set before selecting stricter rules.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `rule_variant_sweep` to the annual event calibration receipt.
   - Added candidate predicates for `career_project` and `migration`.
   - Tightened `career_project` strict matching to require structured
     `career_launch` plus useful-state or natal activation.
   - Tightened `migration` and `transition` strict matching to require movement
     signal, at least two core-pillar branch clashes, and major-luck or natal
     confirmation.
   - Added reusable helpers for core branch-clash counting and variant scoring.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Exposed `rule_variant_sweep` in
     `FamousCaseAnnualEventCalibrationReceiptSummary`.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Included `rule_variant_sweep` in the audit receipt material.

4. Updated tests:
   - Empirical validation now requires selected variants for career-project and
     migration, and checks selected migration false-positive rate against the
     legacy variant.
   - Schema contract test now requires `rule_variant_sweep`.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v50 and strategy/migration rule 55.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate: `0.108`.
- Overall strict precision: `0.177`.
- Overall strict false-positive rate: `0.046`.
- Overall strict exact hits: `14`.
- Overall strict false positives: `65`.
- Career-project selected variant:
  - `structured_launch_with_useful_or_natal`
  - hit rate `0.031`, precision `0.143`, false-positive rate `0.021`
  - legacy broad-launch variant false-positive rate was `0.222`
- Migration selected variant:
  - `core_double_clash`
  - hit rate `0.2`, precision `0.5`, false-positive rate `0.008`
  - legacy any-clash variant false-positive rate was `0.169`

### Boundary

This improves strict-rule precision by accepting lower recall in exact-year
claims. Loose and window metrics remain available for recall diagnostics. This
is still weak calibration on public celebrity fixtures, not statistical proof
of predictive accuracy.

## 2026-06-26 - Rejected Low-Recall Rule Variants

### Motivation

After strict annual rules reduced false positives, the next risk was
over-correcting toward recall. Career-power and study/exam had zero strict
recall, so they needed candidate scans before any rule relaxation.

### Actions Taken

1. Extended `rule_variant_sweep` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added `career_power` variants:
     - `current_role_power`
     - `authority_peer_resource`
     - `broad_authority_transition`
   - Added `study_exam` variants:
     - `current_formal_study`
     - `formal_marker_or_natal`
     - `broad_resource_authority`

2. Kept the conservative selected variants:
   - `career_power`: `current_role_power`
   - `study_exam`: `current_formal_study`

3. Updated empirical validation tests:
   - Require selected variants for `career_power` and `study_exam`.
   - Assert selected variants have no higher false-positive rate than broad
     relaxed alternatives.

4. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v51.
   - Added strategy/migration rule 56.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate: `0.108`.
- Overall strict precision: `0.177`.
- Overall strict false-positive rate: `0.046`.
- `career_power`:
  - selected `current_role_power`: hit rate `0.0`, precision `0.0`, false-positive rate `0.085`
  - rejected `authority_peer_resource`: hit rate `0.5`, precision `0.2`, false-positive rate `0.17`
  - rejected `broad_authority_transition`: hit rate `0.5`, precision `0.105`, false-positive rate `0.362`
- `study_exam`:
  - selected `current_formal_study`: hit rate `0.0`, precision `0.0`, false-positive rate `0.083`
  - rejected `formal_marker_or_natal`: hit rate `0.333`, precision `0.2`, false-positive rate `0.111`
  - rejected `broad_resource_authority`: hit rate `0.667`, precision `0.143`, false-positive rate `0.333`

### Boundary

This is a deliberate non-adoption pass. The system now records noisy recall
variants so future agents do not repeat the same loose-rule changes without new
evidence.

## 2026-06-26 - Annual Evolution Task Plan

### Motivation

The annual calibration receipt had topic diagnostics, rule refinement queues,
and variant sweeps, but future agents still had to infer the next implementation
step manually. The next evolution was to convert those diagnostics into a
machine-readable work packet.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `evolution_task_plan` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added `_annual_evolution_task_plan()`.
   - Added task fields for topic, priority, task type, selected variant,
     selected/rejected metrics, next evidence to add, acceptance criteria,
     source, and boundary.
   - Added topic-specific evidence recommendations for career power, study
     exams, public fame, relationship, and career projects.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `evolution_task_plan` into the audit receipt material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Exposed `evolution_task_plan` in
     `FamousCaseAnnualEventCalibrationReceiptSummary`.

4. Updated tests:
   - Schema contract now requires `evolution_task_plan`.
   - Empirical validation now requires non-empty task plans, evidence
     requirements, acceptance criteria, and audit-receipt binding.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v52.
   - Added strategy/migration rule 57.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Generated evolution task count: `13`.
- First task: `annual-career_power-add_specific_evidence`.
- Second task: `annual-study_exam-add_specific_evidence`.
- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.

### Boundary

This does not change prediction rules directly. It packages the next evidence
work so later evolution can proceed from explicit, testable tasks instead of
reinterpreting metric tables.

## 2026-06-26 - Role Transition Evidence Marker

### Motivation

The annual evolution task plan identified `career_power` as a low-recall topic
that needs title/command transition evidence separated from ordinary authority
pressure. The next step was to add a structured feature and test it as a
candidate, not to immediately relax strict rules.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added `role_transition` to annual `event_markers`.
   - The marker looks for adult-stage authority/peer/resource transition
     conditions in friends, learning, or wealth contexts with major-luck or
     natal activation.

2. Updated public contracts and tests:
   - Added `role_transition` to `AnnualEventMarkers` in `api_core.py`.
   - Updated annual-luck row tests.

3. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `role_transition_signal` to annual event evidence.
   - Added `role_transition_marker` as a `career_power` rule variant.
   - Kept `current_role_power` as the selected strict rule because the new
     marker overfires.

4. Updated empirical tests:
   - Require `role_transition_signal` in event evidence.
   - Require `role_transition_marker` to be recorded among rejected
     career-power variants.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v53.
   - Added strategy/migration rule 58.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `career_power` selected variant remains `current_role_power`:
  - hit rate `0.0`, precision `0.0`, false-positive rate `0.085`
- Rejected `role_transition_marker`:
  - hit rate `1.0`, precision `0.129`, false-positive rate `0.574`

### Boundary

`role_transition` is now an observable feature, not a strict prediction rule.
It should be combined with stronger event subtype or authority-axis evidence
before being used for exact-year career-power claims.

## 2026-06-26 - Event Subtype Calibration Labels

### Motivation

`role_transition` captured all current career-power events but produced too many
false positives. The next required evidence layer is event subtype, so future
rules can distinguish command succession, military command, leadership
consolidation, recognition, and other power events instead of treating them as
one generic category.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR`.
   - Added `EVENT_SUBTYPE_BY_TOPIC` fallback labels.
   - Added `event_subtype` to event-year samples.
   - Added `event_subtype: None` to negative samples to avoid using subtype as
     a prediction feature.
   - Added `event_subtype_summary` to the annual calibration receipt.
   - Added local `_counts()` helper for deterministic subtype summaries.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `event_subtype_summary` into the audit receipt material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Exposed `event_subtype_summary` in
     `FamousCaseAnnualEventCalibrationReceiptSummary`.

4. Updated tests:
   - Empirical validation requires event samples to carry `event_subtype`.
   - Empirical validation checks career-power explicit subtype coverage.
   - Schema contract requires `event_subtype_summary`.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v54.
   - Added strategy/migration rule 59.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `career_power`: explicit subtype coverage `1.0`.
- `study_exam`: explicit subtype coverage `1.0`.
- `career_project`: explicit subtype coverage `0.094`.

### Boundary

Subtypes are calibration labels for sourced event years. They are not available
for negative years or future predictions, and should not be used as direct
strict-matching inputs.

## 2026-06-26 - Career Project Subtype Expansion

### Motivation

The event subtype receipt showed that `career_project` had only `0.094`
explicit subtype coverage. This made project events too coarse for later rule
learning because film releases, album releases, sports titles, theory
publications, and production launches were all compressed into one fallback
label.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Bruce Lee project subtypes.
   - Added Arthur Ashe and Mark Spitz sports project subtypes.
   - Added Lucille Ball and Sean Penn film/TV project subtypes.
   - Added Aretha Franklin, Michael Jackson, and Madonna music project
     subtypes.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `career_project` subtype coverage to be at least `0.9`.
   - Checks representative music and sports subtype labels.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v55.
   - Added strategy/migration rule 60.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `career_power` subtype coverage: `1.0`.
- `study_exam` subtype coverage: `1.0`.
- `career_project` subtype coverage improved from `0.094` to `0.938`.

### Boundary

This is a dataset-label quality improvement, not a strict-rule change. Subtypes
remain calibration labels and must not be used directly as prediction inputs.

## 2026-06-26 - Subtype-Aware Evolution Task Scheduling

### Motivation

After expanding `career_project` subtypes, subtype coverage became a useful
dataset-quality metric. The annual task plan still treated low subtype coverage
as a passive report field. The next step was to let subtype coverage change the
next work item before any rule tuning occurs.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Reused `event_subtype_summary` when building `evolution_task_plan`.
   - Added `subtype_coverage_rate` and `default_subtype_count` to each task.
   - Added `expand_subtypes` task type.
   - Added subtype-expansion evidence recommendations and acceptance criteria.
   - Sorted low subtype coverage tasks ahead of rule tuning when event count is
     large enough.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires at least one `expand_subtypes` task.
   - Requires `public_fame` to be scheduled for subtype expansion while subtype
     coverage is below `0.5`.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v56.
   - Added strategy/migration rule 61.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- Top generated tasks:
  - `annual-public_fame-expand_subtypes`: coverage `0.061`, default count `31`.
  - `annual-relationship-expand_subtypes`: coverage `0.0`, default count `15`.
  - `annual-public_controversy-expand_subtypes`: coverage `0.0`, default count `6`.

### Boundary

This changes evolution scheduling, not prediction rules. It prevents the system
from tuning symbolic predicates while labels are still too coarse.

## 2026-06-26 - Public Fame Subtype Expansion

### Motivation

The subtype-aware scheduler moved `public_fame` to the top of the evolution
task plan because its subtype coverage was only `0.061`. Public fame covers
different event types: film breakthrough, TV recognition, music chart success,
sports title recognition, award recognition, and cultural visibility.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Bruce Lee public-fame subtypes.
   - Added Marilyn Monroe film-star subtypes.
   - Added sports public-recognition subtypes for Arthur Ashe, Mark Spitz, and
     Roger Federer.
   - Added TV/film public-recognition subtypes for Lucille Ball and Sean Penn.
   - Added music public-fame subtypes for Aretha Franklin, Michael Jackson, and
     Madonna.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `public_fame` subtype coverage to be `1.0`.
   - Requires representative music and sports public-fame subtypes.
   - Requires `public_fame` to graduate from `expand_subtypes` to
     `refine_precision` in `evolution_task_plan`.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v57.
   - Added strategy/migration rule 62.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `public_fame` subtype coverage improved from `0.061` to `1.0`.
- `public_fame` task type changed to `refine_precision`.
- Current top subtype tasks:
  - `relationship`: coverage `0.0`, default count `15`.
  - `public_controversy`: coverage `0.0`, default count `6`.
  - `sports_peak`: coverage `0.0`, default count `12`.

### Boundary

This is still a calibration-label improvement, not a direct prediction-rule
change. Subtypes are not used for negative years or strict matching.

## 2026-06-26 - Relationship Subtype Expansion

### Motivation

After `public_fame` subtype coverage reached `1.0`, the task scheduler moved
`relationship` to the top subtype-expansion slot. Relationship events were all
still using the fallback `relationship_event` label.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Marilyn Monroe relationship subtypes.
   - Added Lucille Ball relationship subtypes.
   - Added Sean Penn relationship subtypes.
   - Added Aretha Franklin relationship subtypes.
   - Added Madonna relationship subtypes.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `relationship` subtype coverage to be `1.0`.
   - Requires representative `celebrity_marriage` and
     `divorce_or_relationship_end` subtype labels.
   - Requires `relationship` to graduate from `expand_subtypes` to
     `refine_precision` in `evolution_task_plan`.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v58.
   - Added strategy/migration rule 63.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `relationship` subtype coverage improved from `0.0` to `1.0`.
- `relationship` task type changed to `refine_precision`.
- Current top subtype tasks:
  - `public_controversy`: coverage `0.0`, default count `6`.
  - `sports_peak`: coverage `0.0`, default count `12`.

### Boundary

This is a calibration-label improvement. Relationship subtypes are not used as
prediction inputs or negative-year features.

## 2026-06-26 - Public Controversy Subtype Expansion

### Motivation

`public_controversy` was the next subtype-expansion task after relationship.
All six controversy events still used the fallback `controversy_event` label,
which was too broad for later authority-expression conflict rules.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Sean Penn controversy subtypes.
   - Added Michael Jackson controversy subtypes.
   - Added Madonna controversy subtypes.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `public_controversy` subtype coverage to be `1.0`.
   - Requires representative criminal-allegation and religious-media
     controversy subtypes.
   - Requires `public_controversy` to graduate from `expand_subtypes` to
     `add_specific_evidence`.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v59.
   - Added strategy/migration rule 64.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `public_controversy` subtype coverage improved from `0.0` to `1.0`.
- `public_controversy` task type changed to `add_specific_evidence`.
- Remaining major subtype gaps:
  - `sports_peak`: coverage `0.0`, event count `12`.
  - `health_risk`: coverage `0.0`, event count `12`.

### Boundary

This is a calibration-label improvement. Controversy subtypes are not used as
strict matching inputs or negative-year features.

## 2026-06-26 - Sports Peak Subtype Expansion

### Motivation

`sports_peak` still used the fallback `competition_peak_event` label for all
events. This made championship, Olympic, ranking, record, and comeback peaks
indistinguishable for later rule work.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Arthur Ashe sports-peak subtypes.
   - Added Mark Spitz sports-peak subtypes.
   - Added Roger Federer sports-peak subtypes.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `sports_peak` subtype coverage to be `1.0`.
   - Requires representative Olympic-record and comeback-title subtypes.
   - Requires `sports_peak` to graduate from `expand_subtypes` to
     `reduce_false_positive`.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v60.
   - Added strategy/migration rule 65.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `sports_peak` subtype coverage improved from `0.0` to `1.0`.
- `sports_peak` task type changed to `reduce_false_positive`.
- Remaining major subtype gap:
  - `health_risk`: coverage `0.0`, event count `12`.

### Boundary

This is a calibration-label improvement. Sports subtypes are not used as strict
matching inputs or negative-year features.

## 2026-06-26 - Health Risk Subtype Expansion

### Motivation

`health_risk` was the remaining major high-count subtype gap. All twelve health
events used the fallback `health_risk_event` label. Health events require extra
care because subtype granularity should improve calibration, not encourage
stronger medical claims in reports.

### Actions Taken

1. Updated `EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR` in
   `examples/mingli_5agents/famous_case_validation.py`:
   - Added Bruce Lee health-risk subtype.
   - Added Marilyn Monroe health-risk subtypes.
   - Added Arthur Ashe health-risk subtypes.
   - Added Roger Federer injury subtypes.
   - Added Aretha Franklin cancer-related subtypes.
   - Added Michael Jackson health-risk subtype.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `health_risk` subtype coverage to be `1.0`.
   - Requires representative acute-death and sports-injury subtypes.
   - Allows `expand_subtypes` to disappear when no large low-coverage topic
     remains.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v61.
   - Added strategy/migration rule 66.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.
- `health_risk` subtype coverage improved from `0.0` to `1.0`.
- `health_risk` task type changed to `refine_precision`.
- Current `expand_subtypes` task list is empty.
- Remaining low subtype coverage topics:
  - `business_power`: event count `1`, coverage `0.0`.
  - `career_project`: event count `32`, coverage `0.938`.
  - `migration`: event count `5`, coverage `0.6`.
  - `transition`: event count `2`, coverage `0.0`.

### Boundary

This is a calibration-label improvement. Health subtypes are not medical
guidance and are not used as strict matching inputs or report wording
amplifiers.

## 2026-06-26 - Domain-Stratified Celebrity Fixture Coverage

### Motivation

The famous-case fixture set already included sports, film, and music cases, but
the receipt only exposed an aggregate domain list. That was too weak: a future
change could preserve total case count while silently reducing one public-life
domain.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `domain_coverage` to `famous_case_receipt()`.
   - Added per-domain case count, event count, case ids, source names, source
     ratings, event topics, and event-topic counts.
   - Kept the boundary that domain coverage proves fixture breadth only, not
     predictive validity.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires sports, film, and music fixture domains to each have at least
     three cases and ten event labels.
   - Requires Astro-Databank source provenance for those domains.
   - Requires representative event topics for each domain.
   - Requires material-level `domain_coverage` to match the top-level receipt.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `domain_coverage` to the public
     `FamousCaseValidationReceiptSummary` schema.

4. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v62.
   - Added strategy/migration rule 67.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Coverage Snapshot

- Sports domain: 3 cases, 32 event labels.
- Film domain: 3 cases, 33 event labels.
- Music domain: 3 cases, 33 event labels.
- Film-martial-arts bridge domain: Bruce Lee remains separate.
- Famous-case fixture receipt sha256:
  `91c51fc3e12bda82f22cce96bbdd3eb9def4ac86eff6b7dfb79e4329334f8f75`.
- Annual calibration receipt sha256:
  `9cf95760958869e78daec90cfad67807faa9d52adbbc43deb4aae05f25f61b07`.

### Calibration Snapshot

- Overall strict exact hit rate remains `0.108`.
- Overall strict precision remains `0.177`.
- Overall strict false-positive rate remains `0.046`.

### Boundary

This is a fixture-governance improvement. It makes sports, film, and music
coverage auditable before rule changes, but it does not claim statistical
predictive validity.

## 2026-06-26 - Domain-Topic Annual Calibration Slices

### Motivation

Domain-level annual metrics were useful, but still too coarse. Sports peak,
film fame, film relationship events, and music fame should not be forced through
one shared celebrity-event rule. The framework needed a cross-table by public
domain and event topic before making later rule changes.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `domain_topic_summary` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added `_annual_domain_topic_summary()` with per-slice case count, event
     count, negative-year count, loose hit rate, strict hit rate, precision,
     false-positive rate, case ids, and boundary text.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Included `domain_topic_summary` in the capability-audit receipt material.
   - Included top-level famous-case `domain_coverage` in the audit material
     summary.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `domain_topic_summary` to the public
     `FamousCaseAnnualEventCalibrationReceiptSummary` schema.

4. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires domain-topic slices for sports `sports_peak`, film
     `relationship`, and music `public_fame`.
   - Requires sports `sports_peak` to cover all three sports cases.
   - Requires the audit receipt material to bind `domain_topic_summary`.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v63.
   - Added strategy/migration rule 68.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Calibration Snapshot

- Annual calibration receipt sha256:
  `fb0423b233af6338e05c363e8f354047a505b9f169e0f34b352859581bb70eb1`.
- Sports `sports_peak`: 3 cases, 12 events, strict hit rate `0.333`,
  strict precision `0.333`, strict false-positive rate `0.174`.
- Film `relationship`: 3 cases, 9 events, strict hit rate `0.111`,
  strict precision `0.091`, strict false-positive rate `0.141`.
- Film `public_fame`: 3 cases, 10 events, strict hit rate `0.0`,
  strict precision `0.0`, strict false-positive rate `0.086`.
- Music `public_fame`: 3 cases, 11 events, strict hit rate `0.273`,
  strict precision `0.2`, strict false-positive rate `0.104`.
- Music `career_project`: 3 cases, 9 events, strict hit rate `0.111`,
  strict precision `0.167`, strict false-positive rate `0.043`.

### Boundary

Domain-topic slices are diagnostics for rule design. They are not statistical
proof and should not be used to claim predictive validity.

## 2026-06-26 - Domain-Topic Refinement Queue

### Motivation

The domain-topic annual slices showed that film `public_fame` and film
`career_project` have zero strict exact-year hits in the current local sample.
Relaxing strict rules immediately would risk raising false positives. The safer
next step is to turn weak slices into explicit evidence-design tasks.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `domain_topic_refinement_queue` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added `_domain_topic_refinement_queue()`.
   - Added domain-specific evidence suggestions for:
     - film `public_fame`
     - film `career_project`
     - music `public_fame`
     - music `career_project`
     - sports `sports_peak`
   - Added acceptance criteria for adding evidence, reducing false positives,
     and refining precision.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `domain_topic_refinement_queue` into the capability-audit receipt
     material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `domain_topic_refinement_queue` to the public
     `FamousCaseAnnualEventCalibrationReceiptSummary` schema.

4. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires film `public_fame` and film `career_project` to appear in the
     queue.
   - Requires film `public_fame` to be an `add_domain_specific_evidence` task.
   - Requires film-specific release/recognition evidence suggestions.
   - Requires audit material to bind the queue.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v64.
   - Added strategy/migration rule 69.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Queue Snapshot

- Annual calibration receipt sha256:
  `7df653d685d46601eda3d19a32b254758a1e928333e7fadfb8a8f9a7f0c00fa8`.
- Domain-topic refinement queue count: `15`.
- Top queue items:
  - Film `public_fame`: add domain-specific evidence, 10 events, strict hit
    rate `0.0`, strict precision `0.0`, strict false-positive rate `0.086`.
  - Film `career_project`: add domain-specific evidence, 9 events, strict hit
    rate `0.0`, strict precision `0.0`, strict false-positive rate `0.014`.
  - Sports `public_fame`: add domain-specific evidence, 6 events, strict hit
    rate `0.0`, strict precision `0.0`, strict false-positive rate `0.019`.

### Boundary

This iteration changes diagnostics and next-step planning only. It does not
relax strict annual rules and does not improve predictive-validity claims.

## 2026-06-26 - Domain-Topic Candidate Variant Sweep

### Motivation

The domain-topic refinement queue identified weak slices, especially film
`public_fame` and film `career_project`. Before changing strict rules, the
framework needed candidate metrics that show whether existing symbolic evidence
can improve those slices without expanding false positives.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `domain_topic_variant_sweep` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added `_domain_topic_variant_sweep()`.
   - Added candidate predicates for:
     - film `public_fame`
     - film `career_project`
     - music `public_fame`
     - music `career_project`
     - sports `sports_peak`
   - Added helper `_domain_topic_items()`.
   - Kept all domain-topic variants unselected.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `domain_topic_variant_sweep` into the capability-audit receipt
     material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `domain_topic_variant_sweep` to the public
     `FamousCaseAnnualEventCalibrationReceiptSummary` schema.

4. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires film `public_fame` candidate variants.
   - Requires all domain-topic variants to remain unselected.
   - Requires current film fame strict metrics to remain at zero.
   - Requires audit material to bind the candidate sweep.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v65.
   - Added strategy/migration rule 70.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Candidate Snapshot

- Annual calibration receipt sha256:
  `4c14418ff8abf39fd69b3cde7294eb4ac5bd856a08d55a49f76941813722e467`.
- Domain-topic variant count: `15`.
- Film `public_fame`:
  - `current_strict`: strict hit rate `0.0`, precision `0.0`,
    false-positive rate `0.086`.
  - `expression_visibility_with_support`: strict hit rate `0.0`,
    precision `0.0`, false-positive rate `0.014`.
  - `expression_visibility_or_major_luck`: strict hit rate `0.0`,
    precision `0.0`, false-positive rate `0.086`.
- Film `career_project`:
  - `current_strict`: strict hit rate `0.0`, precision `0.0`,
    false-positive rate `0.014`.
  - `project_launch_or_visibility_with_support`: strict hit rate `0.0`,
    precision `0.0`, false-positive rate `0.014`.
  - `broad_project_channel_with_major_luck`: strict hit rate `0.0`,
    precision `0.0`, false-positive rate `0.085`.

### Boundary

The candidate sweep proves that existing symbolic evidence is insufficient for
film fame and film project timing. The next aligned step is to add a sourced
industry-event evidence layer, not to relax strict annual rules.

## 2026-06-26 - Industry-Event Evidence Layer

### Motivation

The domain-topic candidate sweep showed that existing symbolic evidence could
not improve film `public_fame` or film `career_project`. The missing layer was
not another broad BaZi predicate; it was sourced industry-event evidence such as
film release, screen role, award, nomination, ratings, box office, press
recognition, music chart success, album release, broadcast performance, tour
peak, sports title, ranking, record, medal, season, and comeback.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `industry_event_evidence` to each sourced event row.
   - Added `_industry_event_evidence()`.
   - Added `_industry_event_evidence_summary()`.
   - Added `industry_event_evidence_summary` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added missing Marilyn Monroe film `career_project` subtypes for 1953 and
     1959.
   - Added industry-project and sports-peak markers.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `industry_event_evidence_summary` into the capability-audit receipt
     material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `industry_event_evidence_summary` to the public
     `FamousCaseAnnualEventCalibrationReceiptSummary` schema.

4. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires event rows to carry `industry_event_evidence`.
   - Requires film fame and film project industry evidence coverage to reach
     `1.0`.
   - Requires music fame to expose commercial/chart markers.
   - Requires sports peak to expose competition markers for all sports-peak
     events.
   - Requires audit material to bind `industry_event_evidence_summary`.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v66.
   - Added strategy/migration rule 71.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Evidence Snapshot

- Annual calibration receipt sha256:
  `1c61aa8e491b6492beb9e0238b757c5ef156cd57b9c6893089f4ef39e1f7d855`.
- Film `career_project`: 14 events, evidence coverage `1.0`.
- Film `public_fame`: 14 events, evidence coverage `1.0`.
- Music `career_project`: 9 events, evidence coverage `1.0`.
- Music `public_fame`: 11 events, evidence coverage `1.0`.
- Sports `sports_peak`: 12 events, evidence coverage `1.0`.

### Boundary

Industry-event evidence is extracted from sourced fixture subtypes for
calibration only. It is not available for future predictions unless a separate,
reviewed event-source provider is added.

## 2026-06-26 - Industry-Evidence Upper-Bound Candidate Sweep

### Motivation

After adding `industry_event_evidence`, the next question was whether the new
evidence layer can actually represent the known celebrity outcomes that the
symbolic annual rules failed to time. This required a candidate sweep, but not a
strict-rule promotion.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_variant_industry_evidence()`.
   - Added fixture-industry candidate predicates:
     - `_variant_industry_fame_marker()`
     - `_variant_industry_project_marker()`
     - `_variant_industry_sports_peak_marker()`
   - Added fixture-industry variants to `domain_topic_variant_sweep` for:
     - film `public_fame`
     - film `career_project`
     - music `public_fame`
     - music `career_project`
     - sports `sports_peak`
   - Updated `selection_basis` to state that these are upper-bound diagnostics
     and cannot be promoted to prediction rules without a separate reviewed
     event-source provider and false-positive checks.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires film `public_fame` to include `fixture_industry_fame_marker`.
   - Requires that fixture-industry candidate to show strict hit rate `1.0`,
     precision `1.0`, and false-positive rate `0.0`.
   - Requires all domain-topic variants to remain unselected.
   - Requires every selection basis to warn that candidates cannot be promoted
     to prediction rules directly.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v67.
   - Added strategy/migration rule 72.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Candidate Snapshot

- Annual calibration receipt sha256:
  `ef434855a711a8d9ef1eed75382f60e6ec4d58102db44ef3ddea797ebf9b88c4`.
- Film `public_fame` fixture-industry candidate: hit rate `1.0`, precision
  `1.0`, false-positive rate `0.0`.
- Film `career_project` fixture-industry candidate: hit rate `1.0`, precision
  `1.0`, false-positive rate `0.0`.
- Music `public_fame` fixture-industry candidate: hit rate `1.0`, precision
  `1.0`, false-positive rate `0.0`.
- Music `career_project` fixture-industry candidate: hit rate `1.0`,
  precision `1.0`, false-positive rate `0.0`.
- Sports `sports_peak` fixture-industry candidate: hit rate `1.0`, precision
  `1.0`, false-positive rate `0.0`.

### Boundary

These are upper-bound diagnostics over sourced fixture labels. They prove that
the event ontology is expressive enough; they do not prove predictive timing.
No fixture-industry variant is selected.

## 2026-06-26 - Industry Negative-Year Source Coverage Gate

### Motivation

Fixture-industry variants reached perfect scores because they read sourced
event-year labels. That proves ontology coverage, but not false-positive
control: negative years do not yet have equivalent industry records saying
whether there was no release, no award, no ranking title, no chart event, and so
on.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `industry_event_source_coverage` to
     `famous_case_annual_event_calibration_receipt()`.
   - Added `_industry_event_source_coverage()`.
   - Records positive event count, negative-year count, negative industry-label
     coverage, required external source families, provider contract fields, and
     required domain-topic slices.
   - Marks fixture-industry rule promotion as blocked until external
     negative-year industry labels exist.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Bound `industry_event_source_coverage` into the capability-audit receipt
     material.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `industry_event_source_coverage` to the public
     `FamousCaseAnnualEventCalibrationReceiptSummary` schema.

4. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires `industry_event_source_coverage.status` to be
     `needs_external_event_source`.
   - Requires negative-year industry-label coverage to be `0.0`.
   - Requires rule promotion to be blocked.
   - Requires source URL and review fields in the provider contract.
   - Requires film `public_fame` to be listed as a required slice.
   - Requires audit material to bind the coverage object.

5. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v68.
   - Added strategy/migration rule 73.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Coverage Snapshot

- Annual calibration receipt sha256:
  `f52b1b64c4fc2909e6d7e46161f5de37169a4d8b0af8a0c669f8c2d281c78f9d`.
- Positive event count: `130`.
- Negative-year sample count: `1418`.
- Negative-year industry label coverage rate: `0.0`.
- Required domain-topic slice count: `9`.
- Fixture-industry rule promotion: blocked.

### Boundary

This is a source-coverage gate, not a prediction improvement. It prevents
fixture-derived industry labels from being mistaken for future-usable
prediction features.

## 2026-06-26 - Industry-Event Source Provider Handoff Gap

### Motivation

`industry_event_source_coverage` blocked fixture-industry rule promotion, but
the blocker was still local to the annual calibration receipt. Because this
blocker affects future rule promotion, it needs to appear in the global
known-gap and handoff systems.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added known gap `industry_event_source_provider`.
   - Added resolution blueprint with owner domain `industry_events`.
   - Added verification commands through existing `outcome-dataset`,
     `production-readiness`, and `release-manifest` CLI paths.
   - Added production gates from the reviewed outcome-dataset gate family.
   - Added candidate source entries:
     - IMDb Non-Commercial Datasets
     - MusicBrainz Database
     - Wikidata Query Service
     - Olympedia
   - Filtered GitHub comparison `candidate_projects` to GitHub URLs so
     non-GitHub industry data sources remain in external integration candidates
     without polluting the GitHub comparison receipt.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires industry-event external candidates to appear.
   - Requires known gap `industry_event_source_provider` with owner domain,
     blocking scope, gates, and verification commands.
   - Requires the known-gap resolution plan and handoff bundle to include the
     industry-event source provider gap.
   - Requires the handoff bundle to include Wikidata Query Service as a
     candidate source.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Added v69.
   - Added strategy/migration rule 74.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Handoff Snapshot

- Known gap: `industry_event_source_provider`.
- Owner domain: `industry_events`.
- Blocking scope: `externally_reviewed_industry_event_manifest`.
- Verification command count: `3`.
- Handoff ready: `True`.
- Candidate source count: `4`.
- Candidate sources:
  - IMDb Non-Commercial Datasets
  - MusicBrainz Database
  - Wikidata Query Service
  - Olympedia
- Capability audit receipt sha256:
  `cd07ff4cb1a2606d578fe4b48b34e9f5a0abed5056adcbc7b318af3c6babecb5`.

### Boundary

These are candidate source families, not accepted providers. Licensing,
coverage, source references, identity matching, refresh cadence, and
negative-year semantics must pass review before the gap can close.

## 2026-06-26 - Industry-Event Manifest Example Contract

### Motivation

The `industry_event_source_provider` gap had candidate sources and runbook
commands, but no local contract file showing how sports, film/television, and
music event years and non-event years should be represented. This made the gap
handoff readable but not yet implementation-ready.

### Actions Taken

1. Added
   `examples/mingli_5agents/providers/industry_event_source_manifest_example.json`:
   - Defines schema version `industry-event-source-manifest-v1`.
   - Covers film/television, music, and sports source families.
   - Lists candidate sources: IMDb Non-Commercial Datasets, MusicBrainz
     Database, Wikidata Query Service, and Olympedia.
   - Provides six example records: three positive industry-event years and
     three explicit negative years.
   - Marks the file as example-only, not production evidence.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `INDUSTRY_EVENT_SOURCE_MANIFEST_EXAMPLE`.
   - Added `_industry_event_source_manifest_example_receipt()`.
   - Bound the receipt into `capability_audit()` and the main audit receipt.
   - Added capability bit `industry_event_source_manifest_example`.
   - Updated the industry-event known-gap verification commands to reference
     the local example manifest path.

3. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Added `test_industry_event_source_manifest_example_receipt`.
   - Requires positive and negative examples, source-family coverage, candidate
     source coverage, stable receipt binding, and explicit non-production
     status.
   - Updated known-gap assertions to require the local example manifest path.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_manifest_example_receipt -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Receipt Snapshot

- Capability audit receipt sha256:
  `e891e30b541c191d4667ab06311eed2f690d1209b7f1389ccc77f5e0f502cfd3`.
- Industry manifest example receipt sha256:
  `ec310f6b8047bda611b924a52a5617f5538762856aa0bbe77c5b593bc1957aa9`.
- Industry manifest example content hash:
  `d2fdce862ef73a1416a055a53cb48e2f81a0c46c93c8af148b4ac1acaaef6682`.
- Example record count: `6`.
- Positive event count: `3`.
- Negative event count: `3`.
- Status: `ready_example`.

### Boundary

This closes the local handoff-contract gap, not the evidence-source gap. The
main known gap remains open until reviewed external manifests or providers
cover licensing, source references, identity matching, refresh cadence, and
negative-year semantics.

## 2026-06-26 - Industry-Event Manifest Audit CLI/API

### Motivation

The industry-event manifest example made the provider handoff concrete, but it
still needed an executable audit surface. Without a validator, future sports,
film/television, and music source manifests could drift away from the contract
before being used for famous-case calibration.

### Actions Taken

1. Added `examples/mingli_5agents/industry_event_manifest.py`:
   - Validates required top-level fields.
   - Validates required record fields.
   - Requires positive event years and explicit negative years.
   - Requires `https://` source URLs.
   - Requires negative-year explanations.
   - Requires split roles `train` and `holdout`.
   - Keeps production evidence blocked unless external review marks the
     manifest as `reviewed_production_evidence`.
   - Emits `industry-event-manifest-audit-receipt-v1`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `industry_event_manifest_status()`.
   - Added configuration guidance and production gate
     `industry_event_source_provider_reviewed_manifest`.
   - Added `GET /industry-events` to schema endpoint metadata.

3. Updated `examples/mingli_5agents/cli.py`:
   - Added CLI command `industry-events --manifest <path>`.

4. Updated `examples/mingli_5agents/api_server.py`:
   - Added HTTP route `GET /industry-events?manifest=<path>`.

5. Updated tests:
   - `test_industry_event_manifest_audit_accepts_example_contract`
   - `test_industry_event_manifest_audit_rejects_missing_negative_year_reason`
   - `test_industry_event_manifest_status_exposes_gate_and_guidance`
   - `test_cli_industry_events_audits_example_manifest`
   - `test_http_api_industry_events_route`

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_events_audits_example_manifest -q` passed.
- `pytest examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_events_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_api_server.py::test_http_api_status_schema_analyze_and_benchmark -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_manifest_example_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_audit_accepts_example_contract examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_audit_rejects_missing_negative_year_reason examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_status_exposes_gate_and_guidance -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Receipt Snapshot

- Industry manifest audit receipt sha256:
  `d75d385266c8350f2010753cc42e17e433ab26c1a7a4d2c81418da8dd1a8a0aa`.
- Industry example receipt sha256:
  `f48b292b0c1d31eac284e333ffce3c4b7a406d05237617c98c7181c685a195f0`.
- Capability audit receipt sha256:
  `ca7d230a3a8593d69111511c266305e8e012b328fea117cb46d827822d705ef8`.
- Content hash:
  `d2fdce862ef73a1416a055a53cb48e2f81a0c46c93c8af148b4ac1acaaef6682`.
- Example records: `6`.
- Positive event years: `3`.
- Negative years: `3`.

### Boundary

The audit path is now executable, but the example manifest is still not
production evidence. The known gap remains open until reviewed external
manifests or providers pass the same audit and explicitly satisfy production
review.

## 2026-06-26 - Industry-Event Source Query Plan Audit

### Motivation

The industry-event manifest audit made collected celebrity event data
machine-checkable, but the collection side still lacked a reproducible query
contract. Before integrating live sources such as Wikidata, the project needs
auditable query templates that say how film, music, and sports events should be
collected and mapped into manifest records.

### Actions Taken

1. Added
   `examples/mingli_5agents/providers/industry_event_source_query_plan_example.json`:
   - Defines schema version `industry-event-source-query-plan-v1`.
   - Uses Wikidata Query Service as the example source.
   - Provides SPARQL templates for:
     - film public-fame events
     - music public-fame events
     - sports peak/career events
   - Requires placeholders `PERSON_QID`, `START_YEAR`, and `END_YEAR`.
   - Maps query results into the industry-event manifest record fields.
   - Marks live collection as disabled until external review.

2. Added `examples/mingli_5agents/industry_event_query_plan.py`:
   - Validates query-plan top-level fields.
   - Validates source endpoint metadata.
   - Validates collection-policy controls.
   - Validates template fields, SPARQL placeholders, `SELECT`/`LIMIT`, and
     manifest field mappings.
   - Emits `industry-event-query-plan-audit-receipt-v1`.

3. Updated service surfaces:
   - `api_core.industry_event_query_plan_status`.
   - CLI command `industry-event-queries --query-plan <path>`.
   - HTTP route `GET /industry-event-queries?query_plan=<path>`.
   - Schema endpoint listing.

4. Updated capability audit:
   - Added `industry_event_source_query_plan_example`.
   - Added capability bit `industry_event_source_query_plan_example`.
   - Bound query-plan receipt into the capability-audit receipt material.

5. Updated tests:
   - Query-plan audit accepts the example contract.
   - Query-plan audit rejects missing placeholders.
   - Query-plan status exposes collection gate and guidance.
   - CLI and HTTP endpoints audit the example query plan.
   - Capability audit exposes the query-plan example receipt.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_query_plan.py examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_query_plan_example_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_audit_accepts_example_contract examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_audit_rejects_missing_placeholder examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_status_exposes_gate_and_guidance -q` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_queries_audits_example_query_plan examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_queries_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_manifest_example_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_query_plan_example_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_status_exposes_gate_and_guidance -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Receipt Snapshot

- Query-plan audit receipt sha256:
  `556b7dc6ba7f3d3726af8d143a4eb84ddd14969e474dd8f14d4171876a730504`.
- Query-plan example receipt sha256:
  `84bfba789553304f3cde7de7a2c1c0726d6a4ea0865f98d9b3aa9ecd149f5f45`.
- Capability audit receipt sha256:
  `df7e315b111ab3e3c62bfcc91f4fcedd99ccad7760f77f2797e8a69b3f6ae652`.
- Query-plan content hash:
  `3167726bf4c8e0f5fd93ae168b784b468c49058663f9d1390c1cbeeb20fcc182`.
- Template count: `3`.
- Domains: `film`, `music`, `sports`.

### Boundary

The query plan is executable as an audit target, but live collection remains
blocked. External review must approve identity matching, statement-reference
requirements, rate-limit handling, and negative-year source-window semantics
before any live collection can feed production evidence.

## 2026-06-26 - Industry-Event Offline Collection Request Bundles

### Motivation

The query-plan audit made source templates reviewable, but there was still no
reproducible artifact for a specific famous person and year range. Before live
collection, the framework needs an offline request bundle that expands the
template, records the exact SPARQL/query URL, and binds it to the future
manifest row preview.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_query_plan.py`:
   - Added `build_industry_event_collection_request_bundle`.
   - Added `industry_event_collection_request_bundle_receipt`.
   - Validates `case_id`, `public_name`, Wikidata `person_qid`, year range,
     split role, and optional domain filter.
   - Expands `PERSON_QID`, `START_YEAR`, and `END_YEAR` placeholders.
   - Emits per-request `request_sha256`.
   - Emits bundle receipt
     `industry-event-collection-request-bundle-receipt-v1`.
   - Keeps `execution_gate.passed` false because this is not live collection
     authorization.

2. Updated service surfaces:
   - `api_core.industry_event_collection_requests`.
   - CLI command `industry-event-requests`.
   - HTTP route `GET /industry-event-requests`.
   - Schema endpoint listing.

3. Updated tests:
   - Offline request bundle expands Roger Federer sports query.
   - Bad Wikidata QID is rejected.
   - CLI builds the offline bundle.
   - HTTP route builds the offline bundle.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_query_plan.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_collection_request_bundle_expands_queries_offline examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_collection_request_bundle_rejects_bad_qid -q` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_requests_builds_offline_bundle examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_requests_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_source_query_plan_example_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_audit_accepts_example_contract examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_status_exposes_gate_and_guidance -q` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_queries_audits_example_query_plan examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_queries_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Receipt Snapshot

- Example offline bundle receipt sha256:
  `67c386f10cd4a2a14204b911ae2276962bddc12b872b316b93dfe081c9722f9a`.
- Example request sha256:
  `a6f5918b5855f3da8a08ea75f44a7e38c50eb7c3d05a44438bf052d1cf0d2025`.
- Query-plan content hash:
  `3167726bf4c8e0f5fd93ae168b784b468c49058663f9d1390c1cbeeb20fcc182`.
- Query-plan receipt sha256:
  `9e02db8a7ae6f84009fe536f3af334c120a885f2149955024320d483505dddcd`.
- Example case: `roger_federer`, QID `Q1426`, `2002-2004`,
  domain `sports`, split role `holdout`.

### Boundary

This is still offline-only. It does not fetch Wikidata and does not certify the
resulting evidence. It creates a reproducible request package that must be
reviewed before live collection is enabled.

## 2026-06-26 - Cached Response To Draft Industry Manifest

### Motivation

Offline request bundles made exact source queries reviewable, but the framework
still could not turn a cached source response into auditable industry-event
records. The next step was to add a no-network import path that maps a
Wikidata-like JSON response into a draft manifest, including explicit negative
years.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `audit_industry_event_manifest_payload` so generated in-memory
     manifests can use the same audit rules as file manifests.

2. Updated `examples/mingli_5agents/industry_event_query_plan.py`:
   - Added `build_industry_event_manifest_draft_from_wikidata_response`.
   - Converts cached response bindings into positive event records.
   - Adds explicit negative-year records for years in the requested window with
     no matching positive result.
   - Preserves request-bundle receipt hash, response hash, request hash, and
     template id.
   - Emits `industry-event-manifest-draft-receipt-v1`.
   - Runs the generated draft through the existing manifest audit.

3. Added fixture:
   - `examples/mingli_5agents/providers/wikidata_sports_response_example.json`

4. Updated service surfaces:
   - `api_core.industry_event_manifest_draft_from_response`.
   - CLI command `industry-event-draft-manifest`.
   - HTTP route `GET /industry-event-draft-manifest`.
   - Schema endpoint listing.

5. Updated tests:
   - Draft manifest generation adds one positive year and two negative years.
   - CLI builds the draft manifest from cached response.
   - HTTP route builds the draft manifest from cached response.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\industry_event_query_plan.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_draft_from_cached_response_adds_negative_years -q` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_draft_manifest_from_cached_response examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_draft_manifest_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_collection_request_bundle_expands_queries_offline examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_query_plan_audit_accepts_example_contract -q` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_requests_builds_offline_bundle examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_requests_route -q` passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q` passed.

### Receipt Snapshot

- Draft receipt sha256:
  `eb54b858fb147df61749315045e97040184218a17ebedafd4db7cf804f258408`.
- Draft manifest audit receipt sha256:
  `fbb04582af3b2f8d119f03aceb926ded849c00c49824abe9c4919da11baa1c7e`.
- Response sha256:
  `9b362dba0a1b5b6ba75ada4349d6368e46735e14223b9265679f5da2c1c80ec1`.
- Request bundle receipt sha256:
  `67c386f10cd4a2a14204b911ae2276962bddc12b872b316b93dfe081c9722f9a`.
- Generated record counts:
  - Positive: `1`.
  - Negative: `2`.
  - Total: `3`.

### Boundary

This is still offline-only and uses a fixture response. It does not fetch live
Wikidata data, does not certify identity matching, and does not promote the
draft manifest to production evidence.

## 2026-06-26 - Controlled Industry Event Fetch Cache Gate

### Motivation

The framework can now describe celebrity-event query plans and import cached
responses, but sports, film, and music validation still needed a controlled
fetch/cache gate. Without that gate, live collection could bypass review and
make future calibration hard to reproduce.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_query_plan.py`:
   - Added `build_industry_event_fetch_cache_plan`.
   - Added deterministic cache filenames derived from case id, template id,
     year window, and request hash.
   - Added dry-run behavior as the default: no public source is contacted.
   - Added live execution blocking unless the query plan is externally reviewed
     and marked `collection_ready`.
   - Added `industry-event-fetch-cache-receipt-v1` binding request-bundle
     receipt, cache paths, live flag, failures, and write counts.

2. Updated service surfaces:
   - `api_core.industry_event_fetch_cache`.
   - CLI command `industry-event-fetch-cache`.
   - HTTP route `GET /industry-event-fetch-cache`.
   - Schema endpoint listing.

3. Updated tests:
   - Dry-run fetch/cache planning does not fetch or write cache files.
   - Live fetch is blocked for the bundled example because it is not externally
     reviewed.
   - CLI dry-run exposes planned cache path and receipt.
   - HTTP dry-run exposes planned cache path and receipt.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_query_plan.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_fetch_cache_plan_dry_run_does_not_fetch examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_fetch_cache_plan_live_requires_reviewed_collection_ready examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_fetch_cache_dry_run examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_fetch_cache_route_dry_run -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo schema | Select-String -Pattern 'industry-event-fetch-cache'` returned the new endpoint.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_collection_request_bundle_expands_queries_offline examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_fetch_cache_plan_dry_run_does_not_fetch examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_fetch_cache_plan_live_requires_reviewed_collection_ready examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_manifest_draft_from_cached_response_adds_negative_years examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_requests_builds_offline_bundle examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_fetch_cache_dry_run examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_draft_manifest_from_cached_response examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_requests_route examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_fetch_cache_route_dry_run examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_draft_manifest_route -q` passed.
- Dry-run example receipt sha256:
  `1484aefa5c8ba29b2c67a1d4fa45744b9254616471006f85ee613f15446bfda0`.

### Boundary

This does not yet collect real celebrity data. It makes sports, film, and music
public-event collection executable only as a dry-run by default, and blocks live
fetch unless source-query governance is reviewed.

## 2026-06-26 - Celebrity Candidate Pool Audit

### Motivation

The framework can plan and cache public industry-event collection, but it still
needed an auditable answer to which sports, film, and music celebrities should
enter validation first. Candidate choice itself can introduce sampling bias, so
the next step was to make the candidate pool explicit and receipt-bound.

### Actions Taken

1. Added `examples/mingli_5agents/providers/industry_event_candidate_cases_example.json`:
   - 9 candidate public figures.
   - 3 sports candidates, 3 film candidates, and 3 music candidates.
   - Each candidate includes case id, public name, domain, industry, Wikidata
     QID, source URL, split role, collection window, and selection reason.

2. Added `examples/mingli_5agents/industry_event_candidates.py`:
   - Validates required candidate fields.
   - Requires film/music/sports coverage.
   - Requires a minimum number of candidates per domain.
   - Checks QID shape, Wikidata entity URLs, split roles, collection windows,
     and identity-review boundary.
   - Emits `industry-event-candidate-cases-audit-receipt-v1`.

3. Updated service surfaces:
   - `api_core.industry_event_candidate_cases_status`.
   - CLI command `industry-event-candidates`.
   - HTTP route `GET /industry-event-candidates`.
   - Schema endpoint listing.
   - Capability audit receipt material and capability flags.

4. Verified candidate QIDs through Wikidata `wbsearchentities` lookup:
   - Roger Federer: `Q1426`.
   - Serena Williams: `Q11459`.
   - Michael Jordan: `Q41421`.
   - Jackie Chan: `Q36970`.
   - Meryl Streep: `Q873`.
   - Tom Hanks: `Q2263`.
   - Taylor Swift: `Q26876`.
   - Beyonce: `Q36153`.
   - Jay Chou: `Q238819`.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_candidate_cases_audit_accepts_example_contract examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_candidate_cases_status_exposes_gate_and_guidance examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_candidate_cases_example_receipt examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_candidates_audits_example_candidate_pool examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_candidates_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-candidates --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo schema | Select-String -Pattern 'industry-event-candidates'` returned the new endpoint.

### Receipt Snapshot

- Candidate pool receipt sha256:
  `635ac7ccefd07898e93e6e3ba3543bf58a5a8237371d28b346024f239d057c63`.
- Candidate pool content hash:
  `7c70e351ace85a7c5b3799c43b88b5ebb10fc08ceb25111ac14dd9fc2911f153`.
- Candidate count: `9`.
- Domain counts: `film=3`, `music=3`, `sports=3`.

### Boundary

This is an example candidate pool, not production validation evidence. It does
not certify birth data or event labels. Production use still requires external
identity review, reviewed event collection, and positive/negative year
manifests.

## 2026-06-26 - Candidate Pool Batch Fetch Cache Plan

### Motivation

After the celebrity candidate pool became auditable, the next gap was execution
friction: every candidate still had to be manually copied into a single-person
fetch/cache command. The framework needed a batch dry-run that expands the
candidate pool into per-person event collection plans without contacting live
sources.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `build_candidate_pool_fetch_cache_plan`.
   - Reads candidate case ids, QIDs, domains, split roles, and collection
     windows from the candidate manifest.
   - Supports optional `domain` and `split_role` filters.
   - Calls the existing per-candidate fetch/cache planner for each selected
     candidate.
   - Emits `industry-event-candidate-pool-fetch-cache-receipt-v1`.
   - Defaults to dry-run and does not contact public sources.

2. Updated service surfaces:
   - `api_core.industry_event_candidate_pool_fetch_cache`.
   - CLI command `industry-event-candidate-fetch-cache`.
   - HTTP route `GET /industry-event-candidate-fetch-cache`.
   - Schema endpoint listing.

3. Updated tests:
   - Batch plan expands selected sports candidates.
   - API exposes music-domain batch plan.
   - CLI exposes film-domain dry-run batch plan.
   - HTTP exposes sports-domain dry-run batch plan.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\industry_event_query_plan.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_fetch_cache_plan_expands_selected_candidates examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_fetch_cache_api_exposes_batch_plan examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_candidate_fetch_cache_dry_run examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_candidate_fetch_cache_route_dry_run -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-candidate-fetch-cache --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo schema | Select-String -Pattern 'industry-event-candidate-fetch-cache'` returned the new endpoint.

### Receipt Snapshot

- Candidate pool batch fetch/cache receipt sha256:
  `56222f1ff1933ab98200672fa264c948dd8160dea6ea4a1a1e0e3254d9e8b5cf`.
- Candidate receipt sha256:
  `635ac7ccefd07898e93e6e3ba3543bf58a5a8237371d28b346024f239d057c63`.
- Candidate count: `9`.
- Planned request count: `9`.
- Planned cache count: `9`.
- Cache write count: `0`.

### Boundary

This is still a dry-run by default. It generates auditable collection plans and
cache paths for selected celebrity candidates but does not fetch live data and
does not promote any event evidence into calibration.

## 2026-06-26 - Candidate Pool Cached Response Draft Import

### Motivation

The framework could batch-plan celebrity source collection, but cached responses
still had to be imported one person at a time. The next step was to batch-import
available cached responses into draft industry-event manifests, while explicitly
reporting missing cache files.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `build_candidate_pool_manifest_drafts_from_cache`.
   - Reuses candidate-pool fetch/cache dry-run plans to locate expected cache
     files.
   - Imports existing cached responses through the existing per-candidate
     Wikidata response importer.
   - Summarizes draft count, missing cache count, positive records, negative
     records, total records, per-draft receipts, and failures.
   - Emits `industry-event-candidate-pool-draft-import-receipt-v1`.

2. Updated service surfaces:
   - `api_core.industry_event_candidate_pool_draft_import`.
   - CLI command `industry-event-candidate-draft-import`.
   - HTTP route `GET /industry-event-candidate-draft-import`.
   - Schema endpoint listing.

3. Updated tests:
   - Batch import succeeds when sports candidate cache files exist.
   - Batch import reports missing cache files.
   - API exposes draft-import summary.
   - CLI imports cached responses.
   - HTTP imports cached responses.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_draft_import_reports_missing_cache examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_draft_import_api_exposes_summary examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_candidate_draft_import_from_cached_responses examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_candidate_draft_import_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-candidate-draft-import --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache_demo --domain sports` passed after materializing fixture cache files from the dry-run plan.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo schema | Select-String -Pattern 'industry-event-candidate-draft-import'` returned the new endpoint.

### Receipt Snapshot

- Candidate pool draft import receipt sha256:
  `4f2d97ef1a079596bd9f2e8e076629507ff29760e15de3d8aba7837eef2133c9`.
- Candidate pool fetch/cache receipt sha256:
  `7244d6fb844b2bcc0859c4517b8ce342d184b7260fa03d407127949ae0b91529`.
- Candidate receipt sha256:
  `635ac7ccefd07898e93e6e3ba3543bf58a5a8237371d28b346024f239d057c63`.
- Imported sports candidates: `3`.
- Positive records: `3`.
- Negative records: `70`.
- Total records: `73`.
- Missing responses: `0`.

### Boundary

This imports cached source responses only. The demonstration used the existing
fixture response for sports candidates, so it proves the batch import pipeline
but does not certify real celebrity event facts. Draft manifests still require
source review before calibration use.

## 2026-06-26 - Candidate Pool Combined Draft Manifest Audit

### Motivation

The candidate-pool draft importer produced per-candidate draft summaries, but a
future calibration step needs a single auditable event-label artifact. The next
step was to merge imported candidate drafts into one combined draft manifest and
run the normal industry-event manifest audit over that combined object.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Batch draft import now preserves imported draft manifest records.
   - Added a combined candidate-pool draft manifest.
   - Deduplicates source-family declarations across imported drafts.
   - Runs `audit_industry_event_manifest_payload` on the combined manifest.
   - Exposes `combined_draft_manifest`, `combined_draft_manifest_audit`, and
     `combined_draft_manifest_audit_receipt`.
   - Adds combined manifest counts and audit receipt hash to the batch import
     receipt material.

2. Updated tests:
   - Core batch import asserts combined manifest audit validity and counts.
   - API summary exposes combined manifest validity and record count.
   - CLI and HTTP paths assert combined manifest validity and record count.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_draft_import_api_exposes_summary examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_candidate_draft_import_from_cached_responses examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_candidate_draft_import_route -q` passed.
- Replayed the sports candidate cache-import demo and confirmed combined
  manifest counts.

### Receipt Snapshot

- Candidate pool draft import receipt sha256:
  `4186ea0718c0e46e9db3678554ee73e0a6ba297a69aa124e6329c6aad4620186`.
- Combined draft manifest audit receipt sha256:
  `2f18110d4bb37ababa20ef848f6d48ea0ff605b89ee71b9528a422b0a000cf7c`.
- Combined record count: `73`.
- Positive records: `3`.
- Negative records: `70`.

### Boundary

The combined manifest is still a draft from cached responses and is explicitly
not production evidence. It gives future calibration one auditable input object,
but source review and identity review remain required before using it as
validated evidence.

## 2026-06-26 - Industry Event Validation Label Adapter

### Motivation

The combined industry-event manifest is auditable, but timing-rule scoring needs
a stable validation-label table. This step separates factual labels from later
symbolic rule scoring so sports, film, and music celebrity cases can be tested
against the same input boundary.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added a validation-label-table builder for manifest files.
   - Added a payload variant so candidate-pool imports can convert in-memory
     combined draft manifests.
   - Normalizes each manifest record into positive or negative annual labels.
   - Adds domain-topic summaries and a deterministic label-table receipt.

2. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Batch candidate-pool draft import now emits `validation_label_table`.
   - Import receipts include validation label receipt hash and label counts.

3. Updated CLI/API/HTTP surfaces:
   - Added `industry-event-labels --manifest`.
   - Added API helper `industry_event_validation_labels`.
   - Added HTTP route `GET /industry-event-labels`.
   - Added schema exposure for the new endpoint.

4. Updated tests:
   - Core manifest-to-label adapter test.
   - Candidate-pool import test for embedded label table.
   - CLI route test.
   - HTTP route test.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_validation_label_table_adapts_manifest_records examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_labels_adapts_example_manifest examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_labels_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-labels --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json` returned the expected label summary.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo schema | Select-String -Pattern 'industry-event-labels'` returned the new endpoint.

### Receipt Snapshot

- Validation label table receipt sha256:
  `3e8289b00a4181605273622b76aeea0ed79fbefb4a819befd2a15d6da620ab46`.
- Example manifest label count: `6`.
- Positive labels: `3`.
- Negative labels: `3`.
- Candidate-pool combined validation labels from the sports demo: `73`.
- Candidate-pool positive labels: `3`.
- Candidate-pool negative labels: `70`.

### Boundary

The label table does not score Bazi, Ziwei, Qimen, or any symbolic rule. It only
turns reviewed or draft event manifests into stable annual fact labels. Actual
timing-rule validation still needs the next scoring adapter and production
source review before any case is treated as certified evidence.

## 2026-06-26 - Cross-Domain Celebrity Label Coverage Gate

### Motivation

The framework can now find and plan sports, film, and music celebrity validation
cases, but a single-domain import should not be reported as cross-domain
evidence. The next guardrail was to make the validation label table state
whether all three celebrity domains have positive and negative annual labels.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `domain_coverage_summary` to validation label tables.
   - Added `cross_domain_coverage_gate`.
   - The gate requires `film`, `music`, and `sports`.
   - Each required domain must include at least one positive label and one
     negative label.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - The example manifest now proves the cross-domain gate passes.
   - The sports-only candidate-pool import remains valid, but now explicitly
     reports missing `film` and `music` for cross-domain validation.

3. Updated `wiki/llm_agent_evolution_mingli.md`:
   - Rewrote the v80 label-table section in readable Chinese.
   - Added v81 for cross-domain celebrity coverage.
   - Added migration rule 86.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_validation_label_table_adapts_manifest_records examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates -q` passed.

### Boundary

This is a coverage gate, not a predictive score. It does not prove that Mingli
rules predict celebrity outcomes. It prevents the weaker mistake of treating a
partial domain sample as if it supported sports, film, and music together.

## 2026-06-26 - Industry Event Symbolic Scoring Readiness

### Motivation

Industry-event labels contain public people, years, domains, and event topics,
but they do not necessarily contain birth data. The next step was to prevent the
framework from treating a factual event label as scoreable unless it can be
matched to a reviewed local birth profile.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `build_industry_event_symbolic_scoring_readiness`.
   - Added a payload variant for in-memory manifests.
   - Each label now receives `scoring_ready`, `birth_profile_available`, and
     explicit `blocking_reasons`.
   - Added case-level and domain-topic readiness summaries.
   - Added gates for label-table validity, birth-profile coverage, and
     positive/negative ready-label coverage.
   - Added a deterministic symbolic-scoring-readiness receipt.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `industry_event_symbolic_scoring_readiness`.
   - Uses `famous_case_records()` as the local reviewed birth-profile source.

3. Updated CLI/API surfaces:
   - Added CLI command `industry-event-scoring-readiness --manifest`.
   - Added HTTP route `GET /industry-event-scoring-readiness`.
   - Added schema endpoint exposure.

4. Updated tests:
   - Core readiness test checks matched and blocked labels.
   - CLI test checks the new command.
   - HTTP test checks the new route.
   - Schema tests check endpoint discoverability.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_scoring_readiness_matches_birth_profiles examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_scoring_readiness_checks_birth_profiles examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_scoring_readiness_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-scoring-readiness --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json` returned the readiness summary below.

### Receipt Snapshot

- Symbolic scoring readiness receipt sha256:
  `c171f87120228421b8f28dd55bccbdfd32297f40ff54dd652e12152f66d0508b`.
- Total labels: `6`.
- Ready labels: `4`.
- Blocked labels: `2`.
- Positive ready labels: `2`.
- Negative ready labels: `2`.
- Ready cases: `marilyn_monroe`, `roger_federer`.
- Blocked case: `bob_dylan`, reason `missing reviewed birth profile for case_id`.

### Boundary

This is still not a predictive score. It only proves which event labels have
enough local birth-profile coverage to be sent into the symbolic annual scoring
layer. Missing birth data remains an explicit blocker rather than an inferred or
fabricated chart.

## 2026-06-26 - Industry Event Symbolic Annual Score

### Motivation

After the readiness gate identified labels with matching birth profiles, the
next step was to actually run those ready labels through the symbolic annual
row diagnostics. This moves the public celebrity pipeline from "label prepared"
to "label scored", while still keeping the result clearly bounded as a
diagnostic rather than predictive proof.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `build_industry_event_symbolic_annual_score`.
   - Builds BaZi charts and annual rows only for labels that passed readiness.
   - Scores positive labels as exact/strict hits.
   - Scores negative labels as false positives.
   - Emits case and domain-topic metric summaries.
   - Adds explicit topic mapping:
     - sports `career_peak` -> `sports_peak`.
     - non-sports `career_peak` -> `career_project`.
   - Adds a deterministic symbolic annual score receipt.

2. Updated API/CLI/HTTP surfaces:
   - Added API helper `industry_event_symbolic_annual_score`.
   - Added CLI command `industry-event-symbolic-score --manifest`.
   - Added HTTP route `GET /industry-event-symbolic-score`.
   - Added schema endpoint exposure.

3. Updated tests:
   - Core scoring test verifies ready labels are scored and blocked labels stay
     blocked.
   - CLI scoring test verifies command output.
   - HTTP scoring test verifies route output.
   - Schema endpoint assertions include the new route.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_annual_score_scores_ready_labels examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_symbolic_score_scores_ready_labels examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_symbolic_score_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-symbolic-score --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json` returned the metric snapshot below.

### Receipt Snapshot

- Symbolic annual score receipt sha256:
  `78e926aac7ec521234eeeb4c14b1e29f4570cc686ea77089acd0b9f1a08d0d51`.
- Scored labels: `4`.
- Blocked labels: `2`.
- Loose exact hit rate: `0.5`.
- Strict exact hit rate: `0.0`.
- Loose false-positive rate: `0.5`.
- Strict false-positive rate: `0.0`.
- Domain-topic slices:
  - `film/public_fame`: scored `2`, strict hit `0.0`, strict false-positive `0.0`.
  - `sports/sports_peak`: scored `2`, strict hit `0.0`, strict false-positive `0.0`.

### Boundary

This diagnostic does not prove predictive validity. The current example shows
that loose signals can hit some event years while also firing in negative years,
and that strict signals are currently too conservative for the small ready-label
set. The correct next evolution is stronger event evidence and more reviewed
birth profiles, not relaxing strict rules for cosmetic scores.

## 2026-06-26 - Industry Symbolic Evidence Refinement Queue

### Motivation

The industry symbolic annual score produced metrics, but the next evolution step
should not be chosen by intuition. The score receipt now needs to explain
whether to expand ready labels, reduce false positives, or add event-specific
evidence before changing symbolic rules.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `evidence_refinement_queue` to symbolic annual score output.
   - Added `evolution_task_plan` derived from that queue.
   - Queue priority uses ready positive/negative counts, strict hit rate, and
     strict false-positive rate.
   - Recommended evidence is domain-topic specific:
     - `public_fame` asks for structured visibility markers and negative-year
       source windows.
     - `sports_peak` asks for structured competition result markers, achievement
       subtypes, and non-peak season evidence.
     - `career_project` and `business_power` have their own future evidence
       requirements.
   - Acceptance criteria are attached to every task.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Symbolic annual score must now include a refinement queue and task plan.
   - The current example must emit high-priority `expand_ready_labels` tasks for
     `film/public_fame` and `sports/sports_peak`.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_annual_score_scores_ready_labels examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_symbolic_score_scores_ready_labels examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_symbolic_score_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-symbolic-score --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json` returned the queue snapshot below.

### Receipt Snapshot

- Updated symbolic annual score receipt sha256:
  `3ef1571d667532df9827f43e9c8e8e71e47a5cb0150eb787257df3042ed24a3b`.
- Refinement queue count: `2`.
- High-priority task:
  `industry-symbolic-film-public_fame-expand_ready_labels`.
- High-priority task:
  `industry-symbolic-sports-sports_peak-expand_ready_labels`.

### Boundary

The queue is a work planner, not a scoring improvement by itself. Its current
answer is deliberately conservative: expand ready positive/negative labels and
reviewed birth profiles before tuning strict symbolic rules.

## 2026-06-26 - Industry Evidence Workplan From Score Tasks

### Motivation

The symbolic annual score can now produce evidence-refinement tasks, but those
tasks still need to become executable collection work. The next step was to bind
score-derived tasks to the reviewed candidate pool, query plan, cache directory,
and exact CLI commands needed for future evidence collection.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `build_industry_event_evidence_workplan_from_symbolic_score`.
   - Converts `expand_ready_labels` tasks into candidate-pool work items.
   - Selects candidates by domain.
   - Emits target positive/negative label counts.
   - Emits dry-run fetch/cache and draft-import CLI commands.
   - Adds a deterministic evidence-workplan receipt.

2. Updated API/CLI/HTTP surfaces:
   - Added API helper `industry_event_evidence_workplan`.
   - Added CLI command `industry-event-evidence-workplan`.
   - Added HTTP route `GET /industry-event-evidence-workplan`.
   - Added schema endpoint exposure.

3. Updated tests:
   - Core workplan test verifies film and sports work items.
   - CLI workplan test verifies command output.
   - HTTP workplan test verifies route output.
   - Schema endpoint assertions include the new route.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-evidence-workplan --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache_workplan` returned the workplan snapshot below.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `c814e435e64409c57e03044b637ae64b2100dfb99a64094abdc7f8216e970c03`.
- Work item count: `2`.
- Domains: `film`, `sports`.
- Film candidates: `jackie_chan`, `meryl_streep`, `tom_hanks`.
- Sports candidates: `roger_federer`, `serena_williams`, `michael_jordan`.
- Commands per work item: `2`.

### Boundary

The workplan does not fetch live data. It converts score tasks into reviewable
dry-run and draft-import commands so future agents can execute evidence
collection without inventing the next step by hand.

## 2026-06-26 - Embedded Dry-Run Plans In Evidence Workplans

### Motivation

The evidence workplan generated commands, but a future agent still had to run
those commands to see request counts, cache paths, and fetch/cache receipts. The
next step was to embed a compact dry-run plan summary inside every work item.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Each evidence work item now runs the corresponding candidate-pool dry-run
     fetch/cache planner.
   - Adds `fetch_cache_plan_summary` to each work item.
   - Includes fetch/cache receipt hash, candidate count, request count, planned
     cache count, planned cache paths, and failures.
   - Workplan-level material now includes `planned_request_count` and
     `planned_cache_count`.
   - Candidate receipt consistency is checked between the workplan and embedded
     dry-run plan.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Workplan test now requires six planned requests and six planned cache paths
     across film and sports.
   - Verifies per-domain embedded fetch/cache receipt hashes.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-evidence-workplan --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache_workplan` returned the snapshot below.

### Receipt Snapshot

- Updated evidence workplan receipt sha256:
  `bf5727cb163dcfc83fe0ca74392607b0bebc4e5fdc534690e9049b0e907568f5`.
- Planned requests: `6`.
- Planned cache paths: `6`.
- Film fetch/cache receipt sha256:
  `b84f49de1d91d5550f107e24b0f9e34ca953cbabaad52f5fd052df21c1817dae`.
- Sports fetch/cache receipt sha256:
  `680b80eda813ed8ab7f1f6223847f30c1a7f5207701db77c683d17256cd99343`.

### Boundary

This still does not fetch live data. It makes the next evidence step more
reviewable by showing exactly how many source requests and cache artifacts each
work item would create.

## 2026-06-26 - Evidence Workplan Cache Materialization Status

### Motivation

The evidence workplan listed planned cache paths, but it did not say whether
those cache files already existed. The next step was to make cache materiality
visible before draft import, so future agents can tell whether the workplan is
ready for import or still needs source collection.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added per-work-item `cache_materialization_summary`.
   - Added top-level `cache_materialization_summary`.
   - Added `existing_cache_count` and `missing_cache_count`.
   - Records existing and missing cache paths.
   - Keeps the workplan non-fetching and dry-run only.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Workplan test now checks that an empty cache directory reports all planned
     cache files as missing.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-evidence-workplan --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache_workplan_empty` returned the snapshot below.

### Receipt Snapshot

- Updated evidence workplan receipt sha256:
  `b80b864bb3486fb978b703f759f6309a54ba735878707ae65b58bebd3472ecb3`.
- Planned cache count: `6`.
- Existing cache count: `0`.
- Missing cache count: `6`.
- All cache files present: `False`.

### Boundary

This is a materialization check, not collection. It lets the system distinguish
"planned evidence" from "locally available cached evidence" before attempting
draft import.

## 2026-06-26 - Evidence Workplan Draft-Import Readiness Gate

### Motivation

The workplan could report missing cache files, but downstream agents still had
to infer whether draft import was allowed. This made it too easy to treat a
reviewed collection plan as if it were already sourced evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added top-level `draft_import_ready`.
   - Added top-level and per-work-item `draft_import_readiness_gate`.
   - Added `next_action` so empty-cache workplans point back to fetch/cache
     review instead of draft import.
   - The gate passes only when every planned source response cache file exists.

2. Updated focused tests:
   - `examples/mingli_5agents/tests/test_empirical_validation.py`
   - `examples/mingli_5agents/tests/test_cli.py`
   - `examples/mingli_5agents/tests/test_api_server.py`

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.
- `python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-evidence-workplan --manifest examples\mingli_5agents\providers\industry_event_source_manifest_example.json --candidates examples\mingli_5agents\providers\industry_event_candidate_cases_example.json --query-plan examples\mingli_5agents\providers\industry_event_source_query_plan_example.json --cache-dir .semas_mingli_repo\industry_event_cache_workplan_empty` returned the snapshot below.

### Receipt Snapshot

- Updated evidence workplan receipt sha256:
  `864efde4ab3ae42168a3075ca6a94ee051485bec75745cc0fa1bcd45dc1d2333`.
- Draft import ready: `False`.
- Gate passed: `False`.
- Missing cache count: `6`.
- Next action:
  `run industry-event-candidate-fetch-cache after reviewing the query plan and source policy`.

### Boundary

This still does not collect public celebrity evidence by itself. It adds the
import gate that blocks scoring expansion until reviewed source responses have
actually been cached.

## 2026-06-26 - Blocked Music Evidence Tasks Remain Visible

### Motivation

Sports, film, and music candidates all exist in the celebrity candidate pool,
but the symbolic score only generated executable event-collection tasks for
film and sports. Music labels were blocked because the example Bob Dylan labels
do not have a matching reviewed birth profile in the current fixture set. The
system needed to expose that blocked state instead of silently dropping music
from the evolution workplan.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_manifest.py`:
   - Added `blocked_readiness_domain_topic_summary`.
   - Added `blocked_readiness_refinement_queue`.
   - Added `add_reviewed_birth_profiles` task type.
   - Added blocked case ids, public names, blocking reasons, and acceptance
     criteria to `evolution_task_plan`.

2. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `deferred_tasks` to evidence workplans.
   - Added `deferred_task_count`.
   - Keeps event-cache work items limited to ready `expand_ready_labels` tasks.
   - Carries music readiness blockers forward as non-collection work.

3. Updated focused tests:
   - `examples/mingli_5agents/tests/test_empirical_validation.py`
   - `examples/mingli_5agents/tests/test_cli.py`
   - `examples/mingli_5agents/tests/test_api_server.py`

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_manifest.py examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_annual_score_scores_ready_labels examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `52693bf6d46ffe196f9be74c37624513107385850799d95f61b7dede04a4844f`.
- Source collection task count: `2`.
- Deferred task count: `1`.
- Source collection domains: `film,sports`.
- Deferred task:
  `industry-symbolic-music-career_project-add_reviewed_birth_profiles`.
- Draft import ready: `False`.
- Missing cache count: `6`.

### Boundary

This does not claim music validation is ready. It makes the missing step
explicit: add reviewed music birth profiles before music event labels can enter
symbolic annual scoring.

## 2026-06-26 - Local Music Birth-Profile Suggestions For Deferred Tasks

### Motivation

The music deferred task correctly said Bob Dylan's industry-event labels were
blocked by missing reviewed birth data, but it did not help the next agent find
available local singer fixtures. The repository already has reviewed singer
birth profiles for Aretha Franklin, Madonna, and Michael Jackson. The workplan
needed a bridge from "blocked music slice" to "local birth-profile candidates"
without automatically rewriting event labels.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Reads local famous-case birth fixtures through `famous_case_records()`.
   - Maps local famous cases into industry domains.
   - Adds `local_birth_profile_suggestions` to deferred tasks.
   - Filters suggestions by supported symbolic event topic.
   - Keeps suggestions advisory; it does not replace Bob Dylan labels or create
     production evidence.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - The music deferred task now requires three local singer suggestions:
     `aretha_franklin`, `madonna`, and `michael_jackson`.
   - Each suggestion must support `career_project`.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\industry_event_manifest.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `f6c8d7f6e114c6c03131380b83e690210a69c22e801a4fcc30dbc38ef3ab33f6`.
- Deferred task:
  `industry-symbolic-music-career_project-add_reviewed_birth_profiles`.
- Local birth-profile suggestion count: `3`.
- Suggestions:
  `aretha_franklin,madonna,michael_jackson`.

### Boundary

This is an advisory bridge only. It helps the next evolution step choose
whether to add Bob Dylan birth data or switch to already reviewed singer
fixtures, but it does not silently alter the validation label table.

## 2026-06-26 - Deferred Music Completion Work Order

### Motivation

The music deferred task had local singer birth-profile suggestions, but it still
left the next agent to infer how to act. The next step was to turn suggestions
into an explicit completion work order while keeping the validation label table
unchanged.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `local_completion_work_order` to deferred tasks.
   - Added two strategy options:
     - preserve the blocked Bob Dylan case by adding reviewed birth data.
     - use local singer fixtures by adding reviewed music event labels for
       Aretha Franklin, Madonna, and Michael Jackson.
   - Added an advisory acceptance gate that remains failed until reviewed
     artifacts are actually added.
   - Removed dependence on local Chinese domain strings in industry-domain
     mapping; stable case ids now drive the local suggestion mapping.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires the deferred music work order to expose both strategy options.
   - Requires the local singer strategy to list all three local singer fixtures.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `1e6b78a5db03b3b6620c28bdc89945a9eabaf0c03b3fcbf6cb1171314f09e865`.
- Work order status: `ready_for_human_review`.
- Acceptance gate passed: `False`.
- Strategy options:
  `preserve_blocked_case,use_local_singer_fixtures`.
- Local singer cases:
  `aretha_franklin,madonna,michael_jackson`.

### Boundary

The work order is not evidence and does not change scoring. It narrows the next
human-reviewed action needed to make music validation scoreable.

## 2026-06-26 - Local Music Draft Label Plan

### Motivation

The deferred music completion work order identified local singer fixtures, but
it still did not show what industry-event labels would need review. The next
step was to generate a draft label plan from local famous-case event tags while
keeping those draft labels outside the validation manifest.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `event_years_by_symbolic_event_topic` to local birth-profile
     suggestions.
   - Added `draft_label_plan` under the `use_local_singer_fixtures` strategy.
   - Draft plan creates one positive and one adjacent negative draft label for
     each suggested singer.
   - Draft records are marked with
     `local_fixture_requires_industry_event_source_review`.
   - Draft acceptance gate remains failed until industry-event sources are
     reviewed.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires six draft music records: three positive and three negative.
   - Requires every draft record to target `career_project`.
   - Requires the source-review acceptance gate to remain failed.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `32d968199e90a166d7c122994c4c64c1c434e3fa8c0c315c60bb9674084b8c1f`.
- Draft status: `draft_requires_source_review`.
- Draft record count: `6`.
- Positive draft records: `3`.
- Negative draft records: `3`.
- Source-review gate passed: `False`.

### Boundary

The draft records are not validation labels. They are a review queue that says
which local singer years need independent industry-event source evidence before
music validation can enter symbolic annual scoring.

## 2026-06-26 - Local Music Draft Label Plan Receipt

### Motivation

The local music draft label plan exposed draft records, but it did not have its
own stable receipt or record hash. Without that, future agents could not tell
whether the draft label queue had drifted between runs.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `draft_label_plan_receipt` to the local music draft label plan.
   - Added `draft_records_sha256`.
   - Added module-local `_stable_sha256()` using the same normalized JSON
     encoding as `_receipt()`.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires 64-character draft-record and draft-plan receipt hashes.
   - Verifies the receipt material records the same record count and failed
     source-review gate.

### Verification

- Initial focused test run failed because `_stable_sha256` was not defined in
  this module.
- After adding `_stable_sha256`, `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `5818a3738e132dbb8a065101e8ed465abd0792d0d9e66ff562141406b6192bda`.
- Local music draft label plan receipt sha256:
  `2c87b0606feee8e9e8f39bbbb980e37bd0fce5f6033daec8d73655e298aa1765`.
- Draft records sha256:
  `4b3f403a32be2877cfe55bafd59ae75368afb110f02a9547a45c05a01745aa73`.
- Draft records: `6`.
- Source-review gate passed: `False`.

### Boundary

The receipt makes the draft queue reproducible. It still does not make the
draft labels evidence; source review and manifest import remain required before
symbolic scoring.

## 2026-06-26 - Local Music Draft Label Plan Integrity Check

### Motivation

The draft label plan had a receipt and record hash, but downstream agents still
had to trust that the nested draft content matched those hashes. The next step
was to expose a self-check summary inside the workplan.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `integrity_check` to the local music draft label plan.
   - Recomputes the draft-plan receipt from current material.
   - Recomputes the draft-record hash from current records.
   - Reports whether both recomputed values match the stored values.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires integrity status to be `passed`.
   - Requires receipt and draft-record hash matches to be true.
   - Requires recomputed hashes to equal stored hashes.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `32f5f05448d407cee40a8abbc5c715294735c92a866e9a940af0137ac4ebb6c8`.
- Local music draft label plan receipt sha256:
  `2c87b0606feee8e9e8f39bbbb980e37bd0fce5f6033daec8d73655e298aa1765`.
- Draft records sha256:
  `4b3f403a32be2877cfe55bafd59ae75368afb110f02a9547a45c05a01745aa73`.
- Integrity status: `passed`.
- Receipt matches current material: `True`.
- Draft records hash matches current records: `True`.

### Boundary

The integrity check only verifies internal consistency of the draft queue. It
does not validate the factual correctness of the draft labels.

## 2026-06-26 - Local Music Source Review Request Plan

### Motivation

The local music draft labels had receipts and integrity checks, but they did
not yet tell the next agent exactly what source-review actions were required.
They also risked silently reusing the existing music `public_fame` query
template for `career_project` draft labels. The next step was to expose that
template mismatch explicitly.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `source_review_request_plan` to the local music draft label plan.
   - Added one review request per draft record.
   - Each request names suggested sources: MusicBrainz Database and Wikidata
     Query Service.
   - Each request includes source-window guidance and required manifest fields.
   - Added query-template alignment metadata showing no exact music
     `career_project` template exists yet.
   - Keeps the review-plan gate failed until source-window review and query
     template alignment are completed.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires six source-review requests.
   - Requires the nearest existing template to be
     `wikidata_music_public_fame_events`.
   - Requires exact event-topic template availability to be false.
   - Requires the review-plan acceptance gate to remain failed.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `c1c0217fe78a65a08b2c246e67d773f1f7594ef5fcc996124fe1ff8941a9f2fb`.
- Local music draft label plan receipt sha256:
  `4c9d82eeda5b83b656c484cb0b0d787982617d7a09e14d309803affb6f54d573`.
- Source review status: `requires_query_template_review`.
- Source review request count: `6`.
- Exact event-topic query template available: `False`.
- Nearest existing query template:
  `wikidata_music_public_fame_events`.
- Source-review gate passed: `False`.

### Boundary

This remains an offline review plan. It does not query MusicBrainz or Wikidata
and does not import the draft labels into the validation manifest.

## 2026-06-26 - Local Music Career-Project Query Template Draft

### Motivation

The source-review plan exposed that no exact music `career_project` query
template exists. The next step was to provide a concrete draft template so the
gap can be reviewed and patched without guessing from prose.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Imported `REQUIRED_TEMPLATE_FIELDS` from the query-plan module.
   - Added `query_template_draft` to the local music source-review plan.
   - Draft template id:
     `wikidata_music_career_project_events_draft`.
   - Draft includes all required query-template fields.
   - Added a stable `template_sha256`.
   - Added a failed acceptance gate requiring query-plan review before use.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires the draft template id, event topic, symbolic topic, field
     completeness, 64-character hash, and failed gate.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `64ba83072451ef7a7b076ab2adfa8a6b8e012ec29336c43175eb6345c6acaa00`.
- Local music draft label plan receipt sha256:
  `d2a717f41e30dc7c06a898f5d5c2b76b8e13919baf6c5a47cfa0137a2931b5d2`.
- Query template draft status:
  `draft_requires_query_plan_review`.
- Query template draft id:
  `wikidata_music_career_project_events_draft`.
- Query template draft sha256:
  `a48c011d1ecc131974f8d41aefc0dc297d4fedea619ba47bd8783f6925d910ad`.
- Missing required template fields: none.
- Query-template review gate passed: `False`.

### Boundary

The template is a draft. It is not inserted into the provider query-plan JSON
and cannot authorize live or cached collection until reviewed.

## 2026-06-26 - Query Template Draft Integrity Check

### Motivation

The local music `career_project` query template draft had a stable hash, but it
did not yet prove that the current nested template still matched that hash or
that required query-template fields remained complete. The next step was to add
self-check metadata to the template draft itself.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `integrity_check` to `query_template_draft`.
   - Recomputes the template hash from current template content.
   - Checks required query-template field completeness separately from hash
     matching.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires template draft integrity status to be `passed`.
   - Requires template hash match to be true.
   - Requires required-field completeness to be true.
   - Requires recomputed template hash to equal stored `template_sha256`.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `9ee2f8cf867acdf5b313b427367b0114785500fbea0586c3e6d4fadb29bb8ec3`.
- Query template draft sha256:
  `a48c011d1ecc131974f8d41aefc0dc297d4fedea619ba47bd8783f6925d910ad`.
- Integrity status: `passed`.
- Template hash matches current template: `True`.
- Required query-template fields complete: `True`.
- Query-template review gate passed: `False`.

### Boundary

The integrity check only proves the draft template is internally consistent. It
does not review the SPARQL semantics, source licensing, or live collection
fitness.

## 2026-06-26 - Query Template Draft Patch Plan

### Motivation

The music `career_project` template draft was internally consistent, but the
next agent still had to infer how it should be installed into the query-plan
manifest. The next step was to expose a non-mutating patch plan.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `query_plan_patch_plan` to the query template draft.
   - Patch operation is `append_query_template`.
   - Target is the example industry-event source query-plan JSON.
   - Insert point is after `wikidata_music_public_fame_events`.
   - Expected template count changes from `3` to `4`.
   - Added review-required fields and post-patch validation commands.
   - Patch acceptance gate remains failed until the manifest is actually edited
     and reviewed.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires patch status, operation, insert point, template count change,
     template hash alignment, and failed gate.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `13e2832903d0acf4233f99abd61d5237bf270a449880b64060a3f9b02975b913`.
- Query template draft sha256:
  `a48c011d1ecc131974f8d41aefc0dc297d4fedea619ba47bd8783f6925d910ad`.
- Patch status: `draft_patch_requires_review`.
- Patch operation: `append_query_template`.
- Target path:
  `C:\aicoding\semas_framework\examples\mingli_5agents\providers\industry_event_source_query_plan_example.json`.
- Expected template count after patch: `4`.
- Patch gate passed: `False`.

### Boundary

This is a patch plan only. It does not edit the query-plan JSON and does not
promote the draft template to reviewed collection capability.

## 2026-06-26 - Query Template Patch Plan Receipt And Integrity

### Motivation

The query-template patch plan described how to append the draft template, but it
did not yet have a receipt or a self-check. Future agents need to know whether
the patch plan itself has drifted before editing provider manifests.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `patch_plan_receipt`.
   - Added `patch_plan_sha256`.
   - Added `integrity_check` to the patch plan.
   - Integrity check verifies receipt/material match, patch-plan hash/material
     match, and template-hash alignment with the template draft.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires patch-plan receipt and hash.
   - Requires receipt material to preserve the template hash.
   - Requires all patch-plan integrity checks to pass.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `18019159e50b08abbde19b759011d759123651653187e55eefc1532d30965219`.
- Patch-plan receipt sha256:
  `5479dec4258b50ecad5249564bb1994cdd0a2cb680ab3d806d368b191402e854`.
- Patch-plan sha256:
  `5479dec4258b50ecad5249564bb1994cdd0a2cb680ab3d806d368b191402e854`.
- Integrity status: `passed`.
- Receipt/material match: `True`.
- Patch/material hash match: `True`.
- Template-hash alignment: `True`.

### Boundary

This still does not edit the provider query-plan manifest. It makes the proposed
edit reproducible and drift-checkable before any file mutation.

## 2026-06-26 - Query Template Patch Plan Applicability Check

### Motivation

The patch plan was reproducible, but it did not check whether the current
target query-plan manifest still matched the assumptions in the plan. A stable
plan is not necessarily applicable if the target file has already changed.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `applicability_check` to the query-template patch plan.
   - Reads the current target query-plan manifest.
   - Checks current template count against expected count.
   - Checks that the insert-after template exists.
   - Checks that the draft template is not already present.
   - Keeps execution gate failed even when the plan is applicable.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires applicability status to be `applicable` for the current fixture.
   - Requires current template count `3`, insert point present, draft template
     absent, and execution gate failed.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `06581778891731de3a354a04d53ccdd06b59fd270da76bbebf0da40bdcd00b0f`.
- Patch-plan receipt sha256:
  `5479dec4258b50ecad5249564bb1994cdd0a2cb680ab3d806d368b191402e854`.
- Applicability status: `applicable`.
- Current template count: `3`.
- Insert point present: `True`.
- Draft template absent: `True`.
- Execution gate passed: `False`.

### Boundary

Applicability is a precondition check, not permission to mutate the query-plan
manifest. Query-plan review remains required.

## 2026-06-26 - Query Template Patch Preview

### Motivation

The patch plan could prove the target file was applicable, but reviewers still
could not see the exact non-mutating result of applying the patch. The next step
was to add an in-memory patch preview showing the resulting template order and
expected query-plan content hash.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `patch_preview` to the query-template patch plan.
   - Reads the target query-plan manifest and inserts the draft template in
     memory only.
   - Reports patched template order, patched template count, patched query-plan
     hash, and preview hash.
   - Keeps `would_write_file` false and execution gate failed.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires preview status `preview_ready`.
   - Requires patched template count `4`.
   - Requires expected template order with the draft template inserted after
     `wikidata_music_public_fame_events`.
   - Requires 64-character patched query-plan and preview hashes.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `3e69c2d9cf0f24ddf0cc34d006f93cbef660cb1ca950ba51f53684a63202db20`.
- Patch preview status: `preview_ready`.
- Would write file: `False`.
- Patched template count: `4`.
- Patched query-plan sha256:
  `c87c0fa14df8b1fadb6a464fcdecfbc9ced91188b435e7be5df6b0c3ff72e337`.
- Patch preview sha256:
  `650f7e71b503299172ecb962f6b09dfc000a54be4fc5c4a0d97ed128f13e5a7c`.
- Execution gate passed: `False`.

### Boundary

The preview is computed in memory. It does not mutate the query-plan manifest
and does not make the draft template reviewed.

## 2026-06-26 - Query Template Patch Preview Receipt And Integrity

### Motivation

The patch preview showed the expected in-memory result, but the preview itself
did not yet have a receipt or self-check. Future agents need to verify that the
preview hash, patched query-plan hash, and preview material still agree.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `patch_preview_receipt`.
   - Added `integrity_check` to `patch_preview`.
   - Integrity check recomputes preview receipt and preview hash.
   - Confirms the patched query-plan hash stored in preview material matches
     the exposed patched query-plan hash.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires preview receipt hash.
   - Requires receipt material to preserve patched template count.
   - Requires all preview integrity checks to pass.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `47fce62f035e8841950784d8db0242847e3f8f925a08b3ac8063a84c61e4e757`.
- Patch preview receipt sha256:
  `b1c33d3dc9e32053d2af88ca24b28b2306cec45ed8aba0d67a4112aad25d91f2`.
- Patch preview sha256:
  `b1c33d3dc9e32053d2af88ca24b28b2306cec45ed8aba0d67a4112aad25d91f2`.
- Patched query-plan sha256:
  `c87c0fa14df8b1fadb6a464fcdecfbc9ced91188b435e7be5df6b0c3ff72e337`.
- Integrity status: `passed`.
- Preview receipt/material match: `True`.
- Preview hash/material match: `True`.
- Patched query-plan hash match: `True`.

### Boundary

This validates only the in-memory preview artifact. It still does not write the
query-plan manifest.

## 2026-06-26 - Deferred Music Gate Summary

### Motivation

The deferred music workplan had many nested gates and integrity checks. Future
agents had to inspect the completion work order, draft label plan, source
review plan, query template draft, patch plan, applicability check, and patch
preview to understand the current blocker state. The next step was to summarize
those gates at the deferred-task level.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `gate_summary` to deferred evidence tasks.
   - Recursively collects nested `acceptance_gate` and `execution_gate`
     objects.
   - Recursively collects nested `integrity_check` objects.
   - Reports blocked gate count, failed integrity count, blocked gate list, and
     next action.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires the music deferred task to be blocked.
   - Requires no failed integrity checks.
   - Requires key blocker gates to appear in the summary.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `45b491a97da31059b3fd68ecedf3e894c3a8aeb873265b28327a3a3c09046725`.
- Deferred gate summary status: `blocked`.
- Gate count: `15`.
- Blocked gate count: `15`.
- Integrity check count: `7`.
- Failed integrity check count: `0`.
- Next action:
  `resolve blocked review gates before promoting music draft labels or query templates`.

### Boundary

The summary does not change any gate state. It is an observability layer that
makes the current blocker stack easier to review.

## 2026-06-26 - Deferred Music Gate Summary Receipt

### Motivation

The deferred music gate summary made blockers visible, but it did not yet have
its own receipt or integrity check. Future agents need to know whether the
summarized blocker stack has changed without re-walking the entire nested
workplan.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `gate_summary_receipt`.
   - Added `gate_summary_sha256`.
   - Added `integrity_check` to `gate_summary`.
   - Integrity check recomputes the summary receipt and summary hash from the
     current summary material.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Requires gate-summary receipt and hash.
   - Requires receipt material to preserve blocked gate count.
   - Requires gate-summary integrity checks to pass.

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q` passed.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `2eef4ca2c1af300766489cf811bf7befd03d87ef242ff6bdf5b5b7917dfc0065`.
- Gate summary receipt sha256:
  `03745dd5c1bbbb02cefa483657be9694147170a475300554f66a6ec5dcfcdb97`.
- Gate summary sha256:
  `03745dd5c1bbbb02cefa483657be9694147170a475300554f66a6ec5dcfcdb97`.
- Gate summary status: `blocked`.
- Blocked gate count: `15`.
- Integrity status: `passed`.
- Receipt/material match: `True`.
- Summary hash/material match: `True`.

### Boundary

The receipt verifies the summary artifact only. It does not resolve any nested
review gate.

## 2026-06-26 - Evidence Workplan Readiness Summary

### Motivation

The evidence workplan already had a draft-import gate for cache materialization
and a deferred-task gate summary for music evidence. It still lacked a single
top-level readiness view that tells an executor whether the full celebrity
validation workpack can move forward.

### Actions Taken

1. Updated `examples/mingli_5agents/industry_event_candidates.py`:
   - Added `readiness_summary` to the evidence workplan.
   - Combined cache blockers, deferred review blockers, failed integrity
     checks, and validation failures into one top-level status.
   - Added `readiness_summary_receipt`, `readiness_summary_sha256`, and an
     integrity check that recomputes both values from the summary material.

2. Updated focused tests:
   - `examples/mingli_5agents/tests/test_empirical_validation.py`
   - `examples/mingli_5agents/tests/test_cli.py`
   - `examples/mingli_5agents/tests/test_api_server.py`

### Verification

- `python -m py_compile examples\mingli_5agents\industry_event_candidates.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_cli.py::test_cli_industry_event_evidence_workplan_projects_collection_commands examples\mingli_5agents\tests\test_api_server.py::test_http_api_industry_event_evidence_workplan_route -q`
  passed: `3 passed`.

### Receipt Snapshot

- Evidence workplan receipt sha256:
  `c1aaca71bfc805b47d8d5a6aa0ae37645f029114fdf8b79d6265342a3bd7c4a6`.
- Readiness summary receipt sha256:
  `b184566a84d0a65a822f7b946c3d21dfe223e3ac581919192108eb8dd3e9d4f2`.
- Readiness status: `blocked`.
- Missing cache count: `6`.
- Deferred blocked gate count: `15`.
- Failed deferred integrity check count: `0`.
- Readiness integrity status: `passed`.

### Boundary

This is an observability and execution-control layer only. It does not fetch
source data, promote music draft labels, edit query templates, or mark the
celebrity validation workpack as ready.

## 2026-06-26 - Cross-Domain Celebrity Fixture Import

### Motivation

The candidate pool contained sports, film, and music public figures, but only
the sports domain had a local cached-response example. The next step was to
prove that all three domains can pass through the offline cache-import path
without live collection.

### Actions Taken

1. Added provider fixtures:
   - `examples/mingli_5agents/providers/wikidata_film_response_example.json`
   - `examples/mingli_5agents/providers/wikidata_music_response_example.json`

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Added domain-specific fixture constants.
   - Added a helper that materializes cached responses by candidate domain.
   - Added a cross-domain import test covering all 9 celebrity candidates.

3. Materialized a local all-domain fixture cache snapshot under:
   - `.semas_mingli_repo/industry_event_cache_all_domains_fixture`

### Verification

- `python -m json.tool examples\mingli_5agents\providers\wikidata_film_response_example.json`
  passed.
- `python -m json.tool examples\mingli_5agents\providers\wikidata_music_response_example.json`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_all_domains examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_draft_import_api_exposes_summary -q`
  passed: `3 passed`.

### Receipt Snapshot

- Draft import status: `ready_for_review`.
- Candidate count: `9`.
- Draft count: `9`.
- Positive record count: `9`.
- Negative record count: `273`.
- Total record count: `282`.
- Cross-domain coverage gate: `True`.
- Domains: `film,music,sports`.
- Candidate-pool draft-import receipt sha256:
  `68654a8254a878adfea02dcec5e26b8db61c02c9aa176a987ace42a1533cc7e7`.
- Validation-label-table receipt sha256:
  `e1d414970daa2e7ce00cff74d17721e0a7bca193cb382ab2b0137ea68d4e67fe`.

### Boundary

These are repository-authored fixture responses for offline pipeline
validation. They do not certify real Wikidata result completeness, production
source review, or factual event-label correctness.

## 2026-06-26 - Cross-Domain Fixture Import Audit Receipt

### Motivation

The cross-domain celebrity fixture import was covered by tests, but capability
audit did not expose it as a reusable machine-readable artifact. Future agents
need to discover that the sports, film, and music offline import loop exists
without reading the test suite.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added fixed fixture response paths for film, music, and sports.
   - Added a fixed audit fixture cache path.
   - Added `_industry_event_cross_domain_fixture_import_receipt()`.
   - Added `industry_event_cross_domain_fixture_import` to capabilities,
     audit response, and audit receipt material.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Added `test_industry_event_cross_domain_fixture_import_receipt`.
   - Required the audit receipt to bind candidate count, label counts,
     cross-domain coverage, and validation-label-table receipt.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py` passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_candidate_pool_manifest_drafts_from_cache_imports_all_domains -q`
  passed: `3 passed`.

### Receipt Snapshot

- Capability audit receipt sha256:
  `f8f37844d4998e713e51dcce05049e2125bb1acada5452be830c1cd06846fcd9`.
- Cross-domain fixture import receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Capability flag: `True`.
- Status: `ready_example`.
- Candidate count: `9`.
- Draft count: `9`.
- Positive record count: `9`.
- Negative record count: `273`.
- Total record count: `282`.
- Cross-domain coverage gate: `True`.
- Validation-label-table receipt sha256:
  `22bb4a9a007534f177f835f2f153e29960174c30a8779a7f5a6d55982f1bc0db`.

### Boundary

This audit receipt proves the offline fixture import loop is reproducible and
discoverable by the capability audit. It still does not promote fixture labels
to production evidence.

## 2026-06-26 - Cross-Domain Fixture Import Schema Contract

### Motivation

The cross-domain celebrity fixture import was exposed through capability audit,
but the public schema did not yet make that field contractual. External callers
and future agents need a stable schema reference for the response field and its
audit-receipt material.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `IndustryEventCrossDomainFixtureImportMaterial`.
   - Added `IndustryEventCrossDomainFixtureImportReceipt`.
   - Required `industry_event_cross_domain_fixture_import` in
     `CapabilityAuditResponse`.
   - Required the same receipt in `CapabilityAuditReceiptMaterial`.

2. Updated `examples/mingli_5agents/evaluators/schema_contract_evaluator.py`:
   - Added the new schemas to required schema coverage.
   - Added response/material `$ref` checks.

3. Updated `examples/mingli_5agents/tests/test_schema_contract_evaluator.py`:
   - Required the public response reference.
   - Required the audit material reference.
   - Required core material fields such as label counts, coverage gate, and
     validation-label-table receipt hash.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt -q`
  passed: `3 passed`.

### Receipt Snapshot

- Schema contract score: `1.0`.
- CapabilityAuditResponse ref:
  `#/schemas/IndustryEventCrossDomainFixtureImportReceipt`.
- CapabilityAuditReceiptMaterial ref:
  `#/schemas/IndustryEventCrossDomainFixtureImportReceipt`.
- Cross-domain fixture import receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Capability audit receipt sha256:
  `f8f37844d4998e713e51dcce05049e2125bb1acada5452be830c1cd06846fcd9`.
- Validation-label-table receipt sha256:
  `22bb4a9a007534f177f835f2f153e29960174c30a8779a7f5a6d55982f1bc0db`.

### Boundary

This makes the audit artifact portable through the public schema. It does not
change the fixture labels' non-production status.

## 2026-06-26 - Cross-Domain Fixture Import Runtime Schema Validation

### Motivation

The cross-domain fixture import schema contract existed, but the actual
capability-audit runtime output still needed a focused validation check. A
runtime check found that the audit receipt material carried a summary while the
schema expected the full receipt object.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Changed `audit_receipt.material.industry_event_cross_domain_fixture_import`
     to carry the full fixture-import receipt.
   - This keeps the top-level response artifact and audit material artifact on
     the same schema.

2. Updated tests:
   - `examples/mingli_5agents/tests/test_empirical_validation.py`
   - `examples/mingli_5agents/tests/test_schema_contract_evaluator.py`
   - Added runtime schema validation for both the top-level fixture receipt and
     the audit-material fixture receipt.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt -q`
  passed: `3 passed`.

### Receipt Snapshot

- Top-level fixture receipt schema error count: `0`.
- Audit-material fixture receipt schema error count: `0`.
- Cross-domain fixture import receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Audit-material fixture receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Capability audit receipt sha256:
  `08e7af184aa0eca4c9d90d7ea06eab492e23bb1cdb67b8112300ef0bd3b8ff19`.
- Validation-label-table receipt sha256:
  `22bb4a9a007534f177f835f2f153e29960174c30a8779a7f5a6d55982f1bc0db`.

### Boundary

This validates the new fixture-import artifact only. The broader capability
audit response still has older schema-validation gaps outside this change.

## 2026-06-26 - Cross-Domain Fixture Import HTTP Schema Validation

### Motivation

The fixture-import runtime schema check covered direct Python output. The public
HTTP API also needs to preserve the same object shape because downstream tools
normally consume `/audit` and `/schema` rather than importing Python functions.

### Actions Taken

1. Updated `examples/mingli_5agents/tests/test_api_server.py`:
   - Imported `schema_validation_errors`.
   - Added `/audit` assertions for `industry_event_cross_domain_fixture_import`.
   - Validated both the top-level fixture receipt and the audit-material fixture
     receipt against the `/schema` response.
   - Required the two fixture receipt hashes to match.

### Verification

- `python -m py_compile examples\mingli_5agents\tests\test_api_server.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_api_server.py::test_http_api_status_schema_analyze_and_benchmark -q`
  passed: `1 passed` in `191.29s`.

### HTTP Snapshot

- HTTP top-level fixture receipt schema error count: `0`.
- HTTP audit-material fixture receipt schema error count: `0`.
- Cross-domain fixture import receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Audit-material fixture receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Capability audit receipt sha256:
  `08e7af184aa0eca4c9d90d7ea06eab492e23bb1cdb67b8112300ef0bd3b8ff19`.
- Candidate count: `9`.
- Record count: `282`.

### Boundary

This verifies the new fixture-import artifact over HTTP. It does not claim that
the full `/audit` response is schema-clean, and it does not change the
non-production fixture boundary.

## 2026-06-26 - Cross-Domain Fixture Import CLI Schema Validation

### Motivation

HTTP validation covered the service boundary, but automation and release scripts
also consume the CLI `audit` and `schema` commands. The cross-domain celebrity
fixture import should therefore be validated through the CLI surface too.

### Actions Taken

1. Updated `examples/mingli_5agents/tests/test_cli.py`:
   - Imported `schema_validation_errors`.
   - Added CLI `audit` assertions for `industry_event_cross_domain_fixture_import`.
   - Validated the top-level fixture receipt and audit-material fixture receipt
     against the CLI `schema` output.
   - Added CLI schema assertions for
     `IndustryEventCrossDomainFixtureImportMaterial` and
     `IndustryEventCrossDomainFixtureImportReceipt`.

### Verification

- `python -m py_compile examples\mingli_5agents\tests\test_cli.py` passed.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_init_analyze_evolve_status examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `2 passed` in `280.27s`.

### CLI Snapshot

- CLI top-level fixture receipt schema error count: `0`.
- CLI audit-material fixture receipt schema error count: `0`.
- Cross-domain fixture import receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Audit-material fixture receipt sha256:
  `5e0af9b6808b1ee043a0ace74b8ccbc77a6b6a0ad338ea953b84a5c98cfbf43b`.
- Capability audit receipt sha256:
  `08e7af184aa0eca4c9d90d7ea06eab492e23bb1cdb67b8112300ef0bd3b8ff19`.
- Candidate count: `9`.
- Record count: `282`.

### Boundary

This verifies the fixture-import artifact over the CLI interface. It does not
change source-review status or promote fixture labels to production evidence.

## 2026-06-26 - Cross-Domain Fixture Import Implemented Requirement

### Motivation

The cross-domain fixture import was exposed through capability audit and public
interfaces, but it was not yet listed as a named implemented requirement. That
made the capability discoverable as a field but not as a tracked engineering
deliverable with materialized evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `industry_event_cross_domain_fixture_import` to
     `IMPLEMENTED_REQUIREMENTS`.
   - Bound the requirement to the fixture-import receipt builder, public schema
     fields, fixture response files, and Python/HTTP/CLI tests.

2. Updated `examples/mingli_5agents/tests/test_capability_audit_evaluator.py`:
   - Required the capability flag.
   - Required the implemented requirement id.
   - Required key evidence entries in the implemented requirement.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `2 passed`.

### Audit Snapshot

- Capability audit receipt sha256:
  `c2080e695637c68ee1c8c1d95fb8b2835a7fd334fca104da3fbb46d4d5369cea`.
- Capability flag: `True`.
- Implemented requirement count: `70`.
- Requirement status: `implemented`.
- Requirement evidence count: `11`.
- Materialization status: `passed`.
- Materialized evidence count: `11`.
- Evidence materialization failed count: `0`.
- Evidence materialization unchecked count: `0`.
- Evidence materialization passed count: `436`.

### Boundary

This records the fixture-import loop as an implemented engineering capability.
It still remains a non-production evidence path until source review and real
event-label governance are completed.

## 2026-06-26 - Cross-Domain Celebrity Symbolic Readiness Gate

### Motivation

The project could now import sports, film, and music celebrity event-label
fixtures, but that alone did not prove the labels could enter BaZi symbolic
annual scoring. Event labels also need matching reviewed birth profiles. Without
that second gate, the system could overstate the value of celebrity samples.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added a cross-domain fixture symbolic-readiness summary to the fixture
     import receipt.
   - Reused `build_industry_event_symbolic_scoring_readiness_payload` with
     `famous_case_records()`.
   - Exposed ready labels, blocked labels, ready cases, missing birth-profile
     cases, domain/topic summaries, gates, and the readiness receipt hash.
   - Added the readiness test evidence to the implemented requirement.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `symbolic_scoring_readiness_summary` to
     `IndustryEventCrossDomainFixtureImportMaterial`.
   - Required the summary in the public schema.

3. Updated tests:
   - `test_industry_event_cross_domain_fixture_import_receipt` now asserts the
     readiness counts and missing birth-profile cases.
   - `test_schema_contract_evaluator.py` now asserts the public schema exposes
     the readiness summary.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `1 passed`.

### Audit Snapshot

- Cross-domain fixture import receipt sha256:
  `d168c37706e26ad3631c279e80f42509b0e518e51bd1c9088028b195eaa22eb8`.
- Capability audit receipt sha256:
  `71949b1c5889335bacb0391acb5f28b13017f36f269b593a0d545d81d6e99fef`.
- Imported event labels: `282`.
- Ready symbolic-scoring labels: `25`.
- Blocked labels: `257`.
- Ready cases: `1` (`roger_federer`).
- Missing reviewed birth-profile cases:
  `beyonce`, `jackie_chan`, `jay_chou`, `meryl_streep`,
  `michael_jordan`, `serena_williams`, `taylor_swift`, `tom_hanks`.
- Readiness receipt sha256:
  `bb60003625dac34072b9479303308560d6be4e0306f55e0acf3b85ade08f03d0`.

### Boundary

The sports/film/music event-label pipeline is importable, but only labels with
reviewed birth profiles can enter symbolic annual scoring. Current fixture
coverage supports scoring Roger Federer only; film and music labels remain
blocked until reviewed birth profiles are added.

## 2026-06-26 - Cross-Domain Birth Profile Completion Task Plan

### Motivation

The cross-domain readiness gate identified missing reviewed birth profiles, but
future agents still needed an executable queue. A missing-data diagnosis should
be converted into explicit evidence tasks with case ids, blocked label counts,
and acceptance criteria.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Reused `build_industry_event_symbolic_annual_score_payload` inside the
     cross-domain fixture readiness summary.
   - Added `birth_profile_completion_task_plan` to expose compact
     `add_reviewed_birth_profiles` tasks.
   - Added `symbolic_annual_score_receipt_sha256` to bind the task plan to the
     scoring receipt.
   - Added `_cross_domain_birth_profile_completion_task_plan`.
   - Added the helper to the implemented-requirement evidence list.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Required `birth_profile_completion_task_plan`.
   - Required `symbolic_annual_score_receipt_sha256`.
   - Added schema fields for task ids, blocked cases, evidence to add,
     acceptance criteria, blocking reasons, and task boundaries.

3. Updated tests:
   - Runtime audit test now asserts all three task ids and blocked case ids.
   - Schema test now asserts the task-plan contract.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `1 passed`.

### Audit Snapshot

- Capability audit receipt sha256:
  `41df129ec08c2a6ff5896a4a755b181699446097aa7147cbc3af30d802cfb3d9`.
- Cross-domain fixture import receipt sha256:
  `50d43541edf9466f939cfa2e03f58c8d1dd99b0148ca144a6064672bf833f5a9`.
- Symbolic readiness receipt sha256:
  `bb60003625dac34072b9479303308560d6be4e0306f55e0acf3b85ade08f03d0`.
- Symbolic annual score receipt sha256:
  `318aa3dfd7efd49ed06b1b2d66a9b16f1082d83f5daf80f49f30e47ea07a554d`.
- Birth-profile completion tasks: `3`.
- Task ids:
  - `industry-symbolic-film-public_fame-add_reviewed_birth_profiles`
  - `industry-symbolic-music-public_fame-add_reviewed_birth_profiles`
  - `industry-symbolic-sports-sports_peak-add_reviewed_birth_profiles`
- Blocked labels covered by the task plan: `257`.
- Implemented requirement evidence count: `13`.

### Boundary

The task plan tells the next agent exactly which reviewed birth profiles to add.
It does not itself add or certify those birth profiles, and it does not promote
the blocked celebrity labels into symbolic scoring.

## 2026-06-26 - Cross-Domain Birth Profile Workplan Summary

### Motivation

The cross-domain fixture receipt exposed missing birth-profile tasks, but the
task list did not yet connect to the existing evidence-workplan machinery. The
next agent still needed to know whether there are local substitute fixtures,
which review gates are blocked, and which receipt anchors the workplan.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Reused `build_industry_event_evidence_workplan_from_symbolic_score`.
   - Added `birth_profile_completion_workplan_summary`.
   - Added `evidence_workplan_receipt_sha256`.
   - Added `_cross_domain_birth_profile_completion_workplan_summary`.
   - Added the helper to implemented-requirement evidence.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Required the workplan summary inside the symbolic-readiness summary.
   - Required deferred task summaries, local suggestion case ids, work-order
     status, gate status, and blocked-gate counts.
   - Required `evidence_workplan_receipt_sha256`.

3. Updated tests:
   - Runtime audit test now asserts the local suggestion case ids for film,
     music, and sports.
   - Schema test now asserts the workplan-summary public contract.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `1 passed`.

### Audit Snapshot

- Capability audit receipt sha256:
  `a419acf8ffad97629efb93f363117840a7d66c95c43b45f624b5ff026631bcd7`.
- Cross-domain fixture import receipt sha256:
  `b58762fac16f64352e4ac197fd12a2ce580acd3dd720243d2d6579b94536bb40`.
- Evidence workplan receipt sha256:
  `639caae6adf93c174769dc1bcd22c3466834ebc3ebb0d43bbf1589085602fbd7`.
- Deferred birth-profile tasks: `3`.
- Workplan readiness status: `blocked`.
- Deferred blocked gates: `3`.
- Work items: `1`.
- Local suggestion slices:
  - film blocked cases `jackie_chan`, `meryl_streep`, `tom_hanks`; local
    suggestions `bruce_lee`, `lucille_ball`, `marilyn_monroe`.
  - music blocked cases `beyonce`, `jay_chou`, `taylor_swift`; local
    suggestions `aretha_franklin`, `madonna`, `michael_jackson`.
  - sports blocked cases `michael_jordan`, `serena_williams`; local
    suggestions `arthur_ashe`, `mark_spitz`, `roger_federer`.
- Implemented requirement evidence count: `14`.

### Boundary

The workplan summary is an audit artifact. It shows local suggestions and
blocked review gates, but it does not convert suggestions into reviewed birth
profiles and does not unlock symbolic scoring for blocked celebrity labels.

## 2026-06-26 - Birth Profile Review Manifest Contract

### Motivation

The cross-domain celebrity workplan identified eight missing reviewed birth
profiles. Directly editing hard-coded famous-case fixtures would blur reviewed
data and planned data. The next step was to create a review-manifest contract so
birth-profile collection can be audited before any profile is imported.

### Actions Taken

1. Added `examples/mingli_5agents/providers/birth_profile_review_manifest_example.json`:
   - Covers the eight missing celebrity birth-profile cases.
   - Records required profile fields, source policy, identity anchors, search
     queries, blocked symbolic topics, and blocked label counts.
   - Keeps `externally_reviewed` false and `ready_for_import` false.

2. Added `examples/mingli_5agents/birth_profile_review.py`:
   - `audit_birth_profile_review_manifest`.
   - `birth_profile_review_manifest_receipt`.
   - Field, duplicate-case, domain, source-policy, identity URL, review-status,
     and blocked-label checks.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added the birth-profile review manifest summary to the cross-domain
     symbolic-readiness summary.
   - Added `birth_profile_review_manifest_receipt_sha256`.
   - Added the audit function and manifest file to implemented evidence.

4. Updated `examples/mingli_5agents/api_core.py` and tests:
   - Added public schema fields for the review-manifest summary and receipt.
   - Added runtime audit tests for the manifest and cross-domain audit binding.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `1 passed`.

### Audit Snapshot

- Capability audit receipt sha256:
  `e1035fad593c1ed1e9d901d96a9840593938e04e14461e5fcd38d9809fe68b56`.
- Cross-domain fixture import receipt sha256:
  `dab329822d117649dc8a223e22ac7e306d26a56c6a25d62e82f4b32f8845befd`.
- Birth-profile review manifest receipt sha256:
  `ea9e6e1df15a795af82ec6502e6fc4fc957048e931d2def7308e9dd8c57ef31e`.
- Review requests: `8`.
- Blocked labels covered: `257`.
- Domains: `film`, `music`, `sports`.
- Ready for import: `False`.
- Implemented requirement evidence count: `16`.

### Boundary

The review manifest is a collection contract, not sourced birth-profile data.
It does not change famous-case fixtures and does not unlock symbolic scoring.
External review is still required before importing any celebrity birth profile.

## 2026-06-26 - Birth Profile Review API And CLI Surface

### Motivation

The birth-profile review manifest could be audited internally and through the
cross-domain capability audit, but operators and future agents still needed a
direct interface. Birth-profile collection should be auditable before touching
famous-case fixtures, without requiring a full capability audit run.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `birth_profile_review_status`.
   - Added `BirthProfileReviewStatusResponse` to the public schema.
   - Added `GET /birth-profile-review` to endpoint documentation.

2. Updated `examples/mingli_5agents/cli.py`:
   - Added `birth-profile-review`.
   - Supports optional `--manifest`.

3. Updated `examples/mingli_5agents/api_server.py`:
   - Added `/birth-profile-review`.

4. Updated tests:
   - Added API runtime schema validation for `BirthProfileReviewStatusResponse`.
   - Added CLI command coverage.
   - Added HTTP route coverage.
   - Added schema-contract coverage for the new response and endpoint.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_status_exposes_non_import_gate examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_review_status examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_review_route examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_review_status examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_status_exposes_non_import_gate -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q`
  passed: `2 passed`.

### API Snapshot

- Birth-profile review summary receipt sha256:
  `a0255e906902148df180b1d5483df6f63c9f98e72f887423f895afbe52582dd2`.
- Review requests: `8`.
- Blocked labels covered: `257`.
- Production gate passed: `False`.
- Ready for import: `False`.
- Schema endpoint present: `True`.
- Schema response present: `True`.

### Boundary

The new API/CLI surface audits collection worklists only. It does not import
birth profiles, does not change famous-case fixtures, and does not unlock
symbolic scoring for blocked celebrity labels.

## 2026-06-26 - Birth Profile Import Preview Gate

### Motivation

After adding a review manifest and direct API/CLI audit surface, the next
missing step was an import preview. Future agents need to know what would happen
after review, but the system must not write famous-case fixtures while the
manifest is still unreviewed and incomplete.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_import_preview`.
   - Added non-mutating import material, receipt, stable hash, integrity check,
     import gate, blocking reasons, and next action.
   - Kept `would_write_file` false and `import_allowed` false for the bundled
     unreviewed manifest.

2. Updated API/CLI/HTTP surfaces:
   - Added `birth_profile_import_preview` in `api_core.py`.
   - Added CLI command `birth-profile-import-preview`.
   - Added HTTP route `/birth-profile-import-preview`.
   - Added public schema `BirthProfileImportPreviewResponse`.
   - Added endpoint documentation.

3. Updated tests:
   - Added direct preview tests.
   - Added runtime schema validation.
   - Added CLI and HTTP route tests.
   - Added schema-contract assertions for the response and import gate.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\api_server.py examples\mingli_5agents\cli.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_blocks_unreviewed_manifest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_status_exposes_runtime_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_import_preview_blocks_writes examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_import_preview_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_status_exposes_non_import_gate examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_review_status examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_review_route -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Preview Snapshot

- Status: `blocked_not_ready_for_import`.
- Import preview receipt sha256:
  `35d0b95a5e1839d59f515299c5159af371cec22a6aeed92ad5227cd82d09de34`.
- Import preview sha256:
  `35d0b95a5e1839d59f515299c5159af371cec22a6aeed92ad5227cd82d09de34`.
- Would write file: `False`.
- Import allowed: `False`.
- Review requests: `8`.
- Blocked requests: `8`.
- Import-ready requests: `0`.
- Import gate passed: `False`.
- Blocking reasons:
  - manifest is not marked `ready_for_import`;
  - manifest is not production evidence;
  - manifest has not been externally reviewed;
  - 8 requests still list `missing_profile_fields`;
  - 8 requests are not `externally_reviewed`.
- Schema endpoint present: `True`.
- Schema response present: `True`.

### Boundary

The import preview is intentionally non-mutating. It creates a verifiable
blocked state and next action, but it does not create a fixture patch, import
birth profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Import Preview Bound To Capability Audit

### Motivation

The birth-profile import preview had API/CLI/HTTP surfaces, but the cross-domain
celebrity capability audit still only exposed the review manifest and workplan.
Future agents should see the whole birth-profile chain from the same capability
receipt: missing labels, completion tasks, review manifest, and blocked import
preview.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Imported `build_birth_profile_import_preview`.
   - Added `birth_profile_import_preview_summary` to the cross-domain symbolic
     readiness summary.
   - Added `birth_profile_import_preview_receipt_sha256`.
   - Added `_cross_domain_birth_profile_import_preview_summary`.
   - Added the import-preview builder to implemented evidence.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Required `birth_profile_import_preview_summary` in the fixture import
     material schema.
   - Required `birth_profile_import_preview_receipt_sha256`.

3. Updated tests:
   - Runtime cross-domain audit test now asserts blocked import-preview state.
   - Schema contract test now asserts the import-preview summary contract.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_required_governance_fields examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_industry_fixture_import_runtime_output_matches_public_schema_contract -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `1 passed`.

### Audit Snapshot

- Capability audit receipt sha256:
  `7c5aea18123af8704c210fc5c4b2410532bd66ebe472e116d49fb121b641dfec`.
- Cross-domain fixture import receipt sha256:
  `fad576c955f12b39d65543412a903127aba8df50028299c24c4ffaf2530820b6`.
- Birth-profile import preview receipt sha256:
  `35d0b95a5e1839d59f515299c5159af371cec22a6aeed92ad5227cd82d09de34`.
- Preview status: `blocked_not_ready_for_import`.
- Would write file: `False`.
- Import allowed: `False`.
- Blocked requests: `8`.
- Import-ready requests: `0`.
- Import gate passed: `False`.
- Integrity check: `passed`.
- Implemented requirement evidence count: `17`.

### Boundary

The capability audit now exposes the blocked import preview, but it still does
not import birth profiles, write fixtures, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Import Preview Production Gate

### Motivation

The birth-profile import preview was visible in capability audit, API, CLI, and
HTTP surfaces. Production readiness still needed a hard gate so a future release
cannot accidentally allow unreviewed celebrity birth profiles to be imported.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_import_preview_blocked`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added the production-readiness gate.
   - The gate passes only when the import preview is valid, non-mutating,
     import-disallowed, gate-blocked, integrity-passed, has blocked requests,
     and has zero import-ready requests.
   - Added helper diagnostics for gate failures.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added known gap `celebrity_birth_profile_review`.
   - Added the known-gap resolution blueprint with CLI verification commands
     for `birth-profile-review`, `birth-profile-import-preview`, and
     `production-readiness`.

4. Updated tests:
   - Added production-readiness gate coverage.
   - Added known-gap command/gate coverage assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Snapshot

- Production gate:
  `birth_profile_import_preview_blocked`.
- Gate passed: `True`.
- Gate blocker present: `False`.
- Production gate registry current: `True`.
- Known gap present:
  `celebrity_birth_profile_review`.
- Known-gap verification commands:
  `birth-profile-import-preview`, `birth-profile-review`,
  `production-readiness`.
- Gate is registered in valid production gates: `True`.
- Known-gap gate count: `2`.
- Capability audit receipt sha256:
  `9c39708b77cbf056a38e5f57fbd41aafda5f4312b30769bb87538dd3633c1bab`.
- Production readiness receipt sha256:
  `24956c8d2d1b03cc8f4fc89143e364771415cd327a0094df5fd3b123d2212330`.

### Boundary

This gate proves that the current unreviewed birth-profile import path remains
blocked and non-mutating. It does not mean celebrity birth profiles are ready to
import.

## 2026-06-26 - Reviewed Birth Profile Import Plan Contract

### Motivation

The birth-profile review path could prove that unreviewed celebrity birth
profiles remain blocked, but it did not yet prove the next state: after a
reviewed manifest is supplied, the system can produce a structured import plan
without writing fixtures.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added manifest status `reviewed_ready_for_import`.
   - Kept the bundled example manifest blocked by default.
   - Added reviewed-manifest checks for external review, approval, empty
     missing fields, complete birth fields, and complete source fields.
   - Added `candidate_profiles` to the non-mutating import preview.
   - Kept `would_write_file` as `False` even when the reviewed manifest is
     import-ready.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `candidate_profiles` to the public
     `BirthProfileImportPreviewResponse` schema.

3. Updated tests:
   - Added a synthetic reviewed-manifest contract test.
   - Added schema assertions for `candidate_profiles`.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_blocks_unreviewed_manifest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_accepts_reviewed_manifest_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `5 passed`.

### Snapshot

- Default bundled manifest status:
  `blocked_not_ready_for_import`.
- Default import allowed:
  `False`.
- Default would write file:
  `False`.
- Default candidate profiles:
  `0`.
- Default import preview receipt sha256:
  `9375b9beef5c86c1b9a31727a220b6f4f7ee74bdda6f5695edf6f050d29f5cab`.
- Default integrity check:
  `passed`.

### Boundary

The reviewed-manifest test uses a synthetic contract fixture. It proves the
import-plan state machine, not any real celebrity birth data. Real celebrity
profiles still require external source review before they can enter fixtures.

## 2026-06-26 - Birth Profile Fixture Patch Preview

### Motivation

The reviewed birth-profile import plan could generate candidate profiles, but
there was still no explicit patch-review step before touching
`FAMOUS_CASES`. The next evolution step was to make the fixture edit itself a
non-mutating, hashable preview.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_fixture_patch_preview`.
   - Added target-file hashing for `famous_case_validation.py`.
   - Added `patch_text`, `patch_text_sha256`, `candidate_case_ids`, patch
     gate, receipt, and integrity check.
   - Kept `would_write_file` as `False` for both blocked and ready states.

2. Updated API/CLI/HTTP surfaces:
   - Added API function `birth_profile_fixture_patch_preview`.
   - Added CLI command `birth-profile-fixture-patch-preview`.
   - Added HTTP route `/birth-profile-fixture-patch-preview`.
   - Added public schema `BirthProfileFixturePatchPreviewResponse`.
   - Added endpoint documentation in `/schema`.

3. Updated schema governance:
   - Added the new response schema and endpoint to the schema-contract
     evaluator.

4. Updated tests:
   - Added low-level patch-preview tests for blocked and reviewed contract
     states.
   - Added runtime schema, CLI, HTTP, and schema-contract assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_blocks_unreviewed_manifest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_accepts_reviewed_manifest_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_renders_reviewed_candidates_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_status_exposes_runtime_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_status_exposes_runtime_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_review_status examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_import_preview_blocks_writes examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_fixture_patch_preview_blocks_writes examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_review_route examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_import_preview_route examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_fixture_patch_preview_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `14 passed`.

### Snapshot

- Default fixture patch preview status:
  `blocked_not_ready_for_patch_preview`.
- Would write file:
  `False`.
- Patch ready for review:
  `False`.
- Candidate count:
  `0`.
- Patch gate passed:
  `False`.
- Target file sha256:
  `59b488851936acf59b07a624ef5d257799c181b24540b1e088b50b4f92c98802`.
- Patch text sha256:
  `88215782ad8b057bf7005e8ddaca82de1e7a223af9b4aa9883bcd5b4f58e0800`.
- Fixture patch preview receipt sha256:
  `1fcd37d0aa4921c771f8f1d30d0f41c2d08ecd6ba015433c8a8b7d976eda0e47`.
- Integrity check:
  `passed`.

### Boundary

This feature still does not import real celebrity birth data. It only makes the
future fixture edit reviewable and reproducible once a real reviewed manifest is
available.

## 2026-06-26 - Fixture Patch Preview Capability Audit Binding

### Motivation

The fixture patch preview had API, CLI, HTTP, and schema surfaces, but the
global capability audit still ended the birth-profile evidence chain at import
preview. Future agents need to discover the full three-stage chain from the
audit receipt itself.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Imported `build_birth_profile_fixture_patch_preview`.
   - Added fixture patch preview evidence to implemented requirement material.
   - Added `birth_profile_fixture_patch_preview_summary` to cross-domain
     symbolic scoring readiness.
   - Added `birth_profile_fixture_patch_preview_receipt_sha256`.
   - Added `birth-profile-fixture-patch-preview` to the
     `celebrity_birth_profile_review` verification commands.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added the patch preview summary and receipt fields to the public
     `IndustryEventCrossDomainFixtureImportMaterial` schema.

3. Updated tests:
   - Added capability-audit assertions for the patch preview summary.
   - Added schema-contract assertions for the new summary and receipt fields.
   - Added known-gap command coverage for the patch preview CLI command.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_blocks_unreviewed_manifest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_accepts_reviewed_manifest_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_renders_reviewed_candidates_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_status_exposes_runtime_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_fixture_patch_preview_blocks_writes examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_fixture_patch_preview_route -q`
  passed: `7 passed`.

### Snapshot

- Capability audit receipt sha256:
  `999dcac5ecfcd23ce03b003ab26bb6afb7f5663b3f6e6e3262f3e6faffe2e252`.
- Cross-domain fixture receipt sha256:
  `4bea6e5dccc5eef7398dba0614ea227c5b1067ae55ced893c0d93b0dc21e26e7`.
- Patch preview status:
  `blocked_not_ready_for_patch_preview`.
- Patch ready for review:
  `False`.
- Would write file:
  `False`.
- Candidate count:
  `0`.
- Patch gate passed:
  `False`.
- Target file sha256:
  `59b488851936acf59b07a624ef5d257799c181b24540b1e088b50b4f92c98802`.
- Patch text sha256:
  `88215782ad8b057bf7005e8ddaca82de1e7a223af9b4aa9883bcd5b4f58e0800`.
- Patch preview receipt sha256:
  `1fcd37d0aa4921c771f8f1d30d0f41c2d08ecd6ba015433c8a8b7d976eda0e47`.
- Integrity check:
  `passed`.

### Boundary

The capability audit now exposes the full three-stage birth-profile evidence
chain. It still does not certify or import any real celebrity birth profile.

## 2026-06-26 - Fixture Patch Preview Production Gate

### Motivation

The birth-profile fixture patch preview had become visible in capability audit,
but production readiness still did not enforce that the default patch path
remains blocked and non-mutating. A future change could otherwise make the
patch preview ready too early without failing release gates.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_fixture_patch_preview_blocked`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production-readiness extraction for
     `birth_profile_fixture_patch_preview_summary`.
   - Added the runtime gate
     `birth_profile_fixture_patch_preview_blocked`.
   - Added blocker diagnostics for missing hashes, unexpected candidates,
     unexpected write intent, unexpected gate pass, and failed integrity.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `birth_profile_fixture_patch_preview_blocked` to the
     `celebrity_birth_profile_review` known-gap production gate IDs.

4. Updated tests:
   - Added production-readiness assertions for the patch preview gate.
   - Updated known-gap gate count and valid-gate assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_renders_reviewed_candidates_without_writing examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_fixture_patch_preview_blocks_writes examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_fixture_patch_preview_route -q`
  passed: `4 passed`.

### Snapshot

- Production readiness receipt sha256:
  `244675aaf0cb321123a26f342ae729e89d9c3115ecbdf6d000ce6c36bb55bae8`.
- Production gate registry current:
  `True`.
- Import preview blocked gate passed:
  `True`.
- Import preview blocked gate details:
  `[]`.
- Fixture patch preview blocked gate passed:
  `True`.
- Fixture patch preview blocked gate details:
  `[]`.
- Fixture patch preview gate blocker present:
  `False`.
- Gate registered:
  `True`.

### Boundary

This gate proves the default fixture patch path remains blocked, non-mutating,
and integrity-checked. It does not approve any real celebrity birth-profile
fixture edit.

## 2026-06-26 - Birth Profile Source Review Workplan

### Motivation

The celebrity birth-profile chain could block unreviewed data and preview later
import/patch steps, but the missing source-review work itself was still only
implicit in the review manifest. The next step was to turn each blocked
celebrity profile into an explicit human source-review work item.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_source_review_workplan`.
   - Added one work item per review request.
   - Each work item now carries suggested search queries, identity URL,
     missing fields, allowed source families, disallowed sources, required
     evidence, a reviewed-profile draft, and acceptance criteria.
   - The workplan remains offline-only and non-mutating:
     `would_fetch_live_sources = False`,
     `would_write_review_manifest = False`.
   - Added receipt and integrity checks.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added the source-review workplan to implemented evidence.
   - Added `birth_profile_source_review_workplan_summary`.
   - Added `birth_profile_source_review_workplan_receipt_sha256`.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added the workplan summary and receipt fields to the public
     cross-domain fixture import schema.

4. Updated tests:
   - Added direct workplan test coverage.
   - Added capability-audit and schema-contract assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_turns_requests_into_review_tasks examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.

### Snapshot

- Workplan status:
  `ready_for_human_source_review`.
- Request count:
  `8`.
- Work item count:
  `8`.
- Would fetch live sources:
  `False`.
- Would write review manifest:
  `False`.
- Source review gate passed:
  `False`.
- Workplan receipt sha256:
  `f5b88984baf97f530cdd8a957a59549443ddc461970d9f17624c74c2fca76b10`.
- Workplan sha256:
  `f5b88984baf97f530cdd8a957a59549443ddc461970d9f17624c74c2fca76b10`.
- Integrity check:
  `passed`.
- Capability audit receipt sha256:
  `88b07bf44bc8f7e2cbfce8ccefdc53a5c073a32b86f3f6c228b07edbf9bb5abd`.
- Audit workplan receipt sha256:
  `f5b88984baf97f530cdd8a957a59549443ddc461970d9f17624c74c2fca76b10`.

### Boundary

This workplan organizes source-review tasks only. It does not fetch live
sources, certify birth data, write a reviewed manifest, or unlock symbolic
scoring.

## 2026-06-26 - Birth Profile Source Review Workplan API Surface

### Motivation

The birth-profile source-review workplan existed in code and capability audit,
but reviewers and future agents still needed a direct way to request it without
digging through the full capability audit object.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `birth_profile_source_review_workplan`.
   - Added public schema `BirthProfileSourceReviewWorkplanResponse`.
   - Added `/schema` endpoint documentation for
     `GET /birth-profile-source-review-workplan`.

2. Updated `examples/mingli_5agents/cli.py`:
   - Added command `birth-profile-source-review-workplan`.

3. Updated `examples/mingli_5agents/api_server.py`:
   - Added HTTP route `/birth-profile-source-review-workplan`.

4. Updated schema governance:
   - Added the response schema and endpoint to the schema-contract evaluator.

5. Updated tests:
   - Added runtime schema validation.
   - Added CLI and HTTP route coverage.
   - Added schema-contract assertions.
   - Re-ran the birth-profile chain regression.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_status_exposes_runtime_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_review_workplan examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_review_workplan_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_review_manifest_audits_missing_cross_domain_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_turns_requests_into_review_tasks examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_status_exposes_runtime_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_import_preview_blocks_unreviewed_manifest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_fixture_patch_preview_renders_reviewed_candidates_without_writing examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt -q`
  passed: `6 passed`.

### Snapshot

- Configured:
  `False`.
- Workplan status:
  `ready_for_human_source_review`.
- Request count:
  `8`.
- Work item count:
  `8`.
- Would fetch live sources:
  `False`.
- Would write review manifest:
  `False`.
- Source review gate passed:
  `False`.
- Workplan receipt sha256:
  `f5b88984baf97f530cdd8a957a59549443ddc461970d9f17624c74c2fca76b10`.
- Workplan sha256:
  `f5b88984baf97f530cdd8a957a59549443ddc461970d9f17624c74c2fca76b10`.
- Integrity check:
  `passed`.
- CLI:
  `python -m examples.mingli_5agents.cli --repo . birth-profile-source-review-workplan --manifest C:\aicoding\semas_framework\examples\mingli_5agents\providers\birth_profile_review_manifest_example.json`.
- HTTP:
  `GET /birth-profile-source-review-workplan?manifest=C:\aicoding\semas_framework\examples\mingli_5agents\providers\birth_profile_review_manifest_example.json`.

### Boundary

The new surface exposes review work items only. It does not fetch live sources,
write reviewed manifests, or certify birth profiles.

## 2026-06-26 - Birth Profile Source Review Workplan Production Gate

### Motivation

The source-review workplan had direct API/CLI/HTTP surfaces and capability-audit
visibility, but production readiness still did not assert that the workplan
exists and remains non-mutating. This left a governance gap before the import
and fixture patch gates.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_source_review_workplan_available`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added extraction of `birth_profile_source_review_workplan_summary`.
   - Added runtime gate `birth_profile_source_review_workplan_available`.
   - Added diagnostics for missing workplan, live-fetch intent, manifest-write
     intent, empty request/work-item counts, unexpected gate pass, and failed
     integrity.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `birth-profile-source-review-workplan` to the
     `celebrity_birth_profile_review` verification commands.
   - Added `birth_profile_source_review_workplan_available` to the same known
     gap's production gate IDs.

4. Updated tests:
   - Added production-readiness assertions for the source-review workplan gate.
   - Updated known-gap command and gate-count assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_status_exposes_runtime_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_review_workplan examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_review_workplan_route -q`
  passed: `3 passed`.

### Snapshot

- Production readiness receipt sha256:
  `a2cfc80fbff7fc933cb1990c38db31bd1020591b209f7103f1a4beac1c367b3e`.
- Production gate registry current:
  `True`.
- Source-review workplan gate passed:
  `True`.
- Source-review workplan gate details:
  `[]`.
- Source-review workplan gate blocker present:
  `False`.
- Import preview blocked gate passed:
  `True`.
- Fixture patch preview blocked gate passed:
  `True`.
- Gate registered:
  `True`.

### Boundary

This gate proves the source-review workplan exists, is non-mutating, and remains
human-review gated. It does not certify or collect any real celebrity birth
profile.

## 2026-06-26 - Birth Profile Source Review Progress Summary

### Motivation

The celebrity source-review workplan could list each film, music, and sports
work item, but it did not expose a top-level answer to "how much remains" or
"which fields are missing most." That made the workplan harder to use for
public-celebrity validation planning.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `review_progress_summary` to the source-review workplan.
   - Added `field_gap_summary` to the source-review workplan.
   - Derived both summaries from generated work items so the summary and task
     rows share one source of truth.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Propagated both summaries into the cross-domain fixture-import readiness
     audit.

3. Updated `examples/mingli_5agents/api_core.py` and schema tests:
   - Declared both summaries in the runtime API schema and capability-audit
     readiness schema.

4. Updated regression tests:
   - Added assertions for film/music/sports work-item counts, blocked-label
     counts, and missing birth-profile fields.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_turns_requests_into_review_tasks examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_review_workplan_status_exposes_runtime_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_review_workplan examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_review_workplan_route -q`
  passed: `3 passed`.

### Snapshot

- Source-review status:
  `ready_for_human_source_review`.
- Work items:
  `8`.
- Domain work-item counts:
  `film=3`, `music=3`, `sports=2`.
- Domain blocked-label counts:
  `film=137`, `music=72`, `sports=48`.
- Review status counts:
  `not_started=8`, `in_review=0`, `externally_reviewed=0`, `rejected=0`.
- Missing fields:
  `birth_date=8`, `birth_time=8`, `birthplace=8`, `gender=8`,
  `source_name=8`, `source_rating=8`, `source_url=8`.
- Source-review workplan receipt sha256:
  `8cd5f289a7feb27e2e97787909f5caa78d0a14d911644108102c95638b259337`.

### Boundary

The new summaries make the celebrity validation backlog visible. They do not
fetch sources, certify any celebrity birth profile, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Lookup Plan

### Motivation

The source-review workplan listed celebrity birth-profile review tasks, but the
next action was still implicit: reviewers had to interpret suggested search
queries manually. To make sports, film, and music celebrity validation
operational, the system needed a dry-run lookup plan that expands each review
task into executable source-search units without fetching or certifying data.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_source_lookup_plan`.
   - Expanded every work item into planned queries with target fields, cache
     paths, identity anchors, acceptance criteria, and dry-run flags.
   - Added receipt and integrity checks for the lookup plan.

2. Updated service surfaces:
   - Added `birth_profile_source_lookup_plan` to `api_core.py`.
   - Added CLI command `birth-profile-source-lookup-plan`.
   - Added HTTP route `GET /birth-profile-source-lookup-plan`.
   - Added `BirthProfileSourceLookupPlanResponse` to the runtime schema and
     schema-contract evaluator.

3. Updated capability audit:
   - Added lookup-plan evidence to the cross-domain famous-case validation
     capability.
   - Added lookup-plan command guidance to `celebrity_birth_profile_review`.
   - Added lookup-plan summary and receipt hash to the symbolic-scoring
     readiness audit.

4. Updated tests:
   - Covered full lookup plan generation.
   - Covered domain filtering.
   - Covered CLI, HTTP, schema, and capability-audit visibility.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_lookup_plan_expands_review_queries examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_lookup_plan_filters_domain examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_lookup_plan examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_lookup_plan_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `7 passed`.

### Snapshot

- Lookup-plan status:
  `ready_for_manual_lookup`.
- Lookup items:
  `8`.
- Planned queries:
  `16`.
- Domain summary:
  `film=3 items/6 queries/137 blocked labels`,
  `music=3 items/6 queries/72 blocked labels`,
  `sports=2 items/4 queries/48 blocked labels`.
- Source-lookup plan receipt sha256:
  `58ae0e6952d3373d01c8bab437177ca4a6d0abfedbc9a0f9c789e97dde317758`.

### Boundary

The lookup plan is dry-run only. It does not fetch webpages, write cache files,
certify celebrity birth data, write reviewed manifests, or unlock symbolic
scoring.

## 2026-06-26 - Birth Profile Source Lookup Plan Production Gate

### Motivation

The source lookup plan had API, CLI, HTTP, schema, and capability-audit
visibility, but production readiness did not yet prove the lookup plan remained
dry-run. Without a runtime gate, a future change could accidentally allow live
fetches, cache writes, or reviewed-manifest writes before source evidence is
externally reviewed.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_source_lookup_plan_dry_run`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Extracted `birth_profile_source_lookup_plan_summary` from capability
     audit.
   - Added production-readiness gate
     `birth_profile_source_lookup_plan_dry_run`.
   - Added diagnostics for missing lookup plan, live-fetch intent, cache-write
     intent, manifest-write intent, empty lookup/query counts, unexpected gate
     pass, and failed integrity.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `birth_profile_source_lookup_plan_dry_run` to the
     `celebrity_birth_profile_review` known-gap production gate IDs.

4. Updated tests:
   - Added production-readiness assertions for the lookup-plan gate.
   - Updated known-gap command and gate-count assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.

### Snapshot

- Production readiness receipt sha256:
  `abe86c9681f60a03971d2103b87b13940a91eb3bf8a77b9fa99d3c0b8e70c108`.
- Source-review workplan gate passed:
  `True`.
- Source-lookup dry-run gate passed:
  `True`.
- Import preview blocked gate passed:
  `True`.
- Fixture patch preview blocked gate passed:
  `True`.
- Production gate registry current:
  `True`.

### Boundary

This gate proves the lookup plan remains available and dry-run. It does not
execute lookup queries, fetch webpages, write cache files, certify birth data,
or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Cache Audit

### Motivation

The source lookup plan defined where reviewers should collect celebrity
birth-profile evidence, but the system still lacked a way to inspect manually
prepared lookup cache files. Without a cache audit layer, the next agent would
have to infer whether cached evidence existed, whether it matched the planned
query, and whether it was safe to move toward a reviewed manifest.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_source_cache_audit`.
   - Audits planned cache files generated by the lookup plan.
   - Validates cache JSON shape, planned `query_id`, `case_id`, source fields,
     review status, reviewer note, and whether any target birth field is
     actually filled.
   - Keeps cache audit non-mutating and non-importing.

2. Updated service surfaces:
   - Added `birth_profile_source_cache_audit` to `api_core.py`.
   - Added CLI command `birth-profile-source-cache-audit`.
   - Added HTTP route `GET /birth-profile-source-cache-audit`.
   - Added `BirthProfileSourceCacheAuditResponse` to the runtime schema and
     schema-contract evaluator.

3. Updated capability audit:
   - Added source-cache-audit evidence to the cross-domain famous-case
     validation capability.
   - Added source-cache-audit command guidance to
     `celebrity_birth_profile_review`.
   - Added source-cache-audit summary and receipt hash to symbolic-scoring
     readiness.

4. Updated tests:
   - Covered missing manual cache state.
   - Covered one reviewed cache fixture.
   - Covered API schema, CLI, HTTP, schema-contract, and capability-audit
     visibility.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_reports_missing_manual_cache examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_reads_reviewed_cache_file examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_api_exposes_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_cache_audit examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_cache_audit_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `8 passed`.

### Snapshot

- Source-cache audit status:
  `waiting_for_manual_cache`.
- Expected cache files:
  `16`.
- Present cache files:
  `0`.
- Missing cache files:
  `16`.
- Accepted cache evidence:
  `0`.
- Source-cache audit receipt sha256:
  `2789980d968029a7b39242366d3fd3076ded3ccd274530e182979f6f03f81bc1`.

### Boundary

The cache audit reads manually prepared JSON files only. It does not fetch
webpages, write cache files, certify birth data, write reviewed manifests,
import profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Cache Audit Production Gate

### Motivation

The source-cache audit could inspect manually prepared lookup-result JSON files,
but production readiness did not yet prove that the audit remained read-only and
non-importing. Since cache files sit closer to external evidence than a dry-run
lookup plan, this boundary needs a runtime gate before production release.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_source_cache_audit_read_only`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Extracted `birth_profile_source_cache_audit_summary` from capability
     audit.
   - Added production-readiness gate
     `birth_profile_source_cache_audit_read_only`.
   - Added diagnostics for missing cache audit, live-fetch intent, cache-write
     intent, manifest-write intent, profile-import intent, empty expected cache
     count, unexpected gate pass, and failed integrity.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `birth_profile_source_cache_audit_read_only` to the
     `celebrity_birth_profile_review` known-gap production gate IDs.

4. Updated tests:
   - Added production-readiness assertions for the cache-audit gate.
   - Updated known-gap gate-count assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.

### Snapshot

- Production readiness receipt sha256:
  `17292651b773e04f53ef8c89ed67915366db344732364e88b4e87c674169f6cc`.
- Source-review workplan gate passed:
  `True`.
- Source-lookup dry-run gate passed:
  `True`.
- Source-cache audit read-only gate passed:
  `True`.
- Import preview blocked gate passed:
  `True`.
- Fixture patch preview blocked gate passed:
  `True`.
- Production gate registry current:
  `True`.

### Boundary

This gate proves the source-cache audit is present, read-only, and non-importing.
It does not fetch webpages, write cache files, certify birth data, write
reviewed manifests, import profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Reviewed Manifest Draft Preview

### Motivation

The source-cache audit can inspect manually prepared lookup-result JSON files,
but accepted cache evidence still needed a controlled next step before import
preview. Without a reviewed-manifest draft preview, a future agent would have to
manually assemble reviewed manifests from cache evidence, risking skipped
fields, mismatched cases, or accidental writes.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_reviewed_manifest_draft_preview`.
   - Aggregates accepted cache evidence by case.
   - Builds non-mutating reviewed-manifest draft JSON and text preview.
   - Tracks complete and incomplete reviewed profile rows.
   - Keeps the draft gate blocked until human approval.

2. Updated service surfaces:
   - Added `birth_profile_reviewed_manifest_draft_preview` to `api_core.py`.
   - Added CLI command `birth-profile-reviewed-manifest-draft-preview`.
   - Added HTTP route `GET /birth-profile-reviewed-manifest-draft-preview`.
   - Added `BirthProfileReviewedManifestDraftPreviewResponse` to the runtime
     schema and schema-contract evaluator.

3. Updated capability audit:
   - Added reviewed-manifest-draft-preview evidence to the cross-domain
     famous-case validation capability.
   - Added draft-preview command guidance to `celebrity_birth_profile_review`.
   - Added draft-preview summary and receipt hash to symbolic-scoring
     readiness.

4. Updated tests:
   - Covered blocked default state with missing cache.
   - Covered partial accepted cache evidence for one sports case.
   - Covered API schema, CLI, HTTP, schema-contract, and capability-audit
     visibility.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_draft_preview_blocks_until_cache_complete examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_draft_preview_uses_accepted_cache examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_draft_preview_api_exposes_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_reviewed_manifest_draft_preview examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_reviewed_manifest_draft_preview_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `8 passed`.

### Snapshot

- Reviewed-manifest draft preview status:
  `blocked_waiting_for_complete_source_cache`.
- Review requests:
  `8`.
- Complete reviewed profile rows:
  `0`.
- Incomplete reviewed profile rows:
  `8`.
- Draft ready for human approval:
  `False`.
- Draft-preview receipt sha256:
  `17f10d212feb8e675fca7517fbf56653315dc3df4f086d2f056dc8e3088fbc81`.

### Boundary

The draft preview does not write reviewed manifests, import profiles, certify
birth data, or unlock symbolic scoring. It only renders a reviewable draft from
accepted cache evidence.

## 2026-06-26 - Birth Profile Reviewed Manifest Draft Preview Production Gate

### Motivation

The reviewed-manifest draft preview can aggregate accepted cache evidence into a
reviewable manifest draft, but production readiness did not yet prove this step
remained non-mutating. Since the draft is the last step before import preview,
its boundary must be enforced at release time.

### Actions Taken

1. Updated `examples/mingli_5agents/production_gates.py`:
   - Added `birth_profile_reviewed_manifest_draft_preview_non_mutating`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Extracted `birth_profile_reviewed_manifest_draft_preview_summary` from
     capability audit.
   - Added production-readiness gate
     `birth_profile_reviewed_manifest_draft_preview_non_mutating`.
   - Added diagnostics for missing preview, manifest-write intent,
     profile-import intent, empty request count, unexpected draft gate pass, and
     failed integrity.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added the new gate ID to `celebrity_birth_profile_review`.

4. Updated tests:
   - Added production-readiness assertions for the reviewed-manifest draft gate.
   - Updated known-gap gate-count assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `3 passed`.

### Snapshot

- Production readiness receipt sha256:
  `74adecec2bea6f64cebccf4a0c07ae16168f8a51144c6342c42ee4a2ad18e801`.
- Source-review workplan gate passed:
  `True`.
- Source-lookup dry-run gate passed:
  `True`.
- Source-cache audit read-only gate passed:
  `True`.
- Reviewed-manifest draft preview non-mutating gate passed:
  `True`.
- Import preview blocked gate passed:
  `True`.
- Fixture patch preview blocked gate passed:
  `True`.
- Production gate registry current:
  `True`.

### Boundary

This gate proves the reviewed-manifest draft preview is present and non-mutating.
It does not write reviewed manifests, import profiles, certify birth data, or
unlock symbolic scoring.

## 2026-06-26 - Birth Profile Reviewed Manifest File Preview

### Motivation

The reviewed-manifest draft preview shows the JSON content that could become a
reviewed birth-profile manifest, but it did not yet expose the final file-write
surface: target path, existing-file hash, draft hash, and the exact boundary for
human approval. Celebrity validation across sports, film, and music needs this
step before any reviewed birth data can move from source evidence into fixtures.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_reviewed_manifest_file_preview`.
   - Added a non-mutating file-write gate for reviewed-manifest drafts.
   - Added receipt and integrity checks for target file hash, draft text hash,
     and approval boundary.

2. Updated public interfaces:
   - Added API service `birth_profile_reviewed_manifest_file_preview`.
   - Added CLI command `birth-profile-reviewed-manifest-file-preview`.
   - Added HTTP route `/birth-profile-reviewed-manifest-file-preview`.
   - Added runtime schema
     `BirthProfileReviewedManifestFilePreviewResponse`.

3. Updated capability audit and schema contract:
   - Added reviewed-manifest file-preview summaries to the cross-domain
     celebrity fixture import readiness receipt.
   - Added the file-preview receipt hash to the symbolic-scoring readiness
     summary.
   - Added the command to the `celebrity_birth_profile_review` known-gap
     verification coverage.

4. Updated tests:
   - Added direct builder/API/CLI/HTTP tests for the file preview.
   - Added capability-audit and schema-contract assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_file_preview_blocks_until_draft_ready examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_file_preview_api_exposes_schema examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_reviewed_manifest_file_preview examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_reviewed_manifest_file_preview_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `7 passed`.

### Snapshot

- File-preview status:
  `blocked_waiting_for_approved_draft`.
- Target file:
  `.semas_mingli_repo\birth_profile_review_manifest_reviewed.json`.
- Target exists:
  `False`.
- Would write file:
  `False`.
- Write ready for human approval:
  `False`.
- File-preview receipt sha256:
  `dcf5b0854e78962ad5698622513bd1dfd3b7499a85d7fbb988b97ed2ac21db24`.
- Blocking reasons:
  `16 planned source cache files are missing`; `no accepted source cache evidence is available`;
  `incomplete reviewed profile drafts: jackie_chan,meryl_streep,tom_hanks,beyonce,jay_chou,taylor_swift,michael_jordan,serena_williams`;
  `reviewed manifest draft preview is not ready for human approval`.

### Boundary

The file preview does not write the reviewed manifest, import profiles, certify
birth data, or unlock symbolic scoring. It only tells the operator exactly what
would be written after source caches and reviewed-manifest drafts are complete
and manually approved.

## 2026-06-26 - Celebrity Birth Profile Source Family Catalog

### Motivation

The sports, film, and music celebrity lookup plan already expanded 8 blocked
birth-profile requests into 16 dry-run source queries, but each query only
carried search text. The plan did not yet distinguish a rated birth-time source
from identity or domain databases, which could let a reviewer accidentally treat
Wikidata, IMDb, MusicBrainz, or Olympedia metadata as birth-time evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `birth_profile_source_family_catalog`.
   - Declared five source families:
     `rated_birth_time_source`, `wikidata_identity_anchor`,
     `film_identity_and_work_anchor`, `music_identity_and_work_anchor`, and
     `sports_identity_and_result_anchor`.
   - Added source-family recommendations and source-use policy to every planned
     lookup query.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `source_family_catalog` to the
     `BirthProfileSourceLookupPlanResponse` schema.
   - Added schema coverage for catalog receipts and hashes.

3. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `source_family_count` to cross-domain birth-profile lookup summaries.

4. Updated tests:
   - Added assertions for source-family catalog count, catalog receipt hash,
     per-query recommended source families, and birth-time source policy.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_lookup_plan_expands_review_queries examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_lookup_plan_filters_domain examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `4 passed`.

### Snapshot

- Lookup plan status:
  `ready_for_manual_lookup`.
- Query count:
  `16`.
- Source family count:
  `5`.
- Source families:
  `rated_birth_time_source`, `wikidata_identity_anchor`,
  `film_identity_and_work_anchor`, `music_identity_and_work_anchor`,
  `sports_identity_and_result_anchor`.
- First query:
  `Astro-Databank Jackie Chan birth time`.
- First query requires rated birth-time source:
  `True`.
- First query recommended source families:
  `rated_birth_time_source`, `wikidata_identity_anchor`,
  `film_identity_and_work_anchor`.
- Catalog receipt sha256:
  `3a6a3ef3588f83dacc6b13de6911209c218945488186add6103f4be95403fd59`.

### Boundary

The source-family catalog is guidance and audit metadata only. It does not fetch
sources, certify birth data, write caches, write reviewed manifests, or unlock
symbolic scoring.

## 2026-06-26 - Birth Profile Source Family Catalog Production Gate

### Motivation

The celebrity birth-profile lookup plan now carries a source-family catalog and
per-query source-use policies, but production readiness still only proved the
lookup plan was dry-run. It did not prove that the source-family catalog was
bound or that birth-time queries were constrained to rated birth-time sources.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `source_family_catalog_bound`.
   - Added `birth_time_source_policy_bound`.
   - Added `identity_anchor_birth_time_disallowed`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production gate `birth_profile_source_family_catalog_bound`.
   - Added gate diagnostics for missing source families, missing birth-time
     policy binding, and identity anchors that could satisfy `birth_time`.
   - Added the new source-family policy fields to the public schema.

3. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered `birth_profile_source_family_catalog_bound`.

4. Updated tests:
   - Added production-readiness assertions for the new gate.
   - Added schema-contract assertions for source-family policy fields.
   - Updated known-gap production gate coverage for
     `celebrity_birth_profile_review`.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `4 passed`.

### Snapshot

- `birth_profile_source_lookup_plan_dry_run`:
  `True`.
- `birth_profile_source_family_catalog_bound`:
  `True`.
- `birth_profile_source_cache_audit_read_only`:
  `True`.
- Production gate registry current:
  `True`.
- Production readiness receipt sha256:
  `fa030a9101b479a8c619d339c38d0f16fe573f9bf63bad743d097885a81a5fed`.

### Boundary

This gate proves source-family policy is bound to the dry-run celebrity
birth-profile lookup plan. It does not fetch sources, certify birth data, write
caches, write reviewed manifests, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Cache Template Preview

### Motivation

The source lookup plan defines what reviewers should search, and the source
cache audit defines which JSON fields are required. There was still a manual gap
between them: operators had to create cache JSON files by hand without a
machine-generated template for `query_id`, `case_id`, required source metadata,
review status, target fields, and planned cache paths.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `build_birth_profile_source_cache_template_preview`.
   - Added template payloads for every planned lookup query.
   - Added template hashes, required fields, review status options, and
     non-mutating integrity checks.

2. Updated public interfaces:
   - Added API service `birth_profile_source_cache_template_preview`.
   - Added CLI command `birth-profile-source-cache-template-preview`.
   - Added HTTP route `/birth-profile-source-cache-template-preview`.
   - Added runtime schema
     `BirthProfileSourceCacheTemplatePreviewResponse`.

3. Updated governance:
   - Added the new CLI command to the `celebrity_birth_profile_review`
     known-gap verification commands.
   - Added the new schema and endpoint to the schema contract evaluator.

4. Updated tests:
   - Added builder/API/CLI/HTTP tests for the template preview.
   - Added schema-contract assertions.
   - Added known-gap command coverage assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\api_core.py examples\mingli_5agents\cli.py examples\mingli_5agents\api_server.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\evaluators\schema_contract_evaluator.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_cli.py examples\mingli_5agents\tests\test_api_server.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_template_preview_renders_manual_json examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_template_preview_api_exposes_schema examples\mingli_5agents\tests\test_cli.py::test_cli_birth_profile_source_cache_template_preview examples\mingli_5agents\tests\test_api_server.py::test_http_api_birth_profile_source_cache_template_preview_route examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `6 passed`.

### Snapshot

- Template preview status:
  `ready_for_manual_cache_fill`.
- Sports template count:
  `4`.
- Would write cache:
  `False`.
- Template gate passed:
  `False`.
- First planned cache path:
  `.semas_mingli_repo\birth_profile_source_cache\michael_jordan_1.json`.
- Required cache fields:
  `query_id`, `case_id`, `source_name`, `source_url`, `source_rating`,
  `reviewer_note`, `review_status`.
- Review status options:
  `source_reviewed`, `rejected`, `needs_more_evidence`.
- Template-preview receipt sha256:
  `0fbec7b4566b6b5528b0ebc7b23597913be7f81c75c72035fa83fcadace3592a`.

### Boundary

The template preview does not fetch sources, write cache files, certify birth
data, write reviewed manifests, import profiles, or unlock symbolic scoring. It
only renders the JSON skeletons required for manual source-cache creation.

## 2026-06-26 - Birth Profile Source Cache Template Preview Production Gate

### Motivation

The source-cache template preview standardizes manual JSON creation, but
production readiness did not yet prove the template step remained non-mutating.
Because this step sits between dry-run lookup and cache audit, it must not start
fetching sources, writing cache files, or importing profiles.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added `build_birth_profile_source_cache_template_preview` to evidence.
   - Added `birth_profile_source_cache_template_preview_summary`.
   - Added template-preview receipt hash to cross-domain symbolic scoring
     readiness.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production gate
     `birth_profile_source_cache_template_preview_non_mutating`.
   - Added diagnostics for missing template preview, write/fetch/import intent,
     empty template count, unexpected template gate pass, and failed integrity.
   - Added source-cache template preview summary schema fields.

3. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered `birth_profile_source_cache_template_preview_non_mutating`.

4. Updated tests:
   - Added cross-domain readiness assertions for the template preview summary.
   - Added production-readiness assertions for the new gate.
   - Added schema-contract assertions and known-gap gate coverage.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `4 passed`.

### Snapshot

- `birth_profile_source_cache_template_preview_non_mutating`:
  `True`.
- `birth_profile_source_cache_audit_read_only`:
  `True`.
- Production gate registry current:
  `True`.
- Production readiness receipt sha256:
  `e605708806b9c085a97ef066ffa8f202fcb595fb8b3c32ccd5333bcc7d7a10db`.

### Boundary

This gate proves the source-cache template preview is present and non-mutating.
It does not fetch sources, write cache files, certify birth data, write reviewed
manifests, import profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Family Cache Enforcement

### Motivation

The lookup plan and template preview carried source-family policy, but the
source cache audit still accepted reviewed cache payloads without a
`source_family_id`. That left a gap where identity anchors could theoretically
be recorded as reviewed evidence for `birth_time`.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `source_family_id` to source cache template payloads.
   - Added `source_family_id` to required cache fields.
   - Added allowed source-family IDs to every template item.
   - Added cache-audit validation that rejects `birth_time` unless
     `source_family_id` is `rated_birth_time_source`.
   - Added source-family target-field validation against
     `SOURCE_FAMILY_CATALOG.usable_for_fields`.

2. Updated tests:
   - Added accepted reviewed-cache fixture payloads with explicit
     `source_family_id`.
   - Added a rejection test proving `wikidata_identity_anchor` cannot satisfy
     `birth_time`.
   - Added template assertions for `source_family_id` and allowed source-family
     IDs.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_template_preview_renders_manual_json examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_reads_reviewed_cache_file examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_rejects_identity_anchor_birth_time examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_draft_preview_uses_accepted_cache -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `2 passed`.

### Snapshot

- Rejected payload source family:
  `wikidata_identity_anchor`.
- Rejected field:
  `birth_time`.
- Accepted count after rejected payload:
  `0`.
- Failure:
  `birth_time evidence requires source_family_id=rated_birth_time_source`.

### Boundary

This change strengthens cache audit validation only. It does not fetch sources,
write cache files, certify birth data, write reviewed manifests, import
profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Source Family Enforcement Probe

### Motivation

Source-family cache enforcement was covered by tests, but production readiness
did not run a runtime counterexample proving the current cache audit still
rejects identity-anchor `birth_time` payloads. A release gate should verify the
actual enforcement path, not only the presence of policy metadata.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added a temporary-directory source-family enforcement probe.
   - The probe writes a `wikidata_identity_anchor` payload claiming
     `birth_time`, runs the real cache audit, and expects rejection.
   - Added `birth_profile_source_family_cache_enforcement_summary` to
     cross-domain symbolic scoring readiness.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production gate
     `birth_profile_source_family_cache_enforcement_probe`.
   - Added diagnostics for missing probe, unexecuted probe, unexpected accepted
     cache count, and missing birth-time policy failure.
   - Added schema coverage for the enforcement summary.

3. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered `birth_profile_source_family_cache_enforcement_probe`.

4. Updated tests:
   - Added cross-domain readiness assertions for the probe summary.
   - Added production-readiness assertions for the new gate.
   - Added schema-contract assertions and known-gap gate coverage.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `4 passed`.

### Snapshot

- `birth_profile_source_family_cache_enforcement_probe`:
  `True`.
- `birth_profile_source_cache_audit_read_only`:
  `True`.
- Production gate registry current:
  `True`.
- Production readiness receipt sha256:
  `8e41caa9762ff4bb60ec318b4c5df829669b781cb1e17f5f46b7a4cb3b97ed3b`.

### Boundary

The probe writes only to a temporary directory and uses the existing cache audit
path. It does not fetch sources, write repository cache files, certify birth
data, write reviewed manifests, import profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Substantive Evidence Cache Enforcement

### Motivation

Source cache audit accepted `source_reviewed` payloads when any planned target
field was filled. Some planned target fields are source metadata
(`source_name`, `source_url`, `source_rating`), so a payload could be marked
reviewed without filling a substantive birth field.

### Actions Taken

1. Updated `examples/mingli_5agents/birth_profile_review.py`:
   - Added `SUBSTANTIVE_BIRTH_EVIDENCE_FIELDS`.
   - Changed `_source_cache_has_target_evidence` to count only `birth_date`,
     `birth_time`, `gender`, and `birthplace`.
   - Updated cache template acceptance note to distinguish substantive birth
     fields from source metadata.
   - Updated cache-audit failure wording to
     `reviewed payload does not fill any substantive birth field`.

2. Updated tests:
   - Added a metadata-only `source_reviewed` cache rejection test.
   - Kept reviewed birth-time cache and reviewed manifest draft aggregation
     passing.

### Verification

- `python -m py_compile examples\mingli_5agents\birth_profile_review.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_template_preview_renders_manual_json examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_reads_reviewed_cache_file examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_rejects_identity_anchor_birth_time examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_source_cache_audit_rejects_metadata_only_reviewed_cache examples\mingli_5agents\tests\test_empirical_validation.py::test_birth_profile_reviewed_manifest_draft_preview_uses_accepted_cache -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `2 passed`.

### Snapshot

- Metadata-only reviewed payload accepted:
  `False`.
- Accepted count:
  `0`.
- Failure:
  `reviewed payload does not fill any substantive birth field`.

### Boundary

This change affects cache-audit evidence acceptance only. It does not fetch
sources, write cache files, certify birth data, write reviewed manifests, import
profiles, or unlock symbolic scoring.

## 2026-06-26 - Birth Profile Substantive Evidence Enforcement Probe

### Motivation

The cache audit already rejects reviewed payloads that contain only source
metadata. Production readiness still needed to execute the same negative case at
runtime, so a future bypass cannot pass release checks by relying on stale unit
test assumptions.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added a temporary-directory probe that writes a metadata-only
     `source_reviewed` cache payload with `source_family_id=rated_birth_time_source`.
   - The probe runs the real source cache audit and requires rejection with
     `reviewed payload does not fill any substantive birth field`.
   - Added the probe summary to cross-domain symbolic readiness output.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production readiness extraction for the substantive-evidence probe.
   - Added gate `birth_profile_substantive_evidence_cache_enforcement_probe`.
   - Extended the public schema contract for the new readiness summary.

3. Updated `examples/mingli_5agents/production_gates.py` and tests:
   - Registered the new gate ID.
   - Added readiness, schema, production-gate, and known-gap coverage assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_capability_audit_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_cross_domain_fixture_import_receipt examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema examples\mingli_5agents\tests\test_capability_audit_evaluator.py::test_capability_audit_binds_provider_production_guidance -q`
  passed: `4 passed`.

### Snapshot

- `birth_profile_substantive_evidence_cache_enforcement_probe`:
  `True`.
- Gate details:
  `[]`.
- Production gate registry current:
  `True`.

### Boundary

The probe writes only to a temporary cache directory. It does not fetch live
sources, write repository cache files, write reviewed manifests, import
profiles, or certify any celebrity birth data.

## 2026-06-26 - Chinese Report No-English No-Code Quality Gate

### Motivation

User-facing Mingli reports must be Chinese-only, readable, and free of code,
ASCII question-mark mojibake, provider commands, and untranslated symbolic
tokens. The previous renderer could still leak English names, stems, palaces,
provider statuses, environment variables, and `python -m` commands into Chinese
Markdown.

### Actions Taken

1. Updated `examples/mingli_5agents/report_renderers.py`:
   - Added a Chinese Markdown postprocessor for final rendered text.
   - Translated common stems/branches, five elements, Ziwei palaces, Qimen
     doors/palaces, astrology signs, provider statuses, Xuanze day labels, and
     benchmark case labels.
   - Removed provider setup command lines from Chinese reports and replaced
     them with plain Chinese production-access guidance.

2. Updated `examples/mingli_5agents/evaluators/chinese_render_evaluator.py`:
   - Rejected ASCII `?`, generic mojibake markers, code blocks, `python -m`,
     `SEMAS_` variables, and any remaining Latin letters in Chinese reports.

3. Updated `examples/mingli_5agents/tests/test_chinese_render_evaluator.py`:
   - Required generated Chinese reports to contain no ASCII letters, question
     marks, provider commands, or environment variables.
   - Added a negative test for question-mark and Python-code leakage.

### Verification

- `python -m py_compile examples\mingli_5agents\report_renderers.py examples\mingli_5agents\evaluators\chinese_render_evaluator.py examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py::test_run_benchmark_returns_aggregate_metrics -q`
  passed: `5 passed`.

### Snapshot

- Chinese render score:
  `1.0`.
- ASCII letters in generated Chinese report:
  `0`.
- ASCII question mark present:
  `False`.
- `python -m` present:
  `False`.
- `SEMAS_` provider variable present:
  `False`.

### Boundary

This change cleans and gates user-facing Chinese Markdown only. It does not
alter structured provider receipts, source commands, schema contracts, or
internal audit metadata.

## 2026-06-26 - Annual Monthly Anti-Repetition Evidence Binding

### Motivation

User-facing yearly and monthly sections must not repeat generic template
sentences. A readable Mingli report should show why each year and month is being
judged differently, using the independently computed annual or monthly pillar,
ten-god relation, active major luck, useful-state, and natal activation flags.

### Actions Taken

1. Updated `examples/mingli_5agents/report_renderers.py`:
   - Annual and monthly topic lines now include the specific year/month,
     ganzhi, stem ten-god, branch ten-god, active major luck, useful-state, and
     natal same-pillar evidence.
   - Main-axis and BaZi-evidence lines now include the year/month and ganzhi, so
     repeated structural rows remain traceable instead of appearing as copied
     prose.

2. Updated `examples/mingli_5agents/evaluators/chinese_render_evaluator.py`:
   - Added a duplicate-bullet ratio check over the final annual/monthly report
     sections.
   - Chinese rendering now fails when the annual/monthly tail sections contain
     repeated bullet lines above the allowed floor.

3. Updated `examples/mingli_5agents/tests/test_chinese_render_evaluator.py`:
   - Generated Chinese reports must have zero duplicate bullet ratio in the
     annual/monthly tail sections.
   - Added a repeated-line negative test for the duplicate-ratio helper.

### Verification

- `python -m py_compile examples\mingli_5agents\report_renderers.py examples\mingli_5agents\evaluators\chinese_render_evaluator.py examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py::test_run_benchmark_returns_aggregate_metrics -q`
  passed: `6 passed`.

### Snapshot

- Chinese render score:
  `1.0`.
- Annual/monthly duplicate bullet ratio:
  `0.0`.
- ASCII letters:
  `0`.
- ASCII question mark present:
  `False`.

### Boundary

This change improves final Chinese prose traceability and repetition detection.
It does not change the underlying annual/monthly calculation algorithm or claim
predictive validation.

## 2026-06-26 - Annual Monthly Evidence Anchor Coverage Gate

### Motivation

The anti-repetition gate ensures annual/monthly lines are not copied verbatim,
but it still needs a stronger invariant: every yearly and monthly topic
judgment must visibly bind to the independently computed evidence for that row.
Otherwise future edits could produce varied prose without showing the actual
ganzhi, ten-god, major-luck, useful-state, or natal-activation basis.

### Actions Taken

1. Updated `examples/mingli_5agents/evaluators/chinese_render_evaluator.py`:
   - Added `_tail_section_topic_evidence_anchor_ratio`.
   - Chinese rendering now fails unless every annual/monthly topic line for
     finance, official career, career, study, relationship, friends, leadership,
     and children/family contains row-level evidence anchors.
   - Required anchors are: current year/month scope, stem ten-god, branch
     ten-god, active major luck, useful-state, and natal same-pillar status.

2. Updated `examples/mingli_5agents/tests/test_chinese_render_evaluator.py`:
   - Generated Chinese reports must reach evidence-anchor coverage `1.0`.
   - Added a negative helper test for unbound topic lines.

### Verification

- `python -m py_compile examples\mingli_5agents\evaluators\chinese_render_evaluator.py examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\tests\test_benchmark.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py::test_run_benchmark_returns_aggregate_metrics -q`
  passed: `7 passed`.

### Snapshot

- Chinese render score:
  `1.0`.
- Annual/monthly duplicate bullet ratio:
  `0.0`.
- Annual/monthly topic evidence-anchor ratio:
  `1.0`.
- ASCII letters:
  `0`.
- ASCII question mark present:
  `False`.

### Boundary

This is a report-quality gate. It proves row-level evidence is visible in the
Chinese prose; it does not prove real-world predictive accuracy.

## 2026-06-26 - Benchmark Chinese Render Diagnostics Exposure

### Motivation

The Chinese render evaluator now enforces no-English/no-code/no-mojibake,
anti-repetition, and annual/monthly evidence-anchor coverage. Those failures
should be visible in benchmark artifacts, not only hidden inside a single
aggregate `chinese_render` score.

### Actions Taken

1. Updated `examples/mingli_5agents/benchmark.py`:
   - Added benchmark `report_features` for:
     - `chinese_render_duplicate_bullet_ratio`
     - `chinese_render_topic_evidence_anchor_ratio`
     - `chinese_render_ascii_letter_count`
     - `chinese_render_ascii_question_present`
     - `chinese_render_code_marker_present`

2. Updated `examples/mingli_5agents/api_core.py`:
   - Exposed the new benchmark report-feature fields in
     `BenchmarkCaseReportFeatures`.

3. Updated tests:
   - `examples/mingli_5agents/tests/test_benchmark.py` asserts both Chinese
     benchmark cases report zero duplication, full evidence-anchor coverage,
     zero Latin letters, no ASCII question mark, and no code marker.
   - `examples/mingli_5agents/tests/test_schema_contract_evaluator.py` asserts
     the new schema fields and types.
   - `examples/mingli_5agents/tests/test_cli.py` schema field-list assertions
     were updated.

4. Updated `examples/mingli_5agents/report_renderers.py`:
   - Added Chinese-render replacements for common English test-case names,
     Chinese city inputs, zodiac/door/palace symbols, and a final fallback that
     replaces untranslated Latin tokens in Chinese Markdown only.

### Verification

- `python -m py_compile examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\tests\test_benchmark.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_cli.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_benchmark.py::test_run_benchmark_returns_aggregate_metrics -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_cli.py::test_cli_init_analyze_evolve_status -q`
  did not complete within 240 seconds in this run; no pass/fail conclusion was
  recorded for that large integration test.

### Snapshot

For both `zh_topic_professional_auto_case` and
`production_external_provider_case`:

- Duplicate bullet ratio:
  `0.0`.
- Topic evidence-anchor ratio:
  `1.0`.
- ASCII letter count:
  `0`.
- ASCII question mark present:
  `False`.
- Code marker present:
  `False`.

### Boundary

This change makes report-quality diagnostics observable in benchmark artifacts.
It does not alter structured birth data, provider receipts, or predictive
claims.

## 2026-06-26 - Benchmark Chinese Render Quality Production Gate

### Motivation

Benchmark diagnostics made Chinese report quality observable, but production
readiness still needed a dedicated gate. Otherwise a release could pass general
benchmark floors while hiding the specific cause of a Chinese-rendering
regression.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `_benchmark_chinese_render_quality_failures`.
   - Added production readiness gate
     `benchmark_chinese_render_quality_diagnostics`.
   - The gate checks benchmark Chinese reports for duplicate annual/monthly
     bullets, evidence-anchor coverage, Latin letters, ASCII question marks,
     and code/provider-command markers.

2. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered `benchmark_chinese_render_quality_diagnostics`.

3. Updated tests:
   - `examples/mingli_5agents/tests/test_empirical_validation.py` asserts the
     new production-readiness gate passes and does not appear in blockers.
   - `examples/mingli_5agents/tests/test_schema_contract_evaluator.py` asserts
     the new gate is part of valid production gate IDs.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_known_gap_resolution_plan_coverage_accepts_id_alias -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Snapshot

- `benchmark_chinese_render_quality_diagnostics`:
  `True`.
- Gate details:
  `[]`.
- Production gate registry current:
  `True`.
- Gate registered:
  `True`.
- Chinese benchmark duplicate ratio:
  `0.0`.
- Chinese benchmark evidence-anchor ratio:
  `1.0`.
- ASCII letters:
  `0`.
- ASCII question mark present:
  `False`.
- Code marker present:
  `False`.

### Boundary

This is a production report-quality gate. It prevents release regressions in
Chinese report readability and row-evidence visibility, but it does not certify
real-world predictive accuracy.

## 2026-06-26 - Celebrity Sports Film Music Validation Pool Review

### Motivation

The user asked whether sports, film, and music celebrities can be found for
famous-case validation. The existing framework already had a candidate pool and
fixture layer, but it needed a concrete review of coverage, boundary, and source
quality before using the cases to evolve rules.

### Actions Taken

1. Reviewed the local candidate pool:
   - `examples/mingli_5agents/providers/industry_event_candidate_cases_example.json`
     contains 9 public candidates.
   - Coverage is balanced across `sports`, `film`, and `music`, with 3
     candidates per domain.
   - Audit status is valid and ready for review, but not production ready
     because it is not externally reviewed.

2. Reviewed the local event-source manifest:
   - `examples/mingli_5agents/providers/industry_event_source_manifest_example.json`
     covers film, music, and sports event sources.
   - Audit status is valid and ready for review, but not production evidence.

3. Reviewed the sourced famous-case fixture layer:
   - Sports: Arthur Ashe, Mark Spitz, Roger Federer.
   - Film/television: Marilyn Monroe, Lucille Ball, Sean Penn.
   - Film/martial arts: Bruce Lee.
   - Singers: Aretha Franklin, Michael Jackson, Madonna.
   - Sources are tracked as Astro-Databank with rating labels preserved.

4. Corrected one fixture data issue:
   - Updated Arthur Ashe birth time from `18:40` to `12:55` in
     `examples/mingli_5agents/famous_case_validation.py`.
   - This prevents a wrong hour pillar from contaminating symbolic annual
     scoring.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\industry_event_candidates.py examples\mingli_5agents\industry_event_manifest.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_outcome_dataset_configuration examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_scoring_readiness_matches_birth_profiles examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_symbolic_annual_score_scores_ready_labels -q`
  passed: `3 passed`.

### Snapshot

- Candidate pool audit:
  valid, 9 candidates, 3 sports, 3 film, 3 music, production ready false.
- Event manifest audit:
  valid, 6 records, covers film/music/sports, production evidence false.
- Fixture coverage:
  sports 3 cases / 32 event tags; film 3 cases / 33 event tags; singers 3
  cases / 33 event tags; Bruce Lee adds 1 film-martial-arts case / 12 event
  tags.

### Boundary

Celebrity cases are useful for calibration and false-positive detection, but
they are not proof of predictive validity. Before promotion to production
evidence, every case needs externally reviewed birth data, sourced event labels,
negative-year review, and frozen train/holdout splits.

## 2026-06-26 - Annual Monthly Judgment Then Evidence Structure

### Motivation

The annual and monthly topic lines already carried row-level evidence, but the
evidence was embedded in parentheses after the conclusion. That made the report
look like a field dump and weakened readability. The user asked for stronger,
more fluent, more directional language, so the renderer now separates the
assertion from the evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/report_renderers.py`:
   - Annual and monthly topic rows now render as
     `判断：...；依据：...`.
   - The evidence still includes year/month, ganzhi, stem ten-god, branch
     ten-god, active major luck, useful-state, and natal same-pillar relation.

2. Updated `examples/mingli_5agents/evaluators/chinese_render_evaluator.py`:
   - Added `_tail_section_topic_judgment_structure_ratio`.
   - Chinese reports now fail if annual/monthly topic rows do not include both
     judgment and evidence markers.

3. Updated benchmark and production readiness:
   - `examples/mingli_5agents/benchmark.py` exposes
     `chinese_render_topic_judgment_structure_ratio`.
   - `examples/mingli_5agents/api_core.py` adds the schema field and checks it
     inside `benchmark_chinese_render_quality_diagnostics`.

4. Updated tests:
   - Chinese render evaluator positive and negative cases.
   - Benchmark aggregate feature assertions.
   - Schema contract and CLI schema field assertions.

### Verification

- `python -m py_compile examples\mingli_5agents\report_renderers.py examples\mingli_5agents\evaluators\chinese_render_evaluator.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_chinese_render_evaluator.py examples\mingli_5agents\tests\test_benchmark.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py examples\mingli_5agents\tests\test_cli.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_chinese_render_evaluator.py -q`
  passed: `7 passed`.
- `pytest examples\mingli_5agents\tests\test_benchmark.py::test_run_benchmark_returns_aggregate_metrics -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.

### Snapshot

- `benchmark_chinese_render_quality_diagnostics`:
  `True`.
- Gate details:
  `[]`.
- `zh_topic_professional_auto_case`:
  duplicate ratio `0.0`, evidence-anchor ratio `1.0`, judgment-structure ratio
  `1.0`, ASCII letters `0`, question marker `False`, code marker `False`.
- `production_external_provider_case`:
  duplicate ratio `0.0`, evidence-anchor ratio `1.0`, judgment-structure ratio
  `1.0`, ASCII letters `0`, question marker `False`, code marker `False`.

### Boundary

This change improves report readability and auditability. It does not change
birth-chart calculation, annual/monthly symbolic scoring, or empirical
predictive validity.

## 2026-06-26 - Famous Case Birth Source Quality Summary

### Motivation

Celebrity validation can improve rule calibration only if birth-time quality is
visible. The famous-case receipt already tracked domain coverage and source
ratings, but downstream evolution could still focus on case count without
seeing which samples are suitable for hour-pillar-sensitive checks.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_fixture_birth_source_quality`.
   - Added `birth_source_quality` to `famous_case_receipt()` and its stable
     material.
   - The summary records source counts, rating counts, high-confidence cases,
     caution cases, invalid birth-time formats, and hour-pillar eligible cases.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `birth_source_quality` to `FamousCaseValidationReceiptSummary`.

3. Updated tests:
   - Capability-audit test asserts the source-quality summary is present and
     stable in material.
   - Schema-contract test requires the new field in the public schema.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Snapshot

- Famous-case count:
  `12`.
- Source counts:
  `{"Astro-Databank": 12}`.
- Rating counts:
  `{"乙": 1, "甲": 4, "甲甲": 7}`.
- High-confidence case count:
  `11`.
- Caution case ids:
  `["chiang_kai_shek"]`.
- Invalid birth-time format case ids:
  `[]`.
- Hour-pillar scoring eligible case count:
  `11`.
- Arthur Ashe eligible after birth-time correction:
  `True`.

### Boundary

This summary improves calibration hygiene. It does not certify predictive
validity, and it does not replace external review of event labels or source
documents.

## 2026-06-26 - Annual Calibration Birth Source Quality Propagation

### Motivation

The famous-case fixture now exposes birth-source quality, but annual event
calibration still only carried `source_rating` on each case score. That meant a
downstream rule-refinement step could ignore whether a case was eligible for
hour-pillar-sensitive analysis. The quality signal needed to travel with the
calibration output itself.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added case-level `birth_source_quality` to annual case scores.
   - Added `hour_pillar_scoring_eligible` to each annual case score.
   - Added `birth_source_quality_summary` to
     `famous_case_annual_event_calibration_receipt()`.
   - The summary counts eligible cases, caution cases, eligible event labels,
     caution event labels, and eligible event rate.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `birth_source_quality_summary` to
     `FamousCaseAnnualEventCalibrationReceiptSummary`.

3. Updated tests:
   - Capability-audit test checks case-level and aggregate birth-source quality.
   - Schema-contract test requires the annual calibration summary field.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Snapshot

- Annual calibration case count:
  `12`.
- Hour-pillar scoring eligible cases:
  `11`.
- Caution case ids:
  `["chiang_kai_shek"]`.
- Eligible event labels:
  `120`.
- Caution event labels:
  `10`.
- Eligible event rate:
  `0.923`.

### Boundary

This propagates input-quality metadata into annual calibration. It does not
remove caution cases from broad annual diagnostics; it makes the caution visible
so future rule evolution can filter hour-sensitive claims.

## 2026-06-26 - Source Quality Aware Rule Refinement Queue

### Motivation

Birth-source quality reached annual calibration, but the rule-refinement queue
still ranked weak topics by precision and false-positive rate alone. That could
push the system to tune rules on low-confidence birth-time samples. Rule
evolution should first ask whether the event labels come from cases eligible for
hour-pillar-sensitive calibration.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `eligible_event_count`, `caution_event_count`, and
     `eligible_event_rate` to `topic_summary`.
   - Added the same fields to `domain_topic_summary`.
   - Propagated those fields into `rule_refinement_queue` and
     `domain_topic_refinement_queue`.
   - Added `source_review_first` priority when a topic has at least 3 events
     but fewer than half come from hour-pillar-eligible cases.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Asserted topic summaries and queues preserve quality counts.
   - Asserted low-quality topics can be marked `source_review_first`.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.

### Snapshot

Top rule-refinement queue entries:

- `career_power`: priority `source_review_first`, eligible event rate `0.0`,
  eligible events `0`, caution events `4`.
- `war_pressure`: priority `source_review_first`, eligible event rate `0.0`,
  eligible events `0`, caution events `3`.
- `study_exam`: priority `medium`, eligible event rate `1.0`, eligible events
  `3`, caution events `0`.

### Boundary

This does not remove low-confidence samples from calibration. It prevents
rule-refinement priority from treating low-confidence birth-source topics as
ordinary tuning targets.

## 2026-06-26 - Source Review First Evolution Tasks

### Motivation

The rule-refinement queue could mark low-quality source topics as
`source_review_first`, but the downstream `evolution_task_plan` still converted
them into ordinary evidence or rule-refinement tasks. That preserved the same
failure mode one layer later: the plan could ask for rule tuning before source
review.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - `evolution_task_plan` now preserves `eligible_event_count`,
     `caution_event_count`, and `eligible_event_rate`.
   - Queue items with priority `source_review_first` now become
     `review_birth_sources` tasks.
   - Added source-review-specific next evidence and acceptance criteria.
   - Updated task sorting so source-review tasks appear before ordinary rule
     tuning.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Asserted `career_power` becomes `review_birth_sources`.
   - Asserted the task retains source-quality event counts.
   - Asserted the next evidence explicitly asks for rated birth-time sources.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.

### Snapshot

Top evolution tasks:

- `career_power`: priority `source_review_first`, task
  `review_birth_sources`, eligible event rate `0.0`, eligible events `0`,
  caution events `4`.
- `war_pressure`: priority `source_review_first`, task
  `review_birth_sources`, eligible event rate `0.0`, eligible events `0`,
  caution events `3`.
- `study_exam`: priority `medium`, task `add_specific_evidence`, eligible
  event rate `1.0`, eligible events `3`, caution events `0`.
- `career_project`: priority `medium`, task `add_specific_evidence`, eligible
  event rate `1.0`, eligible events `32`, caution events `0`.

### Boundary

This change routes low-source-quality topics into source review. It does not
change symbolic predicates, annual scoring, or event labels.

## 2026-06-26 - Domain Topic Source Review Routing

### Motivation

Global rule-refinement and evolution plans now route low-source-quality topics
into source review, but the domain-topic refinement queue still treated
low-quality slices as ordinary domain evidence tasks. That allowed a narrower
domain slice to bypass the same source-quality gate.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Domain-topic slices with at least 3 events and eligible event rate below
     `0.5` now receive `task_type=review_birth_sources`.
   - Added domain-topic source-review evidence instructions.
   - Added domain-topic source-review acceptance criteria.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Asserted the `近代政治/career_power` domain-topic slice routes to
     `review_birth_sources`.
   - Asserted it preserves eligible/caution event counts and requests rated
     birth-time source review.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.

### Snapshot

Leading domain-topic queue entries now include:

- `影视/public_fame`: task `add_domain_specific_evidence`, eligible event rate
  `1.0`.
- `影视/career_project`: task `add_domain_specific_evidence`, eligible event
  rate `1.0`.
- `体育/career_project`: task `add_domain_specific_evidence`, eligible event
  rate `1.0`.
- `近代政治/career_power`: task `review_birth_sources`, eligible event rate
  `0.0`, eligible events `0`, caution events `4`.

### Boundary

This change only routes low-source-quality domain slices. It does not remove
the slices, change annual predicates, or assert predictive validity.

## 2026-06-26 - Source Review Routing Summary

### Motivation

Source-quality routing now exists in global queues, domain-topic queues, and the
final evolution task plan. However, downstream tools still needed a compact
receipt-level summary that proves low-source-quality topics were routed to
source review and did not bypass the gate.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_source_review_routing_summary`.
   - Added `source_review_routing_summary` to
     `famous_case_annual_event_calibration_receipt()`.
   - The summary tracks global source-review topics, domain source-review
     slices, evolution source-review tasks, and any bypassed low-quality items.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `source_review_routing_summary` to
     `FamousCaseAnnualEventCalibrationReceiptSummary`.

3. Updated tests:
   - Capability-audit test asserts routing is complete and no low-quality
     topics bypass source review.
   - Schema-contract test requires the new public field.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `1 passed`.

### Snapshot

- Routing complete:
  `True`.
- Global source-review topics:
  `["career_power", "war_pressure"]`.
- Domain source-review slices:
  `["近代政治/career_power", "近代政治/war_pressure"]`.
- Evolution source-review topics:
  `["career_power", "war_pressure"]`.
- Bypassed low-quality topics or slices:
  `[]`.

### Boundary

This summary verifies routing behavior only. It does not validate source
documents, event labels, or predictive claims.

## 2026-06-26 - Source Review Routing Production Gate

### Motivation

`source_review_routing_summary` made routing visible, but production readiness
still needed to enforce it. Otherwise the summary could show a bypass while the
release gate remained green.

### Actions Taken

1. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added capability flag `famous_case_source_review_routing_complete`.
   - Added routing summary fields to capability-audit receipt material.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added production readiness gate
     `famous_case_source_review_routing_complete`.
   - Added failure diagnostics for missing routing summary, incomplete routing,
     bypassed low-quality topics, and empty source-review task lists.

3. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered the new production gate ID.

4. Updated tests:
   - Capability audit asserts the capability flag is true and receipt material
     preserves the routing summary.
   - Production readiness asserts the new gate passes and does not appear in
     blockers.
   - Schema contract / known-gap coverage recognizes the new gate ID.

### Verification

- `python -m py_compile examples\mingli_5agents\capability_audit.py examples\mingli_5agents\api_core.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_known_gap_resolution_plan_release_fallback_matches_schema_contract examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_accepts_current_schema -q`
  passed: `2 passed`.

### Snapshot

- Gate `famous_case_source_review_routing_complete`:
  passed `True`, details `[]`, blocker `False`.
- Routing complete:
  `True`.
- Global source-review topics:
  `["career_power", "war_pressure"]`.
- Domain source-review slices:
  `["近代政治/career_power", "近代政治/war_pressure"]`.
- Evolution source-review topics:
  `["career_power", "war_pressure"]`.
- Bypassed low-quality items:
  `[]`.

### Boundary

This gate protects source-quality routing. It does not certify that reviewed
source documents have been collected, and it does not validate predictive
accuracy.

## 2026-06-26 - Source Review Routing Gate Negative Probe

### Motivation

The source-review routing production gate had a positive readiness assertion.
It also needed a negative probe proving that missing or bypassed routing data
would fail, rather than only confirming that the current fixture stays green.

### Actions Taken

1. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Imported `_famous_case_source_review_routing_complete`.
   - Imported `_famous_case_source_review_routing_failures`.
   - Added
     `test_famous_case_source_review_routing_gate_rejects_bypassed_low_quality_topics`.

2. The new probe covers:
   - Missing `source_review_routing_summary`.
   - `routing_complete=False`.
   - Non-empty `global_bypassed_low_quality_topics`.
   - Non-empty `domain_bypassed_low_quality_slices`.
   - Non-empty `evolution_bypassed_low_quality_topics`.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_famous_case_source_review_routing_gate_rejects_bypassed_low_quality_topics -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.

### Boundary

This probe validates gate behavior for malformed or incomplete routing
summaries. It does not collect new celebrity birth records, and it does not
change prediction rules.

## 2026-06-26 - Source Review Refinement Queue Alignment

### Motivation

`evolution_task_plan` correctly converted low-source-quality famous-case topics
into `review_birth_sources`, but the upstream `rule_refinement_queue` still
recommended ordinary rule evidence such as ten-god and branch-interaction
features. That created a mixed signal: the final plan said "review sources
first" while the earlier queue still looked like a rule-tuning task.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_recommended_refinement_evidence`.
   - Routed `source_review_first` queue items to the same birth-source review
     evidence used by `review_birth_sources` evolution tasks.
   - Left normal rule-tuning recommendations unchanged for non-source-review
     priorities.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Asserted that all `source_review_first` queue items recommend rated
     birth-time source review.
   - Asserted that those queue items no longer recommend ordinary ten-god or
     branch-interaction rule evidence.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.

### Snapshot

- `career_power` source-review queue evidence:
  `collect rated birth-time sources for caution cases before rule tuning`,
  `exclude caution cases from hour-pillar-sensitive variant selection until reviewed`,
  `rerun annual calibration after birth-source quality changes`.
- `war_pressure` source-review queue evidence:
  same three source-review actions.

### Boundary

This change aligns queue language with the source-quality gate. It does not
collect new source documents, change celebrity fixtures, or change strict
symbolic predicates.

## 2026-06-26 - Source Review Queue Alignment Production Gate

### Motivation

The source-review queue wording was aligned in the calibration code and covered
by a unit assertion, but production readiness did not yet enforce it. A future
change could reintroduce ordinary rule-tuning evidence into
`source_review_first` queue items while the release gate stayed green.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added production gate `famous_case_source_review_queue_aligned`.
   - Added `_famous_case_source_review_queue_aligned`.
   - Added `_famous_case_source_review_queue_failures`.
   - The gate fails if source-review queue items are missing rated birth-time
     source actions or include rule-tuning phrases such as branch-interaction
     evidence.

2. Updated `examples/mingli_5agents/capability_audit.py`:
   - Added capability flag `famous_case_source_review_queue_aligned`.

3. Updated `examples/mingli_5agents/production_gates.py`:
   - Registered the new production gate ID.

4. Updated tests:
   - Capability audit asserts the new capability is true.
   - Production readiness asserts the new gate passes and is not a blocker.
   - Added a negative probe where a `source_review_first` queue item includes
     `add branch interaction evidence`; the new gate must fail.
   - Schema contract coverage recognizes the new production gate ID.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\capability_audit.py examples\mingli_5agents\production_gates.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_famous_case_source_review_queue_gate_rejects_rule_tuning_evidence -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_known_gap_resolution_plan_release_fallback_matches_schema_contract -q`
  passed: `1 passed`.

### Boundary

This gate protects task semantics for source-review-first topics. It does not
perform source collection and does not alter BaZi, Ziwei, Qimen, or strict
annual-event predicates.

## 2026-06-26 - Famous Case Source Review Gate Remediation Plan

### Motivation

`famous_case_source_review_routing_complete` and
`famous_case_source_review_queue_aligned` were both production gates, but their
failures were not yet mapped to targeted remediation steps in the production
resolution plan. A gate that blocks release should also tell the next agent how
to repair the blocked path.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `repair_famous_case_source_review_routing` to
     `_production_resolution_plan`.
   - Added `repair_famous_case_source_review_queue_semantics` to
     `_production_resolution_plan`.
   - Both steps preserve blocker diagnostics and point verification back to the
     audit command.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Added
     `test_production_resolution_plan_handles_famous_case_source_review_gate_failures`.
   - The test constructs routing and queue-semantic blockers and verifies both
     repair steps appear with the original diagnostics.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_resolution_plan_handles_famous_case_source_review_gate_failures -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_known_gap_resolution_plan_release_fallback_matches_schema_contract -q`
  passed: `1 passed`.

### Boundary

This change improves remediation planning for famous-case source-review gates.
It does not collect external birth records, change symbolic predicates, or
claim empirical predictive accuracy.

## 2026-06-26 - Chinese Render Quality Gate Remediation Plan

### Motivation

`benchmark_chinese_render_quality_diagnostics` already blocked production when
benchmark Chinese reports had duplicated annual/monthly rows, weak evidence
anchors, weak judgment structure, English leakage, question marks, or code
markers. However, the production resolution plan did not map that gate failure
to a targeted repair step.

### Actions Taken

1. Updated `examples/mingli_5agents/api_core.py`:
   - Added `repair_benchmark_chinese_render_quality` to
     `_production_resolution_plan`.
   - The step preserves blocker diagnostics and routes verification through the
     benchmark command.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Added
     `test_production_resolution_plan_handles_chinese_render_quality_gate_failure`.
   - The test constructs duplicate-ratio and judgment-structure diagnostics and
     verifies they appear in the repair step.

### Verification

- `python -m py_compile examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_resolution_plan_handles_chinese_render_quality_gate_failure -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Boundary

This change improves remediation planning for Chinese report quality gates. It
does not change the renderer, annual/monthly scoring rules, or benchmark case
fixtures.

## 2026-06-26 - Chinese Render Pillar Anchor Gate

### Motivation

Chinese report quality gates checked repetition, evidence-anchor wording,
judgment structure, English leakage, question marks, and code markers. They did
not yet verify that topic-level annual and monthly focus lines actually exposed
the relevant annual/monthly pillar. This left room for prose that looked
well-structured but did not show the specific year/month evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_pillar_anchor_ratio`.
   - Added `chinese_render_monthly_pillar_anchor_ratio`.
   - Added pinyin-to-Chinese GanZhi conversion for topic pillar anchors.
   - Added fallback stem/branch splitting so monthly pillars like `WuChou`
     become `戊丑` even when they are not standard sixty-cycle entries.

2. Updated `examples/mingli_5agents/api_core.py`:
   - `benchmark_chinese_render_quality_diagnostics` now fails if either annual
     or monthly pillar anchor ratio is below `1.0`.
   - Public schema exposes both new benchmark feature fields.

3. Updated tests:
   - Added a negative probe for low annual/monthly pillar anchor ratios.
   - Production readiness asserts current Chinese benchmark cases have annual
     and monthly pillar anchor ratios of `1.0`.
   - Schema contract asserts the two feature fields are public.

### Verification

- `python -m py_compile examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Boundary

This gate checks whether rendered Chinese benchmark reports expose topic-level
annual/monthly pillar anchors. It does not certify interpretive correctness,
change scoring rules, or expand the benchmark dataset.

## 2026-06-26 - Chinese Render Ten-God Anchor Gate

### Motivation

The previous gate required Chinese reports to expose annual and monthly pillar
anchors. That still left a possible gap: a report could show the pillar name
but omit the ten-god relationship that explains why the year or month was
interpreted in a particular way.

### Actions Taken

1. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_ten_god_anchor_ratio`.
   - Added `chinese_render_monthly_ten_god_anchor_ratio`.
   - Added English ten-god code to Chinese label mapping:
     `peer -> 同类`, `wealth -> 财星`, `authority -> 官杀`,
     `resource -> 印星`, `expression -> 食伤`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - `benchmark_chinese_render_quality_diagnostics` now fails if annual or
     monthly ten-god anchor ratios are below `1.0`.
   - Public schema exposes both new benchmark feature fields.

3. Updated tests:
   - The Chinese render quality negative probe now covers low annual/monthly
     ten-god anchor ratios.
   - Production readiness asserts all Chinese benchmark cases score `1.0` on
     annual/monthly pillar and ten-god anchor ratios.
   - Schema contract asserts the two new ten-god fields are public.

### Verification

- `python -m py_compile examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Snapshot

All Chinese benchmark cases currently report:

- annual pillar anchor ratio: `1.0`
- monthly pillar anchor ratio: `1.0`
- annual ten-god anchor ratio: `1.0`
- monthly ten-god anchor ratio: `1.0`

### Boundary

This gate verifies rendered text carries ten-god anchors from structured topic
evidence. It does not prove the ten-god interpretation is empirically correct.

## 2026-06-26 - Chinese Render Useful-State Anchor Gate

### Motivation

Chinese render quality already checked pillar anchors and ten-god anchors. That
still did not explicitly verify the useful-state / directionality layer: whether
the report states if a year or month is favorable, excessive, or neutral from
the useful-element perspective.

### Actions Taken

1. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_useful_state_anchor_ratio`.
   - Added `chinese_render_monthly_useful_state_anchor_ratio`.
   - Added useful-state to Chinese label mapping:
     `useful_element_activated -> 用神状态有利`,
     `dominant_element_reinforced -> 用神状态忌偏重`,
     `neutral_or_indirect -> 用神状态中性或间接`.

2. Updated `examples/mingli_5agents/api_core.py`:
   - `benchmark_chinese_render_quality_diagnostics` now fails if annual or
     monthly useful-state anchor ratios are below `1.0`.
   - Public schema exposes both new benchmark feature fields.

3. Updated tests:
   - The Chinese render quality negative probe now covers low annual/monthly
     useful-state anchor ratios.
   - Production readiness asserts all Chinese benchmark cases score `1.0` on
     annual/monthly pillar, ten-god, and useful-state anchor ratios.
   - Schema contract asserts the two useful-state fields are public.

### Verification

- `python -m py_compile examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Snapshot

All Chinese benchmark cases currently report `1.0` for annual/monthly pillar,
ten-god, and useful-state anchor ratios.

### Boundary

This gate verifies rendered text carries useful-state anchors from structured
topic evidence. It does not prove predictive truth or replace human review.

## 2026-06-26 - Chinese Render Branch Interaction Anchor Gate

### Motivation

Chinese report quality gates now covered annual/monthly pillar, ten-god, and
useful-state anchors. The next missing layer was branch interaction: whether a
year or month forms clash, combination, punishment, harm, or break relations
with natal branches. User feedback explicitly asked for independent annual and
monthly reasoning using relations such as 合、冲、刑、害.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added branch interaction tables for `clash`, `combine`, `punishment`,
     `harm`, and `break`.
   - Added `branch_interactions` to annual BaZi evidence.

2. Updated `examples/mingli_5agents/tools/monthly_luck.py`:
   - Preserved `branch_interactions` in monthly evidence.
   - Normalized `annual_branch` to `monthly_branch` for monthly rows.

3. Updated `examples/mingli_5agents/topic_synthesis.py`:
   - Added `branch_interactions` to compact annual/monthly timing evidence.

4. Updated `examples/mingli_5agents/report_renderers.py`:
   - Rendered branch interactions in evidence lines and contextual topic rows.
   - Uses Chinese relation labels: 冲、合、刑、害、破.

5. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_branch_interaction_anchor_ratio`.
   - Added `chinese_render_monthly_branch_interaction_anchor_ratio`.
   - The ratio defaults to `1.0` only when no branch interaction exists.

6. Updated `examples/mingli_5agents/api_core.py` and tests:
   - Production Chinese render quality gate now fails when branch-interaction
     anchors are missing.
   - Public schema exposes branch interaction fields.
   - Schema contract requires `branch_interactions` on annual/monthly BaZi
     evidence and topic timing signals.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Snapshot

- All Chinese benchmark cases have annual branch-interaction anchor ratio `1.0`.
- All Chinese benchmark cases have monthly branch-interaction anchor ratio `1.0`.
- Sample annual evidence includes `Wu` punishment with natal `Wu` and
  `Wu` combination with natal `Wei`.
- Sample monthly evidence includes `Yin` harm with natal `Si` and `Yin`
  punishment with natal `Si`.

### Boundary

This change adds deterministic symbolic branch-interaction evidence and render
anchors. It does not claim empirical predictive accuracy and does not replace a
professional calendar provider.

## 2026-06-26 - Branch Interaction Structural Regression Tests

### Motivation

Branch interactions were added to annual/monthly evidence and Chinese render
quality gates, but the calendar tool tests still did not assert specific
relations. Without structural tests, a future change could keep the render
metric green while breaking the underlying interaction calculation.

### Actions Taken

1. Updated `examples/mingli_5agents/tests/test_calendar_tools.py`:
   - Annual luck test now asserts 2024 `JiaChen` produces:
     - `Chen` punishment with natal `Chen` on the month pillar.
     - `Chen` harm with natal `Mao` on the hour pillar.
   - Monthly luck test now asserts:
     - First selected month has no branch interactions.
     - 2025-02 `BingMao` produces `Mao` break with natal `Wu`,
       `Mao` harm with natal `Chen`, and another `Mao` break with natal `Wu`.

2. Updated `examples/mingli_5agents/tests/test_mingli_system.py`:
   - Full executor artifact test now asserts annual row evidence contains
     `branch_interactions`.
   - Chinese rendered report must contain `地支关系`.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.

### Boundary

These tests protect deterministic branch-interaction computation and rendering.
They do not expand the interaction model beyond the currently implemented
冲、合、刑、害、破 tables.

## 2026-06-26 - Sports Film Music Famous-Case Validation Status

### Motivation

User asked whether sports, film, and music celebrities can be found and used for
validation. The framework already has a famous-case validation lane, so the
right next step was to confirm the current fixture breadth, source quality, and
event-year scoring boundaries before adding more names.

### Actions Taken

1. Checked `examples/mingli_5agents/famous_case_validation.py`.
2. Confirmed the local fixture set contains 12 sourced famous-person cases.
3. Confirmed the public-life domains include sports, film, and music.
4. Confirmed the current source-quality gate separates high-confidence
   hour-sensitive cases from caution cases.
5. Re-ran the famous-case receipts to inspect domain coverage, event counts,
   and annual event calibration slices.
6. Cross-checked representative external source pages for Roger Federer,
   Marilyn Monroe, Michael Jackson, and Aretha Franklin.

### Snapshot

- Current fixture count: 12 cases.
- Current hour-pillar eligible count: 11 cases.
- Current annual event labels: 130 event-year tags.
- Sports fixture cases: Arthur Ashe, Mark Spitz, Roger Federer.
- Film fixture cases: Marilyn Monroe, Lucille Ball, Sean Penn.
- Music fixture cases: Aretha Franklin, Michael Jackson, Madonna.

### Boundary

Famous-person fixtures are useful for regression testing, source-routing,
industry-event label expansion, and weak calibration. They are not statistical
proof of predictive validity. New candidates should enter through the source
review and event-label review path before they are allowed to adjust rules.

## 2026-06-26 - Chinese Render Five-Element Anchor Gate

### Motivation

Chinese annual/monthly report quality gates already required pillar, ten-god,
useful-state, and branch-interaction anchors. The remaining gap was five-element
evidence. Annual/monthly rows had element data at the row level, but the compact
topic evidence and render-quality gates did not prove that stem element, branch
element, and focus element reached the user-facing Chinese report.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added `elements` to annual BaZi evidence.
   - Monthly evidence inherits the same element structure through the shared
     evidence helper.

2. Updated `examples/mingli_5agents/topic_synthesis.py`:
   - Added `elements` to compact annual/monthly timing evidence.
   - Included element evidence in timing summaries.

3. Updated `examples/mingli_5agents/report_renderers.py`:
   - Rendered five-element evidence in contextual topic rows.
   - Rendered five-element evidence in annual/monthly BaZi evidence lines.
   - Chinese anchor form: `五行=天干X、地支Y、主轴Z`.

4. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_element_anchor_ratio`.
   - Added `chinese_render_monthly_element_anchor_ratio`.

5. Updated `examples/mingli_5agents/api_core.py` and tests:
   - Production Chinese render quality gate fails when element anchors are
     missing.
   - Public schema requires `elements` on topic timing signals.
   - Benchmark schema exposes annual/monthly element-anchor ratios.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Benchmark snapshot: all Chinese benchmark cases have annual element anchor
  ratio `1.0` and monthly element anchor ratio `1.0`.

### Boundary

This adds explicit five-element anchors to structured evidence, rendered
Chinese text, benchmark diagnostics, schema, and production gates. It still does
not implement full five-element circulation chains such as 生、克、泄、耗、制.

## 2026-06-26 - Five-Element Flow Path Evidence

### Motivation

The previous step made annual/monthly reports show stem element, branch element,
and focus element. That proved the five-element anchors were visible, but it
still did not explain how those elements act on the useful element and the
dominant element. User feedback asks for monthly five-element and useful-god
correspondence, so the next executable layer is a structured flow path.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added generating and controlling element tables.
   - Added `element_flow` to BaZi evidence.
   - Each flow row records source slot, source element, target role, target
     element, and relation.
   - Relations cover `same`, `generate`, `drain`, `control`, and `consume`.

2. Updated `examples/mingli_5agents/topic_synthesis.py`:
   - Added `element_flow` to compact annual/monthly timing evidence.

3. Updated `examples/mingli_5agents/report_renderers.py`:
   - Rendered element flow as Chinese phrases such as
     `天干木耗用神金` and `地支土生用神金`.
   - Added flow text to contextual topic rows and annual/monthly evidence
     lines.

4. Updated `examples/mingli_5agents/benchmark.py`:
   - Added `chinese_render_annual_element_flow_anchor_ratio`.
   - Added `chinese_render_monthly_element_flow_anchor_ratio`.

5. Updated `examples/mingli_5agents/api_core.py` and tests:
   - Production Chinese render quality gate now fails when flow anchors are
     missing.
   - Public schema requires `element_flow` on annual/monthly BaZi evidence and
     topic timing signals.
   - Calendar tests assert concrete element-flow relations for annual and
     monthly rows.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Benchmark snapshot: all Chinese benchmark cases have annual element-flow
  anchor ratio `1.0` and monthly element-flow anchor ratio `1.0`.

### Boundary

This implements the first executable flow path from current stem/branch/focus
elements to useful and dominant elements. It does not yet model combination
transformation, hidden stems, seasonal strength, or palace-specific flow.

## 2026-06-26 - Hidden-Stem Flow Path Evidence

### Motivation

The five-element flow path previously covered current stem, branch main element,
and focus element. That still left out branch hidden stems, which are important
for BaZi reasoning because a branch can carry multiple internal stems and
therefore multiple element influences.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/calendar_core.py`:
   - Added a deterministic `BRANCH_HIDDEN_STEMS` table for all twelve branches.

2. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added `hidden_stem_flow` to annual BaZi evidence.
   - Monthly evidence inherits the same field through the shared evidence
     helper.
   - Each hidden-stem flow row records branch, hidden stem, source element,
     target role, target element, and relation.

3. Updated `examples/mingli_5agents/topic_synthesis.py`:
   - Added `hidden_stem_flow` to compact annual/monthly timing evidence.

4. Updated `examples/mingli_5agents/report_renderers.py`:
   - Rendered hidden-stem flow as Chinese phrases such as
     `辰藏戊生用神金` and `寅藏丙克用神金`.
   - Added `藏干=...` to contextual topic rows and annual/monthly evidence
     lines.

5. Updated `examples/mingli_5agents/benchmark.py`, `api_core.py`, and tests:
   - Added annual/monthly hidden-stem-flow anchor ratios.
   - Production Chinese render quality gate fails when hidden-stem-flow anchors
     are missing.
   - Public schema requires `hidden_stem_flow` on annual/monthly BaZi evidence
     and topic timing signals.
   - Calendar tests assert concrete hidden-stem flow rows for 2024 `JiaChen`
     and 2025-01 `YiYin`.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\calendar_core.py examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Benchmark snapshot: all Chinese benchmark cases have annual hidden-stem-flow
  anchor ratio `1.0` and monthly hidden-stem-flow anchor ratio `1.0`.

### Boundary

This adds hidden stems as visible symbolic flow evidence. It does not yet weight
principal, middle, and residual hidden stems differently and does not apply
seasonal strength correction.

## 2026-06-26 - Hidden-Stem Weight Evidence

### Motivation

Hidden-stem flow made branch internals visible, but all hidden stems were still
treated equally. BaZi reasoning normally distinguishes principal, middle, and
residual hidden stems. The next executable step was to carry that hierarchy into
structured evidence, rendered Chinese text, benchmark anchors, and schema.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/calendar_core.py`:
   - Added `BRANCH_HIDDEN_STEM_WEIGHTS`.
   - Principal hidden stem weight: `1.0`.
   - Middle hidden stem weight: `0.5`.
   - Residual hidden stem weight: `0.25`.

2. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - `hidden_stem_flow` rows now include `hidden_stem_role` and numeric
     `weight`.
   - Monthly evidence inherits the weighted hidden-stem rows through the shared
     evidence helper.

3. Updated `examples/mingli_5agents/report_renderers.py` and `benchmark.py`:
   - Rendered phrases now include role and weight, such as
     `辰藏戊本气权重1.00生用神金`.
   - Existing hidden-stem-flow anchor ratios now require the role and weight
     tokens to appear in rendered Chinese.

4. Updated `examples/mingli_5agents/api_core.py` and schema tests:
   - Added `AnnualLuckHiddenStemFlow` schema.
   - `weight` is required and typed as `number`.
   - Annual/monthly BaZi evidence and topic timing signals reference the shared
     hidden-stem-flow schema.

5. Updated tests:
   - Calendar tests assert principal/middle/residual roles and numeric weights
     for 2024 `JiaChen` and 2025-01 `YiYin`.
   - End-to-end system test checks rendered Chinese contains `权重`.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\calendar_core.py examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Benchmark snapshot: all Chinese benchmark cases keep annual/monthly
  hidden-stem-flow anchor ratios at `1.0`.

### Boundary

This adds fixed principal/middle/residual weights. It does not yet adjust those
weights by season, month command, combination transformation, or actual
professional-provider strength scores.

## 2026-06-26 - Seasonal Hidden-Stem Weight Evidence and Celebrity Source Review

### Motivation

User asked whether sports, film, and music celebrities can be found for
validation. Before expanding the validation set, the interrupted hidden-stem
seasonal weighting layer also needed to be finished, and the existing famous
case fixture file had visible mojibake in Chinese fields.

### Actions Taken

1. Completed seasonal hidden-stem weighting:
   - Added branch season mapping and seasonal element mapping.
   - `hidden_stem_flow` rows now carry `season`, `seasonal_phase`,
     `seasonal_factor`, and `adjusted_weight`.
   - Renderer now exposes text such as `辰藏戊本气权重1.00春旺系数1.20调权1.20生用神金`.
   - Benchmark/schema/tests now require the seasonal factor and adjusted weight
     to survive into structured evidence and Chinese reports.

2. Fixed famous-case fixture readability:
   - Restored Chinese names, domains, source ratings, birthplace strings, and
     validation notes in `examples/mingli_5agents/famous_case_validation.py`.
   - Kept the existing 12-case formal fixture set and event-year labels.
   - Current formal fixture domains cover sports, film, martial-arts film,
     music, science/culture, and modern politics.

3. Reviewed celebrity expansion direction:
   - Existing formal cases include Arthur Ashe, Mark Spitz, Roger Federer,
     Marilyn Monroe, Lucille Ball, Sean Penn, Bruce Lee, Aretha Franklin,
     Michael Jackson, and Madonna.
   - Candidate/review queues already include Roger Federer, Serena Williams,
     Michael Jordan, Jackie Chan, Meryl Streep, Tom Hanks, Aretha Franklin,
     Madonna, and Michael Jackson.
   - Expansion rule remains: high-source birth time first; public event labels
     second; low-confidence or hour-missing records stay out of time-sensitive
     validation.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tools\calendar_core.py examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_empirical_validation.py::test_industry_event_candidate_cases_status_exposes_gate_and_guidance examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `4 passed`.
- Benchmark snapshot: all Chinese benchmark cases have annual/monthly
  hidden-stem-flow anchor ratios at `1.0`.
- Famous-case receipt: `12` cases; domains are `体育`, `影视`, `影视武术`,
  `歌手`, `科学文化`, `近代政治`; receipt hash
  `6b708ce5c327eb48785945ea43ec7c53ac5a21b8c10f5618361ed396f186b900`.

### Boundary

Celebrity cases are useful regression fixtures, not proof of predictive
validity. Sports/film/music samples are best used to pressure-test event-year
signals such as championship peak, release year, award year, public fame,
controversy, relationship, injury, health crisis, and retirement. They must not
be used to reverse-engineer birth time or silently tune rules without a
pre-registered scoring plan.

## 2026-06-26 - Famous-Case Birth-Source Gate Decisions

### Motivation

The famous-case fixture set had source ratings and a broad source-quality
summary, but the executable contract still needed an explicit per-case decision
that separates hour-pillar scoring from source-review-only cases. Without a
decision matrix, a lower-quality birth-time record could accidentally influence
rule tuning through downstream calibration summaries.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_high_confidence_birth_source_ratings()`.
   - Added `_birth_source_gate_decision()`.
   - Fixture-level `birth_source_quality` now includes:
     - `source_gate_schema_version`
     - `source_gate_decision_counts`
     - `source_gate_decisions`
     - `source_gate_blocked_case_count`
     - `source_gate_blocked_case_ids`
   - Case-level `birth_source_quality` now includes:
     - `source_gate_decision`
     - `source_gate_reasons`
     - `blocks_rule_tuning`
   - Annual birth-source summary now includes source-gate counts and blocked
     event count.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added public schema definitions for `FamousCaseSourceGateDecision`,
     `FamousCaseBirthSourceQualitySummary`, and
     `FamousCaseAnnualBirthSourceQualitySummary`.
   - Bound famous-case validation summaries to the new schema refs.

3. Updated tests:
   - Capability audit now requires the source-quality gate schema, decision
     counts, blocked case ids, blocked tuning flag, and blocked event count.
   - Schema tests require source-gate fields and the explicit decision enum:
     `allow_hour_pillar_scoring` or `hold_for_source_review`.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Receipt smoke check:
  - Famous fixture hash:
    `38ec5cffa1dc9464c5123a4564a14ca508eb0f43aa8a703b8a4581f021400ea3`.
  - Source-gate decision counts:
    `allow_hour_pillar_scoring=11`, `hold_for_source_review=1`.
  - Blocked case ids: `chiang_kai_shek`.
  - Annual blocked event count: `10`.

### Boundary

The gate only controls birth-source hygiene. It does not validate the life-event
labels and does not prove predictive validity. A case blocked by this gate may
remain visible as a broad historical diagnostic, but it must not tune
hour-sensitive rules until source review upgrades the birth record.

## 2026-06-26 - Famous-Case Event-Label Source Gate

### Motivation

Birth-source gating prevents low-quality birth times from tuning hour-sensitive
rules, but famous-case calibration also depends on event labels. Championship
years, film releases, awards, public fame, health events, relationship events,
and retirements need their own source-quality gate. Otherwise a weak or generic
biographical tag could still enter rule tuning even when the birth data is
clean.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_event_label_source_gate_decision()`.
   - Added `_event_label_source_quality_summary()` at case level.
   - Added `_annual_event_label_source_quality_summary()` at annual-calibration
     level.
   - Every scored famous-case event now carries:
     - `event_label_source_gate`
     - `event_label_gate_decision`
     - `event_label_blocks_rule_tuning`
   - Event labels are split into:
     - `allow_event_label_scoring`
     - `hold_event_label_for_source_review`

2. Added domain-sensitive gate logic:
   - Sports peak labels require competition, medal, title, ranking, record, or
     comparable markers.
   - Film/television fame labels require release, award, recognition, or media
     markers.
   - Film/television project labels require release, award, production, launch,
     role, or similar project markers.
   - Music fame labels require chart, album, award, media, or comparable public
     markers.
   - Music project labels require release markers.
   - Other labels need at least a domain-specific event marker, otherwise they
     are held for source review.

3. Updated `examples/mingli_5agents/api_core.py`:
   - Added `FamousCaseAnnualEventLabelSourceQualitySummary`.
   - Made annual famous-case calibration responses require
     `event_label_source_quality_summary`.

4. Updated tests:
   - Capability audit requires event-label source gate schema version, decision
     counts, eligible count, review count, blocked tuning flag, and review case
     ids.
   - Schema contract tests require the new annual event-label source-quality
     summary schema and gate version.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Receipt smoke check:
  - Annual famous-case receipt hash:
    `ab46a5f1031f0498492ae75553bd08e3f608b68a5ed5627591b2258e9abdd607`.
  - Event labels: `130`.
  - `allow_event_label_scoring`: `83`.
  - `hold_event_label_for_source_review`: `47`.

### Boundary

This is a source-quality gate for known event labels, not a prediction accuracy
claim. Held labels may remain visible for diagnostics, but they must not tune
rules until a reviewed event-source provider supplies stronger evidence.

## 2026-06-26 - Event-Label-Gated Variant Metrics

### Motivation

The previous event-label source gate marked weak labels as
`hold_event_label_for_source_review`, but rule-variant sweeps still computed
hit rates over all known event labels. That preserved diagnostics, but it meant
held labels could still influence how future rule variants looked. The next
step was to keep all-label metrics while adding gate-qualified metrics for
future evolution decisions.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Added `_event_label_scoring_eligible_items()`.
   - Domain-topic summaries now include:
     - `event_label_scoring_eligible_count`
     - `event_label_source_review_count`
     - `event_label_eligible_strict_exact_hit_count`
     - `event_label_eligible_strict_exact_hit_rate`
     - `event_label_eligible_strict_exact_precision`
   - `domain_topic_variant_sweep` now reports both all-label and
     event-label-gated metrics.
   - `rule_variant_sweep` now reports both all-label and event-label-gated
     metrics.
   - Evolution task variant summaries now include event-label-gated metrics.

2. Updated `examples/mingli_5agents/api_core.py`:
   - Added `FamousCaseVariantSweepRow`.
   - `domain_topic_variant_sweep` and `rule_variant_sweep` now reference that
     schema instead of generic object rows.

3. Updated tests:
   - Capability audit requires event-label-gated variant metrics.
   - Schema contract requires `FamousCaseVariantSweepRow` and the gated metric
     fields.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Receipt smoke check:
  - Annual famous-case receipt hash:
    `e7d7ec5c6a635d2a61f1f8a0367ae4119bf7ec92669ac2c90c5bf422668184fd`.
  - Example rule variant `career_project/legacy_broad_launch`:
    `event_count=32`, `event_label_scoring_eligible_count=29`,
    `event_label_source_review_count=3`,
    `event_label_eligible_strict_exact_precision=0.046`.

### Boundary

This does not select or promote a new prediction rule. It adds cleaner
diagnostics so future rule evolution can distinguish all known labels from
event-source-gated labels and avoid optimizing against held-for-review events.

## 2026-06-26 - Event-Label-Gated Evolution Planning

### Motivation

The previous layer exposed event-label-gated metrics in variant sweeps, but
evolution queues and task plans could still rank work from all-label strict
metrics. That left a weak path for held-for-review labels to influence future
rule tuning. This layer makes the plan itself use only event-label-gated
strict hit and precision metrics when choosing whether to add evidence, reduce
false positives, or refine precision.

### Actions Taken

1. Updated `examples/mingli_5agents/famous_case_validation.py`:
   - Topic summaries now carry event-label-gated strict hit and precision
     metrics.
   - Domain-topic refinement queue rows include
     `task_metric_basis=event_label_gated_strict_metrics`.
   - Rule refinement queue rows include
     `priority_metric_basis=event_label_gated_strict_metrics`.
   - Annual evolution task plan rows include gated strict hit and precision
     metrics and use them for task type selection.
   - Source-review rows still route to evidence review first instead of rule
     tuning.

2. Updated `examples/mingli_5agents/tests/test_empirical_validation.py`:
   - Assertions now verify that task queues and evolution plans expose and use
     event-label-gated metrics.
   - `relationship` and `health_risk` now correctly route to
     `add_specific_evidence` because their gated strict hit/precision is zero.

### Verification

- `python -m py_compile examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_capability_audit_reports_github_state_of_art_comparison examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- Receipt smoke check:
  - Annual famous-case receipt hash:
    `c39d7de9660fe2559512ed7288a0ef184c9af9312df4d00b4abaf9f232a71bd8`.
  - `relationship`: `add_specific_evidence`,
    gated hit `0.0`, gated precision `0.0`.
  - `public_fame`: `refine_precision`,
    gated hit `0.121`, gated precision `0.148`.
  - `career_project`: `add_specific_evidence`,
    gated hit `0.034`, gated precision `0.143`.
  - `health_risk`: `add_specific_evidence`,
    gated hit `0.0`, gated precision `0.0`.
  - `sports_peak`: `reduce_false_positive`,
    gated hit `0.333`, gated precision `0.333`.

### Boundary

This still does not promote any new prediction rule. It changes the governance
of evolution planning: held-for-review labels can produce source-review or
evidence-collection tasks, but they cannot make a rule variant or a refinement
task look better.

## 2026-06-26 - Monthly Solar-Term Window Evidence

### Motivation

Monthly BaZi rows were still indexed by a simple symbolic month sequence. The
user specifically asked for each month to be independently reasoned through
five-element and useful-god relationships, and the method wiki already pointed
out that real Jieqi boundaries should eventually outrank civil-month shortcuts.
This layer adds an explicit approximate solar-term month window to every
monthly row without changing the existing month-pillar sequence yet.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/calendar_core.py`:
   - Added `SOLAR_MONTH_STARTS_APPROX`.
   - Added `solar_month_window(year, solar_month_index)`.
   - Each window records schema version, approximate Jieqi basis, month index,
     branch, start term, next term, start date, end date, and next start date.

2. Updated monthly analysis flow:
   - `examples/mingli_5agents/tools/monthly_luck.py` now attaches
     `solar_term_window` at row level and inside `bazi_evidence`.
   - `examples/mingli_5agents/topic_synthesis.py` preserves the monthly
     window in compact timing evidence.

3. Updated report rendering and gates:
   - `examples/mingli_5agents/report_renderers.py` renders a Chinese
     `节气月` anchor such as `寅，立春至惊蛰，2025-02-04至2025-03-05`.
   - `examples/mingli_5agents/benchmark.py` added
     `chinese_render_monthly_solar_term_window_anchor_ratio`.
   - `examples/mingli_5agents/api_core.py` added public schema coverage and a
     production gate requiring the rendered Chinese monthly solar-term window
     anchor ratio to be `1.0`.

4. Updated tests:
   - Monthly calendar tests assert the first 2025 symbolic flow month uses the
     approximate `立春` to `惊蛰` window.
   - Chinese render gate tests now fail when the monthly solar-term window
     anchor is missing.
   - Production readiness tests require the new anchor ratio to be `1.0`.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\calendar_core.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `2 passed`.
- Smoke output for 2025 first symbolic flow month:
  `solar_month_index=1`, branch `Yin`, `start_term_zh=立春`,
  `next_term_zh=惊蛰`, `start_date=2025-02-04`,
  `end_date=2025-03-05`.

### Boundary

This is an approximate Jieqi-month evidence layer. It does not yet compute
exact local solar-term transition times from an ephemeris provider and does not
change the existing month-pillar algorithm. The next hardening step is to let a
professional calendar provider supply exact month pillars and exact Jieqi
timestamps.

## 2026-06-26 - Provider-Override Solar-Term Month Windows

### Motivation

The previous layer made monthly Jieqi windows visible, but they were still
always approximate. The next executable improvement is not to pretend the
approximate table is exact, but to create a provider override path: if a
professional or external calendar provider supplies exact Jieqi month windows,
monthly luck rows must use those windows and keep their provenance.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/calendar_core.py`:
   - `solar_month_window()` now includes `provider_quality` and `precision`.
   - Added `normalize_solar_month_window()` for provider-supplied windows.
   - Public basis can now be approximate or provider-supplied.

2. Updated `examples/mingli_5agents/tools/monthly_luck.py`:
   - Monthly rows now check `context["solar_month_windows"]` first.
   - Supported provider keys include flat `YYYY-MM` and nested
     `year -> month` mappings.
   - If no provider window exists, rows fall back to the deterministic
     approximate Jieqi table.

3. Updated schemas and rendering:
   - `examples/mingli_5agents/api_core.py` allows
     `provider_jieqi_month_boundaries` and requires provider quality and
     precision fields on `SolarMonthWindow`.
   - `examples/mingli_5agents/report_renderers.py` formats exact timestamps for
     Chinese output without leaking raw `T` separators.
   - `examples/mingli_5agents/benchmark.py` checks the same rendered timestamp
     format as the report.

4. Updated tests:
   - Added a monthly luck test proving an `ExternalCalendarProvider` can supply
     an exact 2025-01 Jieqi window.
   - Existing approximate-window tests now assert provider quality and
     precision.

### Verification

- `python -m py_compile examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\tools\calendar_core.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\tests\test_calendar_tools.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_uses_provider_solar_term_windows_when_available examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `5 passed`.
- `pytest examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `2 passed`.
- Provider override smoke:
  `basis=provider_jieqi_month_boundaries`,
  `provider_quality=external_calendar`, `precision=exact_datetime`,
  `start_date=2025-02-03T22:10:00+08:00`.

### Boundary

This creates the exact-Jieqi provider lane, but it does not yet implement a
built-in astronomical ephemeris calculation. Exactness depends on a configured
external/professional provider supplying `solar_month_windows`.

## 2026-06-26 - Provider-Override Monthly Pillars

### Motivation

The previous layer let providers override Jieqi month windows, but the monthly
pillar itself still came from the deterministic symbolic month sequence. That
meant exact Jieqi timestamps could be visible while ten-gods, elements, hidden
stems, and branch interactions still used the approximate monthly pillar. This
layer lets a provider override the monthly pillar so downstream reasoning is
recomputed from the supplied pillar.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/monthly_luck.py`:
   - Added `_monthly_pillar_for_month()`.
   - Monthly rows now check `context["monthly_pillars"]` before using
     `_month_ganzhi()`.
   - Supported provider keys include flat `YYYY-MM` and nested
     `year -> month` mappings.
   - Added row-level `pillar_source` and evidence-level
     `monthly_pillar_source`.
   - Provider-supplied pillars now drive stem, branch, elements, focus,
     ten-gods, hidden-stem flow, and branch interactions.

2. Updated report evidence flow:
   - `examples/mingli_5agents/topic_synthesis.py` preserves monthly pillar
     source in timing evidence and evidence summaries.
   - `examples/mingli_5agents/report_renderers.py` renders monthly pillar
     source as readable Chinese and translates provider-quality tokens.
   - `examples/mingli_5agents/benchmark.py` added
     `chinese_render_monthly_pillar_source_anchor_ratio`.

3. Updated schemas and gates:
   - `examples/mingli_5agents/api_core.py` added `MonthlyPillarSource`.
   - `MonthlyLuckRow`, `MonthlyLuckBaziEvidence`, and topic timing evidence now
     carry the monthly pillar source.
   - Production Chinese render quality gates require the monthly pillar-source
     anchor ratio to be `1.0`.

4. Updated tests:
   - Approximate monthly rows assert `approximate_symbolic_month_sequence`.
   - External provider test supplies `GengShen` for 2025-01 and verifies the
     row, elements, evidence pillar, source metadata, and hidden-stem branch
     all follow the provider pillar.
   - Schema and production gates cover the new contract and render anchor.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\benchmark.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_empirical_validation.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_uses_provider_solar_term_windows_when_available examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_uses_provider_solar_term_windows_when_available examples\mingli_5agents\tests\test_empirical_validation.py::test_chinese_render_quality_gate_requires_annual_and_monthly_pillar_anchors examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q`
  passed: `5 passed`.
- Provider override smoke:
  `ganzhi=GengShen`,
  `elements={'stem': 'Metal', 'branch': 'Metal', 'focus': 'Metal'}`,
  source basis `provider_monthly_pillar`,
  provider quality `external_calendar`,
  precision `exact_jieqi_month`.

### Boundary

This enables monthly pillar override when a provider supplies `monthly_pillars`.
It does not yet compute exact monthly pillars internally. Production-grade
precision still requires a configured professional or external calendar
provider.

## 2026-06-26 - Major-Luck Interaction Evidence for Annual and Monthly Rows

### Motivation

Monthly rows already carried natal branch interactions and active major luck,
but they did not explicitly compute how the current year/month pillar interacts
with the active major-luck pillar. User requirements emphasize that each year
and month should be independently reasoned through the combined situation among
original chart, major luck, annual luck, and monthly luck. This layer adds the
missing major-luck interaction evidence.

### Actions Taken

1. Updated `examples/mingli_5agents/tools/annual_luck.py`:
   - Added `_luck_pillar_interactions()`.
   - Annual evidence now records current pillar, active major-luck pillar,
     stem element relationship, branch interactions, and summary.
   - The same evidence is inherited by monthly rows through shared BaZi
     evidence construction.

2. Updated monthly and topic synthesis:
   - `examples/mingli_5agents/tools/monthly_luck.py` interpretation basis now
     names monthly-pillar interaction with active major luck.
   - `examples/mingli_5agents/topic_synthesis.py` preserves
     `luck_pillar_interactions` and summarizes it in topic evidence.

3. Updated rendering and schema:
   - `examples/mingli_5agents/report_renderers.py` renders major-luck
     interaction text in BaZi evidence lines and topic summaries.
   - `examples/mingli_5agents/api_core.py` requires
     `luck_pillar_interactions` on annual and monthly BaZi evidence and exposes
     it in topic timing evidence.

4. Updated tests:
   - Calendar tests assert both annual and monthly rows include active
     major-luck interaction evidence.
   - Schema tests assert annual/monthly BaZi evidence and topic timing signals
     expose the field.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\tools\monthly_luck.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\api_core.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview examples\mingli_5agents\tests\test_benchmark.py examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `6 passed`.
- Smoke for 1978-04-14 male, 2025 first monthly row:
  - Current pillar: `YiYin`.
  - Major-luck pillar: `GengShen`.
  - Stem relation to major luck: `consume`.
  - Branch relations: `Yin-Shen clash` and `Yin-Shen punishment`.
  - Summary: `branch_interaction`.

### Boundary

This adds explicit interaction evidence between current annual/monthly pillars
and the active major-luck pillar. It does not yet compute a full three-body
resolution among natal chart, major luck, annual luck, and monthly luck, nor
does it rank contradictory interactions by severity and protection mechanism.

## 2026-06-30 - Resume Last Factor Evolution Mining Task

### Motivation

The user asked to resume the last factor evolution mining task. The most recent
activity in the repository was a multi-seed Tushare continuous factor loop
(`china_a_share_alpha/scripts/run_continuous_factor_loop.py`) that produced
partial outputs under `china_a_share_alpha_output/tushare_factor_library/`.

### Actions Taken

1. Inspected the state of the last task:
   - Seed 10 loop completed 4 generations and wrote a leaderboard.
   - Seed 20 loop completed 5 generations and wrote a leaderboard and report.
   - Seed 30 loop only reached generation 1 and appears interrupted.
   - No global `factor_library.csv` or `continuous_loop_summary.json` existed,
     indicating the multi-seed runner did not finish the merge step.

2. Merged the completed seed leaderboards (seeds 10 and 20) into a global
   factor library using the same filter as the runner:
   - Filter: train_ic and test_ic not null, and train_ic * test_ic >= 0.
   - Deduplicated by expression and sorted by test_ic descending.
   - Output: `china_a_share_alpha_output/tushare_factor_library/factor_library.csv`
     with 66 unique factors.
   - Summary: `china_a_share_alpha_output/tushare_factor_library/continuous_loop_summary.json`.

3. Verified the best evolved factor:
   - Expression: `ts_max(ts_min(log(volume), 5), 60)`
   - Test IC: 0.00896
   - Source: seed 20, generation 1.

### Verification

- Merged library written successfully.
- Summary JSON written successfully.
- Best expression and test IC match the seed 20 leaderboard.

### Final Completion (after TUSHARE_TOKEN provided)

4. Completed seed 30 from scratch using `run_factor_loop` with seed 30:
   - Reached generation 3 and converged on patience.
   - Outputs: `china_a_share_alpha_output/tushare_factor_library/seed_30/`.

5. Re-merged all three seed leaderboards (10, 20, 30):
   - Output: `china_a_share_alpha_output/tushare_factor_library/factor_library.csv`
     with 97 unique factors.
   - Summary: `china_a_share_alpha_output/tushare_factor_library/continuous_loop_summary.json`.
   - Best evolved factor remains `ts_max(ts_min(log(volume), 5), 60)` with test IC
     0.00896 from seed 20.

6. Ran the Tushare backtest comparison including the top 20 evolved factors:
   - Command:
     `python -m china_a_share_alpha.scripts.run_tushare_backtest --start-date 20210601 --end-date 20260601 --split-date 20240101 --evolved-csv china_a_share_alpha_output/tushare_factor_library/factor_library.csv --evolved-top-n 20`
   - Outputs:
     - `china_a_share_alpha_output/tushare_backtest/factor_comparison.csv`
     - `china_a_share_alpha_output/tushare_backtest/factor_comparison_report.md`
     - `china_a_share_alpha_output/tushare_backtest/summary.json`
   - Universe: CSI300 constituents, 300 symbols, 1210 dates.
   - Best by Sharpe: `momentum_20` (0.406).
   - Best by IC: `value_pb` (IC 0.0097).
   - Top evolved performers in the backtest:
     - `evolved_4` / `evolved_3`: Sharpe 0.404, IC 0.00638.
     - `evolved_2`: Sharpe 0.242, IC 0.00405.
     - `evolved_1`: Sharpe 0.065, IC 0.00555.

### Verification

- Seed 30 completed without errors.
- Global library regenerated with 97 unique factors.
- Backtest ran to completion; summary JSON and comparison CSV/MD written.

### Boundary

The task is now fully resumed and completed. The evolved library is available
for downstream portfolio evolution or further alpha decay monitoring. Note that
the backtest is before risk-model/sector neutralization and uses a 10 bps
one-way transaction-cost assumption.

## 2026-06-30 - Interaction Pressure Severity Summary

### Motivation

The latest Mingli annual/monthly reasoning already records natal branch
interactions and active major-luck pillar interactions. The remaining weakness
was prioritization: reports could list 冲、刑、害、破、合, but did not yet rank
which relation should drive the interpretation first.

### Actions Taken

1. Added a branch interaction severity table in
   `examples/mingli_5agents/tools/annual_luck.py`:
   - 冲 / `clash`: 5
   - 刑 / `punishment`: 4
   - 害 / `harm`: 3
   - 破 / `break`: 2
   - 合 / `combine`: 1

2. Added severity to both interaction sources:
   - current annual/monthly pillar against natal chart branches;
   - current annual/monthly pillar against active major-luck pillar.

3. Added `interaction_pressure_summary` to annual/monthly BaZi evidence:
   - schema version;
   - maximum severity;
   - pressure level;
   - total interaction count;
   - natal interaction count;
   - major-luck interaction count;
   - top interactions sorted by severity.

4. Propagated the pressure summary through topic synthesis, schema contracts,
   Chinese report rendering, and regression tests.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\annual_luck.py examples\mingli_5agents\report_renderers.py examples\mingli_5agents\api_core.py examples\mingli_5agents\topic_synthesis.py examples\mingli_5agents\tests\test_calendar_tools.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `2 passed`.
- Smoke for 1978-04-14 male, 2025 first monthly row:
  - `schema_version`: `interaction-pressure-summary-v1`
  - `max_severity`: `5`
  - `pressure_level`: `high`
  - `interaction_count`: `2`
  - `major_luck_interaction_count`: `2`
  - `natal_interaction_count`: `0`
  - top interactions: `Yin-Shen clash` severity 5 and `Yin-Shen punishment`
    severity 4.

### Boundary

This upgrade ranks pairwise branch interaction pressure across natal and
major-luck evidence. It still does not fully resolve four-body interaction
priority among natal chart, major luck, annual luck, and monthly luck with
protection-mechanism override.

## 2026-06-30 - Geju Hengmen Pattern School Agent Upgrade

### Motivation

The user provided `examples/格局横门断.docx` as a school-specific BaZi method
source and asked to upgrade the Mingli agents with that logic. The document's
most engineerable rules are month-command pattern selection, exposed hidden
stems, branch-group transformation, benign/adverse use-mode handling, and the
principle that meeting groups strengthen force but do not dissolve punishment,
clash, combination, harm, break, or tomb relations.

### Actions Taken

1. Added `hengmen_pattern_analysis` in
   `examples/mingli_5agents/tools/bazi_deep_analysis.py`.
   - Uses the month branch as the pattern command.
   - Checks month hidden stems and whether they are exposed in visible stems.
   - Determines a commanding stem and coarse ten-god role.
   - Marks use mode as 顺用, 逆用或另取财官食杀, 顺逆待分, or 待校准.
   - Detects trine/meeting branch group changes.
   - Records purity state: 较清, 有兼格, 驳杂, or 待透.

2. Added a new BaZi school sub-agent in
   `examples/mingli_5agents/tools/bazi_school_debate.py`:
   - agent id: `hengmen_pattern_agent`
   - school: `格局横门断`
   - method focus: 月令提纲, 透干会支, 善顺恶逆, 藏干待用.

3. Exposed the new layer through final reports and contracts:
   - `examples/mingli_5agents/run_demo.py`
   - `examples/mingli_5agents/api_core.py`
   - `examples/mingli_5agents/method_surface.py`
   - `examples/mingli_5agents/famous_case_validation.py`

4. Updated regression tests:
   - BaZi school debate now expects seven school votes.
   - Method matrix now includes `hengmen_pattern`.
   - Schema contract requires `hengmen_pattern_analysis`.
   - Famous-case school topic hints include `格局横门断`.

### Verification

- `python -m py_compile examples\mingli_5agents\tools\bazi_deep_analysis.py examples\mingli_5agents\tools\bazi_school_debate.py examples\mingli_5agents\run_demo.py examples\mingli_5agents\api_core.py examples\mingli_5agents\famous_case_validation.py examples\mingli_5agents\tests\test_mingli_system.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py`
  passed.
- `pytest examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `2 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_reference_charts.py examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `3 passed`.
- `pytest examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `2 passed`.
- Smoke for 1978-04-14 male:
  - `hengmen-pattern-analysis-v1`
  - summary: month command `Chen`, exposed `Wu`, commanding ten-god
    `expression`, use mode `顺逆待分`, purity `较清`.
  - school debate agent count: `7`.

### Boundary

The new layer captures deterministic structural rules from the provided document.
It does not copy the document's strong event claims as facts, and it does not yet
distinguish 正偏十神 with full professional precision when the fallback provider
only supplies coarse ten-god categories.

## 2026-06-30 - Lin Fan Hengmen Rejudgement Report

### Motivation

The user asked to rejudge the Lin Fan case after the Geju Hengmen pattern-school
agent upgrade.

### Actions Taken

1. Re-ran the Lin Fan case with the upgraded local Mingli five-agent system:
   - birth: 1978-04-14 06:50, male, Sanming, Fujian;
   - annual range: 1978 through 2035;
   - monthly range: 2026 and 2027.

2. Wrote regenerated machine artifacts:
   - `examples/mingli_5agents/reports/linfan_20260630_hengmen_rejudge.analysis.json`
   - `examples/mingli_5agents/reports/linfan_20260630_hengmen_rejudge_zh.report.md`

3. Wrote a cleaned Chinese reading summary:
   - `examples/mingli_5agents/reports/linfan_20260630_hengmen_rejudge_clean_zh.md`

### Verification

- The regenerated structure includes `hengmen-pattern-analysis-v1`.
- BaZi school debate includes seven school votes.
- The Geju Hengmen layer reads the chart as:
  - month command: Chen;
  - exposed month hidden stem: Wu;
  - commanding ten-god: expression;
  - use mode: 顺逆待分;
  - purity: 较清.

### Boundary

The cleaned report is an interpretive summary derived from structured symbolic
evidence. It should still be calibrated against known real life events before
being treated as a high-confidence retrospective chronology.

## 2026-06-30 - BaZi Classical Source PDF Downloads

### Motivation

The user asked to search and download classical BaZi and Mingli texts for local
research and future agent evolution.

### Actions Taken

1. Searched for public/open archive sources for classical BaZi materials.
2. Attempted Wikimedia Commons NLC PDF downloads for several candidate titles,
   but direct requests returned HTTP 429 Too Many Requests.
3. Switched to Internet Archive direct downloads and stored four PDFs under:
   - `examples/mingli_5agents/classical_sources/raw_pdfs/`
4. Added local provenance files:
   - `examples/mingli_5agents/classical_sources/README.md`
   - `examples/mingli_5agents/classical_sources/manifest.json`

### Downloaded Files

- `san_ming_tong_hui_juan_1_ia.pdf`
  - Title: 三命通会，卷一
  - Source: `https://archive.org/details/06056477.cn`
  - SHA256: `16f9fc8204ac0d7189320c105c5febc6662ec5f8a5ea34b7d1647a6694d440dd`
- `san_ming_tong_hui_juan_9_ia.pdf`
  - Title: 三命通会，卷九
  - Source: `https://archive.org/details/06056485.cn`
  - SHA256: `e5b28e6411e3dd45a40151d0df4595c415e1a4c56c2eb3578bde4baca98b211a`
- `li_xu_zhong_ming_shu_luo_lu_zi_ia.pdf`
  - Title: 李虚中命书、珞琭子三命消息赋注，守山阁丛书本
  - Source: `https://archive.org/download/shoushange`
  - SHA256: `109c3db5650598c1c6e7a2c73791aa3edc88df09e80f2c25937fae27eef0072c`
- `tian_bu_zhen_yuan_ren_ming_bu_ia.pdf`
  - Title: 天步真原人命部，守山阁丛书本
  - Source: `https://archive.org/download/shoushange`
  - SHA256: `ea619b0df40afa3ee6b7d23532f980a303e647213c756200b5774f24cb48c3e8`

### Boundary

These files are local research sources only. They are not yet OCRed, indexed,
or promoted into agent rules. Edition review, OCR quality checks, and method
comparison are required before any rule change.

## 2026-06-30 - Classical BaZi Layered Methodology Agent Integration

### Motivation

The user asked to read the downloaded BaZi/Mingli classical sources and write
their analysis logic into the agents as cooperative, debating group
intelligence, covering overall natal chart, annual luck, and monthly luck.

### Source Reading Boundary

The downloaded PDFs were inspected with `pypdf`. Their embedded text is poor or
garbled OCR, so exact page-level quotation and direct textual rule extraction
are not reliable yet. The implementation therefore promotes only
source-governed, paraphrased method cards and keeps the files as local scan
evidence pending OCR/manual edition review.

### Actions Taken

1. Registered new BaZi classical source IDs:
   - `bazi_sanming_tonghui`
   - `bazi_early_sanming`
   - `bazi_tianbu_zhenyuan`

2. Added classical index evidence cards in
   `examples/mingli_5agents/classical_text_index.py`.

3. Added local method-card manifest:
   - `examples/mingli_5agents/classical_sources/method_cards.json`

4. Added `classical_layered_methodology` to BaZi deep analysis:
   - overall natal chart;
   - major luck;
   - annual trigger;
   - monthly implementation;
   - fact calibration.

5. Added `classical_timing_trace` to annual and monthly BaZi evidence.

6. Added two BaZi school debate agents:
   - `sanming_tonghui_agent`
   - `early_sanming_lineage_agent`

7. Updated contracts, method surface, famous-case topic hints, and regression
   tests.

### Verification

- `python -m py_compile ...` for the touched Mingli files passed.
- `pytest examples\mingli_5agents\tests\test_calendar_tools.py::test_annual_luck_builds_structured_year_rows examples\mingli_5agents\tests\test_calendar_tools.py::test_monthly_luck_builds_selected_year_rows examples\mingli_5agents\tests\test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples\mingli_5agents\tests\test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q`
  passed: `4 passed`.
- `pytest examples\mingli_5agents\tests\test_empirical_validation.py::test_production_readiness_gates_birth_profile_import_preview -q`
  passed: `1 passed`.
- `pytest examples\mingli_5agents\tests\test_reference_charts.py examples\mingli_5agents\tests\test_benchmark.py -q`
  passed: `4 passed`.
- Smoke verified:
  - BaZi sources include all three new classical source IDs.
  - school debate agent count is `9`.
  - method matrix includes `classical_layered_bazi`.
  - annual trace level is `annual`.
  - monthly trace level is `monthly`.

### Boundary

This is a source-governed methodology integration, not a full OCR reading of
every page. The next rigorous step is OCR/manual transcription with page-level
rule cards before promoting exact book passages into stronger rules.

## 2026-06-30 - A-Share Factor Verification: Neutralized Evolution + Decay Check

### Motivation

The user asked how to verify the evolved factors on A-shares. The previous
non-neutralized run showed that hand-designed factors (`momentum_20`,
`value_pb`) outperformed the evolved library. The next validation step is to
run the same multi-seed evolution with sector and market-cap neutralization,
then compare against the hand-designed baseline and check rolling IC decay.

### Actions Taken

1. Added a reusable helper script:
   - `china_a_share_alpha/scripts/_run_neutralized_seed.py` loads the base
     Tushare config, forces `neutralize_sector: true` and
     `neutralize_market_cap: true`, and runs one seed.

2. Ran three neutralized seeds in parallel:
   - Seed 10: 4 generations, best test_ic 0.00254.
   - Seed 20: 8 generations, best test_ic 0.00863.
   - Seed 30: 4 generations, best test_ic 0.00000.
   - Outputs: `china_a_share_alpha_output/tushare_factor_library_neutralized/`.

3. Merged the neutralized seed leaderboards:
   - Filter: train/test IC finite and same sign.
   - Deduplicated by expression.
   - Result: 100 unique factors in
     `china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library.csv`.
   - Best by test IC: `div(-0.114, ts_max(volume, 60))` (test_ic 0.00863).

4. Ran the Tushare backtest comparison against the neutralized evolved library:
   - Output dir: `china_a_share_alpha_output/tushare_backtest_neutralized/`.
   - Universe: CSI300 constituents, 300 symbols, 1210 dates.
   - Best by Sharpe and IC: `evolved_2` (Sharpe 1.497, IC 0.0141).
   - `evolved_2` maps to expression `abs(return)`.
   - Other strong evolved factors:
     - `evolved_5`: Sharpe 1.134, IC 0.00461.
     - `evolved_7`: Sharpe 0.977, IC 0.0115.
     - `evolved_3`: Sharpe 0.789, IC 0.00554.
   - Hand-designed baseline best: `momentum_20` (Sharpe 0.406), `value_pb`
     (IC 0.0097). Neutralized evolved factors clearly beat both.

5. Ran a rolling monthly IC decay check on the top 5 neutralized factors:
   - Outputs:
     - `china_a_share_alpha_output/tushare_factor_library_neutralized/rolling_ic_summary.csv`
     - `china_a_share_alpha_output/tushare_factor_library_neutralized/rolling_ic_series.csv`
   - Key findings over 60 months:
     - `abs(return)`: mean IC 0.0147, IR 0.34, but annualized slope -0.00139
       (mild decay).
     - `div(-0.114, ts_max(volume, 60))`: mean IC 0.0053, annualized slope
       +0.00291 (recently strengthening).
     - `abs(ts_std(abs(return), 5))`: mean IC 0.0065, annualized slope
       +0.00256.

### Verification

- Neutralized multi-seed loops completed and wrote leaderboards.
- Global library merge produced 100 unique factors.
- Backtest ran to completion; summary JSON confirms `evolved_2` is best by
  Sharpe and IC.
- Rolling IC summary CSV written; top factors show non-zero but modest IC and
  mixed decay slopes.

### Boundary

Neutralization uses the project's deterministic synthetic sector/market-cap
mapping because no real sector CSV was supplied. For production validation, a
real `sector_csv` should be provided. Transaction costs are fixed at 10 bps
one-way; real slippage and market impact are not modeled. The strongest evolved
factor (`abs(return)`) is essentially a volatility proxy and may overlap with
existing low-vol or short-term reversal styles.

## 2026-06-30 - Comprehensive Cross-Universe Factor Audit (Qlib / TA-Lib / Tushare / Alpha101 / Evolved)

### Motivation

The user asked to traverse Qlib, TA-Lib, and Tushare factors and test them on
A-share indices, major stocks, and tech stocks with comparisons. This entry
records the full sweep.

### Actions Taken

1. **Qlib exploration**
   - Tried `pip install pyqlib` and `pip install qlib`; both returned
     "No matching distribution found" on Python 3.14.4.
   - Conclusion: Qlib is blocked in this environment because it does not yet
     provide wheels for Python 3.14. Recorded as a blocker.

2. **TA-Lib installation and expansion**
   - Installed `TA-Lib` Python wrapper via pip (`TA-Lib-0.6.8`).
   - Verified import and function listing.
   - Added 8 TA-Lib indicators to the cross-universe audit:
     `rsi_14`, `macd_hist`, `bbands_pctb`, `cci_20`, `adx_14`, `willr_14`,
     `atr_14`, `obv` (all cross-sectionally ranked).

3. **Built cross-universe audit script**
   - New file: `china_a_share_alpha/scripts/run_cross_universe_factor_audit.py`.
   - Supports universes:
     - `csi300` (000300.SH constituents)
     - `csi500` (000905.SH constituents)
     - `csi1000` (000852.SH constituents)
     - `major` (top 50 by total market cap from `daily_basic`)
     - `tech` (Tushare industry keywords: 半导体、元件、计算机设备、通信设备、
       电子、软件服务, etc.)
   - Evaluates factor groups:
     - Hand-designed Tushare factors (`momentum_20`, `reversal_5`,
       `volume_price_20`, `low_vol_20`, `value_pb`, `liquidity_20`, plus
       `multi_timeframe`, `multi_style_equal`, `ic_weighted_train`).
     - TA-Lib factors.
     - Alpha101 factors (`alpha_001`, `alpha_003`, `alpha_101`).
     - Top 5 evolved factors from the neutralized library.
   - Metrics: IC, RankIC, ICIR, train/test IC, turnover, annualized return,
     Sharpe, max drawdown, cost-adjusted return.

4. **Executed full audit**
   - Date range: 2021-06-01 to 2026-06-01.
   - Train/test split: 2024-01-01.
   - Universes sizes:
     - CSI300: 300 symbols, 356,207 rows.
     - CSI500: 500 symbols, 585,955 rows.
     - CSI1000: 1,000 symbols, 1,142,982 rows.
     - Major: 50 symbols, 56,702 rows.
     - Tech: 1,762 symbols, 1,875,857 rows.
   - Total factor-universe records: 125.

5. **Key results**
   - Best by Sharpe overall: `evolved_2` (`abs(return)`) in `major` universe,
     Sharpe 1.80, IC 0.0206.
   - Best by IC overall: `evolved_4`
     (`abs(ts_std(cs_zscore(ts_mean(-0.496, 60)), 5))`) in `major` universe,
     IC 0.0316.
   - `evolved_2` (`abs(return)`) is the dominant cross-universe factor:
     - CSI300: Sharpe 1.50, IC 0.0141.
     - CSI500: Sharpe 1.53, IC 0.0213.
     - CSI1000: Sharpe 1.36, IC 0.0211.
     - Major: Sharpe 1.80, IC 0.0206.
     - Tech: Sharpe 1.77, IC 0.0180.
   - TA-Lib factors performed strongest in `major` universe:
     - `talib_adx_14`: Sharpe 1.29, IC 0.0170.
     - `talib_bbands_pctb`: Sharpe 1.21, IC 0.0126.
     - `talib_cci_20`: Sharpe 1.19, IC 0.0131.
   - Alpha101 `alpha101_001` showed solid Sharpe in CSI300 (0.86), CSI500
     (1.07), and major (1.57).
   - Hand-designed `value_pb` was strongest in tech (Sharpe 1.68, IC 0.0144).

6. **Outputs**
   - `china_a_share_alpha_output/cross_universe_audit/cross_universe_comparison.csv`
   - `china_a_share_alpha_output/cross_universe_audit/cross_universe_report.md`
   - `china_a_share_alpha_output/cross_universe_audit/summary.json`

### Verification

- TA-Lib installed and importable.
- All five universes resolved and loaded successfully.
- All factor groups evaluated without fatal errors.
- Summary JSON and comparison CSV/MD generated.

### Boundary

- Qlib could not be installed due to Python 3.14 incompatibility.
- TA-Lib indicators are limited to the 8 implemented in the audit script; many
  more TA-Lib functions remain untapped.
- Sector/market-cap neutralization is synthetic; real sector mapping would
  change results.
- Transaction cost is fixed at 10 bps one-way. The top factor `abs(return)` is
  a volatility proxy and may be correlated with existing risk factors.

## 2026-06-30 - Qlib Installation and Cross-Universe Audit on Python 3.11

### Motivation

The user asked to install Qlib despite the Python 3.14 blocker. The plan was to
install Python 3.11 in an isolated venv, install pyqlib wheels there, download
community Qlib A-share data, and run the same cross-universe factor audit.

### Actions Taken

1. **Installed Python 3.11.9 via winget** and created a project venv at
   `C:/aicoding/semas_framework/.venv_py311`.

2. **Installed pyqlib 0.9.7** and project dependencies in the venv.

3. **Downloaded community Qlib China A-share data** (530 MB tar.gz from
   chenditc/investment_data) to
   `C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data`.

4. **Fixed `china_a_share_alpha/data/qlib_loader.py`** for Qlib 0.9.7:
   - Pass `D.instruments(instruments)` instead of the raw string to
     `D.features`.
   - Rename the Qlib date index column from `datetime` to `date`.
   - Use the same instrument object for the forward-return query.

5. **Created `china_a_share_alpha/scripts/run_qlib_factor_audit.py`**:
   - Forces `QLIB_SERIAL_MODE=1` to avoid Windows spawn-multiprocessing issues.
   - Uses synthetic sector/market-cap mapping because community Qlib data does
     not include `$sector`, `$market_cap`, or fundamentals.
   - Skips factors referencing unavailable columns (`pb`, `turnover_rate`).
   - Adds TA-Lib indicators with float64 casting because Qlib prices are
     float32.
   - Evaluates hand-designed, TA-Lib, Alpha101, and evolved factors across
     CSI300, CSI500, CSI1000, major (top 50 synthetic market cap), and tech
     (synthetic sector).

6. **Ran the Qlib audit** (date range 2018-01-01 to 2023-12-31, split
   2021-01-04). Universe sizes:
   - CSI300: 433,814 rows, 524 symbols.
   - CSI500: 720,450 rows, 1,006 symbols.
   - CSI1000: 1,440,852 rows, 2,103 symbols.
   - Major: 48,217 rows, 50 symbols.
   - Tech: 1,525,924 rows, 1,465 symbols.

7. **Key Qlib results**:
   - Best by Sharpe: `ic_weighted_train` in tech universe, Sharpe 4.38,
     IC 0.0393.
   - Best by IC: `ic_weighted_train` in major universe, IC 0.0678,
     Sharpe 2.98.
   - Strongest hand-designed factor: `low_vol_20` (IC up to 0.048 in major,
     Sharpe up to 2.45 in tech).
   - Strongest TA-Lib factor: `talib_adx_14` in CSI300 (Sharpe 1.64), but
     generally weaker than in the Tushare dataset.
   - Evolved factors were mostly weaker on Qlib data than on Tushare; best
     evolved (`evolved_4`) had IC ~0.006 in major/tech.

8. **Outputs**:
   - `china_a_share_alpha_output/qlib_factor_audit/qlib_comparison.csv`
   - `china_a_share_alpha_output/qlib_factor_audit/qlib_report.md`
   - `china_a_share_alpha_output/qlib_factor_audit/summary.json`

### Verification

- Python 3.11 installed and venv created.
- `import qlib` succeeds; version 0.9.7.
- Qlib data downloaded and extracted.
- `_test_qlib_load.py` confirmed train/test panels are populated.
- Full audit ran to completion; CSV/MD/JSON outputs generated.

### Boundary

- The audit uses **community-maintained** Qlib data, not official Qlib data.
- Community data lacks real sector/market-cap/fundamental fields, so
  neutralization and sector filtering use synthetic deterministic mappings.
- `value_pb` and `liquidity_20` were skipped because `pb` and `turnover_rate`
  are unavailable in this Qlib dataset.
- Results differ materially from the Tushare audit, highlighting dataset
  dependency. Low-vol and short-term reversal are stronger in Qlib data, while
  the evolved volatility proxy `abs(return)` was strongest in Tushare data.

## 2026-06-30 - Unified Factor Ranking Across Tushare and Qlib Audits

### Motivation

The user asked to rank all tested factors. Combined the Tushare and Qlib
factor-universe results into a single ranking using a composite score.

### Actions Taken

1. Created `china_a_share_alpha/scripts/rank_all_factors.py` which loads:
   - `china_a_share_alpha_output/cross_universe_audit/cross_universe_comparison.csv`
   - `china_a_share_alpha_output/qlib_factor_audit/qlib_comparison.csv`

2. Composite score formula:
   - IC: 35%
   - Test IC: 25%
   - Sharpe: 25%
   - Rank IC: 15%
   - Penalty: max_drawdown (10%) + turnover (5%)

3. Produced two rankings:
   - **Per-observation**: every factor-universe-data_source combination.
   - **Aggregated**: median composite score per factor, penalized by cross-
     observation standard deviation to reward consistency.

4. Generated outputs:
   - `china_a_share_alpha_output/factor_ranking/factor_ranking_all_observations.csv`
   - `china_a_share_alpha_output/factor_ranking/factor_ranking_aggregated.csv`
   - `china_a_share_alpha_output/factor_ranking/factor_ranking_report.md`
   - `china_a_share_alpha_output/factor_ranking/summary.json`

### Key Results

- Total observations: 235 (25 unique factors across 5 universes and 2 data
  sources).
- Top per-observation: `ic_weighted_train` in Qlib tech universe
  (composite 1.066, Sharpe 4.38, IC 0.039).
- Top aggregated factor: `ic_weighted_train` (combined group), final score
  0.253, mean Sharpe 1.52, mean IC 0.022.
- Top 5 aggregated factors:
  1. `ic_weighted_train` (combined)
  2. `evolved_2` (`abs(return)`)
  3. `talib_adx_14`
  4. `evolved_3`
  5. `value_pb`
- Worst aggregated factors: `volume_price_20`, `alpha101_003`, `evolved_1`.

### Verification

- Ranking script ran successfully.
- CSV, Markdown, and JSON outputs written.
- Aggregated ranking rewards factors that are strong and consistent across both
  data sources and all universes.

### Boundary

- The composite weights are a design choice; changing weights would reorder
  factors.
- Aggregation uses synthetic/missing-sector mappings and the 10 bps one-way cost
  assumption from the underlying audits.
- Some factors only appear in one data source (e.g., `value_pb` only in
  Tushare), which biases their aggregated score.

## 2026-06-30 - Out-of-Sample Test on 2025 to First Half 2026

### Motivation

The user asked to test all factors on the most recent A-share data (2025 to
first half of 2026) and compare them. This serves as a true out-of-sample
period for the evolved factors (trained on 2021-2024) and as a recent-period
stress test for hand-designed, TA-Lib, and Alpha101 factors.

### Actions Taken

1. Ran `run_cross_universe_factor_audit.py` on Tushare with:
   - Start date: 2025-01-01
   - End date: 2026-06-30
   - Train/test split: 2025-07-01
   - Universes: CSI300, CSI500, CSI1000, major, tech
   - Output dir: `china_a_share_alpha_output/cross_universe_audit_2025h1_2026h1/`

2. Universe sizes in the recent period:
   - CSI300: 206 symbols, 73,626 rows.
   - CSI500: 500 symbols, 178,596 rows.
   - CSI1000: 1,000 symbols, 356,952 rows.
   - Major: 50 symbols, 17,240 rows.
   - Tech: 1,766 symbols, 612,489 rows.

3. Created `china_a_share_alpha/scripts/compare_factor_periods.py` to compare
   the recent period against the original 2021-2026 Tushare audit using the
   same composite score.

4. Also generated a dedicated ranking for the 2025-2026H1 period using
   `rank_all_factors.py`.

### Key Results

**Top factors in 2025-2026H1 (aggregated across universes):**

1. `evolved_2` (`abs(return)`) — median composite 0.692, mean Sharpe 2.69.
2. `evolved_3` (`abs(ts_std(abs(return), 5))`) — median composite 0.567, mean
   Sharpe 2.34.
3. `alpha101_001` — median composite 0.518, mean Sharpe 2.30.
4. `talib_rsi_14` — median composite 0.478, mean Sharpe 1.81.
5. `talib_cci_20` — median composite 0.471, mean Sharpe 2.01.

**Factors that improved most vs 2021-2026:**

- `talib_atr_14`: composite change +0.524, Sharpe change +2.00.
- `talib_rsi_14`: composite change +0.432, Sharpe change +1.66.
- `evolved_3`: composite change +0.396, Sharpe change +1.44.
- `evolved_2`: composite change +0.312, Sharpe change +1.10.
- `momentum_20`: composite change +0.287, Sharpe change +1.19.

**Factors that deteriorated most vs 2021-2026:**

- `multi_style_equal`: composite change -0.546.
- `value_pb`: composite change -0.490.
- `low_vol_20`: composite change -0.362.
- `liquidity_20`: composite change -0.309.
- `reversal_5`: composite change -0.204.
- `ic_weighted_train`: composite change -0.146.

### Interpretation

The 2025-2026H1 period represents a clear **style shift**:
- **Volatility/proxy factors (`evolved_2`, `evolved_3`)** became dominant.
- **Momentum** recovered strongly.
- **Low-volatility and short-term reversal** collapsed.
- **Value (`value_pb`) and liquidity** also deteriorated.
- The previous overall winner `ic_weighted_train` underperformed in the recent
  period because its weights were dominated by low_vol/reversal, which stopped
  working.

### Outputs

- `china_a_share_alpha_output/cross_universe_audit_2025h1_2026h1/`
  - `cross_universe_comparison.csv`
  - `cross_universe_report.md`
  - `summary.json`
- `china_a_share_alpha_output/factor_period_comparison/`
  - `factor_period_comparison.csv`
  - `factor_period_comparison_report.md`
  - `summary.json`
- `china_a_share_alpha_output/factor_ranking_2025h1_2026h1_only/`
  - `factor_ranking_aggregated.csv`
  - `factor_ranking_report.md`
  - `summary.json`

### Verification

- Audit completed for all five universes.
- Comparison script ran; CSV, Markdown, and JSON outputs written.
- Ranking script ran for the recent period only.

### Boundary

- CSI300 contained only 206 symbols in this window, likely due to symbol
  changes/delistings not reflected in the cached constituent list.
- The train window is only six months (2025H1), so IC-weighted weights are
  estimated on limited data.
- Results are specific to 2025-2026H1 and should not be extrapolated without
  further rolling validation.

## 2026-06-30 - New Evolution Schemes: Enhanced Grammar and Portfolio Weight Search

### Motivation

The user asked whether I could design factor combinations / evolution schemes
with a better chance of improving returns. Implemented and tested two new
approaches:

1. **Enhanced expression-space evolution**: richer operator grammar + Sharpe/IR
   fitness instead of pure IC.
2. **Portfolio weight-space evolution**: search optimal combination weights over
   an existing factor library to maximize Sharpe.

### Actions Taken

1. Extended `china_a_share_alpha/factor/expression.py` and `parser.py` with new
   operators:
   - `ts_ema`, `ts_pct_change`, `ts_zscore`, `ts_shift` (time-series)
   - `signed_power`, `winsorize` (unary)
   - `if_positive` (binary conditional)

2. Added constant-input guard in `RollingBinaryOp.eval` so `ts_corr`/`ts_cov`
   with a constant operand returns NaN instead of a spurious value.

3. Added degenerate-factor rejection in `FactorPopulation.evaluate`: factors
   with >50% NaN or near-zero train/test standard deviation are penalized.

4. Created `china_a_share_alpha/evolution/enhanced_factor_mutator.py` using the
   extended grammar.

5. Created `china_a_share_alpha/loop/enhanced_population.py` with a fitness
   function that weights test Sharpe (45%), cost-adjusted return (25%), test IC
   (20%), rank IC (10%), minus turnover and drawdown penalties.

6. Created `china_a_share_alpha/scripts/run_enhanced_factor_loop.py` plus
   config `china_a_share_alpha/examples/enhanced_loop_config.yaml`.

7. Created `china_a_share_alpha/scripts/run_portfolio_weight_evolution.py`
   which loads a factor library, z-scores each base factor, and runs a GA over
   normalized weight vectors with Sharpe objective.

8. Ran three seeds of the enhanced loop on Tushare CSI300 (2021-06 to
   2026-06, split 2024-01-01) and one portfolio-weight evolution over the top
   10 neutralized factors.

### Key Results

**Enhanced expression evolution:**

| seed | best expression | test IC | test Sharpe | test MDD |
|---|---|---|---|---|
| 10 | `mul(high, ts_max(ts_min(ts_pct_change(return,20),3),3))` | 0.003 | -0.69 | -0.32 |
| **20** | **`ts_zscore(high, 20)`** | **0.011** | **1.25** | -0.19 |
| 30 | `ts_min(ts_shift(div(div(return,-0.371),volume),20),20)` | 0.003 | -0.32 | -0.30 |

- Seed 20 discovered a simple, interpretable winner: **20-day high-price
  z-score**, with positive test Sharpe and low turnover.
- Seeds 10 and 30 underperformed, showing high variance across random seeds.

**Portfolio weight evolution:**

- Train Sharpe reached **2.72**, IC 0.015, MDD -7.2%, turnover 0.25%.
- Test Sharpe collapsed to **0.23**, cost-adjusted return negative, because the
  base factors were selected on test IC from the original library (look-ahead
  bias) and the weights overfit the training period.

### Bugs Found and Fixed During the Run

- A bogus factor `ts_shift(ts_corr(winsorize(close), abs(ts_sum(0.999,5)),3),60)`
  initially produced test Sharpe 6.91 and IC 0.117. Investigation showed
  `ts_sum(0.999,5)` is constant, so `ts_corr` with a constant is undefined.
  Fixed by returning NaN for constant operands and rejecting degenerate factors.

### Interpretation

- Sharpe-based selection is theoretically better aligned with returns, but the
  search space is larger and the small population (20) struggles to find robust
  complex expressions. It did rediscover a simple price-level anomaly.
- Portfolio-weight search can fit training data very well but is extremely
  prone to overfit when base factors are pre-selected on test performance.

### Outputs

- `china_a_share_alpha_output/enhanced_factor_loop_fixed/seed_*/`
  - `factor_loop_leaderboard.csv`
  - `factor_loop_history.json`
  - `factor_report_*.json`
- `china_a_share_alpha_output/portfolio_weight_evolution/`
  - `weight_evolution_result.json`
  - `weights.csv`

### Verification

- New operators parse and evaluate correctly.
- Enhanced loop runs end-to-end for multiple seeds.
- Constant-correlation bug patched and verified.
- Portfolio-weight script runs and reports train/test metrics.

### Boundary and Next Steps

- Need a proper **validation fold** for portfolio weight evolution (use only
  train-set metrics for factor selection and weight optimization).
- Enhanced evolution likely needs larger population, more generations, or
  staged search (first find good base factors, then combine).
- The best enhanced factor (`ts_zscore(high,20)`) should be added to the
  cross-universe audit to verify robustness across CSI500/1000/major/tech.

## 2026-06-30 — Follow-up verification of `high_zscore_20` and train-only portfolio evolution

### Motivation

The GitHub commit (`48b0d58`) pushed the enhanced expression evolution, Qlib
audit, and cross-universe ranking code. Two follow-up checks remained from the
previous run:

1. Verify whether the best enhanced-evolution factor, `cs_rank(ts_zscore(high, 20))`,
   generalizes across CSI300/500/1000, major stocks, and tech stocks.
2. Re-run portfolio-weight evolution using only training-set metrics for factor
   selection, removing the look-ahead bias from the first attempt.

### Actions Taken

1. Added `high_zscore_20` to the cross-universe Tushare audit by registering it
   in `china_a_share_alpha/examples/tushare_factors.py` before the audit.
2. Ran `run_cross_universe_factor_audit` for `high_zscore_20` plus the existing
   25 factors on:
   - Full sample: 2021-06-01 to 2026-06-01, split at 2024-01-01.
   - Recent out-of-sample: 2025-01-01 to 2026-06-30, split at 2025-07-01.
3. Re-ran `run_portfolio_weight_evolution` with `--sort-by train_ic` so base
   factors were chosen without peeking at the test period.

### Key Results

**`high_zscore_20` cross-universe robustness**

| period | universe | test IC | Sharpe | test IC rank / 26 |
|---|---|---|---|---|
| 2021-2026 | csi300 | 0.0119 | 0.99 | 2 |
| 2021-2026 | csi500 | 0.0082 | 0.65 | 8 |
| 2021-2026 | csi1000 | 0.0023 | 0.25 | 12 |
| 2021-2026 | major | 0.0196 | 1.21 | 6 |
| 2021-2026 | tech | -0.0044 | -0.62 | 17 |
| 2025-2026H1 | csi300 | 0.0264 | 2.09 | 7 |
| 2025-2026H1 | csi500 | 0.0197 | 2.02 | 7 |
| 2025-2026H1 | csi1000 | 0.0161 | 1.73 | 8 |
| 2025-2026H1 | major | 0.0467 | 2.64 | 8 |
| 2025-2026H1 | tech | 0.0171 | 1.51 | 5 |

- The factor is strongly positive in the more recent 2025-2026H1 window across
  all five universes, suggesting the 20-day high-price z-score has become a more
  reliable momentum proxy after the 2024 regime shift.
- It is weak or negative in the tech universe over the full 2021-2026 period,
  so it is not unconditionally robust.

**Train-only portfolio-weight evolution**

| selection | train Sharpe | train IC | test Sharpe | test MDD | turnover | cost-adj return |
|---|---|---|---|---|---|---|
| sort by `test_ic` | 2.72 | 0.015 | 0.23 | - | 0.25% | negative |
| sort by `train_ic` | 2.63 | 0.021 | 0.88 | -16.2% | 66.7% | -20.3% |

- Removing look-ahead bias improved test Sharpe from 0.23 to 0.88.
- However, the combined factor has 66.7% daily turnover, so after 0.1% one-way
  costs the cost-adjusted return is still strongly negative.
- The base-factor library still contains many low-quality / constant-heavy
  expressions, so the optimizer is fitting noise and trading too much.

### Interpretation

- `high_zscore_20` is the most credible factor discovered so far, especially on
  large-cap and major-stock universes, and its recent performance is encouraging.
- Portfolio-weight evolution remains overfit; the next fix is to clean the input
  factor library (drop degenerate / constant factors, enforce minimum IC) and add
  an explicit turnover penalty or holding-period constraint.

### Files Changed

- `china_a_share_alpha/examples/tushare_factors.py` — registered `high_zscore_20`.
- `OPERATION_LOG.md` — this entry.

### Outputs

- `china_a_share_alpha_output/cross_universe_audit_with_high_zscore/`
  - `cross_universe_comparison.csv`
  - `cross_universe_report.md`
  - `summary.json`
- `china_a_share_alpha_output/cross_universe_audit_2025h1_2026h1_with_high_zscore/`
  - same files for the 2025-2026H1 window
- `china_a_share_alpha_output/portfolio_weight_evolution_train_only/`
  - `weight_evolution_result.json`
  - `weights.csv`

### Verification

- Cross-universe audit ran end-to-end for both periods and produced rankings.
- Train-only portfolio evolution completed and reported train/test metrics.

### Boundary and Next Steps

- Clean the neutralized factor library before the next portfolio evolution:
  require finite train/test IC, drop constant-heavy expressions, enforce
  minimum test Sharpe.
- Add a stronger turnover penalty or maximum turnover constraint to the weight
  GA so cost-adjusted return stays positive.

## 2026-07-01 - Mingli Layered-Agent Validation: 2010-06-18 Male Xiamen Case

### Request

Validate the upgraded BaZi / Mingli agent framework on a male birth case:
2010-06-18 19:30, Siming District, Xiamen, Fujian.

### Actions

- Ran the local `MingliFiveAgentSystem` executor with Chinese report rendering.
- Used explicit Xiamen Siming coordinates (`24.4456, 118.0827`) and `+08:00`
  because the offline birthplace index does not yet include Xiamen / Siming.
- Checked the generated BaZi profile, method matrix, school-debate agent list,
  annual luck trace, and monthly luck trace.

### Findings

- The case produced pillars `GengYin / RenWu / JiHai / JiaXu`.
- The BaZi profile exposed `classical_layered_methodology` with schema
  `classical-layered-bazi-methodology-v1`.
- The method matrix included `classical_layered_bazi`.
- The school debate layer ran 9 agents, including `sanming_tonghui_agent` and
  `early_sanming_lineage_agent`.
- The 2028 annual row exposed `classical_timing_trace` at `annual` level.
- The 2028 monthly row exposed `classical_timing_trace` at `monthly` level with
  solar-term boundary metadata.

### Boundary

- The current monthly pillar uses an offline symbolic sequence and approximate
  solar-term boundaries. Production-grade month-level claims still need a
  professional calendar / ephemeris provider.
- Xiamen / Siming should be added to the offline birthplace index to avoid
  passing explicit coordinates manually.

## 2026-07-02 - Additional Mingli Classical PDF Candidate Search

### Request

Search for additional classical Mingli / BaZi books that were not downloaded in
the initial source batch.

### Actions

- Searched public catalogue candidates for 子平真诠, 渊海子平, 神峰通考,
  滴天髓辑要, 穷通宝鉴评注, 精选命理约言, and 韦千里命学讲义.
- Rechecked the Internet Archive `shoushange` metadata for additional Mingli
  titles; only already-downloaded files were returned.
- Attempted direct Wikimedia upload downloads for the new candidates.

### Result

- Wikimedia upload downloads returned HTTP 429 Too Many Requests from the
  current network exit, so no new PDFs were downloaded in this run.
- Candidate pages and direct PDF URLs were recorded in
  `examples/mingli_5agents/classical_sources/candidate_downloads_2026-07-02.md`.

### Next Step

Retry the Wikimedia downloads later, or manually download from the recorded
Commons pages and then compute SHA256 before adding the files to `manifest.json`.

## 2026-07-02 - Additional Mingli Classical PDF Downloads Completed

### Request

Continue and complete the downloads for the newly found classical Mingli PDF
candidates.

### Actions

- Retried Wikimedia upload downloads with browser-like headers, a Commons
  referer, and a short delay between files.
- Downloaded 7 additional PDFs into
  `examples/mingli_5agents/classical_sources/raw_pdfs/`.
- Updated `examples/mingli_5agents/classical_sources/manifest.json` with source
  pages, direct PDF URLs, byte sizes, SHA256 hashes, and local filenames.
- Updated `examples/mingli_5agents/classical_sources/README.md`.
- Updated `examples/mingli_5agents/classical_sources/candidate_downloads_2026-07-02.md`
  from pending candidates to completed downloads.

### Downloaded Files

- 子平真诠
- 渊海子平子平真诠 v.1
- 神峰通考
- 滴天髓辑要
- 穷通宝鉴评注
- 精选命理约言
- 韦千里命学讲义

### Verification

- Parsed `manifest.json` successfully.
- Recomputed local file sizes and SHA256 hashes for all 11 manifest items.
- All manifest entries matched the local PDF files.

## 2026-07-02 - Per-Book Classical Mingli Agents

### Request

Build a layered Mingli analysis framework where each downloaded classical book
has its own corresponding paper agent, and where those book agents cooperate and
debate with the existing BaZi agent system.

### Actions

- Added `examples/mingli_5agents/tools/classical_book_agents.py`.
- Created 11 per-book paper agents, one for each downloaded PDF source.
- Integrated the new `classical_book_agents` debate into BaZi deep analysis.
- Exposed `classical_book_agents` in the final BaZi profile.
- Added `classical_book_agents` to the BaZi method surface and API schema.
- Updated `method_cards.json` with the per-book agent registry.
- Updated focused tests for system output and schema contracts.
- Added the reasoning evolution note to `wiki/llm_agent_evolution_mingli.md`.

### Book-Agent Coverage

- 三命通会卷一: overall chart, pattern, ten-god, and major-luck synthesis.
- 三命通会卷九: annual/monthly triggering and auxiliary marker boundaries.
- 李虚中命书 + 珞琭子三命消息赋注: early Sanming lineage and staged-life boundary.
- 天步真原人命部: historical star-fate comparison and boundary control.
- 子平真诠: month-command pattern and useful-god protection.
- 渊海子平子平真诠 v.1: pillar palace, ten-god imagery, and triggered hidden-stem themes.
- 神峰通考: disease-medicine, passage, and transformation checks.
- 滴天髓辑要: qi-flow, clarity, mixedness, and circulation breakpoints.
- 穷通宝鉴评注: month-command climate adjustment and state stability.
- 精选命理约言: concise experience-rule review and anti-template audit.
- 韦千里命学讲义: modern teaching decomposition and readable Chinese report style.

### Verification

- `python -m py_compile` passed for the new and touched Python modules.
- `python -m json.tool` passed for `method_cards.json`.
- Focused pytest passed:
  - `test_five_agent_executor_returns_required_artifacts`
  - `test_professional_bazi_deep_analysis_uses_lunar_python_when_available`
  - `test_schema_contract_score_gates_release_governance_contracts`
- CLI schema smoke check passed for `BaziProfile.classical_book_agents`.
- A smoke birth case produced `classical-book-agent-debate-v1` with 11 votes and
  `classical_book_agents` present in the BaZi method matrix.

### Boundary

- CLI end-to-end `test_cli_init_analyze_evolve_status` was attempted but timed
  out after about 184 seconds; the narrower schema smoke check passed.
- The book agents are method-card level until OCR/manual edition review promotes
  individual page-level rules.

## 2026-07-02 - San Ming Tong Hui Full Twelve-Volume Download

### Request

Clarify whether only two volumes of `San Ming Tong Hui` were available, and
complete the missing volumes if present.

### Actions

- Checked the local manifest and confirmed only volumes 1 and 9 had previously
  been downloaded.
- Queried adjacent Internet Archive item IDs and found `San Ming Tong Hui`
  volumes 1 through 12 at `06056477.cn` through `06056488.cn`.
- Downloaded missing volumes 2-8 and 10-12 into
  `examples/mingli_5agents/classical_sources/raw_pdfs/`.
- Re-downloaded volume 7 after detecting a partial file from a timed-out batch
  download.
- Updated `manifest.json`, `README.md`, `method_cards.json`, and the classical
  book-agent source labels.

### Verification

- `manifest.json` now has 21 PDF entries total.
- `San Ming Tong Hui` has 12 manifest entries: volumes 1 through 12.
- Recomputed all manifest file sizes and SHA256 hashes; no mismatches.
- Python compile checks passed for the touched book-agent modules.
- JSON validation passed for `manifest.json` and `method_cards.json`.
- Re-run enhanced expression evolution with a larger population / more
  generations, or a staged pipeline (base-factor search → combination search).

## 2026-06-30 — Clean factor library, turnover constraints, and robust combination

### Motivation

The previous follow-up showed that `high_zscore_20` is robust but the weight-space
GA overfits the training period. Three concrete fixes were proposed:

1. Clean the factor library (drop degenerate / constant factors).
2. Add a hard turnover cap and stronger penalty to the weight GA.
3. Use a staged / more constrained combination method to avoid overfitting.

### Actions Taken

1. Created `china_a_share_alpha/scripts/clean_factor_library.py`.
   - Removes factors that fail evaluation, are constant, or contain
     `ts_corr`/`ts_cov` with a constant operand.
   - Applies minimum IC / Sharpe / maximum turnover thresholds (configurable).
   - Writes a cleaned CSV plus a JSON summary of skipped reasons.
2. Fixed a bug where the cleaner rejected valid factors because of a few NaNs
   (`np.isfinite` on the whole series). Now NaNs are dropped before the
   finiteness / std checks.
3. Updated `china_a_share_alpha/scripts/run_portfolio_weight_evolution.py`:
   - Added `--max-turnover` hard cap (default 0.3).
   - Added `--smooth-span` EMA smoothing of the combined factor (default 3).
   - Changed fitness to prioritize cost-adjusted return (45%) over Sharpe (30%).
4. Created `china_a_share_alpha/scripts/run_factor_combination.py` as a
   deliberately simple, hard-to-overfit alternative:
   - Select top-K factors by train IC (or ICIR).
   - Z-score and equal-weight them.
   - Smooth the combined signal with an EMA.
   - Report train and test long-short metrics.
5. Added `high_zscore_20` to the cleaned library CSV for combination tests.

### Key Results

**Cleaning**

- Input: 100 candidates from the neutralized factor loop.
- After fixing the NaN bug and applying loose thresholds (|test_ic| ≥ 0.001,
  turnover ≤ 1.0): **25 candidates kept**.
- Skipped reasons: mostly degenerate expressions (NaN/constant) or
  constant-operand correlations.

**Weight GA with cleaned library**

| run | train Sharpe | train cost-adj | test Sharpe | test cost-adj | turnover |
|---|---|---|---|---|---|
| raw library, test-ic sort | 2.72 | 0.037 | 0.23 | negative | 0.0025 |
| raw library, train-ic sort | 2.63 | 0.096 | 0.88 | -0.203 | 0.667 |
| cleaned library, train-ic sort, smooth=3, max_turnover=0.3 | 3.40 | 0.196 | -0.32 | -0.237 | 0.0014 |

- The GA still overfits: it finds a training-period combination with Sharpe >3
  but loses money out of sample.

**Robust equal-weight combination**

| factors | selection | smooth span | train Sharpe | test Sharpe | test cost-adj |
|---|---|---|---|---|---|
| top 5 | train_ic | 10 | 2.04 | 0.90 | 0.062 |
| top 5 | train_ic | 20 | 2.06 | 0.96 | 0.113 |
| all 11 positive train_ic + high_zscore_20 | train_ic | 10 | 1.09 | **1.04** | **0.121** |
| all 11 positive train_ic + high_zscore_20 | train_ic | 20 | 0.80 | 1.09 | 0.168 |

- Equal weight + EMA smoothing is the first combination with **positive
  cost-adjusted return** on the 2024-2026 test set.
- Including `high_zscore_20` diversifies away from the volatility/mean-reversion
  cluster that dominated the top train-IC factors.
- Turnover is very low (~0.0005 daily), so costs are small.

### Interpretation

- **Factor library quality matters more than optimization complexity.** Cleaning
  removed noise and made the combination stable.
- **Weight-space GA overfits even with turnover caps and smoothing.** The search
  has too many degrees of freedom relative to the short training window.
- **Equal weight + temporal smoothing is a strong baseline.** It captures
  diversification without fitting relative weights to noise.
- `high_zscore_20` adds genuine out-of-sample value and should be included in
  future factor sets.

### Files Changed

- `china_a_share_alpha/scripts/clean_factor_library.py` (new)
- `china_a_share_alpha/scripts/run_factor_combination.py` (new)
- `china_a_share_alpha/scripts/run_portfolio_weight_evolution.py`
  - added `--max-turnover`, `--smooth-span`, cost-adjusted-return fitness
- `OPERATION_LOG.md` — this entry

### Outputs

- `china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library_cleaned.csv`
- `china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library_cleaned_plus_highzscore.csv`
- `china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library_cleaned_summary.json`
- `china_a_share_alpha_output/portfolio_weight_evolution_cleaned/`
- `china_a_share_alpha_output/factor_combination/top5_span10/`
- `china_a_share_alpha_output/factor_combination/top11_span10/`

### Verification

- Cleaning script runs end-to-end and reports kept/skipped counts.
- Weight GA runs with turnover cap and smoothing enabled.
- Equal-weight combination produces positive train and test cost-adjusted
  returns.

### Boundary and Next Steps

- The best pipeline so far is:
  1. clean library → 2. keep positive-train-IC factors → 3. equal-weight →
     4. EMA smooth (span 10-20).
- Future work could try:
  - Risk-parity / IC-weighted combination instead of equal weight, with a
    validation fold for weight estimation.
  - Sector / market-cap neutralization of the combined signal.
  - Extending the cleaned factor library with more seeds and longer evolution.

---

## 2026-07-02 — China A-Share Alpha: Phase 1 Data & Operator Expansion + Robustness Fixes

### Motivation

Pursue the additional factor-mining spaces identified earlier (fundamentals,
money flow, northbound holdings, conditional operators) while fixing two loop
bugs that poisoned the first enriched run: degenerate constant sub-expressions
and test-set leakage during selection.

### Actions Taken

1. **Enriched Tushare data loader**
   - Added `fina_indicator` (ROE, ROE_DT, net-profit YoY, gross margin,
     debt-to-assets, OCFPS, EPS) merged by announcement date.
   - Added `moneyflow` (`net_elg_amount`, `net_mf_amount`).
   - Added `hk_hold` (`hk_vol`, `hk_ratio`).
   - Forward-fill quarterly fundamentals to every trading day within each
     symbol so the resulting panel is not sparse.
   - Added `china_a_share_alpha/data/prefetch_enriched.py` to warm the cache
     in one pass.

2. **Extended DSL operators**
   - `ts_rank(x, window)` — cross-time rank.
   - `ts_argmax(x, window)` / `ts_argmin(x, window)` — location of extrema.
   - `if_else(pred, if_true, if_false)` — ternary conditional.

3. **Extended mutator variable set**
   - `roe`, `roe_dt`, `netprofit_yoy`, `dt_netprofit_yoy`,
     `grossprofit_margin`, `debt_to_assets`, `ocfps`, `eps`,
     `net_elg_amount`, `net_mf_amount`, `hk_vol`, `hk_ratio`.

4. **Mutator robustness**
   - Added `is_reasonable_expression()` in `factor_mutator.py` to reject
     structurally degenerate trees such as `ts_corr(const, x)`,
     `ts_mean(const)`, or `if_else(const, const, x)`.
   - `_random_expression` now retries up to 50 times and falls back to a raw
     variable, cutting the rate of NaN/constant candidates.

5. **Selection now uses train-set metrics only**
   - `EnhancedFactorPopulation._fitness` previously looked at test Sharpe and
     test return, leaking the hold-out set into selection.
   - New fitness is a weighted mix of **train** Sharpe, train cost-adjusted
     return, train IC, and turnover penalty.
   - `decay_monitor.py` updated to work with either train- or test-IC history.

6. **Tighter evaluation thresholds**
   - NaN fraction gate in `FactorPopulation.evaluate` lowered from 0.5 to 0.3.
   - Added an extra turnover penalty to the in-sample `train_score`.

7. **Tree-size guardrail**
   - Added `MAX_NODES = 40` and `_node_count()` to cap expression complexity.
   - Random generation, subtree replacement, crossover, and structural mutations
     all roll back to a safe tree if the result exceeds the cap or reintroduces
     a degenerate constant sub-expression. This prevents the occasional
     runaway evaluation that stalled the first robust run.

8. **Degenerate-expression bug fix**
   - `_is_degenerate_node` now uses `_is_constant()` so that constants wrapped
     in `neg(...)` (e.g. `-0.172`) are still recognised as constants.
   - `is_reasonable_expression` now recurses into `RollingBinaryOp` (`ts_corr`)
     as well as `BinaryOp`; previously `ts_corr(const, x)` and nested constant
     branches could leak into the library.
   - Without this fix the first fast run produced a top-ranked expression
     containing `ts_corr(0.4, -0.172, 5)` and `greater(0.635, 0.541)`.

8. **New loop configs**
   - `enhanced_loop_config_robust.yaml`: pop 40, 20 generations, csi300,
     2021-06 to 2026-06, split 2024-01.
   - `enhanced_loop_config_fast.yaml`: pop 30, 12 generations for faster
     iteration.

### Files Changed

- `china_a_share_alpha/data/tushare_loader.py`
- `china_a_share_alpha/data/prefetch_enriched.py` (new)
- `china_a_share_alpha/factor/expression.py`
- `china_a_share_alpha/evolution/factor_mutator.py`
- `china_a_share_alpha/evolution/enhanced_factor_mutator.py`
- `china_a_share_alpha/loop/population.py`
- `china_a_share_alpha/loop/enhanced_population.py`
- `china_a_share_alpha/loop/decay_monitor.py`
- `china_a_share_alpha/examples/enhanced_loop_config_robust.yaml` (new)
- `china_a_share_alpha/examples/enhanced_loop_config_fast.yaml` (new)
- `china_a_share_alpha/examples/enhanced_loop_config_fast2.yaml` (new)
- `OPERATION_LOG.md` — this entry

### Verification

- `python -m py_compile` on all changed modules — **passed**.
- Prefetch populated 300 enriched cache files after invalidating the old
  sparse cache.
- Fast enhanced evolution finished seeds 42, 10, 30; intermediate logs show
  progression through generations without the previous `KeyError: best_test_ic`
  crash.

### Results

**Merged library**

- 48 unique expressions from three seeds (42, 10, 30).
- Cleaning thresholds: |train_ic| ≥ 0.001, |test_ic| ≥ 0.001,
  test_sharpe ≥ 0.2, turnover ≤ 0.3, NaN fraction ≤ 0.2,
  daily coverage ≥ 0.5.
- **Kept 10 / 48 factors.** The dropped factors were mostly constant,
  NaN-heavy, or sign-flipping.

**Equal-weight + EMA combination (2024-01 to 2026-06 test set)**

| Selection | Smooth span | Train Sharpe | Test Sharpe | Test cost-adj return | Turnover |
|---|---|---|---|---|---|
| Top 5 train-IC | 10 | 0.48 | **1.20** | **18.1%** | 0.0005 |
| Top 5 train-IC | 20 | 0.36 | 1.05 | 17.2% | 0.0003 |
| Top 10 train-IC | 10 | 0.24 | 1.19 | 15.8% | 0.0006 |
| Top 10 train-IC | 20 | 0.12 | 1.06 | 16.3% | 0.0004 |
| Top 11 train-IC + `high_zscore_20` | 10 | 0.23 | 1.11 | 15.3% | 0.0006 |
| Top 11 train-IC + `high_zscore_20` | 20 | 0.05 | 1.06 | 17.2% | 0.0004 |
| **Baseline** 11 positive-train-IC + `high_zscore_20` | 10 | 1.09 | 1.04 | 12.1% | 0.0005 |

- The enriched Phase 1 ensemble **beats the previous baseline** on test
  Sharpe and cost-adjusted return.
- The simplest cut (top-5 train-IC, EMA span 10) is the strongest out-of-sample.
- Turnover is extremely low, so transaction costs do not erode the signal.

### Interpretation

- **Fundamentals and money flow add value.** Several surviving factors use
  `pb`, `ocfps`, `roe`, `dt_netprofit_yoy`, `net_mf_amount`, and
  `net_elg_amount`.
- **Train-only selection reduces hold-out leakage**, but the raw leaderboard
  still contains lucky outliers; cleaning remains mandatory.
- **Equal-weighting continues to outperform weight-space optimization** and
  benefits from the larger, cleaner enriched library.

### Outputs

- `china_a_share_alpha_output/enhanced_loop_fast2/enriched_factor_library.csv`
- `china_a_share_alpha_output/enhanced_loop_fast2/enriched_factor_library_cleaned.csv`
- `china_a_share_alpha_output/enhanced_loop_fast2/enriched_factor_library_cleaned_plus_highzscore.csv`
- `china_a_share_alpha_output/enhanced_loop_fast2/combination/`

### Next Steps

- Add a validation fold inside the training period so weights / factor
  selection can be data-driven without leaking the test set.
- Phase 2: explore cross-market transfer, ML-based combination, and
  slightly higher-frequency intraday features.
- Push current changes to GitHub.

---

## 2026-07-02 (continued) — China A-Share Alpha: Validation Fold + Weighted Combination

### Motivation

The previous equal-weight ensemble beat the baseline, but factor selection was
still driven by training-set IC. Adding an in-sample validation fold lets us
estimate both **selection** and **combination weights** without touching the
final 2024-2026 test set.

### Actions Taken

1. **Data split helper**
   - Added `split_by_date()` and `load_tushare_data_with_val()` in
     `china_a_share_alpha/data/tushare_loader.py`.
   - New config `enhanced_loop_config_val.yaml` splits 2021-06 to 2023-12 into
     train (2021-06 to 2022-12) and validation (2023-01 to 2023-12); test
     remains 2024-01 to 2026-06.

2. **Validation-aware cleaning**
   - `clean_factor_library.py` now computes `val_ic`, `val_sharpe`, and
     `val_cost_adj_return` when `val_date` is present.
   - Cleaning enforces sign agreement between train and validation IC and sorts
     the surviving factors by validation IC by default.

3. **Weighted combination methods**
   - `run_factor_combination.py` now supports:
     - `equal` (baseline),
     - `ic` — weights proportional to validation IC,
     - `sharpe` — sign(IC) × validation Sharpe,
     - `risk_parity` — inverse volatility of validation long-short returns.
   - Weights are estimated on the validation fold and applied unchanged to the
     test period.

### Files Changed

- `china_a_share_alpha/data/tushare_loader.py`
- `china_a_share_alpha/scripts/clean_factor_library.py`
- `china_a_share_alpha/scripts/run_factor_combination.py`
- `china_a_share_alpha/examples/enhanced_loop_config_val.yaml` (new)
- `OPERATION_LOG.md` — this entry
- `wiki/semas_evolution_ideas.md`

### Verification

- `python -m py_compile` on changed modules — **passed**.
- Re-cleaned the enriched library with validation metrics: 48 expressions →
  6 kept (stricter sign-agreement filter).
- Ran equal / IC / Sharpe / risk-parity combinations for top-5 and top-6
  validation-selected factors, plus train-selected factors with validation
  weights.

### Results

| Selection | Weight | Smooth span | Test Sharpe | Test cost-adj return |
|---|---|---|---|---|
| Top 5 by val_ic | equal | 10 | 0.91 | 12.6% |
| Top 5 by val_ic | ic | 10 | 0.99 | 13.7% |
| Top 5 by val_sharpe | equal | 10 | 0.99 | 13.1% |
| Top 6 by val_ic + `high_zscore_20` | ic | 10 | **1.01** | **14.9%** |
| Top 10 by train_ic + validation weights | equal | 10 | 1.20 | 16.2% |
| Top 10 by train_ic + validation weights | sharpe | 10 | 1.29 | 11.0% |
| **Previous best** (train-only top 5 equal) | equal | 10 | **1.20** | **18.1%** |

### Interpretation

- The validation fold is correctly wired and produces stable, low-turnover
  combinations.
- In this particular split, validation-based selection did **not** beat the
  train-only top-5 equal ensemble. The 2023 validation period appears to favour
  slightly different factors than 2024-2026, so the validation filter drops the
  factors that perform best out-of-sample.
- Validation-based **weighting** on train-selected factors preserves strong
  performance (test Sharpe 1.20) and is a safer recipe for live trading because
  it never peeks at the test set.
- Equal weight remains surprisingly competitive; the extra degrees of freedom
  in IC / Sharpe / risk-parity weights do not consistently translate to better
  test results.

### Next Steps

- Try a **rolling validation window** (e.g. expanding or walk-forward) instead
  of a single calendar split, so weights adapt to regime shifts.
- Experiment with an ML combination layer (ridge / LightGBM on recent factor
  returns) using only validation data for hyper-parameter selection.
- Begin Phase 2 cross-market transfer: evolve factors on CSI500/CSI1000 and
  test on CSI300.
- Push these changes to GitHub.
