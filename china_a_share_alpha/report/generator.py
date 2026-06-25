"""Factor report generator.

Outputs a structured JSON/Markdown report summarizing the evolved factor,
its in-sample and out-of-sample performance, and backtest statistics.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def generate_report(
    result: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Write JSON and Markdown reports for a factor evolution run."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = output_dir / f"factor_report_{timestamp}"

    json_path = base.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {"result": result, "config": config, "generated_at": datetime.now().isoformat()},
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    md_path = base.with_suffix(".md")
    lines = [
        "# China A-Share Alpha Factor Report",
        "",
        f"**Generated at:** {datetime.now().isoformat()}",
        "",
        "## Factor Expression",
        "",
        f"```text\n{result['expression']}\n```",
        "",
        "## Configuration",
        "",
        "```yaml\n" + yaml.safe_dump(config, allow_unicode=True) + "```",
        "",
        "## Performance",
        "",
        "| Split | IC | RankIC |",
        "|-------|-----|--------|",
        f"| Train | {result['train_ic']:.4f} | {result['train_rank_ic']:.4f} |",
        f"| Test  | {result['test_ic']:.4f} | {result['test_rank_ic']:.4f} |",
        "",
        "## Backtest (quantile long-short)",
        "",
        "| Split | Ann. Return | Sharpe | Max DD | Turnover | Cost | Cost-Adj Return |",
        "|-------|-------------|--------|--------|----------|------|-----------------|",
        f"| Train | {result['train_backtest']['annualized_return']:.4f} | {result['train_backtest']['sharpe']:.4f} | {result['train_backtest']['max_drawdown']:.4f} | {result['train_backtest']['turnover']:.4f} | {result['train_backtest']['cost']:.4f} | {result['train_backtest']['cost_adjusted_return']:.4f} |",
        f"| Test  | {result['test_backtest']['annualized_return']:.4f} | {result['test_backtest']['sharpe']:.4f} | {result['test_backtest']['max_drawdown']:.4f} | {result['test_backtest']['turnover']:.4f} | {result['test_backtest']['cost']:.4f} | {result['test_backtest']['cost_adjusted_return']:.4f} |",
        "",
        f"**Passed threshold:** {result['passed']}",
        "",
    ]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return json_path
