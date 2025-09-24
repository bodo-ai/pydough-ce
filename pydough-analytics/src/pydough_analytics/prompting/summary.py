"""Helpers to summarise PyDough metadata for prompting."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def summarise_metadata(metadata: Mapping[str, Any], *, max_collections: int = 12, max_columns: int = 8) -> str:
    """Produce a compact, human-readable summary of the metadata.

    The summary keeps only the first ``max_columns`` scalar properties per
    collection to avoid overflowing the prompt context window.
    """

    collections = metadata.get("collections", [])
    lines: list[str] = []

    for collection in collections[:max_collections]:
        name = collection["name"]
        props = [p for p in collection.get("properties", []) if p.get("type") == "table column"]
        prop_names = ", ".join(p.get("name", "") for p in props[:max_columns])
        if prop_names:
            lines.append(f"- {name}: columns -> {prop_names}")
        else:
            lines.append(f"- {name}: column definitions available")

    return "\n".join(lines)
