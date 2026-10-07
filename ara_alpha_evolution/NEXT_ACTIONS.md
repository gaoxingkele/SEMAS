# RSI / Stage Next Actions

## Done (2026-09-18)

- [x] Roll back Relative Strength Index mistake → iter 49 / hold 2.056
- [x] DGM-style policy archive RSI (`loop/recursive_self_improve.py`)
- [x] Propose `policy_0001` + start inner iter 50

## Next

1. When iter 50 finishes:
   `py -3 -m china_a_share_alpha.loop.recursive_self_improve --record-fitness policy_0001`
2. Propose next child and continue outer/inner alternating rounds
3. Multi-seed Stage-2 ablations remain orthogonal paper work
