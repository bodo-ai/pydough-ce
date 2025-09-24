"""LLM client abstractions for pydough-analytics."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol

import google.genai as genai
from google.genai import types

from ..config.env import get_env, get_gemini_api_key
from ..prompting.builder import Prompt

logger = logging.getLogger(__name__)


class BaseLLMClient(Protocol):
    def generate(self, prompt: Prompt) -> "LLMResponse":
        ...


@dataclass
class LLMResponse:
    code: str
    explanation: Optional[str]
    raw_text: str
    usage_metadata: Optional[Any]


class LLMInvocationError(RuntimeError):
    """Raised when the LLM call fails or returns an invalid payload."""


class GeminiClient:
    """Thin wrapper around the Google Gemini APIs with JSON-mode defaults."""

    def __init__(
        self,
        *,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.2,
        top_p: Optional[float] = 0.95,
        top_k: Optional[int] = None,
        api_key: Optional[str] = None,
        max_retries: int = 2,
        retry_backoff: float = 2.0,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
        self._client = genai.Client(api_key=api_key or get_gemini_api_key())
        self._response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "code": types.Schema(type=types.Type.STRING),
                "explanation": types.Schema(type=types.Type.STRING),
            },
            required=["code"],
        )
        self._max_retries = max(0, max_retries)
        self._retry_backoff = max(0.5, retry_backoff)

    def generate(self, prompt: Prompt) -> LLMResponse:
        config_kwargs = {
            'system_instruction': prompt.system,
            'temperature': self._temperature,
            'response_mime_type': 'application/json',
            'response_schema': self._response_schema,
        }
        if self._top_p is not None:
            config_kwargs['top_p'] = self._top_p
        if self._top_k is not None:
            config_kwargs['top_k'] = self._top_k
        config = types.GenerateContentConfig(**config_kwargs)

        attempts = self._max_retries + 1
        last_exception: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt.user)])],
                    config=config,
                )
                break
            except Exception as exc:  # pragma: no cover - google-genai provides context
                last_exception = exc
                if attempt >= attempts:
                    raise LLMInvocationError(f"Gemini request failed: {exc}") from exc
                wait_time = self._retry_backoff * attempt
                logger.warning("Gemini request failed (attempt %s/%s): %s", attempt, attempts, exc)
                time.sleep(wait_time)
        else:  # pragma: no cover (guard)
            raise LLMInvocationError(f"Gemini request failed: {last_exception}")

        payload = response.text or ""
        if not payload:
            raise LLMInvocationError("Gemini returned an empty response.")

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            fallback_code = _extract_python_code(payload)
            if fallback_code:
                logger.warning("Gemini returned non-JSON payload; using extracted code block.")
                return LLMResponse(
                    code=fallback_code.strip(),
                    explanation=None,
                    raw_text=payload,
                    usage_metadata=getattr(response, "usage_metadata", None),
                )
            raise LLMInvocationError(
                "Gemini response was not valid JSON as requested."
            ) from exc

        code = (parsed.get("code") or "").strip()
        if not code:
            raise LLMInvocationError("Gemini response did not include code.")

        explanation = parsed.get("explanation")
        if isinstance(explanation, str):
            explanation = explanation.strip()

        return LLMResponse(
            code=code,
            explanation=explanation or None,
            raw_text=payload,
            usage_metadata=getattr(response, "usage_metadata", None),
        )


LLMClientFactory = Callable[..., BaseLLMClient]

_CLIENT_FACTORIES: Dict[str, LLMClientFactory] = {}


def register_llm_client(name: str, factory: LLMClientFactory) -> None:
    _CLIENT_FACTORIES[name.strip().lower()] = factory


def create_llm_client(provider: Optional[str] = None, **kwargs) -> BaseLLMClient:
    resolved = provider or get_env("PYDOUGH_ANALYTICS_LLM_PROVIDER") or "gemini"
    factory = _CLIENT_FACTORIES.get(resolved.strip().lower())
    if factory is None:
        raise ValueError(f"Unknown LLM provider '{resolved}'. Registered providers: {list(_CLIENT_FACTORIES)}")
    return factory(**kwargs)


def _gemini_factory(**kwargs) -> GeminiClient:
    return GeminiClient(
        model=kwargs.get("model", "gemini-2.0-flash"),
        temperature=kwargs.get("temperature", 0.2),
        top_p=kwargs.get("top_p", 0.95),
        top_k=kwargs.get("top_k"),
        api_key=kwargs.get("api_key"),
        max_retries=kwargs.get("max_retries", 2),
        retry_backoff=kwargs.get("retry_backoff", 2.0),
    )


register_llm_client("gemini", _gemini_factory)


__all__ = [
    "GeminiClient",
    "LLMResponse",
    "LLMInvocationError",
    "BaseLLMClient",
    "register_llm_client",
    "create_llm_client",
]


def _extract_python_code(payload: str) -> str | None:
    code_pattern = re.compile(r"```python\s*(.*?)```", re.DOTALL | re.IGNORECASE)
    match = code_pattern.findall(payload)
    if match:
        return match[-1]
    generic_pattern = re.compile(r"```\s*(.*?)```", re.DOTALL)
    match = generic_pattern.findall(payload)
    if match:
        return match[-1]
    return None
