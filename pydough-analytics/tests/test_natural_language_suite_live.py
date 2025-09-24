
from __future__ import annotations

import pytest

from pydough_analytics.pipeline.analytics import AnalyticsPipelineError


@pytest.mark.live_llm
def test_bottom_two_sales_by_amount_rows(live_sales_engine) -> None:
    question = (
        "Return the bottom 2 individual sales by amount from the sales table, "
        "with columns city and amount, sorted by amount ascending."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=2)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert len(df) == 2
    assert {"city", "amount"}.issubset(df.columns)
    amounts = df["amount"].astype(float).tolist()
    assert amounts == sorted(amounts)


@pytest.mark.live_llm
def test_top_two_sales_by_amount_rows(live_sales_engine) -> None:
    question = (
        "Return the top 2 individual sales by amount from the sales table, "
        "with columns city and amount, sorted by amount desc."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=2)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert len(df) == 2
    assert {"city", "amount"}.issubset(df.columns)
    amounts = df["amount"].astype(float).tolist()
    assert amounts == sorted(amounts, reverse=True)
    assert df.loc[0, "city"] == "New York"


@pytest.mark.live_llm
def test_order_by_city_then_amount(live_sales_engine) -> None:
    question = (
        "Show sales ordered by city ascending, then amount descending. "
        "Return columns city and amount and limit 5 rows."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=5)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert {"city", "amount"}.issubset(df.columns)
    cities = df["city"].tolist()
    assert cities == sorted(cities)


@pytest.mark.live_llm
def test_filter_new_york_sales(live_sales_engine) -> None:
    question = (
        "List all sales for New York with their amounts. "
        "Return only city and amount."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert {"city", "amount"}.issubset(df.columns)
    assert all(c == "New York" for c in df["city"].tolist())
    assert len(df) == 2


@pytest.mark.live_llm
def test_limit_and_filter_by_threshold(live_sales_engine) -> None:
    question = (
        "List sales where amount is at least 50. Return city and amount, "
        "sorted by amount desc, limit 3."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert {"city", "amount"}.issubset(df.columns)
    assert df["amount"].astype(float).ge(50).all()
