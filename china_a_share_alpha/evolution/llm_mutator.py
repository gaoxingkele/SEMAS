"""LLM-driven factor expression mutator.

Uses the SEMAS LLM client abstraction to ask a language model to propose a new
factor expression. If the response cannot be parsed, falls back to random
grammar-based mutation.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from semas.genome.genome import AgentGenome
from semas.mutator.mutator import Mutator
from semas.utils.llm_client import LLMClient, default_llm_client

from china_a_share_alpha.evolution.factor_mutator import (
    FactorMutator,
    _random_expression,
)
from china_a_share_alpha.factor.expression import FactorExpr, expr_from_dict, expr_to_dict
from china_a_share_alpha.factor.parser import parse_expression


class LLMFactorMutator(Mutator):
    """SEMAS Mutator that asks an LLM to generate a new factor expression."""

    SYSTEM_PROMPT = """You are a quantitative alpha factor engineer for China A-shares.
Generate a factor expression using ONLY the following DSL.

Functions:
- Unary: abs(x), log(x), sign(x), neg(x), cs_rank(x), cs_zscore(x)
- Binary: add(x,y), sub(x,y), mul(x,y), div(x,y), greater(x,y), less(x,y)
- Time-series: ts_mean(x,n), ts_std(x,n), ts_sum(x,n), ts_min(x,n), ts_max(x,n), ts_delta(x,n), ts_delay(x,n)
- Cross-series: ts_corr(x,y,n), ts_cov(x,y,n)

Variables: open, high, low, close, volume, vwap, return

Respond with ONLY the expression, no explanation, no markdown.
Example: neg(cs_rank(ts_mean(return, 5)))
"""

    def __init__(self, llm_client: LLMClient | None = None, seed: int | None = None):
        self.llm = llm_client or default_llm_client()
        self.fallback = FactorMutator(seed=seed, mode="gp")
        if seed is not None:
            random.seed(seed)

    @staticmethod
    def _get_expr(agent: AgentGenome) -> FactorExpr:
        expr_dict = agent.meta.get("factor_expression", {}).get("expr")
        if expr_dict is None:
            return _random_expression(max_depth=2)
        return expr_from_dict(expr_dict)

    @staticmethod
    def _set_expr(agent: AgentGenome, expr: FactorExpr) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        meta.setdefault("factor_expression", {})
        meta["factor_expression"]["expr"] = expr_to_dict(expr)
        meta["factor_expression"]["string"] = str(expr)
        return agent.evolve_from(meta=meta)

    def mutate_prompt(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        current_expr = self._get_expr(agent)
        user_prompt = (
            f"Current expression: {current_expr}\n"
            f"Recent issues: {failure_logs[:3]}\n"
            "Propose an improved or alternative expression using the DSL."
        )
        try:
            response = self.llm.complete(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=256,
            )
            # Try to extract the first code-like line.
            cleaned = response.strip().splitlines()[0].strip().strip("`")
            expr = parse_expression(cleaned)
            return self._set_expr(agent, expr)
        except Exception:
            return self.fallback.mutate_prompt(agent, failure_logs)

    def mutate_tool(self, agent: AgentGenome, failure_logs: list[str]) -> Any:
        return None

    def mutate_few_shot(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        return agent

    def mutate_topology(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        return agent
