# AGENTS.md

Guide for coding agents (Claude Code, Codex, etc.) and human contributors working in this repo.

## What this is

pseudo2py turns plain-English pseudocode into a runnable Python file: an LLM agent loop that
generates code, can search the web for unfamiliar packages, validates syntax, and writes the
result plus a `requirements.txt`. Talks to any OpenAI-compatible LLM endpoint (vLLM, Ollama,
LM Studio, OpenAI, Together AI, etc.) — no bundled model.

## How to navigate it

- `src/pseudo2py/cli.py` — Click-based CLI entry point (`pseudo2py` command); handles argument
  parsing, including treating unrecognized args as pseudocode input.
- `src/pseudo2py/agent.py` — the generate → search → validate loop.
- `src/pseudo2py/config.py` — config resolution (CLI flags > env vars > config file > defaults);
  `~/.config/pseudo2py/config.toml` is the default config location.
- `src/pseudo2py/search.py` — web search for unfamiliar packages (DuckDuckGo or Brave).
- `src/pseudo2py/extract.py` — pulls code + inferred requirements out of the LLM's response.
- `src/pseudo2py/validate.py` — syntax validation of generated code.
- `src/pseudo2py/prompts.py` — the prompts sent to the LLM.
- `tests/` — one test module per `src/pseudo2py/*.py` file; mirror that layout for new modules.

## Build, test, lint

```bash
uv sync --extra dev     # install runtime + dev (pytest) deps
uv run pytest -q        # run the test suite (verified: 48 tests, all passing)
```

There is no linter configured yet. Match the existing style (type-hinted dataclasses, `from
__future__ import annotations`) in the file you're editing.

## Standards this repo owns

- New modules get a matching `tests/test_<module>.py`; `pytest.ini_options.testpaths` is `tests/`.
- Config changes must respect the existing resolution order (CLI > env > file > defaults) in
  `config.py` — don't add a fifth source or reorder the existing ones.
- Keep the LLM client OpenAI-compatible-only; don't hardcode a specific provider's SDK.

## PR, review, and commit rules

- Branch → PR → full `/code-review` before merge.
- Merge commits, not squash.
- No `Co-Authored-By` or other AI-attribution lines in commits.
- Secrets (LLM API keys, `BRAVE_API_KEY`) live only in `.env` or the user's local
  `~/.config/pseudo2py/config.toml` (both outside this repo), never committed.

Keep this file and the README current when structure or commands change.
