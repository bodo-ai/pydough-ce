from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..config.env import get_env

logger = logging.getLogger(__name__)


def _parse_int(value: Optional[str], *, default: int, var_name: str) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
        if parsed <= 0:
            raise ValueError
        return parsed
    except ValueError:
        logger.warning(
            "Invalid value '%s' for %s; falling back to %s",
            value,
            var_name,
            default,
        )
        return default


@dataclass(slots=True)
class PromptConfig:
    schema_style: str = "markdown"
    schema_max_collections: int = 12
    schema_max_columns: int = 8
    system_instruction: Optional[str] = None
    guide_text: Optional[str] = None

    @classmethod
    def from_env(cls) -> "PromptConfig":
        style = (get_env("PYDOUGH_ANALYTICS_SCHEMA_STYLE") or "markdown").strip().lower()
        max_collections = _parse_int(
            get_env("PYDOUGH_ANALYTICS_SCHEMA_MAX_COLLECTIONS"),
            default=12,
            var_name="PYDOUGH_ANALYTICS_SCHEMA_MAX_COLLECTIONS",
        )
        max_columns = _parse_int(
            get_env("PYDOUGH_ANALYTICS_SCHEMA_MAX_COLUMNS"),
            default=8,
            var_name="PYDOUGH_ANALYTICS_SCHEMA_MAX_COLUMNS",
        )
        system_path = get_env("PYDOUGH_ANALYTICS_SYSTEM_PROMPT_PATH")
        system_instruction = None
        if system_path:
            from pathlib import Path

            try:
                system_instruction = Path(system_path).read_text(encoding="utf-8").strip()
            except Exception as exc:  # pragma: no cover - IO errors
                logger.warning(
                    "Failed to load system prompt from %s: %s", system_path, exc
                )
                system_instruction = None

        guide_path = get_env("PYDOUGH_ANALYTICS_GUIDE_PATH")
        guide_text = None
        if guide_path:
            from pathlib import Path

            try:
                guide_text = Path(guide_path).read_text(encoding="utf-8").strip()
            except Exception as exc:  # pragma: no cover - IO errors
                logger.warning("Failed to load guide from %s: %s", guide_path, exc)
                guide_text = None

        return cls(
            schema_style=style,
            schema_max_collections=max_collections,
            schema_max_columns=max_columns,
            system_instruction=system_instruction,
            guide_text=guide_text,
        )


__all__ = ["PromptConfig"]

