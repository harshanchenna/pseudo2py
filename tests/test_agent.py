"""Tests for the agent loop with mocked LLM responses."""

from unittest.mock import MagicMock, patch

from pseudo2py.agent import AgentResult, run
from pseudo2py.config import Config, LLMConfig, SearchConfig


def _make_config() -> Config:
    return Config(
        llm=LLMConfig(base_url="http://localhost:8000/v1", model="test-model"),
        search=SearchConfig(provider="duckduckgo"),
    )


def _mock_response(content: str, tool_calls=None, finish_reason="stop"):
    """Build a mock OpenAI chat completion response."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls or []

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason

    response = MagicMock()
    response.choices = [choice]
    return response


def _mock_tool_call(call_id: str, name: str, arguments: str):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


class TestAgentRun:
    @patch("pseudo2py.agent.OpenAI")
    def test_simple_generation(self, mock_openai_cls):
        """LLM returns code directly with no tool calls."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        code_response = _mock_response(
            "# filename: hello.py\n```python\nprint('hello world')\n```"
        )
        mock_client.chat.completions.create.return_value = code_response

        result = run("print hello world", _make_config())

        assert result.valid is True
        assert result.code == "print('hello world')"
        assert result.filename == "hello.py"
        assert result.requirements == []
        assert result.searches is None

    @patch("pseudo2py.agent.search")
    @patch("pseudo2py.agent.OpenAI")
    def test_with_tool_call(self, mock_openai_cls, mock_search):
        """LLM calls web_search before generating code."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_search.return_value = "1. pandas docs\n   https://pandas.pydata.org"

        # First call: tool use
        tool_call = _mock_tool_call("tc1", "web_search", '{"query": "pandas read_csv"}')
        tool_response = _mock_response("", tool_calls=[tool_call], finish_reason="tool_calls")

        # Second call: code generation
        code_response = _mock_response(
            "# filename: read_csv.py\n```python\nimport pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df)\n```"
        )

        mock_client.chat.completions.create.side_effect = [tool_response, code_response]

        searches = []
        result = run("read a csv file", _make_config(), on_search=lambda q: searches.append(q))

        assert result.valid is True
        assert "pandas" in result.code
        assert result.filename == "read_csv.py"
        assert "pandas" in result.requirements
        assert result.searches == ["pandas read_csv"]
        assert searches == ["pandas read_csv"]

    @patch("pseudo2py.agent.OpenAI")
    def test_syntax_retry(self, mock_openai_cls):
        """LLM produces invalid code, gets retry, fixes it."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # First response: invalid syntax
        bad_response = _mock_response(
            "# filename: broken.py\n```python\ndef foo(\n```"
        )
        # Retry response: fixed
        good_response = _mock_response(
            "# filename: fixed.py\n```python\ndef foo():\n    pass\n```"
        )

        mock_client.chat.completions.create.side_effect = [bad_response, good_response]

        result = run("define a function foo", _make_config())

        assert result.valid is True
        assert "def foo():" in result.code
        assert mock_client.chat.completions.create.call_count == 2

    @patch("pseudo2py.agent.OpenAI")
    def test_syntax_retry_still_invalid(self, mock_openai_cls):
        """LLM fails twice — result marked invalid with error."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        bad_response = _mock_response("```python\ndef foo(\n```")
        still_bad = _mock_response("```python\ndef bar(\n```")

        mock_client.chat.completions.create.side_effect = [bad_response, still_bad]

        result = run("broken code", _make_config())

        assert result.valid is False
        assert result.error is not None
