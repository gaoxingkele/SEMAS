"""Batch runner for public-figure hour calibration cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.case_studies.hour_calibration.hour_calibration import calibrate_case, render_markdown


DEFAULT_CASES = [
    "mao_zedong_public_events.json",
    "bruce_lee_public_events.json",
    "jackie_chan_public_events.json",
    "marilyn_monroe_public_events.json",
    "audrey_hepburn_public_events.json",
    "taylor_swift_public_events.json",
    "michael_jackson_public_events.json",
    "barack_obama_public_events.json",
    "angelina_jolie_public_events.json",
    "oprah_winfrey_public_events.json",
    "donald_trump_public_events.json",
]


def run_batch(case_dir: Path, out_dir: Path, case_names: list[str]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in case_names:
        path = case_dir / name
        case = json.loads(path.read_text(encoding="utf-8"))
        result = calibrate_case(case)
        stem = str(case.get("case_id") or path.stem)
        (out_dir / f"{stem}.hour_calibration.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (out_dir / f"{stem}.hour_calibration.md").write_text(render_markdown(result), encoding="utf-8")
        rows.append(_summary_row(result))
    summary = {
        "schema_version": "mingli-hour-validation-batch-v1",
        "case_count": len(rows),
        "rows": rows,
        "school_fit_ranking": _school_fit_ranking(out_dir, rows),
        "book_fit_ranking": _book_fit_ranking(out_dir, rows),
        "hit_count": sum(1 for row in rows if row["reference_rank"] == 1),
        "top3_count": sum(1 for row in rows if isinstance(row["reference_rank"], int) and row["reference_rank"] <= 3),
        "ambiguous_count": sum(1 for row in rows if row["decision"] == "ambiguous"),
    }
    (out_dir / "public_figure_validation_batch.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "public_figure_validation_batch.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def _summary_row(result: dict[str, Any]) -> dict[str, Any]:
    reference = result.get("reference_evaluation", {})
    winner_score = result["winner"]["score"]
    return {
        "case_id": result["case_id"],
        "name": result["name"],
        "winner_hour": result["winner"]["hour_label"],
        "decision": result["debate"]["decision"],
        "margin_to_second": result["debate"]["margin_to_second"],
        "reference_rank": reference.get("best_reference_rank"),
        "reference_margin_from_winner": reference.get("best_reference_margin_from_winner"),
        "strategy_total": winner_score["strategy_total"],
        "event_fit_total": winner_score["event_fit_total"],
        "hengmen_ahp_total": winner_score["hengmen_ahp_total"],
        "ziwei_side_total": winner_score["ziwei_side_total"],
        "astrology_side_total": winner_score["astrology_side_total"],
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# 公众人物十二时辰校准批量验证",
        "",
        f"- 案例数：{summary['case_count']}",
        f"- 公开参考时辰命中数：{summary['hit_count']}",
        f"- 公开参考时辰进入前三数：{summary['top3_count']}",
        f"- 判为不明确的案例数：{summary['ambiguous_count']}",
        "",
        "| 案例 | 系统候选 | 参考排名 | 决策 | 领先差 | 综合分 | 横门断 | 紫微侧证 | 星座侧证 |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        rank = row["reference_rank"] if row["reference_rank"] is not None else ""
        lines.append(
            f"| {row['name']} | {row['winner_hour']} | {rank} | {row['decision']} | "
            f"{row['margin_to_second']} | {row['strategy_total']} | {row['hengmen_ahp_total']} | "
            f"{row['ziwei_side_total']} | {row['astrology_side_total']} |"
        )
    lines.extend(
        [
            "",
            "## 七个传统八字流派吻合度",
            "",
            "| 排名 | 流派 | 平均参考排名 | 第一数 | 前三数 | 平均参考分 |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(summary.get("school_fit_ranking", []), start=1):
        lines.append(
            f"| {index} | {row['school_name']} | {row['mean_reference_rank']} | "
            f"{row['top1_count']} | {row['top3_count']} | {row['average_reference_score']} |"
        )
    lines.extend(
        [
            "",
            "## 每本书 AHP 框架吻合度",
            "",
            "| 排名 | 书籍 | 平均参考排名 | 第一数 | 前三数 | 平均参考分 |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(summary.get("book_fit_ranking", []), start=1):
        lines.append(
            f"| {index} | {row['title']} | {row['mean_reference_rank']} | "
            f"{row['top1_count']} | {row['top3_count']} | {row['average_reference_score']} |"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- 该表只检验不同候选时辰对已知事件的解释力，不证明真实出生时辰。",
            "- 横门断、紫微斗数、星座学都只是侧证票；若分差小，必须保留多个候选。",
            "- 公开参考时辰和算法候选不一致时，记录冲突来源，不强行合并。",
        ]
    )
    return "\n".join(lines) + "\n"


def _school_fit_ranking(out_dir: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_ids = {row["case_id"] for row in rows}
    loaded = []
    for path in out_dir.glob("*.hour_calibration.json"):
        if path.stem.replace(".hour_calibration", "") not in case_ids:
            continue
        loaded.append(json.loads(path.read_text(encoding="utf-8")))
    school_ids = sorted(
        {
            school_id
            for result in loaded
            for school_id in result["winner"].get("bazi_school_ahp_totals", {})
        }
    )
    output = []
    for school_id in school_ids:
        ranks = []
        scores = []
        school_name = school_id
        for result in loaded:
            refs = [
                ref
                for ref in result.get("reference_evaluation", {}).get("references", [])
                if isinstance(ref.get("rank"), int)
            ]
            if not refs:
                continue
            reference_label = refs[0]["label"]
            ranking = sorted(
                result["ranking"],
                key=lambda candidate: candidate.get("bazi_school_ahp_totals", {})
                .get(school_id, {})
                .get("score", 0.0),
                reverse=True,
            )
            for index, candidate in enumerate(ranking, start=1):
                if candidate["hour_label"] != reference_label:
                    continue
                school_row = candidate["bazi_school_ahp_totals"][school_id]
                school_name = school_row["school_name"]
                ranks.append(index)
                scores.append(float(school_row["score"]))
                break
        if ranks:
            output.append(
                {
                    "school_id": school_id,
                    "school_name": school_name,
                    "mean_reference_rank": round(sum(ranks) / len(ranks), 2),
                    "top1_count": sum(1 for rank in ranks if rank == 1),
                    "top3_count": sum(1 for rank in ranks if rank <= 3),
                    "average_reference_score": round(sum(scores) / len(scores), 4),
                }
            )
    output.sort(key=lambda item: (item["mean_reference_rank"], -item["top3_count"], -item["top1_count"]))
    return output


def _book_fit_ranking(out_dir: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_ids = {row["case_id"] for row in rows}
    loaded = []
    for path in out_dir.glob("*.hour_calibration.json"):
        if path.stem.replace(".hour_calibration", "") not in case_ids:
            continue
        loaded.append(json.loads(path.read_text(encoding="utf-8")))
    book_ids = sorted(
        {
            book_id
            for result in loaded
            for book_id in result["winner"].get("book_ahp_totals", {})
        }
    )
    output = []
    for book_id in book_ids:
        ranks = []
        scores = []
        title = book_id
        domain = ""
        for result in loaded:
            refs = [
                ref
                for ref in result.get("reference_evaluation", {}).get("references", [])
                if isinstance(ref.get("rank"), int)
            ]
            if not refs:
                continue
            reference_label = refs[0]["label"]
            ranking = sorted(
                result["ranking"],
                key=lambda candidate: candidate.get("book_ahp_totals", {})
                .get(book_id, {})
                .get("score", 0.0),
                reverse=True,
            )
            for index, candidate in enumerate(ranking, start=1):
                if candidate["hour_label"] != reference_label:
                    continue
                book_row = candidate["book_ahp_totals"][book_id]
                title = book_row["title"]
                domain = book_row.get("domain", "")
                ranks.append(index)
                scores.append(float(book_row["score"]))
                break
        if ranks:
            output.append(
                {
                    "book_id": book_id,
                    "title": title,
                    "domain": domain,
                    "mean_reference_rank": round(sum(ranks) / len(ranks), 2),
                    "top1_count": sum(1 for rank in ranks if rank == 1),
                    "top3_count": sum(1 for rank in ranks if rank <= 3),
                    "average_reference_score": round(sum(scores) / len(scores), 4),
                }
            )
    output.sort(key=lambda item: (item["mean_reference_rank"], -item["top3_count"], -item["top1_count"]))
    return output


def main(argv: list[str] | None = None) -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run all public-figure hour calibration cases.")
    parser.add_argument("--case-dir", type=Path, default=base / "cases")
    parser.add_argument("--out-dir", type=Path, default=base / "outputs")
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    args = parser.parse_args(argv)
    summary = run_batch(args.case_dir, args.out_dir, args.cases)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
