# pydough-analytics

Community Edition toolkit that combines the PyDough DSL with LLM-based prompting to deliver text-to-analytics workflows. The package provides:

- Metadata generator that turns relational databases into PyDough knowledge graphs.
- Prompt construction and llm-powered inference to translate natural language questions into PyDough code.
- Safe execution layer that materialises PyDough results as SQL and DataFrames.
- A Typer-based CLI for metadata generation and ad-hoc querying.

## TPCH sample database (download helper)

To make local testing easy, this repo includes a small helper script to download the TPCH demo database.

- **Script location:** `setup_tpch.sh`
- **What it does:** If the target file already exists, it prints `FOUND` and exits. Otherwise it downloads the SQLite DB.
- **Where the DB should live:** `./data/databases/TPCH.db` (from the repo root). The rest of the docs/CLI examples assume this path.

### One-liner (macOS/Linux)

Run from the **repo root**:

```bash
mkdir -p ./data/databases
bash setup_tpch.sh ./data/databases/TPCH.db
```

If you don't have `wget`, you can use `curl` instead:

```bash
mkdir -p ./data/databases
curl -L https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db -o ./data/databases/TPCH.db
```

Verify the file is present:

```bash
ls -lh ./data/databases/TPCH.db
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path .\data\databases | Out-Null
Invoke-WebRequest -Uri https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db -OutFile .\data\databases\TPCH.db

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
- **Gemini and Anthropic via Vertex AI**
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/cred.json"
  export GOOGLE_API_KEY:=...
  export GOOGLE_PROJECT_ID="your-gcp-project"
  export GOOGLE_REGION="us-east5"
  ```

> Tip: If you use a `.env`, you can auto-load it in Python via `import pydough_analytics.config.env`. For the CLI, export env vars in your shell.

