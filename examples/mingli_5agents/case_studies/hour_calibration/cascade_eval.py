"""两级级联融合：3 包等权初筛 → 知识库 LLM 裁决。

Stage 1（无污染）：横门 vote 包 / 流派包 / 书籍包各占 1/3 的等权分，
取 top-K 候选。Stage 2：知识库 LLM 分析（见 llm_skill_analysis/）对
top-K 候选做带推理链的裁决排序。

本脚本对 11 个公众人物案例做回顾性评估（in-sample；LLM 排名来自
llm_rankings_2026-07-28.json，含污染风险声明）。生产用法：
`python -m ...cascade_eval --case cases/x.json --k 4` 输出 stage-1
候选集，随后由知识库分析智能体裁决（协议见 cascade_report）。

[source: sem_fusion_v2_report_2026-07-28.md §3-parcel equal weight]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "outputs" / "sem_fusion_dataset.json"
DEFAULT_LLM_RANKINGS = BASE_DIR / "llm_skill_analysis" / "llm_rankings_2026-07-28.json"
PARCEL_NAMES = ["hengmen_votes", "schools", "books"]


def parcel_equal_weight(row: dict[str, Any], parcel_names: list[str] | None = None) -> float:
    """三包含权 1/3 等权分（要求 row 带 build_parcels 产出的 parcels）。"""
    names = parcel_names or PARCEL_NAMES
    return sum(float(row["parcels"][p]) for p in names) / len(names)


def stage1_topk(case_rows: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """Stage 1：按 3 包等权分取 top-K 候选。"""
    return sorted(case_rows, key=parcel_equal_weight, reverse=True)[:k]


def stage2_adjudicate(topk_rows: list[dict[str, Any]], llm_ranking: list[str]) -> list[str]:
    """Stage 2：按 LLM 全排序对 top-K 候选重排（LLM 排序外的候选保持原序殿后）。"""
    top_branches = [str(r["hour_label"])[0] for r in topk_rows]
    adjudicated = [b for b in llm_ranking if b in top_branches]
    rest = [b for b in top_branches if b not in adjudicated]
    return adjudicated + rest


def cascade_rank(topk_rows: list[dict[str, Any]], llm_ranking: list[str], reference_label: str) -> int | None:
    """参考时辰在级联排序中的名次；未进 stage-1 候选集返回 None（漏判）。"""
    order = stage2_adjudicate(topk_rows, llm_ranking)
    ref = reference_label[0]
    return order.index(ref) + 1 if ref in order else None


def evaluate(k_values: tuple[int, ...] = (3, 4, 5, 6)) -> dict[str, Any]:
    from examples.mingli_5agents.case_studies.hour_calibration import sem_fusion as sf

    dataset = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    rows = sf.within_case_standardize(dataset["rows"])
    screen = sf.screen_features(rows)
    rows, parcel_names = sf.build_parcels(rows, screen)
    llm = json.loads(DEFAULT_LLM_RANKINGS.read_text(encoding="utf-8"))["rankings"]
    cases: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        cases.setdefault(row["case_id"], []).append(row)

    def reference_rank(cid: str, crs: list[dict[str, Any]], score) -> int:
        ref = next(x for x in crs if x["is_reference"])
        ordered = sorted(crs, key=score, reverse=True)
        return ordered.index(ref) + 1

    summary: dict[str, Any] = {"methods": {}}

    def record(name: str, ranks: list[int]) -> None:
        summary["methods"][name] = {
            "mean_reference_rank": round(sum(ranks) / len(ranks), 2),
            "top1_count": sum(1 for x in ranks if x == 1),
            "top3_count": sum(1 for x in ranks if x <= 3),
            "miss_count": sum(1 for x in ranks if x >= 12),
        }

    record("parcel_equal_weight", [reference_rank(cid, crs, parcel_equal_weight) for cid, crs in cases.items()])
    record(
        "llm_knowledge_base",
        [llm[cid].index(next(x for x in crs if x["is_reference"])["hour_label"][0]) + 1 for cid, crs in cases.items()],
    )
    per_case: dict[int, list[dict[str, Any]]] = {}
    for k in k_values:
        ranks, details = [], []
        for cid, crs in cases.items():
            ref = next(x for x in crs if x["is_reference"])
            topk = stage1_topk(crs, k)
            rank = cascade_rank(topk, llm[cid], ref["hour_label"])
            ranks.append(rank if rank is not None else 12)
            details.append(
                {
                    "case_id": cid,
                    "case_name": ref["case_name"],
                    "reference": ref["hour_label"],
                    "stage1_topk": [x["hour_label"] for x in topk],
                    "stage2_order": stage2_adjudicate(topk, llm[cid]),
                    "reference_rank": rank if rank is not None else "miss",
                }
            )
        record(f"cascade_k{k}", ranks)
        per_case[k] = details
    summary["per_case"] = per_case
    return summary


def main() -> int:
    summary = evaluate()
    print("| 方法 | 平均参考排名 | Top1 | Top3 | 漏判 |")
    print("|---|---:|---:|---:|---:|")
    for name, m in summary["methods"].items():
        print(f"| {name} | {m['mean_reference_rank']} | {m['top1_count']} | {m['top3_count']} | {m['miss_count']} |")
    out = BASE_DIR / "outputs" / "cascade_eval.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
