# pydough-ce

Welcome to the `pydough-ce` project! This repository contains the `pydough-analytics` toolkit, a powerful system that turns natural language questions into safe, executable analytics.

It combines a custom Domain-Specific Language (DSL) called PyDough with Gemini-powered LLM prompting to create a seamless text-to-analytics workflow.

## Quick Start

1. **Clone and enter the repo root**

   ```bash
   git clone https://github.com/bodo-ai/pydough-ce.git
   cd pydough-ce
   ```

2. **Provision Python 3.11 (>=3.10 works) and a clean virtualenv**

   ```bash
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the toolkit into the venv**

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e pydough-analytics
   export PATH="$(pwd)/.venv/bin:$PATH"
   hash -r
   pydough-analytics --version
   ```

4. **Generate metadata JSON from a SQLite database**

   ```bash
   pydough-analytics generate-json \
      --engine sqlite \
      --database ./metadata/tpch.db \
      --graph-name TPCH \
      --json-path ./metadata/tpch_graph.json
   ```

   This introspects the bundled SQLite DB (metadata/tpch.db) and produces a PyDough V2 metadata graph as JSON (metadata/tpch_graph.json).

5. **Export Markdown docs from the metadata**

   ```bash
   pydough-analytics generate-md \
      --graph-name TPCH \
      --json-path ./metadata/tpch_graph.json \
      --md-path ./docs/tpch.md
   ```

   The Markdown file will contain a human-readable version of the metadata graph.

6. **(Optional) Run tests**

   ```bash
   python -m pip install pytest
   pytest -q pydough-analytics/tests
   ```

## What It Does

At its core, this project lets you ask questions of your relational database in plain English. The pipeline handles the heavy lifting:

1. **Generate Metadata** – Reflect your database schema into a PyDough knowledge graph.
2. **Ask a Question** – Phrase your analytics request in natural language (e.g., “Which cities have the highest sales?”).
3. **Translate to PyDough** – The LLM converts the question into the PyDough DSL, a declarative language purpose-built for analytics.
4. **Execute Safely** – PyDough compiles to SQL, runs against your database, and returns a tidy DataFrame.

## Key Features

- **Natural language interface** – Query data without writing SQL.
- **Automatic schema analysis** – Works with SQLite.
- **Safety by design** – PyDough limits execution to declarative analytics, reducing blast radius.
- **Developer friendly** – Includes a CLI, Python API.
- **Extensible** – Plug in custom prompts, LLM providers.

## Repository Structure

```
/ 
│
├── pydough-analytics/     # Core Python package.
│   ├── data/              # Sanmple metadata files.
│   ├── docs/              # Additional guides.
│   ├── samples/           # Sample code with notebooks.
│   ├── src/               # Library source code.
│   ├── tests/             # Unit and integration tests.
│   └── README.md          # In-depth package documentation.
└── README.md              # You are here!
```

## Getting Started

### Requirements

- Python 3.10 or newer (3.11 recommended).
- SQLite database file to introspect.
- Pydough 1.0.10 or newer.

### Configure the environment

   If you skipped the “Quick Start” section, here is the full shell sequence again. Replace /path/to/pydough-ce with your clone path.

   ```bash
   cd /path/to/pydough-ce
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e pydough-analytics
   export PATH="$(pwd)/.venv/bin:$PATH"
   hash -r
   pydough-analytics --version
   ```

### Generate metadata from SQLite

   Use the bundled sample database (metadata/live_sales.db) to generate a PyDough metadata graph in JSON:

   ```bash
   pydough-analytics generate-json \
      --engine sqlite \
      --database ./metadata/live_sales.db \
      --graph-name SALES \
      --json-path ./metadata/live_sales.json
  ```

   This inspects the SQLite file and creates a metadata graph definition under metadata/live_sales.json.

### Export Markdown docs

   Convert the generated JSON graph into Markdown documentation:

   ```bash
   pydough-analytics generate-md \
      --graph-name SALES \
      --json-path ./metadata/live_sales.json \
      --md-path ./docs/live_sales.md
   ```

   The Markdown file provides a human-friendly overview of the metadata: collections, properties, and relationships.

### Run the test suite (optional)

   ```bash
   python -m pip install pytest
   pytest -q pydough-analytics/tests
   ```

   With these steps you now have the full CE pipeline:
   SQLite DB → JSON metadata graph → Markdown documentation.

This command exercises the full Community Edition pipeline: prompt building, Gemini invocation, PyDough execution, and result preview. For more usage examples (metadata generation, JSON output, module entry point), see [pydough-analytics/README.md](pydough-analytics/README.md).

## The PyDough DSL

PyDough is a Pythonic DSL designed for the LLM to emit—and for you to read—concise analytics logic. Typical patterns include filtering, aggregation, and ranking.

```python
# Top 3 sales by amount
result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())
```

Dive deeper in the [PyDough DSL Prompt Authoring Guide](pydough-analytics/docs/pydough-prompt-guide.md).

## What’s Next?

We welcome ideas and contributions. Current focus areas include:

- New version with a mcp server.
- Support for more databases.
