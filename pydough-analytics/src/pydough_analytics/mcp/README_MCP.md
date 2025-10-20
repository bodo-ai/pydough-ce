# PyDough-Analytics — MCP Server Guide

This document explains how to run the PyDough-Analytics MCP server and use its available tools, resources, and templates.

## Installation

Install the MCP extras to enable the server from the project root folder:

```bash
cd /path/to/pydough-ce/pydough-analytics
pip install "pydough-analytics[mcp]"
```

## Running the MCP Server

Navigate to the root of your local clone and run:

```bash
cd /path/to/pydough-ce/pydough-analytics
fastmcp run src/pydough_analytics/mcp/mcp_entry.py:server
```

This launches the Machine Cooperation Protocol (MCP) server for PyDough-Analytics.  
The server can run over STDIO or SSE, and is compatible with MCP Inspector and Claude Desktop.

## Available Tools

| Tool | Description | Key Parameters |
|------|--------------|----------------|
| **init_metadata** | Generates graph metadata and Markdown for a given database. | `url`: DB connection string (e.g. `sqlite:///data/databases/TPCH.db`)<br>`graph_name`: optional name (default `"DATABASE"`) |
| **open_session** | Opens a PyDough/LLM session using metadata (either inline or from file). | `database_url`: DB connection string<br>`metadata_path`: path to metadata JSON<br>`metadata`: full metadata object (inline alternative)<br>`provider`: `"google"`, `"anthropic"`, etc.<br>`model`: LLM model name |
| **ask** | Runs a natural-language query against the session using the metadata and database. | `session_id`: from `open_session`<br>`question`: the natural-language question<br>`provider_params`: optional JSON (temperature, top_p, etc.)<br>Also supports `metadata` or `metadata_path` directly if you don’t want to open a session first. |
| **schema_markdown** | Returns the Markdown summary of the session’s metadata. | `session_id` |
| **list_sessions** | Lists all active sessions with minimal info. | *(no arguments)* |
| **close_session** | Closes a session and removes temporary files. | `session_id` |

## Resources

| Resource | Description | Example |
|-----------|--------------|----------|
| `pydough://metadata/{session_id}` | Markdown schema for that session. | `pydough://metadata/1234abcd` |
| `pydough://result/{session_id}` | Last LLM query result (code, SQL, rows). | `pydough://result/1234abcd` |

Resources appear only after running tools that produce them (e.g., `open_session` or `ask`).  
They are read-only, and remain available until the session is closed.

## How the MCP Server Works

- Each tool acts like an endpoint callable by any MCP client (e.g. MCP Inspector).  
- Resources expose read-only artifacts (metadata, results).  
- The server communicates using JSON-RPC via STDIO or SSE.  
- All configuration (API keys, credentials, etc.) uses the same environment variables as the CLI.  
- Metadata and Markdown are persisted as temporary files per session and deleted automatically when closed.

## Example Templates

You can use these ready-made templates in MCP Inspector or Claude Desktop’s Templates tab.  
They provide quick access to the most common operations.

### 1. Init Metadata (Generic)
```json
{
  "tool": "init_metadata",
  "arguments": {
    "url": "sqlite:////ABSOLUTE/PATH/TO/DB.sqlite",
    "graph_name": "DATABASE",
    "return_markdown": true,
    "split_groups": true
  }
}
```

### 2. Open Session (with metadata_path)
```json
{
  "tool": "open_session",
  "arguments": {
    "database_url": "sqlite:////ABSOLUTE/PATH/TO/DB.sqlite",
    "metadata_path": "/ABSOLUTE/PATH/TO/metadata.json",
    "db_name": "DATABASE",
    "graph_name": "DATABASE",
    "max_rows": 100,
    "provider": "google",
    "model": "gemini-2.5-pro"
  }
}
```

### 3. Open Session (inline metadata)
```json
{
  "tool": "open_session",
  "arguments": {
    "database_url": "sqlite:////ABSOLUTE/PATH/TO/DB.sqlite",
    "metadata": { "name": "DATABASE", "collections": [] },
    "graph_name": "DATABASE",
    "max_rows": 100,
    "provider": "google",
    "model": "gemini-2.5-pro"
  }
}
```

### 4. Ask (generic query)
```json
{
  "tool": "ask",
  "arguments": {
    "session_id": "PASTE_SESSION_ID",
    "question": "Give me all the regions",
    "auto_correct": false,
    "max_corrections": 1,
    "provider_params": {}
  }
}
```

Alternatively, ask can take metadata or metadata_path directly instead of a session:

```json
{
  "tool": "ask",
  "arguments": {
    "metadata_path": "/ABSOLUTE/PATH/TO/metadata.json",
    "database_url": "sqlite:////ABSOLUTE/PATH/TO/DB.sqlite",
    "question": "Show me all parts and suppliers"
  }
}
```

### 5. Schema Markdown
```json
{
  "tool": "schema_markdown",
  "arguments": {
    "session_id": "PASTE_SESSION_ID"
  }
}
```

### 6. Close Session
```json
{
  "tool": "close_session",
  "arguments": {
    "session_id": "PASTE_SESSION_ID"
  }
}
```

### 7. List Sessions
```json
{
  "tool": "list_sessions",
  "arguments": {}
}
```

Notes:
- Use absolute paths for database and metadata files.  
- The server cleans up session files automatically when you run close_session.  
- Resources only appear once a session is created and a query has been executed.