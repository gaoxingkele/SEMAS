"""Meta-evolution loop for the SEMAS framework itself.

This script treats the framework configuration in
`framework_genome/framework_config_v1.yaml` as an `AgentGenome`. It runs the
downstream benchmark, and when tasks fail it deterministically mutates the
framework genome. The evolved genomes are archived under `archive/`.

This is a Phase-3 scaffold: the mutations are rule-based rather than LLM-driven,
so it can run without API keys while demonstrating the self-upgrade loop.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from semas.genome.genome import AgentGenome


BENCH_DIR = Path(__file__).parent
FRAMEWORK_GENOME_PATH = BENCH_DIR / "framework_genome" / "framework_config_v1.yaml"
ARCHIVE_DIR = BENCH_DIR / "archive"
TARGET_PASS_RATE = 1.0
MAX_META_ROUNDS = 5


def load_framework_genome() -> AgentGenome:
    data = yaml.safe_load(FRAMEWORK_GENOME_PATH.read_text(encoding="utf-8"))
    return AgentGenome(**data)


def save_framework_genome(genome: AgentGenome, suffix: str) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / f"framework_config_{suffix}.yaml"
    path.write_text(yaml.safe_dump(genome.model_dump(), sort_keys=False), encoding="utf-8")
    return path


def run_benchmark() -> dict[str, Any]:
    """Run the downstream benchmark and return the JSON report."""
    cmd = [
        sys.executable,
        "-m",
        "benchmarks.semas_self_upgrade.run_benchmark",
        "--json",
    ]
    result = subprocess.run(
        cmd,
        cwd=BENCH_DIR.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    # The JSON report is the last line of stdout.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"Benchmark produced no output: {result.stderr}")
    return json.loads(lines[-1])


def mutate_framework_genome(
    genome: AgentGenome,
    report: dict[str, Any],
) -> AgentGenome | None:
    """Apply deterministic meta-mutations based on benchmark failures."""
    failed_tasks = {r["task_id"] for r in report["task_results"] if not r["passed"]}
    if not failed_tasks:
        return None

    meta = dict(genome.meta)
    changed = False

    if "math_tool_evolution_v1" in failed_tasks:
        modules = set(meta["sandbox_policy"]["allowed_modules"])
        if "datetime" not in modules:
            modules.add("datetime")
            meta["sandbox_policy"]["allowed_modules"] = sorted(modules)
            changed = True
        # Make the framework more eager to evolve tools.
        if meta["trigger_policy"]["cooldown_tasks"] > 0:
            meta["trigger_policy"]["cooldown_tasks"] -= 1
            changed = True

    if "plugin_convergence_v1" in failed_tasks:
        if not meta["plugin_policy"]["enable_function_evolve"]:
            meta["plugin_policy"]["enable_function_evolve"] = True
            changed = True

    if "sandbox_safety_v1" in failed_tasks:
        # If safety fails, tighten rather than loosen: make sure os/sys are not
        # in the allowed list (they shouldn't be, but this is a defensive mutation).
        modules = set(meta["sandbox_policy"]["allowed_modules"])
        for forbidden in ("os", "sys", "subprocess"):
            modules.discard(forbidden)
        meta["sandbox_policy"]["allowed_modules"] = sorted(modules)
        changed = True

    if not changed:
        # Fallback: bump max_versions_without_improvement to give more chances.
        meta["trigger_policy"]["max_versions_without_improvement"] += 1
        changed = True

    new_genome = genome.evolve_from(meta=meta)
    return new_genome if changed else None


def main() -> int:
    print("=== SEMAS Self-Upgrade Meta-Evolution ===\n")

    genome = load_framework_genome()
    save_framework_genome(genome, "v1_seed")

    for round_idx in range(1, MAX_META_ROUNDS + 1):
        print(f"--- Meta round {round_idx} ---")
        report = run_benchmark()
        pass_rate = report["pass_rate"]
        print(f"Benchmark pass rate: {pass_rate:.2f}")

        if pass_rate >= TARGET_PASS_RATE:
            print("\n[OK] Target pass rate reached. Stopping meta-evolution.")
            save_framework_genome(genome, f"v{genome.version}_final")
            return 0

        new_genome = mutate_framework_genome(genome, report)
        if new_genome is None:
            print("\n[~] No applicable framework mutation. Stopping.")
            return 0

        genome = new_genome
        saved = save_framework_genome(genome, f"v{genome.version}_round{round_idx}")
        print(f"Evolved framework genome saved to: {saved}")

    print("\n[~] Max meta-evolution rounds reached.")
    save_framework_genome(genome, f"v{genome.version}_final")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
