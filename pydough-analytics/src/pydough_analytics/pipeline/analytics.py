"""High level orchestration for text-to-analytics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from ..llm.client import (
    LLMInvocationError,
    LLMResponse,
    BaseLLMClient,
    create_llm_client,
)
from ..prompting.builder import PromptBuilder
from ..prompting.config import PromptConfig
from ..runtime.executor import ExecutionResult, PyDoughExecutionError, PyDoughExecutor


@dataclass
class AnalyticsResult:
    dataframe: pd.DataFrame
    sql: str
    code: str
    explanation: Optional[str]
    attempts: int
    llm_raw: str


class AnalyticsPipelineError(RuntimeError):
    """Raised when the text-to-analytics pipeline exhausts retries."""


class AnalyticsEngine:
    """Coordinates prompting, LLM execution, and PyDough evaluation."""

    def __init__(
        self,
        *,
        metadata_path: Path | str,
        graph_name: str,
        database_url: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.2,
        top_p: Optional[float] = 0.95,
        top_k: Optional[int] = None,
        llm_client: Optional[BaseLLMClient] = None,
        llm_provider: Optional[str] = None,
        llm_max_retries: int = 2,
        llm_retry_backoff: float = 2.0,
        execution_timeout: float = 10.0,
        prompt_config: Optional[PromptConfig] = None,
    ) -> None:
        self._metadata_path = Path(metadata_path)
        self._metadata = _load_metadata(self._metadata_path, graph_name)
        self._prompt_builder = PromptBuilder(self._metadata, config=prompt_config)
        self._runtime = PyDoughExecutor(
            metadata_path=metadata_path,
            graph_name=graph_name,
            database_url=database_url,
            execution_timeout=execution_timeout,
        )
        if llm_client is not None:
            self._llm = llm_client
        else:
            self._llm = create_llm_client(
                provider=llm_provider,
                model=model,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_retries=llm_max_retries,
                retry_backoff=llm_retry_backoff,
            )
        self._execution_timeout = execution_timeout

    def ask(
        self,
        question: str,
        *,
        max_attempts: int = 2,
        max_rows: int = 100,
    ) -> AnalyticsResult:
        last_error: Optional[str] = None
        previous_code: Optional[str] = None
        for attempt in range(1, max_attempts + 1):
            prompt = self._prompt_builder.build(
                question,
                previous_code=previous_code,
                error_message=last_error,
            )
            try:
                llm_response = self._llm.generate(prompt)
            except LLMInvocationError as exc:
                raise AnalyticsPipelineError(str(exc)) from exc

            code = llm_response.code
            try:
                execution = self._runtime.execute(
                    code,
                    max_rows=max_rows,
                    timeout=self._execution_timeout,
                )
            except PyDoughExecutionError as exc:
                last_error = str(exc)
                previous_code = code
                if attempt == max_attempts:
                    raise AnalyticsPipelineError(last_error) from exc
                continue

            return AnalyticsResult(
                dataframe=execution.dataframe,
                sql=execution.sql,
                code=execution.executed_code,
                explanation=llm_response.explanation,
                attempts=attempt,
                llm_raw=llm_response.raw_text,
            )

        raise AnalyticsPipelineError(last_error or "Unknown failure")


def _load_metadata(path: Path, graph_name: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Metadata file '{path}' does not exist")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Metadata file must contain a list of graphs")

    for graph in payload:
        if isinstance(graph, dict) and graph.get("name") == graph_name:
            return graph

    raise ValueError(f"Graph '{graph_name}' not found in metadata file {path}")


__all__ = ["AnalyticsEngine", "AnalyticsResult", "AnalyticsPipelineError"]
