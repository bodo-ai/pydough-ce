from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Mapping

from .markdown import metadata_to_markdown
from .summary import summarise_metadata

logger = logging.getLogger(__name__)

SchemaRenderer = Callable[[Mapping[str, Any], int, int], str]


def _markdown_renderer(metadata: Mapping[str, Any], max_collections: int, max_columns: int) -> str:
    return metadata_to_markdown(metadata)


def _summary_renderer(metadata: Mapping[str, Any], max_collections: int, max_columns: int) -> str:
    return summarise_metadata(
        metadata,
        max_collections=max_collections,
        max_columns=max_columns,
    )


def _json_renderer(metadata: Mapping[str, Any], max_collections: int, max_columns: int) -> str:
    return json.dumps(metadata, indent=2)


_RENDERERS: Dict[str, SchemaRenderer] = {
    "markdown": _markdown_renderer,
    "summary": _summary_renderer,
    "json": _json_renderer,
    "none": lambda _metadata, _max_collections, _max_columns: "",
}


def register_schema_renderer(name: str, renderer: SchemaRenderer) -> None:
    _RENDERERS[name.strip().lower()] = renderer


def render_schema(
    metadata: Mapping[str, Any],
    *,
    style: str = "markdown",
    max_collections: int = 12,
    max_columns: int = 8,
) -> str:
    normalized = (style or "markdown").strip().lower()
    renderer = _RENDERERS.get(normalized)
    if renderer is None:
        logger.warning(
            "Unknown schema style '%s'; falling back to markdown", normalized
        )
        renderer = _RENDERERS["markdown"]
    return renderer(metadata, max_collections, max_columns)


__all__ = ["render_schema", "register_schema_renderer", "SchemaRenderer"]
