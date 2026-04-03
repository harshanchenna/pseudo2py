"""Tests for code extraction, filename detection, and requirements parsing."""

from pseudo2py.extract import extract_code, extract_filename, extract_requirements


class TestExtractCode:
    def test_fenced_python_block(self):
        text = "Here's the code:\n```python\nprint('hello')\n```\nDone."
        assert extract_code(text) == "print('hello')"

    def test_bare_fenced_block(self):
        text = "```\nprint('hello')\n```"
        assert extract_code(text) == "print('hello')"

    def test_no_fences_returns_full_text(self):
        text = "print('hello')"
        assert extract_code(text) == "print('hello')"

    def test_multiple_blocks_takes_first_python(self):
        text = "```python\nfirst()\n```\ntext\n```python\nsecond()\n```"
        assert extract_code(text) == "first()"

    def test_strips_whitespace(self):
        text = "```python\n\n  print('hi')\n\n```"
        assert extract_code(text) == "print('hi')"

    def test_multiline_code(self):
        text = "```python\nimport os\n\ndef main():\n    pass\n```"
        assert "import os" in extract_code(text)
        assert "def main():" in extract_code(text)


class TestExtractFilename:
    def test_filename_comment(self):
        text = "# filename: group_salaries.py\n```python\nprint(1)\n```"
        assert extract_filename(text) == "group_salaries.py"

    def test_case_insensitive(self):
        text = "# Filename: MyScript.py\ncode"
        assert extract_filename(text) == "MyScript.py"

    def test_no_filename_returns_default(self):
        text = "```python\nprint(1)\n```"
        assert extract_filename(text) == "output.py"

    def test_filename_with_extra_spaces(self):
        text = "#  filename:  sort_list.py\ncode"
        assert extract_filename(text) == "sort_list.py"

    def test_path_traversal_stripped(self):
        text = "# filename: ../../evil.py\ncode"
        assert extract_filename(text) == "evil.py"

    def test_absolute_path_stripped(self):
        text = "# filename: /etc/passwd.py\ncode"
        assert extract_filename(text) == "passwd.py"

    def test_nested_path_stripped(self):
        text = "# filename: src/utils/helper.py\ncode"
        assert extract_filename(text) == "helper.py"


class TestExtractRequirements:
    def test_simple_imports(self):
        code = "import pandas\nimport numpy\nprint('hi')"
        reqs = extract_requirements(code)
        assert "pandas" in reqs
        assert "numpy" in reqs

    def test_from_imports(self):
        code = "from sklearn.model_selection import train_test_split"
        reqs = extract_requirements(code)
        assert "scikit-learn" in reqs

    def test_stdlib_excluded(self):
        code = "import os\nimport sys\nimport json\nimport pandas"
        reqs = extract_requirements(code)
        assert reqs == ["pandas"]

    def test_known_mappings(self):
        code = "import cv2\nfrom PIL import Image\nimport yaml"
        reqs = extract_requirements(code)
        assert "opencv-python" in reqs
        assert "pillow" in reqs
        assert "pyyaml" in reqs

    def test_empty_code(self):
        assert extract_requirements("") == []

    def test_no_third_party(self):
        code = "import os\nimport sys"
        assert extract_requirements(code) == []

    def test_dotted_import(self):
        code = "import matplotlib.pyplot"
        reqs = extract_requirements(code)
        assert "matplotlib" in reqs

    def test_deduplication(self):
        code = "import pandas\nfrom pandas import DataFrame"
        reqs = extract_requirements(code)
        assert reqs.count("pandas") == 1

    def test_relative_imports_excluded(self):
        code = "from . import utils\nfrom .models import Foo\nimport pandas"
        reqs = extract_requirements(code)
        assert reqs == ["pandas"]
