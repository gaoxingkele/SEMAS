"""AST-based structural tool mutation inspired by FunctionEvolve.

This module parses a Python tool function, extracts its return expression,
and generates structurally plausible variants by applying local AST edits
(e.g. replacing operators or perturbing constants). It does not depend on
the external FunctionEvolve repository.
"""

from __future__ import annotations

import ast
import copy
import random
from typing import Any

from semas.genome.genome import AgentGenome, ToolGenome
from semas.genome.repository import GenomeRepository
from semas.plugins.base import MutatorStrategy


class _ExpressionMutator(ast.NodeTransformer):
    """Generate local variants of an expression AST."""

    def __init__(self, max_candidates: int = 4, seed: int | None = None) -> None:
        self.max_candidates = max_candidates
        if seed is not None:
            random.seed(seed)

    def mutate(self, expr: ast.expr) -> list[ast.expr]:
        """Return a list of mutated copies of ``expr``."""
        candidates: list[ast.expr] = []

        # Operator substitution on BinOp nodes
        for node in ast.walk(expr):
            if isinstance(node, ast.BinOp):
                mutated = self._swap_operator(copy.deepcopy(expr), node)
                if mutated:
                    candidates.append(mutated)

        # Constant perturbation
        for node in ast.walk(expr):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                for delta in (0.5, -0.5, 2.0):
                    mutated = self._perturb_constant(copy.deepcopy(expr), node, delta)
                    if mutated:
                        candidates.append(mutated)

        # Name -> constant substitution (e.g. replace a variable with 1)
        for node in ast.walk(expr):
            if isinstance(node, ast.Name):
                mutated = self._replace_name_with_constant(copy.deepcopy(expr), node, 1.0)
                if mutated:
                    candidates.append(mutated)

        # Deduplicate by source text
        unique: list[ast.expr] = []
        seen: set[str] = set()
        for cand in candidates:
            src = ast.unparse(cand)
            if src not in seen:
                seen.add(src)
                unique.append(cand)
                if len(unique) >= self.max_candidates:
                    break
        return unique

    def _swap_operator(self, tree: ast.expr, target: ast.BinOp) -> ast.expr | None:
        """Swap the operator of ``target`` in ``tree``."""
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and self._same_node(node, target):
                swaps = {
                    ast.Add: [ast.Sub, ast.Mult],
                    ast.Sub: [ast.Add, ast.Mult],
                    ast.Mult: [ast.Add, ast.Div],
                    ast.Div: [ast.Mult, ast.Sub],
                }
                op_type = type(node.op)
                if op_type in swaps:
                    node.op = random.choice(swaps[op_type])()
                    return tree
        return None

    def _perturb_constant(
        self,
        tree: ast.expr,
        target: ast.Constant,
        factor: float,
    ) -> ast.expr | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and self._same_node(node, target):
                if isinstance(node.value, (int, float)):
                    node.value = node.value + factor if abs(factor) <= 1 else node.value * factor
                    return tree
        return None

    def _replace_name_with_constant(
        self,
        tree: ast.expr,
        target: ast.Name,
        value: float,
    ) -> ast.expr | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and self._same_node(node, target):
                node.id = "__const_placeholder__"
        # Replace placeholder with constant node
        class _Replacer(ast.NodeTransformer):
            def visit_Name(self, n: ast.Name) -> ast.AST:  # noqa: N802
                if n.id == "__const_placeholder__":
                    return ast.Constant(value=value)
                return n

        return _Replacer().visit(tree)

    @staticmethod
    def _same_node(a: ast.AST, b: ast.AST) -> bool:
        """Crude identity check based on AST dump."""
        return ast.dump(a, annotate_fields=False) == ast.dump(b, annotate_fields=False)


class FunctionEvolveToolMutator(MutatorStrategy):
    """Generate tool-code variants using AST local edits.

    This mutator looks at the tools referenced by ``agent.tools``, loads each
    tool source from the repository, and produces new AgentGenome candidates
    whose tool lists have been replaced with structurally mutated versions.
    """

    def __init__(self, max_candidates_per_tool: int = 3, seed: int | None = None) -> None:
        self.max_candidates_per_tool = max_candidates_per_tool
        self.seed = seed

    def mutate(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
        context: dict[str, Any],
    ) -> list[AgentGenome]:
        repo = context.get("repository")
        if not isinstance(repo, GenomeRepository):
            return []

        candidates: list[AgentGenome] = []
        for tool_name in agent.tools:
            try:
                tool = repo.load_tool(tool_name)
            except FileNotFoundError:
                continue

            variants = self._mutate_tool(tool)
            for idx, variant in enumerate(variants):
                variant.name = f"{tool.name}_fe_{idx + 1}"
                variant.version = 1
                repo.save_tool(variant)
                new_tools = list(agent.tools)
                new_tools[new_tools.index(tool_name)] = variant.name
                candidate = agent.evolve_from(
                    tools=new_tools,
                    meta={
                        **agent.meta,
                        "function_evolve": {
                            "parent_tool": tool.name,
                            "evolved_tool": variant.name,
                        },
                    },
                )
                candidates.append(candidate)

        return candidates

    def _mutate_tool(self, tool: ToolGenome) -> list[ToolGenome]:
        try:
            tree = ast.parse(tool.source_code)
        except SyntaxError:
            return []

        return_expr = self._extract_return_expression(tree)
        if return_expr is None:
            return []

        mutator = _ExpressionMutator(
            max_candidates=self.max_candidates_per_tool,
            seed=self.seed,
        )
        mutated_exprs = mutator.mutate(return_expr)

        variants: list[ToolGenome] = []
        for expr in mutated_exprs:
            new_source = self._replace_return_expression(tree, expr)
            variants.append(
                ToolGenome(
                    name="",
                    description=tool.description,
                    source_code=new_source,
                    signature=tool.signature,
                    dependencies=tool.dependencies,
                )
            )
        return variants

    @staticmethod
    def _extract_return_expression(tree: ast.Module) -> ast.expr | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Return) and stmt.value is not None:
                        return stmt.value
        return None

    @staticmethod
    def _replace_return_expression(tree: ast.Module, new_expr: ast.expr) -> str:
        new_tree = copy.deepcopy(tree)
        for node in ast.walk(new_tree):
            if isinstance(node, ast.FunctionDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Return) and stmt.value is not None:
                        stmt.value = new_expr
                        break
        return ast.unparse(new_tree)
