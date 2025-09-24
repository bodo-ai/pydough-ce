# pydough-analytics

Community Edition toolkit that combines the PyDough DSL with LLM-based prompting
to deliver text-to-analytics workflows. The package provides:

- Metadata generator that turns relational databases into PyDough knowledge graphs.
- Prompt construction and Gemini-powered inference to translate natural language questions into PyDough code.
- Safe execution layer that materialises PyDough results as SQL and DataFrames.
- A Typer-based CLI for metadata generation and ad-hoc querying.

## Quick usage

```bash
# Included sample (SQLite)
pydough-analytics ask "Top 3 sales by amount" \
  --metadata metadata/live_sales.json \
  --graph-name SALES \
  --url sqlite:///metadata/live_sales.db \
  --show-sql --show-code

# Or generate metadata for your DB
pydough-analytics init-metadata sqlite:///data/your.db -o metadata/your.json --graph-name YOURDB
pydough-analytics ask "Your question here" --metadata metadata/your.json --graph-name YOURDB --url sqlite:///data/your.db
```

You can also run the CLI via the module entrypoint:

```bash
python -m pydough_analytics --version
python -m pydough_analytics ask "Top 3 sales by amount" --metadata metadata/live_sales.json --graph-name SALES --url sqlite:///metadata/live_sales.db
```

## Advanced Example: Relationship Aggregation

With metadata for the Postgres `pagila` demo, you can aggregate over relationships. For example, total payments per customer (top 5):

```bash
# Ensure you have metadata for the pagila database first
# pydough-analytics init-metadata postgresql://USER:PASS@HOST:PORT/pagila -o metadata/pagila.json --graph-name PAGILA

pydough-analytics ask "For each customer, show total payment amount. Show the top 5 customers." \
  --metadata metadata/pagila.json \
  --graph-name PAGILA \
  --url postgresql://USER:PASS@HOST:PORT/pagila \
  --show-code
```

Expected PyDough shape:

```python
result = customer.CALCULATE(
    first_name,
    last_name,
    total_amount=SUM(payments.amount)
).TOP_K(5, by=total_amount.DESC())
```

## Installation

```bash
pip install pydough-analytics

# Optional database extras
pip install "pydough-analytics[postgres]"    # installs psycopg2-binary
pip install "pydough-analytics[snowflake]"   # installs snowflake-connector-python
```

Environment

- Set `GEMINI_API_KEY` in your environment or `.env` file.
- Optional flags: `--model`, `--temperature`, `--attempts`, `--max-rows` on the CLI.

Tip: CLI options can also be set via environment variables with the prefix `PYDOUGH_ANALYTICS_` (e.g., `PYDOUGH_ANALYTICS_MODEL=gemini-2.0-flash`).

CLI flags

- `--json` to emit machine-readable output (includes code, sql, rows)
- `--log-level DEBUG` for verbose tracing
- `--timeout` to cap execution time per query (defaults to 10s)
- `--max-rows` to limit DataFrame size

See also `docs/quickstart.md` and `docs/pydough-prompt-guide.md`.


### Supported backends

- SQLite (local files or in-memory)
- PostgreSQL / Postgres-compatible (psycopg2-binary required)
- Snowflake (snowflake-connector-python required)

Example for Postgres using the Pagila demo:

```bash
# run metadata generation and use target database
pydough-analytics init-metadata postgresql://USER:PASS@HOST:PORT/pagila -o metadata/pagila.json --graph-name PAGILA
pydough-analytics ask "Top 5 cities by total payment amount" \n  --metadata metadata/pagila.json \n  --graph-name PAGILA \n  --url postgresql://USER:PASS@HOST:PORT/pagila \n  --attempts 3 --show-sql --show-code
```

```bash
# Postgres requirements
pip install psycopg2-binary

# Snowflake requirements
pip install "snowflake-connector-python[pandas]"
```

### Troubleshooting

- **`FileNotFoundError` or `Graph ... not found`** – The path passed to `--metadata` is incorrect, or the name passed to `--graph-name` does not exist in the metadata file. Double-check your file paths and the `name` field inside your metadata JSON.
  - Tip: open the generated Markdown summary (same path as the JSON, `.md` extension) to confirm names and casing.
  - Ensure Python 3.10+ (`python3.11 -V`) when installing/running.
- **`Expected a collection, but received an expression`** – the generated code referenced a scalar property where a collection was expected. The CLI will retry with feedback; if the error persists, inspect the emitted PyDough or run with `--json` to capture the failing code.
- **`Imports are not allowed`** – the sandbox rejects import or filesystem calls; ensure prompts request pure PyDough.
- **Large result sets** – use `--max-rows` to limit output (defaults to 100); the JSON output (`--json`) returns a records array suitable for automation.
- **Logging** – adjust verbosity with `--log-level DEBUG` to inspect prompt/response flow.

### Live LLM tests (optional)

Run natural-language tests against the sample SQLite data.

```bash
# 1) Python ≥3.10
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .

# 2) Ensure GEMINI_API_KEY is set (env or .env)

# 3) Enable live tests and run
export PYDOUGH_ANALYTICS_RUN_LIVE=1
pytest -m live_llm -q

# Run only the general + suite tests
pytest -q tests/test_natural_language_live.py tests/test_natural_language_suite_live.py tests/test_natural_language_general_live.py
```

