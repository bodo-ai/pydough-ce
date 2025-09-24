"""Environment and configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()


class MissingConfig(RuntimeError):
    """Raised when a required configuration value is missing."""


def get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> str | None:
    """Fetch an environment variable, optionally enforcing its presence."""

    value = os.getenv(key, default)
    if required and value in {None, ""}:
        raise MissingConfig(f"Environment variable '{key}' is required.")
    return value


@lru_cache(maxsize=None)
def get_gemini_api_key() -> str:
    """Convenience accessor for the Gemini API key."""

    key = get_env("GEMINI_API_KEY", required=True)
    assert key is not None
    return key
