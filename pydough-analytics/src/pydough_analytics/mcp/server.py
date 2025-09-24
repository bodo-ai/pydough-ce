"""Machine Cooperation Protocol server for pydough-analytics."""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "fastmcp is required to run the MCP server. Install with 'pip install pydough-analytics[mcp]'."
    ) from exc

from ..metadata.generator import generate_metadata
from ..pipeline.analytics import AnalyticsEngine, AnalyticsResult
from ..prompting.markdown import metadata_to_markdown

logger = logging.getLogger(__name__)

server = FastMCP("pydough-analytics")


@dataclass
class SessionData:
    engine: AnalyticsEngine
    metadata_path: Path
    metadata_markdown: str
    default_max_rows: int
    last_result: Optional[AnalyticsResult]


_sessions: Dict[str, SessionData] = {}


def _create_engine(
    metadata_path: Path,
    graph_name: str,
    database_url: str,
    execution_timeout: float,
) -> AnalyticsEngine:
    return AnalyticsEngine(
        metadata_path=metadata_path,
        graph_name=graph_name,
        database_url=database_url,
        execution_timeout=execution_timeout,
    )


async def init_metadata_impl(
    *,
    url: str,
    graph_name: str = "DATABASE",
    schema: Optional[str] = None,
    include_reverse_relationships: bool = True,
    return_markdown: bool = True,
) -> Dict[str, Any]:
    """Generate metadata for a database and return it inline."""

    metadata = generate_metadata(
        url,
        graph_name=graph_name,
        schema=schema,
        include_reverse_relationships=include_reverse_relationships,
    )
    markdown = metadata_to_markdown(metadata) if return_markdown else None
    return {
        "metadata": metadata,
        "graph_name": graph_name,
        "markdown": markdown,
    }


async def open_session_impl(
    *,
    database_url: str,
    graph_name: str = "DATABASE",
    metadata_path: Optional[str] = None,
    metadata: Optional[Any] = None,
    max_rows: int = 100,
    execution_timeout: float = 10.0,
) -> Dict[str, Any]:
    """Open a session against a database and metadata graph."""

    if not metadata_path and metadata is None:
        raise ToolError("Either metadata_path or metadata must be provided.")

    if metadata_path:
        metadata_file = Path(metadata_path).expanduser().resolve()
        if not metadata_file.exists():
            raise ToolError(f"Metadata file not found: {metadata_file}")
        metadata_obj = json.loads(metadata_file.read_text(encoding="utf-8"))
    else:
        metadata_obj = metadata
        metadata_file = _write_temp_metadata(metadata_obj)

    graph_entry = _extract_graph(metadata_obj, graph_name)
    metadata_markdown = metadata_to_markdown(graph_entry)

    engine = _create_engine(metadata_file, graph_name, database_url, execution_timeout)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = SessionData(
        engine=engine,
        metadata_path=metadata_file,
        metadata_markdown=metadata_markdown,
        default_max_rows=max_rows,
        last_result=None,
    )

    return {"session_id": session_id}


async def close_session_impl(*, session_id: str) -> Dict[str, Any]:
    """Close an existing session and release resources."""

    data = _sessions.pop(session_id, None)
    if not data:
        raise ToolError(f"Session '{session_id}' not found")

    # remove generated metadata file if it resides in temp directory
    try:
        temp_dir = Path(tempfile.gettempdir()).resolve()
        if data.metadata_path.is_relative_to(temp_dir) and data.metadata_path.exists():
            data.metadata_path.unlink()
    except Exception:  # pragma: no cover - best effort cleanup
        logger.debug("Failed to remove temporary metadata file", exc_info=True)

    return {"closed": True}


async def ask_impl(
    *,
    session_id: str,
    question: str,
    attempts: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    """Ask a natural language question using an existing session."""

    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")

    effective_max_rows = max_rows if max_rows is not None else session.default_max_rows
    try:
        result = session.engine.ask(
            question,
            max_attempts=attempts or 2,
            max_rows=effective_max_rows,
        )
    except Exception as exc:  # pragma: no cover - bubble up error message
        raise ToolError(f"Analytics error: {exc}") from exc

    session.last_result = result

    rows = result.dataframe.to_dict(orient="records")
    return {
        "code": result.code,
        "sql": result.sql,
        "rows": rows,
        "attempts": result.attempts,
        "explanation": result.explanation,
    }


async def schema_markdown_impl(*, session_id: str) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")
    return {"markdown": session.metadata_markdown}


async def list_sessions_impl() -> Dict[str, Any]:  # pragma: no cover - convenience endpoint
    return {
        "sessions": [
            {
                "session_id": sid,
                "default_max_rows": data.default_max_rows,
                "has_last_result": data.last_result is not None,
            }
            for sid, data in _sessions.items()
        ]
    }


async def metadata_resource_impl(session_id: str) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")
    return {"markdown": session.metadata_markdown}


async def result_resource_impl(session_id: str) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")
    if session.last_result is None:
        raise ToolError("No result available for this session")
    rows = session.last_result.dataframe.to_dict(orient="records")
    return {
        "code": session.last_result.code,
        "sql": session.last_result.sql,
        "rows": rows,
        "attempts": session.last_result.attempts,
        "explanation": session.last_result.explanation,
    }


init_metadata = server.tool()(init_metadata_impl)
open_session = server.tool()(open_session_impl)
close_session = server.tool()(close_session_impl)
ask = server.tool()(ask_impl)
schema_markdown = server.tool()(schema_markdown_impl)
list_sessions = server.tool()(list_sessions_impl)
metadata_resource = server.resource("metadata/{session_id}")(metadata_resource_impl)
result_resource = server.resource("result/{session_id}")(result_resource_impl)


def _extract_graph(metadata: Any, graph_name: str) -> Dict[str, Any]:
    if isinstance(metadata, dict):
        graphs = [metadata]
    else:
        graphs = list(metadata)

    for graph in graphs:
        if isinstance(graph, dict) and graph.get("name") == graph_name:
            return graph

    for graph in graphs:
        if isinstance(graph, dict):
            return graph

    raise ToolError(f"Graph '{graph_name}' not found in metadata")


def _write_temp_metadata(metadata: Any) -> Path:
    directory = Path(tempfile.gettempdir()) / "pydough_analytics_mcp"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"metadata_{uuid.uuid4().hex}.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def main() -> None:
    """Run the MCP server."""
    logging.basicConfig(level=logging.INFO)
    server.run()


__all__ = [
    "server",
    "main",
    "init_metadata",
    "open_session",
    "close_session",
    "ask",
    "schema_markdown",
    "list_sessions",
]
