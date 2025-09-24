"""Execution utilities wrapping the PyDough runtime."""

from __future__ import annotations

import ast
import contextlib
import linecache
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent
from typing import Any, Callable, Dict, Optional

import pandas as pd
import pydough
from pydough import init_pydough_context
from sqlalchemy.engine import make_url

from pydough.database_connectors import DatabaseConnection, DatabaseContext
from pydough.database_connectors.builtin_databases import DatabaseDialect

logger = logging.getLogger(__name__)

SAFE_BUILTINS: Dict[str, Any] = {
    "True": True,
    "False": False,
    "None": None,
    "__import__": __import__,  # needed by PyDough decorators during compilation
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "sum": sum,
}

FORBIDDEN_NAMES = {
    "__import__",
    "eval",
    "exec",
    "open",
    "compile",
    "breakpoint",
    "exit",
    "quit",
}

DEFAULT_EXECUTION_TIMEOUT = 10.0

DatabaseConnector = Callable[[Any], None]

_DATABASE_CONNECTORS: Dict[str, DatabaseConnector] = {}


class PyDoughExecutionError(RuntimeError):
    """Raised when executing LLM-generated PyDough code fails."""


@dataclass
class ExecutionResult:
    dataframe: pd.DataFrame
    sql: str
    executed_code: str


