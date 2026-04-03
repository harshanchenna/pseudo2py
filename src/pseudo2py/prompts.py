"""System prompt and tool definitions for the agent loop."""

SYSTEM_PROMPT = """\
You are a Python code generator. You receive pseudocode written in plain \
English and convert it to clean, runnable Python code.

Rules:
- Output the final Python code in a single ```python fenced block.
- Include all necessary imports at the top.
- Use the web_search tool when you need to look up a package's API, find \
the right package for a task, or verify usage patterns.
- Keep the code minimal — implement exactly what was asked, nothing more.
- Add a comment on the first line: # filename: descriptive_name.py
- After the code block, list any third-party packages needed on a line like:
  # requires: pandas, matplotlib
- The code must be directly runnable with no modifications.
- Prefer standard library when possible, but use third-party packages when \
they're clearly the right tool.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for Python package documentation, usage "
                "examples, or API references. Use this when you're unsure "
                "about a package's API or need to find the right package."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query, e.g. 'pandas read_csv documentation' "
                            "or 'python library for PDF generation'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    }
]
