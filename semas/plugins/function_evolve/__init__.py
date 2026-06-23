"""FunctionEvolve-style plugin for SEMAS.

Provides a structure-aware tool mutator and a numeric-constant optimizer that
operate directly on Python ASTs. This is a minimal, dependency-free
implementation of the ideas in:

    FunctionEvolve: Structure-Guided Symbolic Regression with LLMs
    arXiv:2606.07704, https://github.com/Phoinikas03/FunctionEvolve
"""

from __future__ import annotations

from semas.plugins.function_evolve.ast_tool_mutator import FunctionEvolveToolMutator
from semas.plugins.function_evolve.optimizer import FunctionEvolveToolOptimizer

__all__ = [
    "FunctionEvolveToolMutator",
    "FunctionEvolveToolOptimizer",
]
