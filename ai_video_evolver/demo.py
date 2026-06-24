"""Minimal deterministic demo of the AI Video Evolver.

The demo starts with a basic prompt engineer that does not enhance prompts.
After one evolution round, the prompt engineer learns to use cinematic
keywords, and the video quality score improves.
"""

from __future__ import annotations

from pathlib import Path

from ai_video_evolver.run_video_evolution import run


TASK_PATH = Path(__file__).parent / "examples" / "sample_task.yaml"


def main() -> int:
    print("=== AI Video Evolver Demo ===\n")
    result = run(TASK_PATH, max_rounds=3)

    print("\n=== Result ===")
    print(f"Passed: {result['passed']}")
    print(f"Final score: {result['final_score']:.3f}")
    print(f"Final prompt: {result['final_prompt']}")
    print(f"Clip metadata: {result['clip']}")

    if result["passed"]:
        print("\n[OK] Video pipeline evolved to meet quality threshold.")
    else:
        print("\n[~] Video pipeline improved but did not meet threshold.")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
