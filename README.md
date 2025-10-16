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

## Provider Setup — Vertex (default) vs API-Key Mode

This project supports **two authentication modes** for AI providers:

1. **Vertex AI mode** (default, recommended) — uses **Application Default Credentials (ADC)** through Google Cloud IAM.  
2. **API-Key mode** — optional fallback for Gemini via the public **Google AI Studio API** (no IAM, less control).

Both **Gemini** and **Claude** run on Vertex AI by default.

---

### Vertex AI prerequisite (ADC) — Required by default

The default AI providers in this repo (Gemini and Claude) are wired through **Google Vertex AI**, which **requires Application Default Credentials (ADC)**.  
An API key alone is **not** sufficient in this mode.

---

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

## API-Key Mode (Google AI Studio)

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

## TPCH sample database (download helper)

To make local testing easy, this repo includes a small helper script to download the TPCH demo database.

- **Script location:** `pydough-analytics/setup_tpch.sh`
- **What it does:** If the target file already exists, it prints `FOUND` and exits. Otherwise it downloads the SQLite DB.
- **Where the DB should live:** `./pydough-analytics/data/databases/TPCH.db` (from the repo root). The rest of the docs/CLI examples assume this path.

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
pydough-analytics generate-json   --url sqlite:///data/databases/TPCH.db   --graph-name TPCH   --json-path ./data/metadata/Tpch_graph.json
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
pydough-analytics ask   --question "Give me the name of all the suppliers from the United States"   --url sqlite:///data/databases/TPCH.db   --db-name TPCH   --md-path ./data/metadata_markdowns/Tpch.md   --kg-path ./data/metadata/Tpch_graph.json   --show-sql --show-df --show-explanation
```

Notes:
- `--db-name` should match the `--graph-name` used during metadata generation (here: `TPCH`).
- To switch providers (e.g., Anthropic), pass a valid provider/model for your integration:
  ```bash
  --provider anthropic --model claude-sonnet-4-5@20250929
  ```
- Use `--rows` to control how many DataFrame rows are displayed (default: 20).

### Run the test suite (optional)

Install the [dev] version and run the tests with:
```bash
python -m pip install -e .[dev]
pytest -q tests
```

Or, if you prefer to install the dependencies directly:
```bash
python -m pip install pytest
python -m pip install pytest-mock
pytest -q tests
```

With these steps you now have the full CE pipeline:
SQLite DB → JSON metadata graph → Markdown documentation → **LLM Ask**.

### Run notebook samples (optional)

To explore the demo notebooks, install the [notebooks] version, or directly install the following dependencies:
```bash
python -m pip install -e .[notebooks]
```

Or manually install:
```bash
python -m pip install jupyterlab
python -m pip install ipykernel
python -m pip install matplotlib
```

Then open the notebook sample in `./samples/llm_demo.ipynb`.

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

- Support for more databases.