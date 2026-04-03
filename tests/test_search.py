"""Tests for web search tool."""

from unittest.mock import MagicMock, patch

import pytest

from pseudo2py.config import SearchConfig
from pseudo2py.search import _format_results, search


def test_format_results():
    results = [
        ("Title 1", "https://example.com/1", "Snippet 1"),
        ("Title 2", "https://example.com/2", "Snippet 2"),
    ]
    formatted = _format_results(results)
    assert "1. Title 1" in formatted
    assert "https://example.com/1" in formatted
    assert "2. Title 2" in formatted


def test_format_results_empty():
    assert _format_results([]) == ""


def test_search_routes_to_brave():
    config = SearchConfig(provider="brave", brave_api_key="test-key")
    with patch("pseudo2py.search._brave_search", return_value="brave results") as mock:
        result = search("pandas groupby", config)
        mock.assert_called_once_with("pandas groupby", "test-key", max_results=5)
        assert result == "brave results"


def test_search_routes_to_ddg():
    config = SearchConfig(provider="duckduckgo")
    with patch("pseudo2py.search._ddg_search", return_value="ddg results") as mock:
        result = search("pandas groupby", config)
        mock.assert_called_once_with("pandas groupby", max_results=5)
        assert result == "ddg results"


def test_brave_search_mocked():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "web": {
            "results": [
                {
                    "title": "pandas docs",
                    "url": "https://pandas.pydata.org",
                    "description": "pandas is a data analysis library",
                }
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pseudo2py.search.httpx.get", return_value=mock_response):
        from pseudo2py.search import _brave_search

        result = _brave_search("pandas", "fake-key")
        assert "pandas docs" in result
        assert "pandas.pydata.org" in result


def test_brave_search_no_results():
    mock_response = MagicMock()
    mock_response.json.return_value = {"web": {"results": []}}
    mock_response.raise_for_status = MagicMock()

    with patch("pseudo2py.search.httpx.get", return_value=mock_response):
        from pseudo2py.search import _brave_search

        result = _brave_search("nonexistent", "fake-key")
        assert result == "No results found."
