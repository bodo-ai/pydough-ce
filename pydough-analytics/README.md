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
```

## Provider Setup — Vertex (default) vs API-Key Mode

This project supports **two authentication modes** for AI providers:

1. **Vertex AI mode** (default, recommended) — uses **Application Default Credentials (ADC)** through Google Cloud IAM.  
2. **API-Key mode** — optional fallback for Gemini via the public **Google AI Studio API** (no IAM, less control).

Both **Gemini** and **Claude** run on Vertex AI by default.

---

### Vertex AI prerequisite (ADC) — Required by default

The default AI providers in this repo (Gemini and Claude) are wired through **Google Vertex AI**, which **requires Application Default Credentials (ADC)**.  
An API key alone is **not** sufficient in this mode.

### Quick setup (local dev)

```bash
# 1) Authenticate to Google Cloud and generate ADC
gcloud auth application-default login

# 2) Set your active project and region
export GOOGLE_PROJECT_ID="your-gcp-project"
export GOOGLE_REGION="us-east5"

# 3) (Optional) Use a service account JSON instead of your user identity
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```

> **Important:** When using Vertex mode, `GOOGLE_API_KEY` is **ignored**.  
> Both **Gemini** and **Claude** authenticate via ADC under Vertex.

Tip: If you use a `.env`, you can auto-load it in Python via `import pydough_analytics.config.env`. For the CLI, export env vars in your shell.

### Setup (service account)

1. Create a **Service Account** with Vertex permissions (e.g. `roles/aiplatform.user`).
2. Enable the Vertex AI API in your GCP project.
3. Download the service account JSON key and set environment variables:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
   export GOOGLE_PROJECT_ID="your-gcp-project"
   export GOOGLE_REGION="us-east5"
   ```
4. Verify that the selected region supports the models you intend to use.

### Quick sanity check (Python)

```python
# Test Gemini connection through Vertex AI
import os, google.genai as genai
from google.genai import types

client = genai.Client(
    project=os.environ["GOOGLE_PROJECT_ID"],
    location=os.environ["GOOGLE_REGION"],
)
resp = client.models.generate_content(
    model="gemini-1.5-flash-002",
    contents="Say 'Vertex OK' if you can see this.",
    config=types.GenerateContentConfig(system_instruction="Healthcheck"),
)
print(resp.text)
```

If you encounter errors:
- Ensure ADC exists: `gcloud auth application-default print-access-token`
- Check `GOOGLE_PROJECT_ID` and `GOOGLE_REGION` values
- Confirm IAM permissions (`roles/aiplatform.user`)

### Using Claude via Vertex

This repo’s Claude integration uses the **Anthropic on Vertex** endpoint.  
It **also requires ADC**, and must be configured in the same environment as Gemini.

Make sure your chosen region (e.g. `us-east5`) supports Claude models.

## API-Key Mode (Google AI Studio) - Not implemented

If you **prefer not to use Vertex AI**, you can run Gemini through the **Google AI Studio API** using an **API key** instead of ADC.  
This method is simpler but lacks IAM integration and regional control.

### Environment
```bash
export GOOGLE_API_KEY="your-api-key"
```

### Client setup (Python)
```python
import google.genai as genai

# Create a client using only the API key (no project/location)
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
resp = client.models.generate_content(
    model="gemini-1.5-flash-002",
    contents="Hello from API-key mode!"
)
print(resp.text)
```

>  **Note:**  
> - API-Key mode does **not** use ADC or IAM roles.  
> - Recommended only for experimentation or limited environments.

With ADC configured, both **Gemini** and **Claude** authenticate and stream responses securely through **Vertex AI**.

## Quick usage

Get from **database → metadata (JSON) → Markdown → ask** in a few commands. This section includes *everything necessary* to run quickly.

---

## One-time setup

```bash
# From the repo root 
# Make sure to using the environment setup when running it.
pip install -e .    # installs the CLI: `pydough-analytics`
# (Optional) Verify:
pydough-analytics --help
```

> If you prefer not to install, you can run via module:
> ```bash
> PYTHONPATH=./src python -m pydough_analytics.cli --help
> ```

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

## MCP Server (Optional)

You can optionally run **PyDough-Analytics** as a [Machine Cooperation Protocol (MCP)](https://modelcontextprotocol.io) server to expose its analytics tools programmatically (for example, from **Claude Desktop**).

### Installation

Install the MCP extras:
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

### 🛠️ Available Tools

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

### 🧠 Example Manifest (Claude Desktop)

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