"""Render PyDough metadata into a Markdown cheat sheet."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping


def _format_columns(properties: Iterable[Mapping[str, Any]]) -> list[str]:
    lines: list[str] = []
    for prop in properties:
        if prop.get("type") != "table column":
            continue
        name = prop.get("name", "<unknown>")
        data_type = prop.get("data type")
        column_name = prop.get("column name")
        detail_parts = []
        if data_type:
            detail_parts.append(str(data_type))
        if column_name and column_name != name:
            detail_parts.append(f"col: {column_name}")
        detail = f" ({', '.join(detail_parts)})" if detail_parts else ""
        lines.append(f"  - `{name}`{detail}")
    return lines


def _format_relationship(rel: Mapping[str, Any]) -> str:
    rel_type = rel.get("type")
    if rel_type == "simple join":
        child = rel.get("child collection")
        keys = rel.get("keys", {})
        key_pairs = []
        for parent_key, child_keys in keys.items():
            joined = ", ".join(child_keys)
            key_pairs.append(f"{parent_key} -> {joined}")
        key_text = "; ".join(key_pairs) if key_pairs else ""
        singular = "one" if rel.get("singular") else "many"
        suffix = f" (keys: {key_text})" if key_text else ""
        return f"  - `{rel['name']}` → `{child}` ({singular}){suffix}"
    if rel_type == "reverse":
        parent = rel.get("original parent")
        original = rel.get("original property")
        return f"  - `{rel['name']}` (reverse of `{parent}.{original}`)"
    return f"  - `{rel.get('name', '<unknown>')}` ({rel_type})"


def metadata_to_markdown(metadata: Mapping[str, Any]) -> str:
    """Convert PyDough metadata JSON (single-graph) to Markdown."""

    graph_name = metadata.get("name", "Graph")
    collections = metadata.get("collections", [])
    relationships = metadata.get("relationships", [])

    simple_join_lookup = {
        (rel.get("parent collection"), rel.get("name")): rel
        for rel in relationships
        if rel.get("type") == "simple join"
    }

    rel_map: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for rel in relationships:
        rel_type = rel.get("type")
        if rel_type == "simple join":
            parent = rel.get("parent collection")
            if parent:
                rel_map[parent].append(rel)
        elif rel_type == "reverse":
            original_parent = rel.get("original parent")
            original_property = rel.get("original property")
            original = simple_join_lookup.get((original_parent, original_property))
            child_collection = None
            if original:
                child_collection = original.get("child collection")
            if child_collection:
                rel_map[child_collection].append(rel)

    lines: list[str] = [f"# PyDough Graph: {graph_name}"]

    if collections:
        lines.append("## Collections overview")
        for collection in collections:
            lines.append(f"- `{collection.get('name', '<unknown>')}`")
        lines.append("")

    for collection in collections:
        name = collection.get("name", "<unknown>")
        lines.append(f"## `{name}`")
        columns = _format_columns(collection.get("properties", []))
        if columns:
            lines.append("- Columns:")
            lines.extend(columns)
        else:
            lines.append("- Columns: (none listed)")

        rels = rel_map.get(name, [])
        if rels:
            lines.append("- Relationships:")
            lines.extend(_format_relationship(rel) for rel in rels)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


__all__ = ["metadata_to_markdown"]
