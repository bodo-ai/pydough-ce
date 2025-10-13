# PyDough-CE

Welcome to the `pydough-ce` project! This repository contains the `pydough-analytics` toolkit, a powerful system that turns natural language questions into safe, executable analytics.

It combines a custom Domain-Specific Language (DSL) called PyDough with LLM-powered system to create a seamless text-to-analytics workflow.

## What It Does

At its core, this project lets you ask questions of your relational database in plain English. The pipeline handles the heavy lifting:

1. **Generate Metadata** – Reflect your database schema into a PyDough knowledge graph.
2. **Ask a Question** – Phrase your analytics request in natural language (e.g., “Which cities have the highest sales?”).
3. **Translate to PyDough** – The LLM converts the question into the PyDough DSL, a declarative language purpose-built for analytics.
4. **Execute Safely** – PyDough compiles to SQL, runs against your database, and returns a tidy DataFrame.

## Key Features

- **Natural language interface** – Query data without writing SQL.
- **Automatic schema analysis** – Works with SQLite, Snowflake, MySQL and PostgSQL.
- **Safety by design** – PyDough limits execution to declarative analytics, reducing blast radius.
- **Developer friendly** – Includes a CLI, Python API.
- **Extensible** – Plug in custom prompts, LLM providers.

# Getting Started

## Provider Setup — Env (Vertex vs API‑Key)

Below are concise **`.env` examples** reflecting the two modes we support for both Claude and Gemini and a variant with explicit region.  
> **Do not commit real credentials or API keys to Git.** Use placeholders in docs and local `.env` files.

---

### 1) Minimal Vertex (recommended, default)

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
- You can also use the SDK alt env names: `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION`.
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
mkdir -p ./pydough-analytics/data/databases
bash pydough-analytics/setup_tpch.sh ./pydough-analytics/data/databases/TPCH.db
```

If you don't have `wget`, you can use `curl` instead:

```bash
mkdir -p ./pydough-analytics/data/databases
curl -L https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db -o ./pydough-analytics/data/databases/TPCH.db
```

Verify the file is present:

```bash
ls -lh ./pydough-analytics/data/databases/TPCH.db
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path .\pydough-analytics\data\databases | Out-Null
Invoke-WebRequest -Uri https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db -OutFile .\pydough-analytics\data\databases\TPCH.db
```

### Requirements

- Python 3.10 or newer (3.11 recommended).
- SQLite database file to introspect.
- PyDough 1.0.10 or newer.

### Configure the environment

Make sure to use the following environment setup when running the app.
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

## **Terminal location:** 

Run all of the next commands **from the `pydough-analytics` folder** (the folder that contains `data/`, `docs/`, `samples/`, `src/`, etc.).  
 Quick check:
 ```bash
 ls data
 # → databases  metadata  metadata_markdowns  prompts
 ```

### Default paths (data at `pydough-analytics` folder)

We keep project artifacts in **`./data/`** for consistency:
- **Database (SQLite):** `./data/databases/TPCH.db`
- **Metadata JSON:** `./data/metadata/Tpch_graph.json`
- **Metadata Markdown:** `./data/metadata_markdowns/Tpch.md`

### Generate metadata from SQLite

```bash
pydough-analytics generate-json   --url sqlite:///data/databases/TPCH.db   --graph-name tpch   --json-path ./data/metadata/Tpch_graph.json
```

This inspects the SQLite file and creates a metadata graph definition under `data/metadata/Tpch_graph.json`.

### Export Markdown docs

```bash
pydough-analytics generate-md   --graph-name tpch   --json-path ./data/metadata/Tpch_graph.json   --md-path ./data/metadata_markdowns/Tpch.md
```

The Markdown file provides a human-friendly overview of the metadata: collections, properties, and relationships.

### Ask the LLM (after generating JSON + Markdown)

Run natural-language questions on your dataset. The **PyDough code is always printed**; you can optionally include **SQL**, a **DataFrame** preview, and an **explanation**. The CE default is **Google / Gemini 2.5 Pro**.

```bash
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --url sqlite:///data/databases/TPCH.db   --db-name tpch   --md-path ./data/metadata_markdowns/Tpch.md   --kg-path ./data/metadata/Tpch_graph.json   --show-sql --show-df --show-explanation
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
python -m pip install pytest-mock
pytest -q tests
```

With these steps you now have the full CE pipeline:
SQLite DB → JSON metadata graph → Markdown documentation → **LLM Ask**.

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
