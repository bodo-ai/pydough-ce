"""Utilities for generating PyDough metadata from relational databases.

The implementation is inspired by the internal tooling in the text2pydough
repository but rewritten for the Community Edition. The goal is to translate a
relational schema (via SQLAlchemy reflection) into the JSON structure expected
by PyDough.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import inflect
from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.sqltypes import (  # type: ignore[attr-defined]
    BIGINT,
    BOOLEAN,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    INTEGER,
    NUMERIC,
    SMALLINT,
    String,
    TIME,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MetadataGenerationConfig:
    """Configuration options for the metadata generator."""

    graph_name: str = "DATABASE"
    schema: Optional[str] = None
    include_reverse_relationships: bool = True
    max_sample_values: int = 0
    relationship_namer: Optional[
        Callable[[str, str, bool, set[str], set[str]], Tuple[str, Optional[str]]]
    ] = None


class MetadataGenerationError(RuntimeError):
    """Raised when metadata generation fails."""


def generate_metadata(
    url: str,
    *,
    graph_name: str = "DATABASE",
    schema: Optional[str] = None,
    include_reverse_relationships: bool = True,
    relationship_namer: Optional[
        Callable[[str, str, bool, set[str], set[str]], Tuple[str, Optional[str]]]
    ] = None,
) -> Dict[str, Any]:
    """Generate a PyDough metadata graph for the database at ``url``.

    Parameters
    ----------
    url:
        SQLAlchemy connection URL (e.g. ``sqlite:///tpch.db``).
    graph_name:
        Name assigned to the generated PyDough graph.
    schema:
        Optional explicit schema to reflect. Defaults to the engine's default.
    include_reverse_relationships:
        Whether to emit reverse relationship entries alongside forward joins.
    """

    config = MetadataGenerationConfig(
        graph_name=graph_name,
        schema=schema,
        include_reverse_relationships=include_reverse_relationships,
        relationship_namer=relationship_namer,
    )

    try:
        engine = create_engine(url)
    except SQLAlchemyError as exc:  # pragma: no cover - SQLAlchemy handles messaging
        raise MetadataGenerationError(f"Failed to create engine for {url}: {exc}") from exc

    try:
        return _generate_metadata(engine, config)
    finally:
        engine.dispose()


def write_metadata(metadata: Mapping[str, Any], path: Path | str) -> Path:
    """Write *metadata* to ``path`` in the PyDough JSON structure.

    The metadata specification expects a JSON array of graphs. For convenience we
    accept a single-graph mapping and wrap it during serialization.
    """

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump([metadata], fh, indent=2)
    return target


# ---------------------------------------------------------------------------
# Implementation details
# ---------------------------------------------------------------------------

_inflector = inflect.engine()


_SQLALCHEMY_TYPE_TO_PYDOUGH = {
    BOOLEAN: "bool",
    SMALLINT: "numeric",
    INTEGER: "numeric",
    BIGINT: "numeric",
    FLOAT: "numeric",
    NUMERIC: "numeric",
    DECIMAL: "numeric",
    DATE: "datetime",
    TIME: "datetime",
    DATETIME: "datetime",
}

try:  # pragma: no cover - optional dialect imports
    from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
    from sqlalchemy.dialects.postgresql import JSON as PG_JSON
    from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
except Exception:  # pragma: no cover - dialect not installed
    PG_ARRAY = PG_JSON = PG_JSONB = PG_UUID = None

try:  # pragma: no cover - optional dialect imports
    from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON
except Exception:  # pragma: no cover - dialect not installed
    MYSQL_JSON = None

if PG_JSON is not None:
    _SQLALCHEMY_TYPE_TO_PYDOUGH[PG_JSON] = "string"
if PG_JSONB is not None:
    _SQLALCHEMY_TYPE_TO_PYDOUGH[PG_JSONB] = "string"
if PG_UUID is not None:
    _SQLALCHEMY_TYPE_TO_PYDOUGH[PG_UUID] = "string"
if PG_ARRAY is not None:
    _SQLALCHEMY_TYPE_TO_PYDOUGH[PG_ARRAY] = "string"
if MYSQL_JSON is not None:
    _SQLALCHEMY_TYPE_TO_PYDOUGH[MYSQL_JSON] = "string"

_SQLITE_FALLBACK = {
    "INTEGER": "numeric",
    "REAL": "numeric",
    "NUMERIC": "numeric",
    "TEXT": "string",
    "BLOB": "string",
}

_STRING_TYPES = (String,)


def _generate_metadata(engine: Engine, config: MetadataGenerationConfig) -> Dict[str, Any]:
    inspector = inspect(engine)

    schema = config.schema or inspector.default_schema_name
    tables = inspector.get_table_names(schema=schema)
    if not tables:
        raise MetadataGenerationError(f"No tables discovered in schema '{schema}'.")

    collections: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    pk_map: Dict[str, List[str]] = {
        table: inspector.get_pk_constraint(table, schema=schema).get("constrained_columns", [])
        for table in tables
    }

    for table in tables:
        columns = inspector.get_columns(table, schema=schema)
        collection = _build_collection(table, schema, columns, pk_map[table])
        collections.append(collection)

    forward_names: dict[str, set[str]] = defaultdict(set)
    reverse_names: dict[str, set[str]] = defaultdict(set)

    for table in tables:
        fks = inspector.get_foreign_keys(table, schema=schema)
        for fk in fks:
            if not fk.get("referred_table"):
                continue
            parent = fk["referred_table"]
            forward, reverse = _build_relationships(
                parent_table=parent,
                child_table=table,
                constrained_columns=fk.get("constrained_columns", []),
                referred_columns=fk.get("referred_columns", []),
                pk_map=pk_map,
                forward_existing=forward_names[parent],
                reverse_existing=reverse_names[table],
                naming_strategy=config.relationship_namer,
            )
            relationships.append(forward)
            forward_names[parent].add(forward["name"])
            if reverse and config.include_reverse_relationships:
                relationships.append(reverse)
                reverse_names[table].add(reverse["name"])

    return {
        "name": config.graph_name,
        "version": "V2",
        "collections": collections,
        "relationships": relationships,
    }


def _build_collection(
    table: str,
    schema: Optional[str],
    columns: Iterable[Mapping[str, Any]],
    primary_keys: List[str],
) -> Dict[str, Any]:
    properties = [_build_column_property(col) for col in columns]

    if len(primary_keys) == 1:
        unique_properties: Iterable[str] | Iterable[List[str]] = primary_keys
    elif primary_keys:
        unique_properties = [primary_keys]
    else:
        unique_properties = [[]]

    table_path = f"{schema}.{table}" if schema else table

    return {
        "name": table,
        "type": "simple table",
        "table path": table_path,
        "unique properties": list(unique_properties),
        "properties": properties,
    }


def _build_column_property(column: Mapping[str, Any]) -> Dict[str, Any]:
    raw_type = column.get("type")
    data_type = _resolve_type_string(raw_type, column.get("dialect_options", {}))

    return {
        "name": column["name"],
        "type": "table column",
        "column name": column["name"],
        "data type": data_type,
    }


def _resolve_type_string(raw_type: Any, dialect_options: Mapping[str, Any]) -> str:
    if raw_type is None:
        return "string"

    # SQLAlchemy types may be instances or classes; normalise to class for lookup.
    type_class = getattr(raw_type, "__class__", raw_type)

    for sa_type, py_type in _SQLALCHEMY_TYPE_TO_PYDOUGH.items():
        try:
            if isinstance(raw_type, sa_type):
                return py_type
        except TypeError:
            # Some SQLAlchemy types are not hashable; fall back to class comparison.
            if issubclass(type_class, sa_type):  # type: ignore[arg-type]
                return py_type

    if isinstance(raw_type, _STRING_TYPES):
        return "string"

    # Dialect specific fallback (SQLite)
    affinity = getattr(raw_type, "affinity", None)
    if affinity and affinity.__name__.upper() in _SQLITE_FALLBACK:
        return _SQLITE_FALLBACK[affinity.__name__.upper()]

    # Literal type string fallback
    compiled = getattr(raw_type, "__visit_name__", "")
    if compiled:
        candidate = compiled.upper()
        for key, value in _SQLITE_FALLBACK.items():
            if key in candidate:
                return value

    # Strings reported via dialect options
    if "type" in dialect_options:
        literal = str(dialect_options["type"]).upper()
        for key, value in _SQLITE_FALLBACK.items():
            if key in literal:
                return value

    return "string"


def _unique_name(base: str, existing: set[str]) -> str:
    candidate = base
    counter = 2
    while candidate in existing:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate




def _build_relationships(
    *,
    parent_table: str,
    child_table: str,
    constrained_columns: Iterable[str],
    referred_columns: Iterable[str],
    pk_map: Mapping[str, List[str]],
    forward_existing: set[str],
    reverse_existing: set[str],
    naming_strategy: Optional[
        Callable[[str, str, bool, set[str], set[str]], Tuple[str, Optional[str]]]
    ] = None,
) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    constrained = list(constrained_columns)
    referred = list(referred_columns)
    if not constrained or not referred:
        raise MetadataGenerationError(
            f"Foreign key between {child_table} and {parent_table} is missing column mapping."
        )

    key_map = {parent: [child] for parent, child in zip(referred, constrained)}

    child_pk = set(pk_map.get(child_table, []))
    is_singular = set(constrained).issuperset(child_pk) and bool(child_pk)

    if naming_strategy:
        proposed_forward, proposed_reverse = naming_strategy(
            parent_table,
            child_table,
            is_singular,
            forward_existing,
            reverse_existing,
        )
    else:
        proposed_forward, proposed_reverse = _default_relationship_names(
            parent_table,
            child_table,
            is_singular,
            forward_existing,
            reverse_existing,
        )

    forward_name = proposed_forward
    if forward_name in forward_existing:
        forward_name = _unique_name(forward_name, forward_existing)
    reverse_name = proposed_reverse
    if reverse_name and reverse_name in reverse_existing:
        reverse_name = _unique_name(reverse_name, reverse_existing)

    forward = {
        "type": "simple join",
        "name": forward_name,
        "parent collection": parent_table,
        "child collection": child_table,
        "keys": key_map,
        "singular": is_singular,
    }

    reverse: Optional[Dict[str, Any]] = None
    if reverse_name:
        reverse = {
            "type": "reverse",
            "name": reverse_name,
            "original parent": parent_table,
            "original property": forward_name,
            "singular": True,
        }

    return forward, reverse


def _default_relationship_names(
    parent_table: str,
    child_table: str,
    is_singular: bool,
    forward_existing: set[str],
    reverse_existing: set[str],
) -> tuple[str, Optional[str]]:
    base_forward = _inflector.plural(child_table) if not is_singular else child_table
    forward_candidate = _ensure_identifier(base_forward or f"{child_table}_items")
    forward_name = _unique_name(forward_candidate, forward_existing)

    base_reverse = _inflector.singular_noun(parent_table) or parent_table
    reverse_candidate = _ensure_identifier(base_reverse or f"{parent_table}_record")
    reverse_name = _unique_name(reverse_candidate, reverse_existing) if reverse_candidate else None
    return forward_name, reverse_name


def _ensure_identifier(name: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", name).strip("_")
    if not slug:
        slug = "relationship"
    return slug


__all__ = ["generate_metadata", "write_metadata", "MetadataGenerationError", "MetadataGenerationConfig"]
