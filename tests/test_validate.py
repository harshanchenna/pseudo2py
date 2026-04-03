"""Tests for syntax validation."""

from pseudo2py.validate import validate_syntax


def test_valid_python():
    result = validate_syntax("print('hello')\n")
    assert result.valid is True
    assert result.error is None


def test_invalid_python():
    result = validate_syntax("def foo(\n")
    assert result.valid is False
    assert result.error is not None


def test_invalid_reports_line():
    code = "x = 1\ny = 2\ndef broken(\n"
    result = validate_syntax(code)
    assert result.valid is False
    assert result.line is not None


def test_empty_string_is_valid():
    result = validate_syntax("")
    assert result.valid is True


def test_multiline_valid():
    code = "import os\n\ndef main():\n    print(os.getcwd())\n\nmain()\n"
    result = validate_syntax(code)
    assert result.valid is True


def test_unicode_valid():
    code = "msg = '你好世界'\nprint(msg)\n"
    result = validate_syntax(code)
    assert result.valid is True
