# Frozen candidates need a second axis of independence

An out-of-sample time split does not establish cross-sectional generalization
when the same securities appear throughout discovery and evaluation. A useful
additional gate is a stock-disjoint audit: freeze candidates before observing
the new universe, remove all original symbols, and score the entire frozen set
without further candidate selection. [source: local external-validation design]

For the 5D/10D campaign, historical CSI500 membership must be treated as a
time-indexed universe. Replacing it with today's CSI500 constituents produces
survivorship bias. Membership is therefore applied using the most recent
historical constituent record as of each trading date. [source: https://tushare.pro/document/2?doc_id=96]

The first external audit used a deterministic 30-stock sample from the unused
CSI500 union (seed `20260721`). It evaluated all 178 frozen candidates, rather
than only the ex-post external winners. Three candidates remained positive and
had Sharpe >= 1.5 in the full, 2025, and 2026 partitions, but their maximum
drawdowns remain too large for deployment. The outcome is evidence of a
research lead, not an automatic promotion decision. [source: local artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/metadata.json]