### **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → databases  metadata  metadata_markdowns  prompts
 ```

### 1) Generate metadata JSON

```bash
pydough-analytics generate-json   --url 'sqlite:///data/databases/TPCH.db'   --graph-name TPCH   --json-path ./data/metadata/Tpch_graph.json
```

- `--url`: Connection string.
- `--graph-name`: Logical name for this dataset (you’ll reuse it as `--db-name` in `ask`).
- `--json-path`: Where to save the graph JSON.


### 2) Export Markdown (used by the LLM)

```bash
pydough-analytics generate-md   --graph-name TPCH   --json-path ./data/metadata/Tpch_graph.json   --md-path ./data/metadata_markdowns/Tpch.md
```

- `--graph-name`: Logical name for this dataset in the JSON.
- `--json-path`: Where to save the graph JSON.
- `--md-path`: Where to save the Markdown.

- Markdown helps the LLM stay grounded during `ask`.
- Keep JSON + Markdown in version control for reproducibility.

---

### 3) Ask the LLM

The **PyDough code is always printed**. You can optionally show **SQL**, a **DataFrame** preview, and an **explanation**.

```bash
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --url 'sqlite:///data/databases/TPCH.db'   --db-name TPCH   --md-path ./data/metadata_markdowns/Tpch.md   --kg-path ./data/metadata/Tpch_graph.json   --show-sql --show-df --show-explanation
```

- `--question`: Natural language question to be answered.
- `--url`: Full database connection string (See **## Supported Backends**).
- `--db-name`: Logical database name, typically matching the graph name.
- `--md-path`: Path to the Markdown documentation describing the database.
- `--kg-path`: Path to the JSON file containing the metadata.
- `--provider`: **Optional** LLM provider (e.g. openai, anthropic).
- `--model`: **Optional** LLM model identifier (e.g. gpt-4o-mini, claude-3-haiku).
- `--show-sql`: **Optional** Print the SQL query generated (default: False).
- `--show-df`: **Optional** Display the resulting DataFrame (default: False).
- `--show-explanation`: **Optional** Print the reasoning or explanation provided by the LLM (default: False).
- `--as-json`: **Optional** Output the query result as raw JSON (default: False).
- `--rows`: **Optional** Number of rows to display from the resulting DataFrame (default: 20).

- If you switch from defaults (e.g., to Anthropic), add:
  ```bash
  --provider anthropic --model claude-sonnet-4-5@20250929
  ```

---

### Troubleshooting

- **No such file or directory** → Check paths and casing; ensure `./data/metadata` and `./data/metadata_markdowns` exist.
- **Model not found** → Model IDs vary by provider (Anthropic direct vs Vertex vs Bedrock). Use the correct one.
- **Vertex AI auth error** → Use an **absolute** path for `GOOGLE_APPLICATION_CREDENTIALS` and set project/region.

## Supported backends

PyDough supports multiple database backends through SQLAlchemy connection strings.
Each connection string must include all required parameters (user, password, host, port, database, and optional schema/warehouse where applicable).

### SQLite

Used for local files or in-memory databases.    
All values are required in the URL format.

```bash
sqlite:///path/to/mydb.db
```

- Uses a local .sqlite or .db file.      

To use an in-memory database (for testing):

```bash
sqlite:///:memory:
```

### Snowflake

Used for analytical data warehouses.      
The connection string must include credentials, account, database, schema, and warehouse.

```bash
snowflake://user:password@account/db/schema?warehouse=WH&role=PUBLIC
```

**Required values:**
- `user`: Snowflake username.
- `password`: Snowflake password.
- `account`: Snowflake account identifier (e.g. xy12345.us-east-1).
- `db`: Database name.
- `schema`: Schema name.
- Query parameters (`warehouse` and `role`) are required for most configurations.

### MySQL

Used for transactional databases.   
The URL must include user, password, host, port, and database.    
Internally converted to mysql+mysqlconnector://.    

```bash
mysql://user:password@host:port/mydb
```

Converted internally to:

```bash
mysql+mysqlconnector://user:password@host:port/mydb
```

**Required values:**
- `user`: MySQL username.
- `password`: MySQL password.
- `host`: Server hostname or IP address.
- `port`: Port number (default: 3306).
- `mydb`: Database name.

### PostgreSQL

Used for relational and analytical databases.   
The URL must include all connection details.    
Internally converted to postgresql+psycopg2://.   

```bash
postgres://user:password@host:port/mydb
```

Converted internally to:

```bash
postgresql+psycopg2://user:password@host:port/mydb
```

**Required values:**
- `user`: PostgreSQL username.
- `password`: PostgreSQL password.
- `host`: Server hostname or IP address.
- `port`: Port number (default: 5432).
- `mydb`: Database name.

## Suggested next steps

- To expand database coverage updating the CLI to accept engine-specific flags and extending the metadata.
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
| (generate-json, generate-md,|                               
|  ask)                       |                               
+-------------+---------------+                               
              |                                               
              v                                               
+-----------------------------+       +---------------------------+       
| Metadata Generator          | ----> | Metadata JSON             |       
| (SQLAlchemy inspector +     |       | (graph definition, V2)    |       
|  identifier sanitizer,      |       +---------------------------+       
|  type mapping)              |                                               
+-------------+---------------+                                               
              |                                               
              v                                               
+-----------------------------+       +---------------------------+       
| Markdown Exporter           | ----> | Markdown Docs             |       
| (render schema from graph)  |       | (human-readable overview) |       
+-------------+---------------+       +---------------------------+       

              |
              v
+-----------------------------+       +---------------------------+       
| Ask Command (Typer)         | ----> | LLM Client                |       
| (natural language question) |       | (prompt + schema + guide) |       
+-------------+---------------+       +-------------+-------------+       
              |                                                    
              v                                                    
+-----------------------------+       +---------------------------+       
| AI Providers                | ----> | Gemini / Claude / aisuite |       
| (google, anthropic,         |       |                           |       
|  other via aisuite)         |       +---------------------------+       
+-------------+---------------+                                      
              |                                                    
              v                                                    
+-----------------------------+       +---------------------------+       
| PyDough Executor            | ----> | SQL + DataFrame           |       
| (extract code, run on DB,   |       | (results + explanation)   |       
|  sanitize, retry on errors) |       +---------------------------+       
+-----------------------------+                                            

Notes:
- **Engines**: SQLite (built-in), Snowflake, MySQL and PostgreSQL.
- **LLM Providers**: Google Gemini, Anthropic (Claude), aisuite (others).
- **Artifacts**: JSON graph, Markdown docs, generated PyDough code, SQL, result DataFrame.
```