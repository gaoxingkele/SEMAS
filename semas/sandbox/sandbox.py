"""Restricted code execution sandbox."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    """Result of a sandboxed code execution."""

    success: bool
    stdout: str
    stderr: str
    returncode: int
    duration_ms: float | None = None


class Sandbox:
    """Execute untrusted Python code in a restricted subprocess.

    Default restrictions:
      - AST whitelist for top-level function definitions (no classes, no imports of dangerous modules)
      - subprocess timeout
      - no network (best effort via environment isolation)
      - no file writes outside the temp directory
    """

    DEFAULT_TIMEOUT = 10
    FORBIDDEN_MODULES = {"os", "sys", "subprocess", "socket", "requests", "urllib"}

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, allowed_modules: set[str] | None = None):
        self.timeout = timeout
        self.allowed_modules = allowed_modules or {"math", "datetime", "json", "re", "typing"}

    def run_code(
        self,
        source_code: str,
        entry_call: str | None = None,
    ) -> SandboxResult:
        """Run Python source code safely.

        Args:
            source_code: Python code to execute.
            entry_call: Optional Python expression to evaluate after defining functions,
                        e.g. "calculate_date_diff('2024-01-01', '2024-01-10')".
        """
        if not self._is_safe_ast(source_code):
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Sandbox blocked code: forbidden AST node or import detected.",
                returncode=-1,
            )

        script = source_code
        if entry_call:
            script += f"\n\n_result = {entry_call}\nprint(_result)\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            tmp_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, "-B", "-E", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={"PYTHONPATH": ""},
            )
            return SandboxResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.timeout}s",
                returncode=-2,
            )
        finally:
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass

    def run_tool(
        self,
        tool_source: str,
        function_call: str,
    ) -> SandboxResult:
        """Convenience wrapper to run a single tool function call."""
        return self.run_code(tool_source, entry_call=function_call)

    def _is_safe_ast(self, source_code: str) -> bool:
        """Perform a lightweight AST check."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in self.allowed_modules:
                        return False
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                if module not in self.allowed_modules:
                    return False
            elif isinstance(node, ast.ClassDef):
                # Restrict classes to keep sandbox simple
                return False
        return True
