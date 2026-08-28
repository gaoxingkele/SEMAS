# Resume factor evolution on a frozen snapshot

The legacy Tushare loop is not reproducible when credentials expire, even if
the per-symbol cache is present: it still asks the service for the index
constituents before reading the cache. A frozen train/validation/test panel is
therefore a better execution substrate for resumed research.

The resumed iteration reads the checksum-described 2026-07-17 snapshot rather
than making a live provider call. Candidate generation continues from the
existing live-library seed. The initial resume used `promotion_enabled: false`
to protect the audited baseline; on 2026-07-19 the user explicitly enabled
automatic promotion for subsequent runs, subject to the existing hard gates.

This keeps three concerns distinct: candidate exploration can continue, the
evaluator input is reproducible, and promotion remains constrained by the
configured quality gates.

[source: wiki/factor_horizon_no_lookahead_audit_20260716.md]
[source: china_a_share_alpha_output/tushare_snapshot_20260717/manifest.json]
