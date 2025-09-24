# Contributing to pydough-full

Thanks for your interest in contributing! This repo contains the `pydough-analytics` Community Edition package and sample data.

## Getting set up

- Python 3.10+ recommended (3.11 preferred)
- Create a virtualenv and install locally:
  - `python3.11 -m venv .venv && source .venv/bin/activate`
  - `cd pydough-analytics && pip install -e .[mcp]`
- Configure `GEMINI_API_KEY` (env or a root `.env`).

## Running tests

- Unit tests only (fast):
  - `source .venv/bin/activate && pytest -q`
- Live LLM tests (call Gemini; opt-in):
  - `export PYDOUGH_ANALYTICS_RUN_LIVE=1`
  - `pytest -m live_llm -q`
  - Uses sample SQLite DB at `metadata/live_sales.db`.

## Prompt customization

- Schema-to-prompt rendering:
  - `PYDOUGH_ANALYTICS_SCHEMA_STYLE=markdown|summary|json|none`
  - `PYDOUGH_ANALYTICS_SCHEMA_MAX_COLLECTIONS=12`, `PYDOUGH_ANALYTICS_SCHEMA_MAX_COLUMNS=8`
- System prompt & guide overrides:
  - `PYDOUGH_ANALYTICS_SYSTEM_PROMPT_PATH=/path/to/system.md`
  - `PYDOUGH_ANALYTICS_GUIDE_PATH=/path/to/guide.md`

## Extensibility hooks

- Register a custom LLM provider:
  ```python
  from pydough_analytics.llm.client import register_llm_client, LLMResponse

  class MyLLM:
      def generate(self, prompt):
          return LLMResponse(code="result = ...", explanation=None, raw_text="{}", usage_metadata=None)

  register_llm_client("myprovider", lambda **kwargs: MyLLM())
  # export PYDOUGH_ANALYTICS_LLM_PROVIDER=myprovider
  ```
- Add a schema renderer (prompting format):
  ```python
  from pydough_analytics.prompting.schema import register_schema_renderer
  register_schema_renderer("myformat", lambda md, mc, mcol: "...")
  # export PYDOUGH_ANALYTICS_SCHEMA_STYLE=myformat
  ```
- Database connector (advanced):
  ```python
  from pydough_analytics.runtime.executor import register_database_connector
  register_database_connector("mydialect", lambda url: ...)
  ```

## Pull requests

- Keep changes focused and well-scoped.
- Include tests when feasible; avoid making live LLM a requirement.
- Follow the style of existing modules; keep files small and readable.

Thanks again for helping improve pydough-analytics!
