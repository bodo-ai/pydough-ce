# pydough-analytics

Community Edition toolkit that combines the PyDough DSL with LLM-based prompting to deliver text-to-analytics workflows. The package provides:

- Metadata generator that turns relational databases into PyDough knowledge graphs.
- Prompt construction and llm-powered inference to translate natural language questions into PyDough code.
- Safe execution layer that materialises PyDough results as SQL and DataFrames.
- A Typer-based CLI for metadata generation and ad-hoc querying.

## Quick usage

Get from **database → metadata (JSON) → Markdown → ask** in a few commands. This section includes *everything necessary* to run quickly.

---

## 0) One-time setup

```bash
# From the repo root
pip install -e .    # installs the CLI: `pydough-analytics`
# (Optional) Verify:
pydough-analytics --help
```

> If you prefer not to install, you can run via module:
> ```bash
> PYTHONPATH=./src python -m pydough_analytics.cli --help
> ```

### Provider credentials (pick one path)
- **Defaults (Google/Gemini)**: no extra env if already configured.
- **Anthropic via Vertex AI**
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/cred.json"
  export GOOGLE_PROJECT_ID="your-gcp-project"
  export GOOGLE_REGION="us-east5"
  ```
  
- **AWS Bedrock (Claude via AWS)**
  ```bash
  export AWS_ACCESS_KEY_ID=...
  export AWS_SECRET_ACCESS_KEY=...
  export AWS_DEFAULT_REGION=us-east-1
  ```

> Tip: If you use a `.env`, you can auto-load it in Python via `import pydough_analytics.config.env`. For the CLI, export env vars in your shell.

### **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → Databases  metadata  metadata_markdowns  prompts
 ```

### 1) Generate metadata JSON

```bash
pydough-analytics generate-json   --engine sqlite   --database ./data/databases/tpch.db   --graph-name TPCH   --json-path ./data/metadata/tpch.json
```

- `--engine`: Database engine (currently: `sqlite`).
- `--database`: DB file or connection string.
- `--graph-name`: Logical name for this dataset (you’ll reuse it as `--db-name` in `ask`).
- `--json-path`: Where to save the graph JSON.


### 2) Export Markdown (used by the LLM)

```bash
pydough-analytics generate-md   --graph-name TPCH   --json-path ./data/metadata/tpch.json   --md-path ./data/metadata_markdowns/tpch.md
```

- Markdown helps the LLM stay grounded during `ask`.
- Keep JSON + Markdown in version control for reproducibility.

---

### 3) Ask the LLM

The **PyDough code is always printed**. You can optionally show **SQL**, a **DataFrame** preview, and an **explanation**.

```bash
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --engine sqlite   --database ./data/databases/tpch.db   --db-name TPCH   --md-path ./data/metadata_markdowns/tpch.md   --kg-path ./data/metadata/tpch.json   --show-sql --show-df --show-explanation
```

- If you switch from defaults (e.g., to Anthropic), add:
  ```bash
  --provider anthropic --model claude-sonnet-4-5@20250929
  ```
- Control table size with `--rows` (default: 20).

---

### Troubleshooting

- **No such file or directory** → Check paths and casing; ensure `./data/metadata` and `./data/metadata_markdowns` exist.
- **Model not found** → Model IDs vary by provider (Anthropic direct vs Vertex vs Bedrock). Use the correct one.
- **Vertex AI auth error** → Use an **absolute** path for `GOOGLE_APPLICATION_CREDENTIALS` and set project/region.

## Supported backends

- SQLite (local files or in-memory).

## Suggested next steps

- To expand database coverage, add connectors for MySQL, PostgreSQL, and Snowflake, updating the CLI to accept engine-specific flags and extending the metadata.
- Improve the troubleshooting documentation by covering engine-specific errors, connection problems, missing database files, and common CLI usage mistakes with clear resolutions.
- Introduce an MCP server app that exposes the existing CLI commands as tools, enabling integration with editors and external orchestrators through a simple JSON-RPC interface.
- Provide richer examples and Jupyter notebooks, showing end-to-end pipelines from SQLite, connecting to different databases, and visualizing metadata graphs for more practical learning.


## Source folder structure

```
pydough-analytics/
├── src/                   # Library source code.
│   └── pydough_analytics/
│       ├── commands/      # CLI command implementations.
│       ├── config/        # Default settings and configuration helpers.
│       ├── data/          # Internal data loaders or fixtures.
│       ├── llm/           # Modules for LLM integration.
│       ├── metadata/      # Metadata generation and validation logic.
│       ├── utils/         # Shared utility functions.
│       ├── __init__.py    # Package entry.
│       ├── __main__.py    # Allows `python -m pydough_analytics` execution.
│       ├── _version.py    # Package version constant.
│       └── cli.py         # Typer CLI entrypoint (`pydough-analytics`).
└── README.md              # Package-specific documentation.
```

## Architecture Overview

```
+-----------------------------+                     
| CLI (Typer)                 |                     
| (generate-json, generate-md)|                    
+-------------+---------------+                     
              |                                    
              v                                    
+----------------------------+         +---------------------------+       
| Metadata Generator         | ----->  | Metadata JSON             |       
| (SQLAlchemy inspector +    |         | (graph definition, V2)    |       
|  identifier sanitizer,     |         +---------------------------+       
|  type mapping)             |                                    
+-------------+--------------+                                    
              |                                    
              v                                    
+----------------------------+         +---------------------------+       
| Markdown Exporter          | ----->  | Markdown Docs             |       
| (render schema from graph) |         | (human-readable overview) |       
+----------------------------+         +---------------------------+       

Notes:
- **Engines**: SQLite (built-in).
- **Storage**: local JSON + Markdown files.
```