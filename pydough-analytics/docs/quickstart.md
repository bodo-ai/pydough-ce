# Quickstart

## Installation

```bash
# From source (development mode)
cd pydough-analytics && pip install -e .

# Or from PyPI (when published)
pip install pydough-analytics
```

Ensure the following environment variables are configured (a local `.env` is supported):

- `GEMINI_API_KEY`: API key for Google Gemini models.
- (Optional) `PYDOUGH_ANALYTICS_MODEL`, `PYDOUGH_ANALYTICS_TEMPERATURE` if you want to use Typer's auto env var integration.

## Generating metadata (sample)

```bash
pydough-analytics init-metadata sqlite:///metadata/live_sales.db -o metadata/live_sales.json --graph-name SALES
```

- Supports SQLite out of the box.
- PostgreSQL/MySQL/Snowflake are available via optional extras (see `pyproject.toml`).
- Use `--no-reverse` to suppress reverse relationships if required.

## Asking a question (sample)

```bash
pydough-analytics ask "Top 3 sales by amount" \
  --metadata metadata/live_sales.json \
  --graph-name SALES \
  --url sqlite:///metadata/live_sales.db \
  --show-sql --show-code
```

The CLI prints the PyDough code, generated SQL, and a table preview. Use `--max-rows` to limit the DataFrame slice returned from the database.

## Python API

```python
from pydough_analytics.pipeline.analytics import AnalyticsEngine

engine = AnalyticsEngine(
    metadata_path="metadata/live_sales.json",
    graph_name="SALES",
    database_url="sqlite:///metadata/live_sales.db",
    model="gemini-2.0-flash",
)

result = engine.ask("Top 3 sales by amount", max_rows=10)
print(result.dataframe)
print(result.sql)
```

`AnalyticsResult` includes the DataFrame, SQL, PyDough code, explanation, and the number of attempts taken.
