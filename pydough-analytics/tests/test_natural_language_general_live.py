
from __future__ import annotations

import pytest

from pydough_analytics.pipeline.analytics import AnalyticsPipelineError


@pytest.mark.live_llm
def test_general_preview_sales(live_sales_engine) -> None:
    question = "Give me a quick preview of the sales data with city and amount, sorted by amount descending."
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=5)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed: {exc}")
    df = result.dataframe
    assert not df.empty
    assert "amount" in df.columns


@pytest.mark.live_llm
def test_general_show_top_sales(live_sales_engine) -> None:
    question = "Show me the top sales."
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=3)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed: {exc}")
    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert "amount" in df.columns
    amounts = df["amount"].astype(float).tolist()
    assert amounts == sorted(amounts, reverse=True)


@pytest.mark.live_llm
def test_general_sales_for_specific_cities(live_sales_engine) -> None:
    question = "Show sales for New York or Chicago (only those cities)."
    try:
        result = live_sales_engine.ask(question, max_attempts=4, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed: {exc}")
    df = result.dataframe
    assert not df.empty
    assert "city" in df.columns
    cities = set(df["city"].tolist())
    assert cities.issubset({"New York", "Chicago"})
    assert {"New York", "Chicago"}.intersection(cities)


@pytest.mark.live_llm
def test_general_smallest_sales(live_sales_engine) -> None:
    question = "Show the smallest sales amounts."
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=2)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed: {exc}")
    df = result.dataframe.reset_index(drop=True)
    assert len(df) >= 1
    assert "amount" in df.columns
    amounts = df["amount"].astype(float).tolist()
    assert amounts == sorted(amounts)
