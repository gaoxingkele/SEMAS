# Mingli Classical Source Downloads

This directory stores local public-source classical astrology and BaZi materials
used for citation-backed method research. Raw scans are kept under `raw_pdfs/`.

Current download batch: 2026-06-30.

Source policy:

- Prefer public libraries, Internet Archive, Wikisource, Wikimedia Commons, or
  other open catalogue sources.
- Keep every downloaded file tied to a source URL, size, and SHA256 hash.
- Treat scans as research sources. Do not treat OCR or later commentaries as
  automatically authoritative without edition review.
- Before redistributing any file outside this workspace, re-check the hosting
  source's rights statement and local legal requirements.

Downloaded works:

- 三命通会，卷一至卷十二
- 李虚中命书、珞琭子三命消息赋注，守山阁丛书本
- 天步真原人命部，守山阁丛书本
- 子平真诠
- 渊海子平子平真诠 v.1
- 神峰通考
- 滴天髓辑要
- 穷通宝鉴评注
- 精选命理约言
- 韦千里命学讲义

Additional download batch: 2026-07-02.

- The Wikimedia / NLC candidates previously blocked by HTTP 429 were retried
  with browser-like headers and delay, then downloaded successfully.
- New files are recorded in `manifest.json` with source URLs, direct PDF URLs,
  byte sizes, and SHA256 hashes.

See `manifest.json` for exact URLs and hashes.

## Agent Integration Status

Current integration batch: 2026-06-30.

- `method_cards.json` records the absorbed methodology in a portable form.
- Embedded PDF text is not reliable enough for page-level quotation, so the
  current agent rules use paraphrased, source-governed method cards pending OCR
  or manual edition review.
- The BaZi profile now exposes `classical_layered_methodology` for the five
  layers: natal chart, major luck, annual trigger, monthly implementation, and
  fact calibration.
- Annual and monthly luck evidence now exposes `classical_timing_trace`, linking
  each prediction back to natal chart, luck cycle, and current pillar layers.
- The school debate layer now includes `sanming_tonghui_agent` and
  `early_sanming_lineage_agent` so classical synthesis and early Sanming lineage
  can debate with the existing Ziping, Hengmen, blind-school, and evidence agents.

Additional integration batch: 2026-07-02.

- Every downloaded PDF source now has a corresponding sub-agent in
  `examples/mingli_5agents/tools/classical_book_agents.py`.
- The BaZi profile now exposes `classical_book_agents`, a separate debate layer
  with 11 votes, layer mapping, conflicts, and consensus.
- The book-agent layer is source-book oriented, while the older school-debate
  layer is method-school oriented. Both are intended to cooperate and challenge
  each other before final synthesis.
- San Ming Tong Hui now has 12 volume-level sub-agents under the full-corpus
  parent agents; these sub-agents are source-level active units pending OCR or
  manual edition review before page-level rule promotion.

Additional integration batch: 2026-07-04.

- The wording has been normalized to "子智能体"; the earlier mistyped wording
  should not appear in generated artifacts.
- Every book-level sub-agent now exposes its own
  `book-layered-analysis-architecture-v1` structure before joining the group
  debate.
- Each book architecture maps its primary layers into active layer sub-agents,
  with a functional module, evidence fields, method rule, output contract, and
  calibration role.
- Current runtime counts: 11 book-level sub-agents, 12 San Ming Tong Hui
  volume-level source sub-agents, and 33 book-internal layer sub-agents.
- This is still method-card-level structuring. Page-level textual rules require
  later OCR or manual collation before they can be promoted into quotable rules.
