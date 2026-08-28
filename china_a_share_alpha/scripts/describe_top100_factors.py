"""Create a readable Chinese structural description for each TOP100 expression.

Descriptions are deterministic expression interpretations, not claims of
economic causality or live-trading validity.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

FEATURES = [
    ("net_mf_amount", "主力净资金流"),
    ("net_elg_amount", "超大单净流"),
    ("buy_elg_amount", "超大单买入额"),
    ("sell_elg_amount", "超大单卖出额"),
    ("buy_lg_amount", "大单买入额"),
    ("sell_lg_amount", "大单卖出额"),
    ("buy_md_amount", "中单买入额"),
    ("sell_md_amount", "中单卖出额"),
    ("buy_sm_amount", "小单买入额"),
    ("sell_sm_amount", "小单卖出额"),
    ("turnover_rate", "换手率"),
    ("total_mv", "总市值"),
    ("circ_mv", "流通市值"),
    ("roe_dt", "扣非ROE"),
    ("roe", "ROE"),
    ("ocfps", "每股经营现金流"),
    ("eps", "每股收益"),
    ("pb", "市净率"),
    ("netprofit_yoy", "净利润同比"),
    ("dt_netprofit_yoy", "扣非净利同比"),
    ("grossprofit_margin", "毛利率"),
    ("debt_to_assets", "资产负债率"),
    ("hk_ratio", "北向持仓比例"),
    ("hk_vol", "北向持仓量"),
    ("rsi_14", "RSI动量"),
    ("macd_hist", "MACD柱"),
    ("macd_signal", "MACD信号线"),
    ("macd", "MACD"),
    ("willr_14", "Williams %R"),
    ("adx_14", "ADX趋势强度"),
    ("cci_20", "CCI"),
    ("atr_14", "ATR波动"),
    ("bband_upper", "布林上轨"),
    ("bband_middle", "布林中轨"),
    ("bband_lower", "布林下轨"),
    ("mom_10", "10日动量"),
    ("sma_20", "20日均线"),
    ("ema_12", "12日EMA"),
    ("ema_26", "26日EMA"),
    ("volume", "成交量"),
    ("vwap", "成交额/量价代理VWAP"),
    ("return", "个股收益率"),
    ("close", "收盘价"),
    ("open", "开盘价"),
    ("high", "最高价"),
    ("low", "最低价"),
]

OPERATIONS = [
    ("ts_corr", "滚动相关性"),
    ("ts_cov", "滚动协方差"),
    ("ts_autocorr", "滚动自相关"),
    ("ts_entropy", "滚动熵/离散度"),
    ("ts_skew", "滚动偏度"),
    ("ts_kurt", "滚动峰度"),
    ("ts_decay_linear", "线性衰减加权"),
    ("ts_delta", "时间变化"),
    ("ts_pct_change", "时间变化率"),
    ("ts_mean", "滚动均值"),
    ("ts_sum", "滚动累计"),
    ("ts_max", "滚动极值"),
    ("ts_min", "滚动极值"),
    ("ts_rank", "时间序列排序"),
    ("ts_zscore", "时间序列标准化"),
    ("ts_argmax", "极值位置"),
    ("ts_argmin", "极值位置"),
    ("ts_median", "滚动中位数"),
    ("ts_min_max_scale", "滚动区间归一化"),
    ("cs_zscore", "截面标准化"),
    ("cs_rank", "截面排序"),
    ("cs_percentile", "截面分位"),
    ("winsorize", "截面去极值"),
]


def describe(expression: str) -> str:
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression))
    features = [label for token, label in FEATURES if token in tokens]
    operations = []
    for token, label in OPERATIONS:
        if token in expression and label not in operations:
            operations.append(label)
    feature_text = "、".join(features[:4]) if features else "常数/条件表达式"
    if len(features) > 4:
        feature_text += "等"
    operation_text = "、".join(operations[:3]) if operations else "加减乘除/条件组合"
    if "div(" in expression and "相对值" not in operation_text:
        operation_text += "、相对值构造"
    if "if_else(" in expression or "if_positive(" in expression:
        operation_text += "、条件筛选"
    return f"以{feature_text}为输入，经{operation_text}形成的复合信号。"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--wiki", type=Path, required=True)
    args = parser.parse_args()
    factors = pd.read_csv(args.input).sort_values("top100_rank")
    factors["factor_description"] = factors["expression"].map(describe)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    factors.to_csv(args.output_csv, index=False)
    lines = [
        "# TOP100 因子快照及结构说明（2026-07-09）",
        "",
        "以下为当前 60 日无前视滚动 Sharpe 排名的 TOP100 快照。说明仅解释表达式使用的数据与算子结构，"
        "不构成经济因果、交易可行性或未来收益承诺。实际再入仍需满足因子自身冷却期。",
        "",
        "[source: local artifact china_a_share_alpha_output/external_unused_csi500_2025_2026/"
        "ranked_reentry_top100/top100_latest_20260709.csv]",
        "",
        "| 排名 | 因子 ID | 周期 | 60日 Sharpe | 大致说明 | 表达式 |",
        "|---:|---|---:|---:|---|---|",
    ]
    for _, row in factors.iterrows():
        lines.append(
            f"| {int(row.top100_rank)} | `{row.factor_id}` | {int(row.horizon)}D | "
            f"{float(row.ranking_score):.3f} | {row.factor_description} | `{row.expression}` |"
        )
    args.wiki.parent.mkdir(parents=True, exist_ok=True)
    args.wiki.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"described={len(factors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
