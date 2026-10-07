"""One-shot tech-subset hold backtest for live library (CSI300 ∩ tech industries)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from china_a_share_alpha.scripts.run_multihizon_audit import evaluate_library_hold
from china_a_share_alpha.scripts.run_t1_full_library_audit import _load_snapshot

TECH_KEYWORDS = [
    "半导体",
    "元件",
    "计算机设备",
    "通信设备",
    "电子",
    "软件服务",
    "互联网",
    "通信",
    "IT设备",
    "电器仪表",
    "元器件",
    "芯片",
    "软件",
    "计算机",
]


def _is_tech(industry: object) -> bool:
    text = str(industry or "")
    return any(kw in text for kw in TECH_KEYWORDS)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = yaml.safe_load(
        (root / "china_a_share_alpha/examples/enhanced_loop_config_val_frozen.yaml").read_text(
            encoding="utf-8"
        )
    )
    snapshot_dir = root / cfg["snapshot_dir"]
    panel, metadata, manifest = _load_snapshot(snapshot_dir)
    if "return" not in panel.columns:
        panel = panel.copy()
        panel["return"] = panel.groupby(level="symbol")["close"].pct_change()

    code_col = "ts_code" if "ts_code" in metadata.columns else "symbol"
    meta = metadata.copy()
    panel_syms = set(panel.index.get_level_values("symbol").unique())
    meta = meta[meta[code_col].isin(panel_syms)].copy()
    meta["is_tech"] = meta["industry"].map(_is_tech)
    tech_syms = meta.loc[meta["is_tech"], code_col].astype(str).tolist()

    split_date = pd.Timestamp(cfg["split_date"])
    val_date = pd.Timestamp(cfg.get("val_date", "20230101"))

    def _slice(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        train = data.loc[pd.IndexSlice[:, : val_date - pd.Timedelta(days=1)], :]
        # history for factor warmup = train+val
        hist = data.loc[pd.IndexSlice[:, : split_date - pd.Timedelta(days=1)], :]
        test = data.loc[pd.IndexSlice[:, split_date:], :]
        return train, hist, test

    full_train, full_hist, full_test = _slice(panel)
    tech_panel = panel.loc[panel.index.get_level_values("symbol").isin(tech_syms)]
    tech_train, tech_hist, tech_test = _slice(tech_panel)

    library = pd.read_csv(root / "china_a_share_alpha_output/factor_mining_loop/live_library.csv")

    common = dict(
        library=library,
        horizon=5,
        transaction_cost=0.001,
        smooth_span=10,
        evaluation_mode="dynamic_trim",
        min_factor_coverage=0.5,
    )

    results = {
        "csi300_full": evaluate_library_hold(
            test_data=full_test, history_data=full_hist, **common
        ),
        "csi300_tech": evaluate_library_hold(
            test_data=tech_test, history_data=tech_hist, **common
        ),
    }

    # Per-factor IC on tech test (diagnostic)
    from china_a_share_alpha.factor.parser import parse_expression
    from china_a_share_alpha.evaluator.metrics import ic_score

    fwd = (
        tech_test.groupby(level="symbol")["close"].pct_change(5).shift(-5)
        if "close" in tech_test.columns
        else tech_test["forward_return"]
    )
    factor_rows = []
    for i, row in library.reset_index(drop=True).iterrows():
        name = str(row.get("factor", f"factor_{i+1}"))
        try:
            expr = parse_expression(row["expression"])
            # eval on hist+test for lookback, then align to test
            eval_data = pd.concat([tech_hist, tech_test])
            eval_data = eval_data[~eval_data.index.duplicated(keep="last")].sort_index()
            series = expr.eval(eval_data).reindex(tech_test.index)
            factor_rows.append(
                {
                    "factor": name,
                    "expression": row["expression"],
                    "tech_test_ic": float(ic_score(series, fwd.reindex(series.index))),
                    "n_tech_symbols": int(len(tech_syms)),
                }
            )
        except Exception as exc:  # noqa: BLE001
            factor_rows.append(
                {
                    "factor": name,
                    "expression": row["expression"],
                    "tech_test_ic": None,
                    "error": str(exc),
                    "n_tech_symbols": int(len(tech_syms)),
                }
            )

    out_dir = root / "china_a_share_alpha_output/factor_mining_loop/tech_hold_backtest"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "contract": {
            "horizon": 5,
            "evaluation_mode": "dynamic_trim",
            "transaction_cost": 0.001,
            "smooth_span": 10,
            "split_date": str(split_date.date()),
            "snapshot": str(snapshot_dir),
            "tech_keywords": TECH_KEYWORDS,
        },
        "universe": {
            "csi300_symbols": int(len(panel_syms)),
            "tech_symbols_in_csi300": int(len(tech_syms)),
            "tech_industry_counts": meta.loc[meta["is_tech"], "industry"]
            .value_counts()
            .to_dict(),
            "tech_symbols": tech_syms,
        },
        "hold": {
            name: {
                k: v
                for k, v in receipt.items()
                if k
                in {
                    "valid",
                    "sharpe",
                    "annualized_return",
                    "cost_adjusted_return",
                    "max_drawdown",
                    "total_return",
                    "average_daily_turnover",
                    "n_observations",
                    "n_factors_evaluated",
                    "error",
                }
            }
            for name, receipt in results.items()
        },
        "manifest_snapshot_id": manifest.get("snapshot_id"),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(factor_rows).to_csv(out_dir / "per_factor_tech_ic.csv", index=False, encoding="utf-8")

    lines = [
        "# 科技股子集回测（CSI300 ∩ 科技行业）",
        "",
        f"- 快照: `{snapshot_dir.name}`",
        f"- CSI300 成分: {len(panel_syms)}；科技子集: **{len(tech_syms)}**",
        f"- 合约: 5d dynamic-trim hold / 10bps / EMA10 / coverage≥50%",
        "",
        "## 合奏 Hold 对比",
        "",
        "| 宇宙 | Hold Sharpe | 年化收益 | 最大回撤 | 总收益 | 日换手 | 有效 |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for name, receipt in results.items():
        if not receipt.get("valid"):
            lines.append(
                f"| {name} | — | — | — | — | — | N ({receipt.get('error','')}) |"
            )
            continue
        lines.append(
            "| {name} | {sharpe:.4f} | {ann:.2%} | {dd:.2%} | {tot:.2%} | {to:.4f} | Y |".format(
                name=name,
                sharpe=receipt["sharpe"],
                ann=receipt["annualized_return"],
                dd=receipt["max_drawdown"],
                tot=receipt.get("total_return", float("nan")),
                to=receipt.get("average_daily_turnover", float("nan")),
            )
        )
    lines.append("")
    lines.append("## 科技子集行业分布")
    lines.append("")
    for ind, cnt in meta.loc[meta["is_tech"], "industry"].value_counts().items():
        lines.append(f"- {ind}: {cnt}")
    lines.append("")
    lines.append("## 单因子 Tech Test IC（诊断）")
    lines.append("")
    lines.append("| 因子 | Tech Test IC |")
    lines.append("|---|---:|")
    for row in sorted(
        [r for r in factor_rows if r.get("tech_test_ic") is not None],
        key=lambda r: abs(r["tech_test_ic"]),
        reverse=True,
    ):
        lines.append(f"| {row['factor']} | {row['tech_test_ic']:.4f} |")
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print((out_dir / "REPORT.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
