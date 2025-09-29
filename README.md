# pydough-full

Welcome to the `pydough-full` project! This repository contains the `pydough-analytics` toolkit, a powerful system that turns natural language questions into safe, executable analytics.

It combines a custom Domain-Specific Language (DSL) called PyDough with Gemini-powered LLM prompting to create a seamless text-to-analytics workflow.

## Quick Start

1. **Clone and select the repo root**
   ```bash
   cd /path/to/pydough-ce
   ```
2. **Provision Python 3.11 (or any >=3.10) and a clean virtualenv**
   ```bash
   pyenv install 3.11.9
   pyenv local 3.11.9
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install the toolkit into the venv**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e pydough-analytics
   export PATH="$(pwd)/.venv/bin:$PATH"
   unalias pydough-analytics 2>/dev/null
   hash -r
   type -a pydough-analytics
   pydough-analytics --version
   ```
4. **Provide your Gemini API key**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
   (You can also place it in a `.env` file in the repo root.)
5. **Run the sample question against the bundled SQLite database**
   ```bash
   pydough-analytics --log-level DEBUG ask \
  "List the top 3 rows by the column 'amount' from the 'sales' table. Return only 'city' and 'amount', sorted by 'amount' in descending order." \
  --metadata metadata/live_sales.json \
  --graph-name SALES \
  --url sqlite:///metadata/live_sales.db \
  --show-sql --show-code
   ```
   The DEBUG line confirms the full prompt length being sent to Gemini; the output includes the generated PyDough, SQL, and result preview.
6. **(Optional) Run a live LLM smoke test from the repo root**
   ```bash
   python -m pip install pytest
   export PYDOUGH_ANALYTICS_RUN_LIVE=1
   python -m pytest -q pydough-analytics/tests/test_natural_language_live.py::test_live_sales_top_rows_natural
   ```
   This executes a single pytest marked `live_llm`, calling Gemini once via the bundled SQLite fixtures. If the test is skipped because the sample metadata is not found, create `pydough-analytics/metadata -> ../metadata` (symlink) or run the test from inside `pydough-analytics/`.

## What It Does

At its core, this project lets you ask questions of your relational database in plain English. The pipeline handles the heavy lifting:

1. **Generate Metadata** – Reflect your database schema into a PyDough knowledge graph.
2. **Ask a Question** – Phrase your analytics request in natural language (e.g., “Which cities have the highest sales?”).
3. **Translate to PyDough** – The LLM converts the question into the PyDough DSL, a declarative language purpose-built for analytics.
4. **Execute Safely** – PyDough compiles to SQL, runs against your database, and returns a tidy DataFrame.

## Key Features

- **Natural language interface** – Query data without writing SQL.
- **Automatic schema analysis** – Works with SQLite, PostgreSQL, MySQL, and Snowflake.
- **Safety by design** – PyDough limits execution to declarative analytics, reducing blast radius.
- **Developer friendly** – Includes a CLI, Python API, and optional MCP server.
- **Extensible** – Plug in custom prompts, LLM providers, or database connectors.

## Repository Structure

```
/ 
├── metadata/              # Sample metadata files.
├── pydough-analytics/     # Core Python package.
│   ├── src/               # Library source code.
│   ├── tests/             # Unit and integration tests.
│   ├── docs/              # Additional guides.
│   └── README.md          # In-depth package documentation.
└── README.md              # You are here!
```

## Getting Started

### Requirements

- Python 3.10 or newer (3.11 recommended).
- A Google Gemini API key available as `GEMINI_API_KEY`.
- (Optional) Additional database drivers if you target PostgreSQL, MySQL, or Snowflake.

### Configure the environment

If you skipped the “Quick Start” section, here is the full shell sequence again. Replace `/path/to/pydough-ce` with your clone path.

```bash
cd /path/to/pydough-ce
pyenv install 3.11.9
pyenv local 3.11.9
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e pydough-analytics
export PATH="$(pwd)/.venv/bin:$PATH"
unalias pydough-analytics 2>/dev/null
hash -r
pydough-analytics --version
```

Set your Gemini key (either in the shell or `.env`):

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### Run the sample question

```bash
pydough-analytics --log-level DEBUG ask \
  "List the top 3 rows by the column 'amount' from the 'sales' table. Return only 'city' and 'amount', sorted by 'amount' in descending order." \
  --metadata metadata/live_sales.json \
  --graph-name SALES \
  --url sqlite:///metadata/live_sales.db \
  --show-sql --show-code
```

This command exercises the full Community Edition pipeline: prompt building, Gemini invocation, PyDough execution, and result preview. For more usage examples (metadata generation, JSON output, module entry point), see [pydough-analytics/README.md](pydough-analytics/README.md).

## The PyDough DSL

PyDough is a Pythonic DSL designed for the LLM to emit—and for you to read—concise analytics logic. Typical patterns include filtering, aggregation, and ranking.

```python
# Top 3 sales by amount
result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())
```

Dive deeper in the [PyDough DSL Prompt Authoring Guide](pydough-analytics/docs/pydough-prompt-guide.md).

## Troubleshooting

### Python / virtualenv setup keeps finding the wrong CLI

If `pydough-analytics --version` reports “ModuleNotFoundError: No module named 'pydough_analytics'”, it usually means your shell is invoking an outdated console script. Reset the environment:

```bash
cd /path/to/pydough-ce
pyenv local 3.11.9
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -e pydough-analytics
export PATH="$(pwd)/.venv/bin:$PATH"
unalias pydough-analytics 2>/dev/null
hash -r
pydough-analytics --version
```

### Prompt looks “short” or empty

Enable debug logging to inspect the payload lengths sent to Gemini:

```bash
pydough-analytics --log-level DEBUG ask "List the top 3 rows..." --metadata metadata/live_sales.json --graph-name SALES --url sqlite:///metadata/live_sales.db
```

Look for `Gemini generate() with system len=..., user len=...`. If the lengths are non-zero, the prompt built correctly; adjust the question wording if Gemini returns invalid code.

### Pytest cannot find the live test file

When running from the repository root (`pydough-ce`):

```bash
python -m pip install pytest
export PYDOUGH_ANALYTICS_RUN_LIVE=1
python -m pytest -q pydough-analytics/tests/test_natural_language_live.py::test_live_sales_top_rows_natural
```

Ensure you are using the repo virtualenv (`which python` → `.venv/bin/python`). If you see the test skipped because metadata files are missing, create a symlink `ln -s ../metadata pydough-analytics/metadata` or run the command from within `pydough-analytics/` so the fixtures can locate the sample data.

## What’s Next?

We welcome ideas and contributions. Current focus areas include:

- Smarter schema trimming to send only the most relevant context.
- Few-shot prompt libraries tuned to analytics intents.
- Richer, error-aware retry strategies.
