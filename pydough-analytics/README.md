# pydough-analytics

Community Edition toolkit that combines the PyDough DSL with LLM-based prompting to deliver text-to-analytics workflows. The package provides:

- Metadata generator that turns relational databases into PyDough knowledge graphs.
- Prompt construction and llm-powered inference to translate natural language questions into PyDough code.
- Safe execution layer that materialises PyDough results as SQL and DataFrames.
- A Typer-based CLI for metadata generation and ad-hoc querying.


## Provider Setup — Env (Vertex vs API‑Key)

Below are concise **`.env` examples** reflecting the two modes we support and a variant with explicit region.  
> **Do not commit real credentials or API keys to Git.** Use placeholders in docs and local `.env` files.

---

### 1) Minimal Vertex (recommended, default) (Gemini & Claude)

Use **ADC + Vertex**. No API key required. The SDK will use Vertex if you pass `project/location` in code **or** set `GOOGLE_GENAI_USE_VERTEXAI=true`.

```bash
# .env — minimal Vertex
GOOGLE_PROJECT_ID="your-gcp-project-id"
GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/service-account.json
GOOGLE_GENAI_USE_VERTEXAI=true
# Optional: explicit region selection (see #3), defaults noted below
# GOOGLE_REGION="us-east5"    # e.g., Claude default region
# GOOGLE_REGION="us-central1" # e.g., Gemini default region
```

**Defaults / notes**
- **Gemini on Vertex**: default region on code if not provided is **`us-central1`**.
- **Claude on Vertex**: default region on code if not provided is **`us-east5`**.
- Vertex can also use credentials via gcloud auth application-default login
- Ensure IAM role like `roles/aiplatform.user` and **Vertex AI API** enabled.

---

### 2) API‑Key mode (no Vertex) — *Gemini only*

If you set `GOOGLE_GENAI_USE_VERTEXAI=false`, the code will use the **Google AI Studio (API‑key) SDK** for Gemini.  
In this mode, `GOOGLE_API_KEY` is **required**, and ADC / project / region are **not used** by the Gemini client.

```bash
# .env — API‑key mode (Gemini via Google AI Studio API)
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_GENAI_USE_VERTEXAI=false

# These may exist in your shell and are harmless here, but are not required by API‑key mode:
# GOOGLE_PROJECT_ID="your-gcp-project-id"
# GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/service-account.json
# GOOGLE_REGION="us-central1"
```

**Notes**
- No IAM or Vertex regional control; intended for quick tests or limited environments.

---

### 3) Vertex with explicit region (Gemini & Claude)

Set an explicit region that supports the models you plan to use. if you do not set either one of the they have the next default values:
- **Gemini** → `us-central1`
- **Claude** → `us-east5`

```bash
# .env — Vertex with explicit region
GOOGLE_PROJECT_ID="your-gcp-project-id"
GOOGLE_REGION="us-east5"  # or us-central1, europe-west4, etc., if supported
GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/service-account.json
GOOGLE_GENAI_USE_VERTEXAI=true
# GOOGLE_API_KEY can be unset in Vertex mode
```

---

### Recap

- **Switch** between modes using **`GOOGLE_GENAI_USE_VERTEXAI`**:
  - `true`  → Vertex (ADC). Requires `GOOGLE_PROJECT_ID` (+ `GOOGLE_REGION` optional) and credentials.
  - `false` → API‑key mode for Gemini. Requires `GOOGLE_API_KEY`.
- **Claude** in this repo runs **only via Vertex** (ADC), so it needs `project` and a supported `region` (e.g., `us-east5`).

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
```

## Quick Guide

### **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → databases  metadata  metadata_markdowns  prompts
 ```

### 1) Generate metadata JSON

```bash
pydough-analytics generate-json   --url 'sqlite:///data/databases/TPCH.db'   --graph-name tpch   --json-path ./data/metadata/Tpch_graph.json
```

- `--url`: Connection string.
- `--graph-name`: Logical name for this dataset (you’ll reuse it as `--db-name` in `ask`).
- `--json-path`: Where to save the graph JSON.


### 2) Export Markdown (used by the LLM)

