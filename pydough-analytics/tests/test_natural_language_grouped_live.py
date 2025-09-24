
from __future__ import annotations

import pandas as pd
import pytest

from pydough_analytics.pipeline.analytics import AnalyticsPipelineError


@pytest.mark.live_llm
@pytest.mark.xfail(reason="Aggregate grouping via CALCULATE may fail with current PyDough version", strict=False)
def test_grouped_total_by_city(live_sales_engine) -> None:
    question = (
        "Total sales amount by city. Return columns city and total_amount; sort by total_amount desc."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert "city" in df.columns
    metric = next((c for c in df.columns if c not in {"city", "id"} and pd.api.types.is_numeric_dtype(df[c])), None)
    assert metric is not None
    totals = {row["city"]: float(row[metric]) for _, row in df.iterrows()}
    assert totals.get("New York") == pytest.approx(150.0)
    assert totals.get("Chicago") == pytest.approx(80.0)
    assert totals.get("San Francisco") == pytest.approx(40.0)


@pytest.mark.live_llm
@pytest.mark.xfail(reason="Aggregate grouping via CALCULATE may fail with current PyDough version", strict=False)
def test_grouped_average_by_city(live_sales_engine) -> None:
    question = (
        "Average sales amount by city. Return columns city and avg_amount; sort by avg_amount desc."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert "city" in df.columns
    metric = next((c for c in df.columns if c not in {"city", "id"} and pd.api.types.is_numeric_dtype(df[c])), None)
    assert metric is not None
    avgs = {row["city"]: float(row[metric]) for _, row in df.iterrows()}
    assert avgs.get("Chicago") == pytest.approx(80.0)
    assert avgs.get("New York") == pytest.approx(75.0)
    assert avgs.get("San Francisco") == pytest.approx(40.0)


@pytest.mark.live_llm
@pytest.mark.xfail(reason="Aggregate grouping via CALCULATE may fail with current PyDough version", strict=False)
def test_highest_grossing_city(live_sales_engine) -> None:
    question = (
        "Which city has the highest total sales? Return city and a total metric; limit 1."
    )
    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=1)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert len(df) >= 1
    assert df.loc[0, "city"] == "New York"
