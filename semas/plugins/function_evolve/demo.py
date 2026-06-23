"""Standalone demo: evolve a symbolic expression tool with FunctionEvolve plugin.

The demo sets up a temporary genome repository, seeds an agent with an
initially wrong formula, and uses the FunctionEvolve plugin to discover the
correct formula ``2 * x`` from input-output samples.
"""

from __future__ import annotations

import math
import shutil
import tempfile
from pathlib import Path

from semas.genome.genome import AgentGenome, ToolGenome
from semas.genome.repository import GenomeRepository
from semas.plugins.function_evolve.ast_tool_mutator import FunctionEvolveToolMutator
from semas.plugins.function_evolve.optimizer import FunctionEvolveToolOptimizer


TARGET_SAMPLES = [
    (0.0, 0.0),
    (1.0, 2.0),
    (2.0, 4.0),
    (3.0, 6.0),
    (-1.0, -2.0),
]

INITIAL_TOOL_SOURCE = """def my_formula(x):
    return x * 1
"""


def main() -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="semas_function_evolve_demo_"))

    def fitness_fn(candidate: AgentGenome) -> float:
        """Score a candidate by inverse MSE against target samples."""
        tool_name = candidate.tools[0]
        try:
            tool = repo.load_tool(tool_name)
        except FileNotFoundError:
            return 0.0

        namespace: dict = {}
        try:
            exec(tool.source_code, namespace)  # noqa: S102
        except Exception:  # noqa: BLE001
            return 0.0

        func = namespace.get("my_formula")
        if not callable(func):
            return 0.0

        errors = []
        for x, y_true in TARGET_SAMPLES:
            try:
                y_pred = float(func(x))
            except Exception:  # noqa: BLE001
                return 0.0
            errors.append((y_pred - y_true) ** 2)

        mse = sum(errors) / len(errors)
        return 1.0 / (1.0 + math.sqrt(mse))

    try:
        repo = GenomeRepository(tmp_dir)

        # Seed tool and agent
        tool = ToolGenome(
            name="my_formula",
            description="A formula to fit the data",
            source_code=INITIAL_TOOL_SOURCE,
        )
        repo.save_tool(tool)

        agent = AgentGenome(
            name="formula_agent",
            role="symbolic_regressor",
            system_prompt="Find the formula that fits the data.",
            tools=[tool.name],
        )
        repo.save_agent(agent)

        context = {
            "repository": repo,
            "fitness_fn": fitness_fn,
        }

        # Phase 1: structural mutation (keep the original agent as a baseline)
        mutator = FunctionEvolveToolMutator(max_candidates_per_tool=6, seed=42)
        candidates = mutator.mutate(agent, failure_logs=["formula misfit"], context=context)
        candidates.insert(0, agent)
        print(f"[Mutator] generated {len(candidates) - 1} structural variants")

        # Phase 2: constant optimization
        optimizer = FunctionEvolveToolOptimizer(seed=42)
        optimized = [optimizer.optimize(c, context) for c in candidates]

        # Phase 3: selection
        best = max(optimized, key=fitness_fn)
        best_score = fitness_fn(best)

        best_tool_name = best.tools[0]
        best_tool = repo.load_tool(best_tool_name)

        print("\n=== Best evolved tool ===")
        print(best_tool.source_code)
        print(f"Fitness score: {best_score:.4f}")

        if best_score > 0.95:
            print("\n[OK] Demo converged to a high-fitness formula.")
        else:
            print("\n[~] Demo improved the formula but did not fully converge.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