class PyDoughExecutor:
    """Sets up the PyDough session and executes generated code safely."""

    def __init__(
        self,
        *,
        metadata_path: Path | str,
        graph_name: str,
        database_url: str,
        execution_timeout: float = DEFAULT_EXECUTION_TIMEOUT,
    ) -> None:
        self._metadata_path = str(metadata_path)
        self._graph_name = graph_name
        self._database_url = database_url
        self._initialised = False
        self._execution_timeout = execution_timeout

    def ensure_ready(self) -> None:
        if self._initialised:
            return
        self._load_metadata()
        self._connect_database()
        self._initialised = True

    def execute(
        self,
        code: str,
        *,
        max_rows: Optional[int] = 100,
        timeout: Optional[float] = None,
        _allow_retry: bool = True,
    ) -> ExecutionResult:
        self.ensure_ready()

        code = _preprocess_code(code)
        _validate_code(code)

        wrapped_code = self._wrap_code(code)
        safe_globals, local_ns = _build_environment()
        execution_timeout = timeout or self._execution_timeout
        start_time = time.perf_counter()

        compiled = compile(wrapped_code, '<pydough_analytics>', 'exec')
        linecache.cache['<pydough_analytics>'] = (
            len(wrapped_code),
            None,
            wrapped_code.splitlines(True),
            '<pydough_analytics>',
        )
        try:
            exec(compiled, safe_globals, local_ns)
        except Exception as exc:
            raise PyDoughExecutionError(str(exc)) from exc

        if time.perf_counter() - start_time > execution_timeout:
            raise PyDoughExecutionError(
                f"Execution exceeded timeout of {execution_timeout} seconds."
            )

        result_obj = local_ns.get("__pydough_result__")
        if result_obj is None:
            raise PyDoughExecutionError("Generated code did not assign to 'result'.")

        try:
            sql = pydough.to_sql(result_obj)
            df = pydough.to_df(result_obj)
        except Exception as exc:
            message = str(exc)
            if _allow_retry:
                sanitized = _sanitize_code(code, message)
                if sanitized and sanitized != code:
                    logger.debug("Retried execution with sanitized code due to: %s", message)
                    return self.execute(
                        sanitized,
                        max_rows=max_rows,
                        timeout=timeout,
                        _allow_retry=False,
                    )
            raise PyDoughExecutionError(f"PyDough evaluation failed: {message}") from exc

        if time.perf_counter() - start_time > execution_timeout:
            raise PyDoughExecutionError(
                f"Execution exceeded timeout of {execution_timeout} seconds."
            )

        if max_rows is not None and max_rows > 0:
            df = df.head(max_rows).copy()

        return ExecutionResult(dataframe=df, sql=sql, executed_code=code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _wrap_code(self, code: str) -> str:
        body = indent(code.strip(), "    ")
        return (
            "@init_pydough_context(pydough.active_session.metadata)\n"
            "def __pydough_program__():\n"
            f"{body}\n"
            "    return result\n\n"
            "__pydough_result__ = __pydough_program__()\n"
        )

    def _load_metadata(self) -> None:
        try:
            pydough.active_session.load_metadata_graph(self._metadata_path, self._graph_name)
        except Exception as exc:
            raise PyDoughExecutionError(
                f"Failed to load metadata graph '{self._graph_name}' from {self._metadata_path}: {exc}"
            ) from exc

    def _connect_database(self) -> None:
        url = make_url(self._database_url)
        dialect = url.get_backend_name()
        connector = _DATABASE_CONNECTORS.get(dialect)
        if connector is None:
            raise PyDoughExecutionError(
                f"Unsupported database dialect '{dialect}'."
            )
        connector(url)


def _validate_code(code: str) -> None:
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise PyDoughExecutionError(f"Generated code has syntax error: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise PyDoughExecutionError("Imports are not allowed in generated code.")
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise PyDoughExecutionError("Global/nonlocal statements are not allowed.")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_NAMES:
                raise PyDoughExecutionError(
                    f"Forbidden call to '{func.id}' detected in generated code."
                )
            if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_NAMES:
                raise PyDoughExecutionError(
                    f"Forbidden call to '{func.attr}' detected in generated code."
                )


def _build_environment() -> tuple[Dict[str, Any], Dict[str, Any]]:
    globals_ns: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "pydough": pydough,
        "init_pydough_context": init_pydough_context,
    }
    locals_ns: Dict[str, Any] = {}
    return globals_ns, locals_ns


def _sanitize_code(code: str, error_message: str) -> Optional[str]:
    """Attempt to fix common LLM mistakes automatically."""

    # Only handle obvious self-referential prefixes for now
    root_match = re.search(r"\b([A-Za-z_][\w]*)\.(CALCULATE|WHERE|TOP_K|ORDER_BY)", code)
    if not root_match:
        sanitized = _fix_isin_usage(code, error_message)
        if sanitized != code:
            return sanitized
        return None
    root = root_match.group(1)
    if not root:
        return None

    # Trigger on common PyDough errors mentioning the collection name
    sanitized = code
    if "Unrecognized term" in error_message or "mix between subcollection" in error_message:
        sanitized = _strip_root_prefix(sanitized, root)
        sanitized = _strip_aggregate_prefixes(sanitized, root)
    sanitized = _fix_isin_usage(sanitized, error_message)
    if sanitized != code:
        sanitized = re.sub(r"(\b[A-Za-z_][\w]*)\s*=\s*\1\b", r"\1", sanitized)
        logger.debug("Sanitized generated code due to PyDough error: %s", sanitized)
        return sanitized

    return None


def _preprocess_code(code: str) -> str:
    root_match = re.search(r"\b([A-Za-z_][\w]*)\.(CALCULATE|WHERE|TOP_K|ORDER_BY)", code)
    sanitized = code
    if root_match:
        root = root_match.group(1)
        sanitized = _strip_root_prefix(sanitized, root)
    sanitized = re.sub(r"(\b[A-Za-z_][\w]*)\s*=\s*\1\b", r"\1", sanitized)
    if sanitized != code:
        logger.debug("Preprocessed generated code: %s", sanitized)
    return sanitized


def _strip_root_prefix(code: str, root: str) -> str:
    pattern = rf"\b{re.escape(root)}\.(?=[a-z_])"
    return re.sub(pattern, "", code)


def _strip_aggregate_prefixes(code: str, root: str) -> str:
    aggregate_pattern = re.compile(r"\b(SUM|AVG|MIN|MAX|COUNT|STDDEV|VARIANCE)\s*\(([^()]*)\)")

    def _replace(match: re.Match[str]) -> str:
        func = match.group(1)
        expr = match.group(2)
        cleaned = re.sub(rf"\b{re.escape(root)}\.", "", expr)
        return f"{func}({cleaned})"

    return aggregate_pattern.sub(_replace, code)


def _fix_isin_usage(code: str, error_message: str) -> str:
    if " isin" not in code and ".isin" not in code:
        return code
    if "isin" not in error_message and "object" not in error_message:
        # avoid rewriting unless error references it
        return code
    return re.sub(r"\b([A-Za-z_][\w]*)\.isin\(", r"\1.IN(", code)


def register_database_connector(dialect: str, connector: DatabaseConnector) -> None:
    _DATABASE_CONNECTORS[dialect] = connector


def _connect_sqlite(url) -> None:
    database = url.database or ":memory:"
    if database and not str(database).startswith(":"):
        database = str(Path(database).expanduser())
    pydough.active_session.connect_database("sqlite", database=database)


def _connect_postgres(url) -> None:
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise PyDoughExecutionError(
            "Postgres support requires psycopg2-binary; install via `pip install pydough-analytics[postgres]`."
        ) from exc

    conn = psycopg2.connect(
        user=url.username,
        password=url.password,
        host=url.host or "localhost",
        port=url.port or 5432,
        dbname=url.database,
    )
    connection = DatabaseConnection(conn)
    # Use ANSI dialect as a reasonable default; PyDough currently lacks a POSTGRES dialect in this release
    pydough.active_session.database = DatabaseContext(connection, DatabaseDialect.ANSI)


def _connect_mysql(url) -> None:
    pydough.active_session.connect_database(
        "mysql",
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=url.database,
    )


def _connect_snowflake(url) -> None:
    params = {"user": url.username, "password": url.password}
    params.update(url.query)
    pydough.active_session.connect_database("snowflake", **params)


register_database_connector("sqlite", _connect_sqlite)
register_database_connector("postgresql", _connect_postgres)
register_database_connector("postgres", _connect_postgres)
register_database_connector("mysql", _connect_mysql)
register_database_connector("mysql+pymysql", _connect_mysql)
register_database_connector("snowflake", _connect_snowflake)


__all__ = ["PyDoughExecutor", "ExecutionResult", "PyDoughExecutionError", "register_database_connector"]
