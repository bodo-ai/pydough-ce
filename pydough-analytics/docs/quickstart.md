# Quickstart

## Installation

  ```bash
  # From source (development mode)
  cd pydough-analytics && pip install -e .

  # Or from PyPI (when published)
  pip install pydough-analytics
  ```

## Generating metadata (sample)

Generate a PyDough metadata graph in JSON from the bundled SQLite database:

  ```bash
  pydough-analytics generate-json \
    --engine sqlite \
    --database ./metadata/live_sales.db \
    --graph-name SALES \
    --json-path ./metadata/live_sales.json
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
    --json-path ./metadata/live_sales.json \
    --md-path ./docs/live_sales.md
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
    database="./metadata/live_sales.db",
    graph_name="SALES",
    json_path="./metadata/live_sales.json"
)

# Reload the JSON metadata (optional)
metadata_loaded = load_json(Path("./metadata/live_sales.json"))

# Convert metadata to Markdown
md_content = generate_markdown(metadata_loaded, graph_name="SALES")

# Save Markdown to file
save_markdown("./docs/live_sales.md", md_content)

print("✅ Metadata JSON and Markdown generated successfully!")
```

This gives you the same workflow as the CLI:
Database → Metadata JSON → Markdown docs.