```bash
pydough-analytics generate-md   --graph-name tpch   --json-path ./data/metadata/Tpch_graph.json   --md-path ./data/metadata_markdowns/Tpch.md
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
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --url 'sqlite:///data/databases/TPCH.db'   --db-name tpch   --md-path ./data/metadata_markdowns/Tpch.md   --kg-path ./data/metadata/Tpch_graph.json   --show-sql --show-df --show-explanation
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

## MCP Server (Optional)

You can optionally run **PyDough-Analytics** as a [Machine Cooperation Protocol (MCP)](https://modelcontextprotocol.io) server to expose its analytics tools programmatically (for example, from **Claude Desktop**).

### Installation

Install the MCP extras from the root folder:
```bash
pip install "pydough-analytics[mcp]"
```

### Run the server

1. Navigate to the main project directory and then to pydough-analytics
  ```bash
  cd pydough-analytics
  ```

2. Start the MCP server:
  ```bash
  fastmcp run src/pydough_analytics/mcp/mcp_entry.py:server
  ```

The server exposes a full suite of **tools** and **resources** under the MCP name **`pydough-analytics`**.

See more on the README_MCP.md under the mcp folder.
---

### Available Tools

| Tool | Description |
|------|--------------|
| **pydough.init_metadata(url, graph_name="DATABASE")** | Generates metadata JSON and optionally Markdown from a live database. |
| **pydough.open_session(database_url or db_config, metadata_path=..., graph_name="DATABASE")** | Opens a PyDough session and returns a unique `session_id`. |
| **pydough.ask(session_id, question, auto_correct=False, max_corrections=1)** | Runs an LLM-assisted query using the session’s metadata and DB configuration. Returns PyDough code, SQL, and result rows. |
| **pydough.schema_markdown(session_id)** | Returns the Markdown schema documentation for the active session. |
| **pydough.list_sessions()** | Lists active sessions with basic diagnostic info. |
| **pydough.close_session(session_id)** | Closes the session and removes its temporary metadata files. |

---

### Resources

| Resource URI | Description |
|---------------|-------------|
| **`pydough://metadata/{session_id}`** | Markdown representation of the session’s graph schema. |
| **`pydough://result/{session_id}`** | JSON object containing the last query’s PyDough code, SQL, and results. |

---

### Environment Variables

The MCP server uses the same environment configuration as the CLI:
- `GOOGLE_PROJECT_ID`, `GOOGLE_REGION`, and `GOOGLE_APPLICATION_CREDENTIALS` — for Vertex/Claude/Gemini clients.  
- `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` — if using direct SDK mode.  

When metadata is passed inline (instead of via `metadata_path`), it’s persisted temporarily in  
`/tmp/pydough_analytics_mcp/` and automatically deleted when `close_session()` is called.

---

### Example Manifest (Claude Desktop)

```json
{
  "name": "pydough-analytics",
  "command": [
    "fastmcp",
    "run",
    "src/pydough_analytics/mcp/mcp_entry.py:server"
  ]
}
```

## Suggested next steps

- To expand database coverage updating the CLI to accept engine-specific flags and extending the metadata.
- Improve the troubleshooting documentation by covering engine-specific errors, connection problems, missing database files, and common CLI usage mistakes with clear resolutions.
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
│       ├── mcp/           # Machine Cooperation Protocol (MCP) server and entrypoint.
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
+-------------+---------------+                                            
              |
              v
+-----------------------------+       +---------------------------+
| MCP Server (FastMCP)        | ----> | External Clients (MCP)    |
| (tools + resources:         |       | Inspector / Claude / IDEs | 
|  init_metadata, ask, etc.)  |       |                           |
+-----------------------------+       +---------------------------+

Notes:
- **Engines**: SQLite (built-in), Snowflake, MySQL and PostgreSQL.
- **LLM Providers**: Google Gemini, Anthropic (Claude), aisuite (others).
- **Artifacts**: JSON graph, Markdown docs, generated PyDough code, SQL, result DataFrame.
- **MCP Server**: Exposes PyDough-Analytics functions to external tools through a Machine Cooperation Protocol interface.
```