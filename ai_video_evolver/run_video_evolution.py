"""High-level runner that evolves the AI Video Evolver pipeline on a task."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox

from ai_video_evolver.bootstrap import initialize_video_repo
from ai_video_evolver.evaluator.metrics import video_quality_score
from ai_video_evolver.executor import create_video_executor
from ai_video_evolver.mutator import VideoEvolverMutator


def load_task(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(task_path: Path, max_rounds: int = 3) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="ai_video_evolver_"))
    try:
        repo = initialize_video_repo(tmp)

        # Pipeline agent uses the video_pipeline topology.
        pipeline_agent = AgentGenome(
            name="video_pipeline_runner",
            role="pipeline_runner",
            system_prompt="Run the AI video generation pipeline.",
            topology="video_pipeline",
            meta={
                "domain": "ai_video",
                "prompt_engineering": {"use_enhancement": False},
            },
        )
        repo.save_agent(pipeline_agent)

        evaluator = Evaluator()
        evaluator.register_metric("video_quality", video_quality_score)

        executor = create_video_executor(repo)

        orch = Orchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=VideoEvolverMutator(),
            sandbox=Sandbox(),
            agent_name=pipeline_agent.name,
            executor=executor,
            cooldown_tasks=0,
        )

        task = load_task(task_path)
        task_input = {"user_idea": task["user_idea"], "captions": task.get("captions", "")}
        expected = {"user_idea": task["user_idea"]}

        best_trace = None
        for round_idx in range(max_rounds + 1):
            trace = orch.run_task(task_input, expected=expected)
            best_trace = trace
            print(f"Round {round_idx}: score={trace.evaluation.score:.3f}")
            if trace.evaluation.passed:
                break

        final_state = best_trace.task_output if best_trace else {}
        return {
            "passed": best_trace.evaluation.passed if best_trace else False,
            "final_score": best_trace.evaluation.score if best_trace else 0.0,
            "final_prompt": final_state.get("final_prompt", ""),
            "clip": final_state.get("clip", {}),
            "rounds": round_idx,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolve an AI video generation pipeline")
    parser.add_argument("task", type=Path, help="Path to a task YAML file")
    parser.add_argument("--max-rounds", type=int, default=3, help="Max evolution rounds")
    args = parser.parse_args()

    result = run(args.task, max_rounds=args.max_rounds)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
