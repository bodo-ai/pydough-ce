from __future__ import annotations

import json
import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from sqlalchemy import create_engine, inspect

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ..metadata.generate_knowledge_graph import generate_metadata
from ..metadata.generate_mark_down import generate_markdown_from_metadata
from ..llm.llm_client import LLMClient, Result


logger = logging.getLogger(__name__)
server = FastMCP("pydough-analytics")


@dataclass
class SessionData:
    client: LLMClient
    kg_path: Path          
    md_path: Path           
    metadata_markdown: str  
    db_name: str
    db_config: Dict[str, Any]
    default_max_rows: int
    last_result: Optional[Result]


_sessions: Dict[str, SessionData] = {}


# -------- helpers --------

def _write_temp_file(suffix: str, text: str) -> Path:
    directory = Path(tempfile.gettempdir()) / "pydough_analytics_mcp"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4().hex}{suffix}"
    path.write_text(text, encoding="utf-8")
    return path


def _extract_graph(metadata: Any, graph_name: str) -> Dict[str, Any]:
    graphs = [metadata] if isinstance(metadata, dict) else list(metadata)
    # 1) match por nombre
    for g in graphs:
        if isinstance(g, dict) and g.get("name") == graph_name:
            return g
    # 2) fallback: el primero dict
    for g in graphs:
        if isinstance(g, dict):
            return g
    raise ToolError(f"Graph '{graph_name}' not found in metadata")


def _db_config_from_url(database_url: str) -> Dict[str, Any]:
    # Conversión mínima para tu LLMClient (que espera dict tipo {"engine": "...", "database": "..."})
    if database_url.startswith("sqlite:///"):
        return {"engine": "sqlite", "database": database_url.replace("sqlite:///", "", 1)}
    if database_url.startswith("sqlite://"):
        return {"engine": "sqlite", "database": database_url.replace("sqlite://", "", 1)}
    # Extiéndelo si necesitas Postgres/MySQL; por ahora devolvemos un marcador genérico
    return {"engine": "url", "database": database_url}


# -------- tools --------

async def init_metadata_impl(
    *,
    url: str,
    graph_name: str = "DATABASE",
    return_markdown: bool = True,
    split_groups: bool = True,
) -> Dict[str, Any]:
    """
    Genera metadata usando tu firma actual:
      generate_metadata(engine, graph_name, db_type, tables, split_groups)
    y (opcional) el Markdown del grafo.
    """
    engine = create_engine(url)
    try:
        insp = inspect(engine)
        db_type = engine.dialect.name  # "sqlite", "postgresql", "mysql", etc.

        # Lista de tablas (usa el schema por defecto si aplica)
        try:
            default_schema = insp.default_schema_name
        except Exception:
            default_schema = None

        tables = insp.get_table_names(schema=default_schema) if default_schema else insp.get_table_names()

        # Llama a tu generate_metadata con la firma real
        metadata_graphs = generate_metadata(
            engine=engine,
            graph_name=graph_name,
            db_type=db_type,
            tables=tables,
            split_groups=split_groups,
        )

        # Extrae el grafo pedido y genera Markdown si se solicitó
        graph_entry = _extract_graph(metadata_graphs, graph_name)
        markdown = generate_markdown_from_metadata(graph_entry) if return_markdown else None

        return {
            "metadata": metadata_graphs,   # lista de grafos (V2)
            "graph_name": graph_name,
            "markdown": markdown,
        }
    finally:
        try:
            engine.dispose()
        except Exception:
            pass


