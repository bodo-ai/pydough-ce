# pydough-analytics

Community Edition toolkit that combines the PyDough DSL with LLM-based prompting
to deliver text-to-analytics workflows. The package provides:

- Metadata generator that turns relational databases into PyDough knowledge graphs.
- Prompt construction and Gemini-powered inference to translate natural language questions into PyDough code.
- Safe execution layer that materialises PyDough results as SQL and DataFrames.
- A Typer-based CLI for metadata generation and ad-hoc querying.

## Quick usage

  ```bash
  # Generate metadata for a TPC-H SQLite database
  pydough-analytics generate-json \
    --engine sqlite \
    --database ./data/tpch.db \
    --graph-name TPCH \
    --json-path ./metadata/tpch.json
  ```

  ```bash
  # Export that metadata to Markdown docs
  pydough-analytics generate-md \
    --graph-name TPCH \
    --json-path ./metadata/tpch.json \
    --md-path ./docs/tpch.md
  ```

You can also run the CLI via the module entrypoint:

  ```bash
  python -m pydough_analytics --version
  python -m pydough_analytics generate-json \
    --engine sqlite \
    --database ./data/tpch.db \
    --graph-name TPCH \
    --json-path ./metadata/tpch.json
  ```

## Supported backends

- SQLite (local files or in-memory).

Example for Postgres using the Pagila demo:

  ```bash
  # Generate metadata from a Postgres demo DB
  pydough-analytics generate-json \
    --engine postgres \
    --database postgresql://USER:PASS@HOST:PORT/pagila \
    --graph-name PAGILA \
    --json-path ./metadata/pagila.json
  ```

  ```bash
  # Export to Markdown
  pydough-analytics generate-md \
    --graph-name PAGILA \
    --json-path ./metadata/pagila.json \
    --md-path ./docs/pagila.md
  ```


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