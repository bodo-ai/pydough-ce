# Quickstart

## Installation

  ```bash
  # From source (development mode)
  cd pydough-analytics && pip install -e .

  # Or from PyPI (when published)
  pip install pydough-analytics
  ```

## Command reference

```bash
pydough-analytics --help
pydough-analytics generate-json --help
pydough-analytics generate-md --help
pydough-analytics ask --help
```

## **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → Databases  metadata  metadata_markdowns  prompts
 ```

## Generating metadata (sample)

Generate a PyDough metadata graph in JSON from the bundled SQLite database:

  ```bash
  pydough-analytics generate-json \
    --engine sqlite \
    --database ./data/metadata/live_sales.db \
    --graph-name SALES \
    --json-path ./data/metadata/live_sales.json
  ```

- Supported now: SQLite (local files or in-memory).
- Planned: PostgreSQL, MySQL, Snowflake.
- The --graph-name flag is required to name your graph.
- The CLI will create output directories if they don’t exist.

## Exporting documentation (Markdown)

Convert the generated JSON metadata into a human-readable Markdown file:

  ```bash
  pydough-analytics generate-md \
    --graph-name SALES \
    --json-path ./data/metadata/live_sales.json \
    --md-path ./data/metadata_markdowns/live_sales.md
  ```

The Markdown output will include the collections, properties, and relationships of the graph.

## Python API (programmatic usage)

You can also call the generators directly from Python:

```python
from pathlib import Path
from pydough_analytics.commands.generate_json_cmd import generate_metadata_from_config
from pydough_analytics.utils.storage.file_service import load_json, save_markdown
from pydough_analytics.schema.markdown import generate_markdown

# Generate JSON metadata from SQLite
metadata = generate_metadata_from_config(
    engine="sqlite",
    database=".data/metadata/live_sales.db",
    graph_name="SALES",
    json_path=".data/metadata/live_sales.json"
)

# Reload the JSON metadata (optional)
metadata_loaded = load_json(Path(".data/metadata/live_sales.json"))

# Convert metadata to Markdown
md_content = generate_markdown(metadata_loaded, graph_name="SALES")

# Save Markdown to file
save_markdown(".data/metadata_markdowns/live_sales.md", md_content)

print(" Metadata JSON and Markdown generated successfully!")
```

This gives you the same workflow as the CLI:
Database → Metadata JSON → Markdown docs.

---

## Ask questions with an LLM

Natural language → PyDough code (+ optional SQL / DataFrame / explanation).

### Provider credentials

Set credentials for your chosen provider. Examples:

**Gemini and Anthropic via Vertex AI**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/cred.json"
export GOOGLE_API_KEY:=...
export GOOGLE_PROJECT_ID="your-gcp-project"
export GOOGLE_REGION="us-east5"
```

**AWS Bedrock (Claude via AWS)**
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

> If you use a `.env`, importing `pydough_analytics.config.env` in Python will auto-load it.  
> The CLI uses your shell environment.

### CLI usage

The **code is always printed**. You can optionally show SQL, a table (DataFrame), and an explanation.

```bash
pydough-analytics ask   --question "What are the most common transaction statuses and their respective counts?"   --engine sqlite   --database ./metadata/live_sales.db   --db-name SALES   --md-path .data/metadata_markdowns/live_sales.md   --kg-path .data/metadata/live_sales.json   --provider anthropic   --model claude-sonnet-4-5@20250929   --show-sql --show-df --show-explanation
```

Flags summary

- `--provider`, `--model` are optional if you stay on client defaults (Google/Gemini 2.5 Pro).  
  If you switch to **Anthropic**, pass a **valid model** for that provider.
- `--show-sql`, `--show-df`, `--show-explanation` are optional (code is always printed).
- `--rows` controls how many table rows are displayed (default: 20).

### Python API (ask programmatic)

```python
from pydough_analytics.llm.llm_client import LLMClient

client = LLMClient(
    # If you rely on defaults (Google/Gemini 2.5 Pro), omit provider/model.
    # Example: Claude via Vertex AI
    provider="anthropic",
    model="claude-sonnet-4-5@20250929",
)

result = client.ask(
    question="What are the most common transaction statuses and their respective counts?",
    kg_path="./data/metadata/live_sales.json",                 # Knowledge Graph JSON
    md_path="./data/metadata_markdowns/live_sales.md",         # Markdown doc for the DB
    db_name="SALES",
    db_config={"engine": "sqlite", "database": "./metadata/live_sales.db"},
)

print("PyDough code:
", result.code)            # always available
print("SQL:
", result.sql or "<no sql>")
if result.df is not None:
    print(result.df.head())
print("Explanation:
", result.full_explanation or "<no explanation>")
print("Exception:", result.exception)            # None if all good
```

---

## Troubleshooting

- **No such file or directory**  
  Check exact paths & casing (`.data/metadata/...`, `./data/metadata_markdowns/...`).  
  Quick check:
  ```bash
  ls -al ./metadata/live_sales.json
  ls -al ./metadata_markdowns/live_sales.md
  ```

- **Model not found / Invalid model**  
  Model IDs differ per provider (Anthropic direct vs Vertex AI vs Bedrock).  
  Use the correct ID for your integration.

- **Vertex AI auth error**  
  Ensure `GOOGLE_APPLICATION_CREDENTIALS` is an **absolute path** to a valid JSON key,
  and set `GOOGLE_PROJECT_ID` + `GOOGLE_REGION` (e.g., `us-east5`).

- **Package not found (`pydough_analytics`) when calling as module**  
  If not using `pip install -e .`, set `PYTHONPATH=./src`. Editable install is recommended.