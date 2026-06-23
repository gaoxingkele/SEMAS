"""Tests for the evaluator."""

import pytest

from semas.evaluator.evaluator import Evaluator


def test_exact_match_default_metric():
    evaluator = Evaluator(threshold=1.0)
    result = evaluator.evaluate({"output": "42"}, {"output": "42"})
    assert result.passed
    assert result.score == 1.0


def test_exact_match_failure():
    evaluator = Evaluator(threshold=1.0)
    result = evaluator.evaluate({"output": "41"}, {"output": "42"})
    assert not result.passed
    assert result.score == 0.0


def test_custom_metric_and_weights():
    evaluator = Evaluator(threshold=0.5)
    evaluator.register_metric("length", lambda r, e: 1.0 if len(r["output"]) > 2 else 0.0)
    result = evaluator.evaluate({"output": "hello"}, weights={"length": 1.0})
    assert result.passed
    assert result.score == 1.0


def test_threshold_comparison_tolerates_float_boundary():
    evaluator = Evaluator(threshold=0.9)
    evaluator.register_metric("a", lambda r, e: 1.0)
    evaluator.register_metric("b", lambda r, e: 1.0)
    evaluator.register_metric("c", lambda r, e: 0.9)
    evaluator.register_metric("d", lambda r, e: 1.0)
    evaluator.register_metric("e", lambda r, e: 0.5)
    evaluator.register_metric("f", lambda r, e: 1.0)
    result = evaluator.evaluate({"output": "ok"})
    assert result.score == pytest.approx(0.9)
    assert result.passed


def test_regression_suite():
    evaluator = Evaluator(threshold=1.0)
    evaluator.register_metric("eq", lambda r, e: 1.0 if r["output"] == e["output"] else 0.0)
    evaluator.add_regression_test("t1", {"x": 1}, {"output": "1"})
    evaluator.add_regression_test("t2", {"x": 2}, {"output": "2"})

    def executor(input_data):
        return {"output": str(input_data["x"])}

    all_passed, results = evaluator.run_regression_suite(executor)
    assert all_passed
    assert len(results) == 2
