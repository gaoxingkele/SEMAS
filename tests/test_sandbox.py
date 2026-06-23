"""Tests for the sandbox."""

import pytest

from semas.sandbox.sandbox import Sandbox


def test_run_simple_function():
    sandbox = Sandbox()
    code = "def add(a, b):\n    return a + b\n"
    result = sandbox.run_tool(code, "add(2, 3)")
    assert result.success
    assert "5" in result.stdout


def test_forbidden_import_blocked():
    sandbox = Sandbox()
    code = "import os\nprint(os.getcwd())\n"
    result = sandbox.run_code(code)
    assert not result.success
    assert "blocked" in result.stderr.lower()


def test_timeout():
    sandbox = Sandbox(timeout=1)
    code = "while True:\n    pass\n"
    result = sandbox.run_code(code)
    assert not result.success
    assert "timed out" in result.stderr.lower()


def test_allowed_module():
    sandbox = Sandbox(allowed_modules={"datetime"})
    code = (
        "from datetime import datetime\n"
        "def diff_days(a, b):\n"
        "    return (datetime.strptime(b, '%Y-%m-%d') - datetime.strptime(a, '%Y-%m-%d')).days\n"
    )
    result = sandbox.run_tool(code, "diff_days('2024-01-01', '2024-01-10')")
    assert result.success
    assert "9" in result.stdout
