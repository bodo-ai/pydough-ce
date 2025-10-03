# pydough-ce

Welcome to the `pydough-ce` project! This repository contains the `pydough-analytics` toolkit, a powerful system that turns natural language questions into safe, executable analytics.

It combines a custom Domain-Specific Language (DSL) called PyDough with LLM-powered system to create a seamless text-to-analytics workflow.

# Getting Started

### Requirements

- Python 3.10 or newer (3.11 recommended).
- SQLite database file to introspect.
- PyDough 1.0.10 or newer.

### Configure the environment

Here is the full shell sequence. Replace `/path/to/pydough-ce` with your clone path.

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

### Provider credentials (.env or shell)

You can export credentials directly in your shell **or** keep them in a `.env` at the repo root.

**.env example (pick only what you use):**
```dotenv
# Anthropic via Vertex AI (Claude on Vertex)
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/gcp-key.json
GOOGLE_PROJECT_ID=your-gcp-project
GOOGLE_REGION=us-east5

# AWS Bedrock (Claude via AWS)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

**Load .env into your shell (bash/zsh):**
```bash
set -a; source .env; set +a
# or
export $(grep -v '^#' .env | xargs)
```

> The CLI reads environment variables from your shell. (Using Python, you can also auto-load `.env` by importing `pydough_analytics.config.env`.)

## **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → Databases  metadata  metadata_markdowns  prompts
 ```

### Default paths (data at `pydough-analytics` folder)

We keep project artifacts in **`./data/`** for consistency:
- **Database (SQLite):** `./data/Databases/TPCH.db`
- **Metadata JSON:** `./data/metadata/Tpch_graph.json`
- **Metadata Markdown:** `./data/metadata_markdowns/Tpch.md`

### Generate metadata from SQLite

```bash
pydough-analytics generate-json   --engine sqlite   --database ./data/Databases/TPCH.db   --graph-name TPCH   --json-path ./data/metadata/Tpch_graph.json
```

This inspects the SQLite file and creates a metadata graph definition under `data/metadata/Tpch_graph.json`.

### Export Markdown docs

```bash
pydough-analytics generate-md   --graph-name TPCH   --json-path ./data/metadata/Tpch_graph.json   --md-path ./data/metadata_markdowns/Tpch.md
```

The Markdown file provides a human-friendly overview of the metadata: collections, properties, and relationships.

### Ask the LLM (after generating JSON + Markdown)

Run natural-language questions on your dataset. The **PyDough code is always printed**; you can optionally include **SQL**, a **DataFrame** preview, and an **explanation**. The CE default is **Google / Gemini 2.5 Pro**.

```bash
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --engine sqlite   --database ./data/Databases/TPCH.db   --db-name TPCH   --md-path ./data/metadata_markdowns/Tpch.md   --kg-path ./data/metadata/Tpch_graph.json   --show-sql --show-df --show-explanation
```

Notes:
- `--db-name` should match the `--graph-name` used during metadata generation (here: `TPCH`).
- To switch providers (e.g., Anthropic), pass a valid provider/model for your integration:
  ```bash
  --provider anthropic --model claude-sonnet-4-5@20250929
  ```
- Use `--rows` to control how many DataFrame rows are displayed (default: 20).

### Run the test suite (optional)

```bash
python -m pip install pytest
pytest -q pydough-analytics/tests
```

With these steps you now have the full CE pipeline:
SQLite DB → JSON metadata graph → Markdown documentation → **LLM Ask**.

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

## The PyDough DSL

PyDough is a Pythonic DSL designed for the LLM to emit—and for you to read—concise analytics logic. Typical patterns include filtering, aggregation, and ranking.

```python
# Top 3 sales by amount
result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())
```
You can check the full PyDough repo and documentation here: https://github.com/bodo-ai/PyDough/tree/main

## What’s Next?

We welcome ideas and contributions. Current focus areas include:

- New version with a mcp server.
- Support for more databases.