async def open_session_impl(
    *,
    database_url: Optional[str] = None,
    db_config: Optional[Dict[str, Any]] = None,
    db_name: str = "DATABASE",
    graph_name: str = "DATABASE",
    metadata_path: Optional[str] = None, 
    metadata: Optional[Any] = None,
    max_rows: int = 100,
    provider: str = "google",
    model: str = "gemini-2.5-pro",
) -> Dict[str, Any]:
    if not metadata_path and metadata is None:
        raise ToolError("Either metadata_path or metadata must be provided.")

    
    if metadata_path:
        kg_file = Path(metadata_path).expanduser().resolve()
        if not kg_file.exists():
            raise ToolError(f"Metadata file not found: {kg_file}")
        metadata_obj = json.loads(kg_file.read_text(encoding="utf-8"))
    else:
        metadata_obj = metadata
        kg_file = _write_temp_file(".json", json.dumps(metadata_obj, indent=2))

    
    graph_entry = _extract_graph(metadata_obj, graph_name)
    md_text = generate_markdown_from_metadata(graph_entry)
    md_file = _write_temp_file(".md", md_text)

    
    if not db_config:
        if not database_url:
            raise ToolError("Provide either db_config or database_url")
        db_config = _db_config_from_url(database_url)

    
    client = LLMClient(provider=provider, model=model)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = SessionData(
        client=client,
        kg_path=kg_file,
        md_path=md_file,
        metadata_markdown=md_text,
        db_name=db_name,
        db_config=db_config,
        default_max_rows=max_rows,
        last_result=None,
    )
    return {"session_id": session_id}


async def close_session_impl(*, session_id: str) -> Dict[str, Any]:
    """Cierra una sesión y limpia archivos temporales."""
    data = _sessions.pop(session_id, None)
    if not data:
        raise ToolError(f"Session '{session_id}' not found")

    for p in (data.kg_path, data.md_path):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            logger.debug("Failed to remove temporary file: %s", p, exc_info=True)

    return {"closed": True}


async def ask_impl(
    *,
    session_id: str,
    question: str,
    auto_correct: bool = False,
    max_corrections: int = 1,
    provider_params: Optional[Dict[str, Any]] = None,  # ✅ JSON-friendly
) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")

    try:
        res: Result = session.client.ask(
            question=question,
            kg_path=str(session.kg_path),
            md_path=str(session.md_path),
            db_name=session.db_name,
            db_config=session.db_config,
            auto_correct=auto_correct,
            max_corrections=max_corrections,
            **(provider_params or {}), 
        )
    except Exception as exc:
        raise ToolError(f"LLM error: {exc}") from exc

    session.last_result = res
    rows = res.df.to_dict(orient="records") if res.df is not None else None
    return {
        "code": res.code,
        "sql": res.sql,
        "rows": rows,
        "full_explanation": res.full_explanation,
        "exception": res.exception,
        "original_question": res.original_question,
    }


async def schema_markdown_impl(*, session_id: str) -> Dict[str, Any]:
    session = _sessions.get(session_id)
    if not session:
        raise ToolError(f"Session '{session_id}' not found")
    return {"markdown": session.metadata_markdown}


async def list_sessions_impl() -> Dict[str, Any]:
    return {
        "sessions": [
            {
                "session_id": sid,
                "db_name": data.db_name,
                "default_max_rows": data.default_max_rows,
                "has_last_result": data.last_result is not None,
            }
            for sid, data in _sessions.items()
        ]
    }


# -------- resources --------

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
    rows = session.last_result.df.to_dict(orient="records") if session.last_result.df is not None else None
    return {
        "code": session.last_result.code,
        "sql": session.last_result.sql,
        "rows": rows,
        "full_explanation": session.last_result.full_explanation,
        "exception": session.last_result.exception,
        "original_question": session.last_result.original_question,
    }


init_metadata    = server.tool()(init_metadata_impl)
open_session     = server.tool()(open_session_impl)
close_session    = server.tool()(close_session_impl)
ask              = server.tool()(ask_impl)
schema_markdown  = server.tool()(schema_markdown_impl)
list_sessions    = server.tool()(list_sessions_impl)

metadata_resource = server.resource("pydough://metadata/{session_id}")(metadata_resource_impl)
result_resource   = server.resource("pydough://result/{session_id}")(result_resource_impl)

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server.run()


__all__ = ["server", "main", "init_metadata", "open_session", "close_session",
           "ask", "schema_markdown", "list_sessions"]