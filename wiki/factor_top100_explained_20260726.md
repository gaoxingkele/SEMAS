# TOP100 因子快照及结构说明（2026-07-09）

以下为当前 60 日无前视滚动 Sharpe 排名的 TOP100 快照。说明仅解释表达式使用的数据与算子结构，不构成经济因果、交易可行性或未来收益承诺。实际再入仍需满足因子自身冷却期。

[source: local artifact china_a_share_alpha_output/external_unused_csi500_2025_2026/ranked_reentry_top100/top100_latest_20260709.csv]

| 排名 | 因子 ID | 周期 | 60日 Sharpe | 大致说明 | 表达式 |
|---:|---|---:|---:|---|---|
| 1 | `50320a738dbe371b` | 10D | 11.561 | 以布林下轨为输入，经滚动偏度、线性衰减加权、时间变化形成的复合信号。 | `ts_delta(ts_decay_linear(ts_skew(ts_skew(bband_lower, 60), 20), 20), 20)` |
| 2 | `a9a0e79c9dd76f10` | 5D | 10.286 | 以Williams %R为输入，经滚动峰度、时间变化、滚动累计形成的复合信号。 | `ts_sum(ts_kurt(sign(ts_delta(willr_14, 10)), 10), 60)` |
| 3 | `422b2e5d8ec27a4c` | 10D | 8.238 | 以换手率为输入，经截面去极值形成的复合信号。 | `winsorize(turnover_rate)` |
| 4 | `19896b6587b731f2` | 10D | 8.238 | 以换手率为输入，经加减乘除/条件组合形成的复合信号。 | `turnover_rate` |
| 5 | `b537e1ad089acbff` | 10D | 7.580 | 以换手率、每股收益为输入，经滚动偏度、时间变化、滚动极值、条件筛选形成的复合信号。 | `if_else(ts_delta(ts_max(eps, 60), 3), mul(sign(ts_ema(ts_skew(ts_skew(turnover_rate, 5), 20), 60)), 1.044), turnover_rate)` |
| 6 | `1e81291869e6bb46` | 5D | 7.429 | 以换手率、总市值、每股经营现金流、每股收益为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(eps, winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 7 | `aa63407727da9afa` | 10D | 7.281 | 以换手率为输入，经滚动中位数、截面去极值形成的复合信号。 | `ts_median(winsorize(turnover_rate), 20)` |
| 8 | `d035f4cbd49f8fc7` | 5D | 6.917 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(turnover_rate, sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 9 | `8dd63aa98c9b5ba2` | 5D | 6.871 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, total_mv), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 10 | `60de020d2f0af4d0` | 5D | 6.865 | 以换手率、总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(adx_14, turnover_rate)), winsorize(total_mv)))` |
| 11 | `afb8e3976d78ac66` | 5D | 6.865 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(ocfps, sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 12 | `9da0d53834bf45b9` | 5D | 6.865 | 以换手率、总市值为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(turnover_rate, winsorize(total_mv)))` |
| 13 | `4ebff5353b49df3b` | 5D | 6.865 | 以换手率、总市值为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(turnover_rate, winsorize(total_mv)), winsorize(total_mv)))` |
| 14 | `a43f3adc5a63932f` | 5D | 6.790 | 以换手率、总市值、每股经营现金流、每股收益为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 15 | `6fad684a410b7401` | 5D | 6.790 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 16 | `ba6753d49febe12f` | 5D | 6.756 | 以换手率、总市值、每股经营现金流、每股收益为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, turnover_rate), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 17 | `adcba1052aff192b` | 5D | 6.655 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, turnover_rate)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 18 | `f86ce5aeee315cb1` | 5D | 6.632 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(adx_14, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 19 | `27354323fe0db9b4` | 5D | 6.632 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(ocfps, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 20 | `18350bbb179f5185` | 5D | 6.554 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 21 | `477c1b272f10c3c8` | 5D | 6.550 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 22 | `a2059e61d8fc5ecb` | 5D | 6.464 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(cs_zscore(div(sub(adx_14, cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv)))), winsorize(total_mv))), sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 23 | `9e5c3004d210d194` | 5D | 6.457 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(adx_14))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 24 | `893fbaa536c3cf0b` | 5D | 6.455 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 25 | `27131724a1e342bd` | 5D | 6.455 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, winsorize(total_mv)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 26 | `5a3f3e8dd4baad9c` | 5D | 6.455 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv)))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 27 | `c595107e154efecc` | 5D | 6.454 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), winsorize(total_mv)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 28 | `ccae1e575692de59` | 5D | 6.447 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)), turnover_rate)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 29 | `8a236da64a7b509b` | 5D | 6.445 | 以换手率、总市值、每股经营现金流、成交量为输入，经滚动熵/离散度、截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(mul(sign(ts_entropy(volume, 60)), 2.314), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 30 | `25a8cdfb6346910c` | 5D | 6.445 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)), turnover_rate)), winsorize(total_mv)))` |
| 31 | `aeb4938fb1467511` | 5D | 6.438 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(adx_14)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 32 | `93783c0cc57b7e10` | 5D | 6.438 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(sub(adx_14, sub(ocfps, turnover_rate)))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 33 | `9b98a8bf6978e917` | 5D | 6.438 | 以换手率、总市值、每股经营现金流、每股收益为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 34 | `7dc0b2fed797dc39` | 5D | 6.431 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(sub(ocfps, turnover_rate), winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 35 | `66a2381fb33fa28c` | 5D | 6.390 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(total_mv))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 36 | `0b7233ec0816716f` | 5D | 6.326 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 37 | `d28a655cd35d57b9` | 5D | 6.326 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(winsorize(total_mv), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 38 | `4191319a53a71660` | 5D | 6.326 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(winsorize(total_mv), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 39 | `54d8ab630d69e012` | 5D | 6.326 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, adx_14), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 40 | `54d4d2460fa13116` | 5D | 6.326 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, sub(adx_14, sub(ocfps, turnover_rate))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 41 | `34b0050c23fc9cb2` | 5D | 6.302 | 以换手率、每股经营现金流、ADX趋势强度为输入，经截面标准化、相对值构造形成的复合信号。 | `cs_zscore(div(sub(sub(adx_14, sub(ocfps, turnover_rate)), sub(ocfps, turnover_rate)), sub(adx_14, sub(ocfps, turnover_rate))))` |
| 42 | `b39811cf288268a3` | 5D | 6.236 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(total_mv), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 43 | `94c8808414db8b63` | 5D | 6.159 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 44 | `7685ddf78f7fe0fc` | 5D | 6.045 | 以主力净资金流、换手率、总市值、流通市值等为输入，经滚动相关性、滚动均值、截面标准化、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, neg(mul(add(mul(sign(ts_mean(ts_corr(grossprofit_margin, circ_mv, 5), 10)), 0.552), net_mf_amount), 1.437))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 45 | `f07f5afc328983c8` | 5D | 6.033 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 46 | `1ab6c97b77dd98a1` | 5D | 6.023 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(turnover_rate, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 47 | `ab191057a07ae462` | 5D | 5.989 | 以换手率、总市值、每股经营现金流、每股收益等为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(greater(eps, cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 48 | `407a71dc45b53baa` | 5D | 5.798 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(winsorize(total_mv), turnover_rate)), winsorize(total_mv)))` |
| 49 | `574af384cf06deb8` | 5D | 5.541 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(ocfps))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 50 | `6a01c51afa35a871` | 5D | 5.313 | 以换手率、总市值、每股经营现金流为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(total_mv, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 51 | `d1878578cc7b02f8` | 5D | 4.930 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(sub(adx_14, sub(ocfps, winsorize(ocfps)))))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 52 | `91e7de907e978488` | 5D | 4.805 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate))), winsorize(total_mv)), winsorize(total_mv)))` |
| 53 | `270e21fca2aaf4eb` | 5D | 4.648 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(adx_14))), winsorize(total_mv))), sub(ocfps, turnover_rate)))` |
| 54 | `0a8edac33ebf5131` | 5D | 4.065 | 以小单卖出额、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(sell_sm_amount))), winsorize(total_mv))), winsorize(total_mv)), winsorize(total_mv)))` |
| 55 | `fba63101c4038813` | 5D | 3.529 | 以小单卖出额为输入，经滚动熵/离散度形成的复合信号。 | `ts_entropy(ts_entropy(sell_sm_amount, 20), 20)` |
| 56 | `3f144e58eb7c9755` | 10D | 3.475 | 以最高价为输入，经时间序列标准化、截面排序形成的复合信号。 | `cs_rank(ts_zscore(high, 20))` |
| 57 | `ce26bf64e860560a` | 10D | 3.214 | 以CCI为输入，经加减乘除/条件组合形成的复合信号。 | `cci_20` |
| 58 | `598c04e12b4d8fa1` | 5D | 3.185 | 以个股收益率为输入，经滚动偏度、滚动极值、滚动区间归一化形成的复合信号。 | `ts_skew(ts_min_max_scale(return, 3), 5)` |
| 59 | `409d490476cedf7e` | 10D | 2.522 | 以Williams %R为输入，经加减乘除/条件组合形成的复合信号。 | `willr_14` |
| 60 | `062345335e9ac0e7` | 10D | 2.480 | 以RSI动量为输入，经滚动自相关形成的复合信号。 | `ts_autocorr(rsi_14, 20)` |
| 61 | `d6e1d28fb1323d16` | 5D | 2.164 | 以市净率、MACD柱为输入，经滚动相关性、滚动自相关、滚动均值形成的复合信号。 | `cs_percentile(ts_mean(ts_corr(mul(sign(ts_autocorr(pb, 3)), 0.682), ts_percentile_10(ts_min_max_scale(macd_hist, 5), 10), 10), 5))` |
| 62 | `0fe0f8cff196a73e` | 5D | 2.011 | 以换手率、每股经营现金流、ADX趋势强度为输入，经截面标准化、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), 2.314))` |
| 63 | `1f31f9900a516316` | 5D | 2.011 | 以换手率、每股经营现金流、ADX趋势强度为输入，经截面标准化形成的复合信号。 | `cs_zscore(sub(adx_14, sub(ocfps, turnover_rate)))` |
| 64 | `8f51b83d72ef364d` | 5D | 2.011 | 以换手率、每股经营现金流、ADX趋势强度为输入，经加减乘除/条件组合形成的复合信号。 | `sub(adx_14, sub(ocfps, turnover_rate))` |
| 65 | `400258747b72804b` | 5D | 1.624 | 以Williams %R为输入，经滚动中位数、截面排序、截面去极值形成的复合信号。 | `winsorize(cs_rank(ts_median(willr_14, 10)))` |
| 66 | `68b53b70ce20b4c1` | 5D | 1.597 | 以主力净资金流、流通市值、扣非ROE、每股收益等为输入，经滚动相关性、滚动均值、滚动极值、条件筛选形成的复合信号。 | `if_else(roe_dt, mul(ts_max(winsorize(eps), 3), neg(0.639)), mul(add(mul(sign(ts_mean(ts_corr(grossprofit_margin, circ_mv, 5), 10)), 0.552), net_mf_amount), 1.437))` |
| 67 | `477f79caa83af71e` | 10D | 1.048 | 以主力净资金流为输入，经滚动均值形成的复合信号。 | `ts_mean(net_mf_amount, 20)` |
| 68 | `e7e09c4bdbb58ff8` | 5D | 0.985 | 以中单买入额为输入，经滚动自相关、线性衰减加权形成的复合信号。 | `ts_autocorr(ts_percentile_10(ts_decay_linear(buy_md_amount, 3), 20), 10)` |
| 69 | `0bce8477ca17c3d1` | 5D | -0.482 | 以总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, total_mv), winsorize(total_mv))), winsorize(total_mv)), winsorize(total_mv)))` |
| 70 | `fc70b332ada43801` | 5D | -0.804 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), sub(ocfps, div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)))), winsorize(total_mv)))` |
| 71 | `927221326a0b6309` | 10D | -1.053 | 以布林中轨为输入，经滚动自相关形成的复合信号。 | `ts_autocorr(bband_middle, 10)` |
| 72 | `aa91d42f399e3bf3` | 5D | -1.067 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(sub(adx_14, sub(ocfps, turnover_rate)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 73 | `e0d6d98c9ce5f28e` | 10D | -1.291 | 以超大单卖出额为输入，经滚动峰度、极值位置、截面标准化形成的复合信号。 | `ts_argmin(ts_kurt(cs_zscore(add(0.588, sell_elg_amount)), 20), 60)` |
| 74 | `cfa1697b954bfd45` | 5D | -2.213 | 以换手率、总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(cs_zscore(adx_14), turnover_rate)), winsorize(total_mv)))` |
| 75 | `2b030ece3ecca4cf` | 10D | -2.332 | 以大单买入额、扣非净利同比、北向持仓比例、MACD等为输入，经滚动相关性、滚动自相关、滚动熵/离散度、条件筛选形成的复合信号。 | `ts_autocorr(if_else(ts_min_max_scale(ts_entropy(less(adx_14, 0.909), 10), 5), ts_corr(winsorize(if_else(hk_ratio, close, dt_netprofit_yoy)), ts_kurt(ts_max(buy_lg_amount, 20), 20), 3), macd), 60)` |
| 76 | `f17ec5ad0b540b5f` | 5D | -2.648 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(sub(ocfps, winsorize(ocfps)), turnover_rate)), winsorize(total_mv)))` |
| 77 | `f2bed0261643ec88` | 5D | -2.931 | 以换手率、总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(winsorize(total_mv), turnover_rate)), winsorize(total_mv)))` |
| 78 | `d8fea28b72b7d440` | 5D | -2.931 | 以换手率、总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(div(turnover_rate, winsorize(total_mv)), turnover_rate)), winsorize(total_mv)))` |
| 79 | `c3af9446e8dcb3be` | 5D | -2.947 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 80 | `9895582eac0ebb28` | 5D | -2.947 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面去极值、相对值构造形成的复合信号。 | `div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))` |
| 81 | `46fee3eccca983f1` | 5D | -2.947 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))))` |
| 82 | `4169f5f3d281b0e4` | 5D | -2.947 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), total_mv))` |
| 83 | `e37bb992b8ae4e34` | 5D | -3.009 | 以总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), winsorize(ocfps)), winsorize(total_mv)))` |
| 84 | `a41819f879486ac2` | 10D | -3.027 | 以开盘价为输入，经滚动自相关形成的复合信号。 | `ts_autocorr(open, 20)` |
| 85 | `4da8b9f61ed84c9b` | 5D | -3.172 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv))), div(adx_14, winsorize(total_mv))), turnover_rate)), winsorize(total_mv)))` |
| 86 | `9ebab445dbe1333e` | 5D | -3.342 | 以换手率、总市值、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(total_mv, turnover_rate)), winsorize(total_mv)))` |
| 87 | `7b725aaa1083c925` | 5D | -3.540 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(sub(cs_zscore(div(sub(adx_14, sub(ocfps, turnover_rate)), div(adx_14, winsorize(total_mv)))), cs_zscore(div(adx_14, winsorize(total_mv)))), turnover_rate)), winsorize(total_mv)))` |
| 88 | `f7778c0c0133eed8` | 5D | -3.613 | 以总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), ocfps), winsorize(total_mv)))` |
| 89 | `872d4af09b9ce2c0` | 5D | -3.621 | 以总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), total_mv), winsorize(total_mv)))` |
| 90 | `b559e306edf2fb05` | 10D | -3.806 | 以最低价为输入，经滚动自相关、滚动熵/离散度、滚动偏度、相对值构造形成的复合信号。 | `ts_mean(ts_skew(div(ts_autocorr(low, 10), abs(ts_entropy(low, 10))), 3), 60)` |
| 91 | `a306f14ffe301c65` | 10D | -3.879 | 以每股收益为输入，经滚动自相关、截面去极值形成的复合信号。 | `neg(winsorize(ts_autocorr(eps, 60)))` |
| 92 | `0f0e8f53cf350119` | 10D | -3.879 | 以每股收益为输入，经滚动自相关、截面去极值形成的复合信号。 | `cs_winsorize(neg(winsorize(ts_autocorr(eps, 60))))` |
| 93 | `f7ec463bf8dfd521` | 5D | -4.032 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(cs_zscore(div(sub(cs_zscore(div(sub(sub(adx_14, sub(ocfps, winsorize(total_mv))), sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv))), turnover_rate)), winsorize(total_mv)))` |
| 94 | `144a84806a7c7e3d` | 5D | -4.051 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(cs_zscore(div(sub(cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv))), turnover_rate)), winsorize(total_mv)))` |
| 95 | `d5d112a0cb3167d5` | 5D | -4.051 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(adx_14, sub(cs_zscore(div(sub(cs_zscore(div(sub(adx_14, sub(ocfps, winsorize(ocfps))), winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv))), turnover_rate)), winsorize(total_mv)))` |
| 96 | `71dab51d71642354` | 5D | -4.176 | 以换手率、总市值、每股经营现金流、ADX趋势强度为输入，经截面标准化、截面去极值、相对值构造形成的复合信号。 | `cs_zscore(div(sub(cs_zscore(div(div(sub(adx_14, sub(ocfps, turnover_rate)), winsorize(total_mv)), winsorize(total_mv))), winsorize(total_mv)), winsorize(total_mv)))` |
| 97 | `76011c2ad3b5c3d5` | 10D | -4.323 | 以ADX趋势强度为输入，经滚动均值形成的复合信号。 | `ts_mean(log(adx_14), 60)` |
| 98 | `36fd26067f408420` | 5D | -4.420 | 以20日均线、最高价为输入，经滚动自相关、滚动累计、截面去极值形成的复合信号。 | `ts_autocorr(sub(abs(winsorize(sma_20)), ts_sum(high, 20)), 10)` |
| 99 | `5632e1b09680dcb7` | 10D | -4.741 | 以每股经营现金流为输入，经滚动自相关、滚动极值、截面排序形成的复合信号。 | `ts_autocorr(ts_min(cs_rank(ocfps), 60), 60)` |
| 100 | `1deb2db78193655c` | 10D | -4.942 | 以12日EMA为输入，经滚动自相关形成的复合信号。 | `ts_autocorr(ema_12, 20)` |
