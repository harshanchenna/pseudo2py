"""Syntax validation via py_compile."""

from __future__ import annotations

import py_compile
import tempfile
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    error: str | None = None
    line: int | None = None


def validate_syntax(code: str) -> ValidationResult:
    """Check Python code for syntax errors without executing it."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=True
    ) as f:
        f.write(code)
        f.flush()
        try:
            py_compile.compile(f.name, doraise=True)
            return ValidationResult(valid=True)
        except py_compile.PyCompileError as exc:
            line = None
            error_msg = str(exc)
            # Extract line number from the underlying SyntaxError.
            if exc.exc_value and hasattr(exc.exc_value, "lineno"):
                line = exc.exc_value.lineno
            elif exc.__cause__ and hasattr(exc.__cause__, "lineno"):
                line = exc.__cause__.lineno
            return ValidationResult(valid=False, error=error_msg, line=line)
