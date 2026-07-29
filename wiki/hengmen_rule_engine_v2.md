---
date: 2026-07-13
tags: [mingli, hengmen, bazi, rule-engine, ahp, falsification]
sources:
  - "tools/格局横门断.docx"
  - "C:/Users/xmupt/.codex/skills/mingli-bazi-hengmen/references/hengmen_meta_graph.md"
related: [mingli_book_profiles_hour_calibration.md, think/hengmen_rule_engine_v2.md]
---

# Hengmen Rule Engine V2

The Hengmen implementation now separates concrete pattern candidates from
event-fit scoring. A candidate records its month-command stem, visibility,
roots, supporting conditions, failure conditions, rescue conditions, and
affection or damage from branch relations. [source: `tools/格局横门断.docx`]

Annual activation and monthly activation are distinct. Missing event months are
neutral rather than optimized retrospectively. Counterexample years require
their own annual rows; otherwise the engine reports missing evidence instead of
inventing a penalty. [source: `hengmen_meta_graph.md`]

The extension records the four storage branches with their full hidden-stem
sets, treats a storage month command as requiring exposure review, and records
storage clash as bounded timing activation. Head/foot support is incorporated
only in the existing stem-root dimension. Combination direction and partial
trines are labelled candidate-only or needs-corroboration, so they cannot
independently create an event explanation. [source: `tools/格局横门断.docx`]

The candidate generator now distinguishes a Yang Blade month command for Yang
day masters from a generic peer/Jianlu-Yuejie candidate. Each response carries
a coverage receipt for the source rule families; a family absent from a chart is
therefore not confused with an unimplemented rule. [source: `tools/格局横门断.docx`]

The AHP timing receipt separates major-luck support from annual activation and
monthly confirmation. Its annual/monthly dimension is annual-primary, with an
unverified month held neutral; this prevents a named flow-month field from
silently becoming a replacement for annual evidence. [source: `tools/格局横门断.docx`]

Full-text review also corrected the peer-family boundary: a Jianlu/Yuejie
candidate needs external officer, wealth, or expression undertaking, rather
than treating the day master itself as a peer failure. A Yang Blade candidate
records authority control, companion conditions, and damage to that control
separately. [source: `tools/格局横门断.docx`]

Candidate conditions now retain three source-specific distinctions: wealth
prefers food-god generation over hurting-officer generation; food generating
wealth while exposing killing is a failure condition; and food may clear a
mixed authority candidate by controlling the killing side. [source:
`tools/格局横门断.docx`]

Palace-trigger evidence now records target pillars and relation type. Severe
relations score highest for disruptive event themes, while combinations receive
their stronger interpretation only for non-disruptive themes. [source:
`tools/格局横门断.docx`]

Major luck is now evaluated from its stem and branch-hidden-stem roles against
the selected pattern's support and adverse sets. An active period alone is not
evidence of stage support. [source: `tools/格局横门断.docx`]

Combination affection is directed to the candidate stem's root branches. A
partner may bring same/generating elements, controlling elements, or mixed
evidence; only the first two have bounded score effects. Disruptions outside a
candidate's root branches are retained as natal facts but do not damage that
candidate's affection score. [source: `tools/格局横门断.docx`]

Virtual invitation records the count of matching partial-trine branch pairs.
Repeated pairs receive stronger, but still non-decisive, evidence status; no
virtual structure may create a pattern candidate unless exposure or independent
corroboration is available. [source: `tools/格局横门断.docx`]

The independent method layers are exported as named receipts: month-command
pattern, success/failure/rescue, branch affection, structural evidence,
event-ten-god mapping, palace trigger, annual/monthly timing, and
falsification. AHP consumers can therefore audit each vote against its own
inputs rather than reading only an aggregate score. [source:
`tools/格局横门断.docx`]

The AHP output includes its eight criteria, normalized priorities, and a
reciprocal pairwise matrix derived from those source-method priorities. This is
explicitly separate from the current candidate event set and is exactly
consistent by construction. [source: `tools/格局横门断.docx`]

The output carries a rule catalog that separates executable symbolic rules from
partial areas needing fuller textual case context and outcome claims requiring
human factual review. This is a coverage receipt, not a claim that event
outcomes have been validated. [source: `tools/格局横门断.docx`]

Visible stem order is now retained as candidate evidence. In a hurting-officer
candidate with finance and resource visibly separated, the receipt remains
needs-corroboration rather than asserting that finance and resource are
non-interfering. [source: `tools/格局横门断.docx`]

Counterexample penalties now require annual evidence keyed to every declared
non-event year. A row-count match is insufficient; malformed or missing years
leave the falsification layer neutral. [source: `tools/格局横门断.docx`]

Monthly timing resolves explicit months and ISO dates independently. If they
conflict, the monthly layer remains neutral with a conflict receipt instead of
choosing one calendar convention. [source: `tools/格局横门断.docx`]

Event-topic evidence normalizes equivalent theme vocabulary on both sides of
the AHP comparison, so peer/friends labels cannot suppress a valid topic match.
[source: `tools/格局横门断.docx`]

Fact calibration now combines source traceability with the counterexample
receipt, exposing both components rather than letting a neutral or missing
counterexample field stand in for event quality. [source:
`tools/格局横门断.docx`]

Candidate selection now includes the leading margin, runner-up, and confidence
class. Close candidates are marked ambiguous and receive only a bounded
month-pattern AHP discount; the selected label does not conceal that ambiguity.
[source: `tools/格局横门断.docx`]

## Related pages

- [Mingli Book Profiles and Hour Calibration](mingli_book_profiles_hour_calibration.md)
- [Thinking Note](think/hengmen_rule_engine_v2.md)