Notes:
- Calls the Gemini API; costs may apply. Keep `max_rows` small.
- Postgres live test: set `PYDOUGH_ANALYTICS_LIVE_PG_URL`, `PYDOUGH_ANALYTICS_LIVE_PG_METADATA` and run `pytest -m live_llm`.

### Prompt customization

Control how metadata is rendered into the prompt and override the base prompt text via env (succinct):

- Schema rendering: `PYDOUGH_ANALYTICS_SCHEMA_STYLE=markdown|summary|json|none`
- Limits (when using `summary`): `PYDOUGH_ANALYTICS_SCHEMA_MAX_COLLECTIONS` (default 12), `PYDOUGH_ANALYTICS_SCHEMA_MAX_COLUMNS` (default 8)
- System prompt override: `PYDOUGH_ANALYTICS_SYSTEM_PROMPT_PATH=/path/to/system_prompt.md`
- Guide override: `PYDOUGH_ANALYTICS_GUIDE_PATH=/path/to/pydough_guide.md`
- LLM client override: `PYDOUGH_ANALYTICS_LLM_PROVIDER=gemini` (register custom providers via `pydough_analytics.llm.client.register_llm_client`)

Example:

```bash
export PYDOUGH_ANALYTICS_SCHEMA_STYLE=summary
export PYDOUGH_ANALYTICS_SYSTEM_PROMPT_PATH=prompts/system.md
export PYDOUGH_ANALYTICS_GUIDE_PATH=prompts/guide.md
pydough-analytics ask "Top sales" --metadata metadata/live_sales.json --graph-name SALES --url sqlite:///metadata/live_sales.db
```

Custom LLM provider (advanced):

```python
from pydough_analytics.llm.client import register_llm_client, LLMResponse

class MyLLM:
    def generate(self, prompt):
        return LLMResponse(code="result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())", explanation=None, raw_text="{}", usage_metadata=None)

register_llm_client("myprovider", lambda **kwargs: MyLLM())
# Then set: export PYDOUGH_ANALYTICS_LLM_PROVIDER=myprovider
```

### Suggested next steps

- Add CLI flags mirroring env knobs: `--schema-style`, `--schema-max-collections`, `--schema-max-columns`, `--system-prompt-path`, `--guide-path`.
- Introduce prompt strategies behind `PYDOUGH_ANALYTICS_PROMPT_STRATEGY` (e.g., `concise`, `rich`, `aggregate`, `row`).
- Context trimming per question: include only relevant collections/columns (keyword match or lightweight embedding filter).
- Few-shot library: inject 1–3 examples matched to intent (top‑k, filter, ordering, aggregates, relationship rollups).
- Error‑aware retries: map common PyDough runtime errors to explicit “fix hints” injected into the next prompt.

### MCP server (optional)

Install the MCP extras if you want to expose pydough-analytics as a Machine Cooperation Protocol server:

```bash
pip install "pydough-analytics[mcp]"
python -m pydough_analytics.mcp.server
```

Available tools:

- `pydough.init_metadata(url, graph_name="DATABASE")`: returns metadata JSON and (optionally) markdown.
- `pydough.open_session(database_url, metadata_path=..., graph_name="DATABASE")`: opens a session, returning a `session_id`.
- `pydough.ask(session_id, question, attempts=2, max_rows=100)`: runs a question and returns code, SQL, and rows.
- `pydough.schema_markdown(session_id)`: returns the markdown summary for an active session.
- `pydough.close_session(session_id)`: closes the session and cleans up temporary files.
- `pydough.list_sessions()`: auxiliary tool to inspect active sessions.

Resources exposed via MCP:

- `metadata/{session_id}` – markdown schema.
- `result/{session_id}` – last query result (code, SQL, rows).

The server uses the same environment variables as the CLI (e.g., `GEMINI_API_KEY`). When metadata is passed inline, it is persisted in a temporary file per session; closing the session removes that file.

Example Claude Desktop manifest entry:

```json
{
  "name": "pydough-analytics",
  "command": ["python", "-m", "pydough_analytics.mcp.server"]
}
```


## Architecture Overview

```
+----------------------------+    +------------------------------+    +------------------------+
| CLI / Python API / MCP     | -> | Prompt Builder               | -> | LLM Client             |
| (ask / init / MCP tools)   |    | (metadata + cheat sheet +    |    | (JSON schema, retries) |
+-------------+--------------+    |  guide)                      |    +-----------+------------+
              |                   +---------------+--------------+                |
              |                                   |                               v
              |                                   v                     +------------------------+
              |                        +-----------------------+        | PyDough Executor       |
              |                        | Metadata Generator    | <----- | (load graph, to_sql/   |
              |                        | (SQLAlchemy -> JSON)  |        |  to_df, sanitize+retry)|
              |                        +-----------+-----------+        +-----------+------------+
              v                                    |                                ^
+----------------------------+         +-----------v-----------+                    |
| GEMINI_API_KEY (env/.env)  |         | Metadata JSON / MD    | <------------------+
+----------------------------+         | (graph + markdown)    |      Runtime feedback (errors)
                                       +-----------------------+
```
