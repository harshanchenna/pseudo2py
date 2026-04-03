# pseudo2py

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A whiteboard that comes to life. Write pseudocode in plain English, get runnable Python back.

## Quick Start

```bash
# Install
pip install git+https://github.com/harshanchenna/pseudo2py.git

# Set up config (LLM endpoint + search)
pseudo2py init
# Edit ~/.config/pseudo2py/config.toml with your LLM endpoint

# Run
pseudo2py "read a csv, group by department, plot average salary as a bar chart"
```

## What It Does

You describe what you want in human language — like you would on a whiteboard — and pseudo2py hands you back a working Python file with dependencies listed.

The agent can search the web to learn about packages it doesn't know, validates the generated code for syntax errors, and auto-names the output file.

```
$ pseudo2py "read a csv, group by department, plot average salary as a bar chart"

 ── pseudo2py ──────────────────
   Searching: "pandas groupby bar chart matplotlib"
   Generating code...

   1 │ # filename: group_salaries.py
   2 │ import pandas as pd
   3 │ import matplotlib.pyplot as plt
   4 │
   5 │ df = pd.read_csv("data.csv")
   6 │ avg = df.groupby("department")["salary"].mean()
   7 │ avg.plot(kind="bar")
   8 │ plt.ylabel("Average Salary")
   9 │ plt.title("Average Salary by Department")
  10 │ plt.tight_layout()
  11 │ plt.savefig("output.png")
  12 │ plt.show()

   Saved: ./group_salaries.py
   Saved: ./requirements.txt (pandas, matplotlib)
```

## Install

**With pip:**
```bash
pip install git+https://github.com/harshanchenna/pseudo2py.git
```

**With uv:**
```bash
uv pip install git+https://github.com/harshanchenna/pseudo2py.git
```

**From source:**
```bash
git clone https://github.com/harshanchenna/pseudo2py.git
cd pseudo2py
pip install -e .
```

## Configuration

Run `pseudo2py init` to create a config file at `~/.config/pseudo2py/config.toml`:

```toml
[llm]
base_url = "http://localhost:8000/v1"   # OpenAI-compatible endpoint
model = "meta-llama/Llama-3-70B"        # Model name
api_key = "not-needed"                  # Optional

[search]
provider = "duckduckgo"                 # "brave" or "duckduckgo"
brave_api_key = ""                      # Required if provider = "brave"

[output]
save_dir = "."                          # Where to save generated files
```

### LLM Backend

pseudo2py uses the OpenAI-compatible API format. Any backend that serves this format works:

| Backend | base_url example |
|---------|-----------------|
| vLLM | `http://localhost:8000/v1` |
| Ollama | `http://localhost:11434/v1` |
| LM Studio | `http://localhost:1234/v1` |
| OpenAI | `https://api.openai.com/v1` |
| Together AI | `https://api.together.xyz/v1` |

### Config Resolution

Values are resolved in this order (first wins):

1. CLI flags
2. Environment variables (`PSEUDO2PY_BASE_URL`, `PSEUDO2PY_MODEL`, `PSEUDO2PY_API_KEY`, `PSEUDO2PY_SEARCH_PROVIDER`, `BRAVE_API_KEY`)
3. Config file
4. Defaults

## Usage

### As an argument
```bash
pseudo2py "sort a list of dicts by the 'age' key"
```

### From a file
```bash
pseudo2py -f sketch.txt
```

### From stdin
```bash
echo "fibonacci sequence up to n" | pseudo2py
```

### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--file` | `-f` | Read pseudocode from a file |
| `--output` | `-o` | Override output filename |
| `--config` | `-c` | Custom config file path |
| `--no-save` | | Print code only, don't save files |
| `--quiet` | `-q` | Raw code output, no formatting (pipeable) |

### Quiet mode (pipe-friendly)

```bash
pseudo2py -q "hello world" > hello.py
pseudo2py -q "parse json from stdin" | python3
```

## How It Works

1. Your pseudocode is sent to the configured LLM with a system prompt for Python code generation
2. If the LLM needs info about a package, it searches the web (Brave or DuckDuckGo)
3. The LLM's response is parsed for code blocks, filename suggestions, and import statements
4. Generated code is syntax-validated; if invalid, the LLM gets one retry with the error
5. Output is displayed with syntax highlighting and saved to disk with a `requirements.txt`

## License

MIT
