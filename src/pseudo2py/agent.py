"""Agentic loop: LLM calls with tool use for pseudocode-to-Python conversion."""

from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from pseudo2py.config import Config
from pseudo2py.extract import extract_code, extract_filename, extract_requirements
from pseudo2py.prompts import SYSTEM_PROMPT, TOOLS
from pseudo2py.search import search
from pseudo2py.validate import validate_syntax

MAX_TOOL_ITERATIONS = 5
MAX_SYNTAX_RETRIES = 1


@dataclass
class AgentResult:
    code: str
    filename: str
    requirements: list[str]
    valid: bool
    error: str | None = None
    searches: list[str] | None = None


def run(pseudocode: str, config: Config, *, on_search: object = None) -> AgentResult:
    """Convert pseudocode to Python via an LLM agent loop.

    Args:
        pseudocode: Human-language description of desired code.
        config: Loaded and validated Config.
        on_search: Optional callback(query: str) called when a search is performed.

    Returns:
        AgentResult with generated code, filename, requirements, and validity.
    """
    client = OpenAI(
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
    )

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Convert this pseudocode to Python:\n\n{pseudocode}"},
    ]

    searches: list[str] = []
    iterations = 0

    while iterations < MAX_TOOL_ITERATIONS:
        iterations += 1

        response = client.chat.completions.create(
            model=config.llm.model,
            messages=messages,
            tools=TOOLS,
            max_tokens=4096,
        )

        choice = response.choices[0]

        # Handle tool calls.
        if choice.finish_reason == "tool_calls" or (
            choice.message.tool_calls and len(choice.message.tool_calls) > 0
        ):
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                if tool_call.function.name == "web_search":
                    import json
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                    searches.append(query)

                    if on_search:
                        on_search(query)

                    result = search(query, config.search)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
            continue

        # End turn — extract code from response.
        text = choice.message.content or ""
        return _finalize(text, config, client, messages, searches)

    # Exhausted iterations — try to extract whatever we have.
    last_text = ""
    if messages and messages[-1].get("content"):
        last_text = messages[-1]["content"]
    return _finalize(last_text, config, client, messages, searches)


def _finalize(
    text: str,
    config: Config,
    client: OpenAI,
    messages: list[dict],
    searches: list[str],
) -> AgentResult:
    """Extract code, validate, and retry once on syntax failure."""
    code = extract_code(text)
    filename = extract_filename(text)
    requirements = extract_requirements(code)

    result = validate_syntax(code)
    if result.valid:
        return AgentResult(
            code=code,
            filename=filename,
            requirements=requirements,
            valid=True,
            searches=searches or None,
        )

    # Retry once: send the syntax error back to the LLM.
    messages.append({"role": "assistant", "content": text})
    messages.append(
        {
            "role": "user",
            "content": (
                f"The generated code has a syntax error:\n{result.error}\n\n"
                "Please fix it and return the corrected code in a ```python block."
            ),
        }
    )

    response = client.chat.completions.create(
        model=config.llm.model,
        messages=messages,
        max_tokens=4096,
    )

    retry_text = response.choices[0].message.content or ""
    code = extract_code(retry_text)
    filename = extract_filename(retry_text) if extract_filename(retry_text) != "output.py" else filename
    requirements = extract_requirements(code)

    result = validate_syntax(code)
    return AgentResult(
        code=code,
        filename=filename,
        requirements=requirements,
        valid=result.valid,
        error=result.error if not result.valid else None,
        searches=searches or None,
    )
