"""Syntax validation via the built-in compile()."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    error: str | None = None
    line: int | None = None


def validate_syntax(code: str) -> ValidationResult:
    """Check Python code for syntax errors without executing it.

    Uses the built-in compile() — no temp files, no .pyc side effects.
    """
    try:
        compile(code, "<pseudo2py>", "exec")
        return ValidationResult(valid=True)
    except SyntaxError as exc:
        return ValidationResult(
            valid=False,
            error=str(exc),
            line=exc.lineno,
        )
