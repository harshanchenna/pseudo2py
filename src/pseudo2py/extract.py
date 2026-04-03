"""Extract code blocks, filenames, and requirements from LLM output."""

from __future__ import annotations

import re
import sys


# Common import-name → pip-package mismatches.
IMPORT_TO_PACKAGE: dict[str, str] = {
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "gi": "PyGObject",
    "attr": "attrs",
    "serial": "pyserial",
    "usb": "pyusb",
    "wx": "wxPython",
    "Crypto": "pycryptodome",
    "jose": "python-jose",
    "magic": "python-magic",
    "dateutil": "python-dateutil",
}

# Standard library module names (Python 3.10+).
_STDLIB: frozenset[str] = frozenset(sys.stdlib_module_names)


def extract_code(text: str) -> str:
    """Extract Python code from LLM response.

    Tries fenced ```python blocks first, then bare ``` blocks,
    then returns the full text as a fallback.
    """
    # Fenced python block
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Bare fenced block
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # No fences — return full text stripped
    return text.strip()


def extract_filename(text: str) -> str:
    """Extract suggested filename from LLM output.

    Looks for `# filename: foo.py` convention. Falls back to `output.py`.
    """
    m = re.search(r"#\s*filename:\s*(\S+\.py)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return "output.py"


def extract_requirements(code: str) -> list[str]:
    """Extract third-party package names from import statements."""
    top_level_modules: set[str] = set()

    for line in code.splitlines():
        line = line.strip()

        # import foo / import foo.bar / import foo as f
        m = re.match(r"^import\s+([\w.]+)", line)
        if m:
            top_level_modules.add(m.group(1).split(".")[0])
            continue

        # from foo import bar / from foo.bar import baz
        m = re.match(r"^from\s+([\w.]+)\s+import", line)
        if m:
            top_level_modules.add(m.group(1).split(".")[0])

    # Filter to third-party only, map to pip names.
    packages: list[str] = []
    for mod in sorted(top_level_modules):
        if mod in _STDLIB:
            continue
        packages.append(IMPORT_TO_PACKAGE.get(mod, mod))

    return packages
