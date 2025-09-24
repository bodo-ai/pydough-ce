from __future__ import annotations

import pytest

from pydough_analytics.pipeline.analytics import AnalyticsPipelineError


@pytest.mark.live_llm
def test_live_sales_top_rows_natural(live_sales_engine) -> None:
    question = (
        "List the top 3 rows by the column 'amount' from the 'sales' table. "
        "Return only 'city' and 'amount', sorted by 'amount' in descending order."
    )

    try:
        result = live_sales_engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on live LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    df = result.dataframe.reset_index(drop=True)
    assert not df.empty
    assert "city" in df.columns
    assert "amount" in df.columns

    assert len(df) >= 3
    top3_amounts = list(df["amount"].astype(float)[:3])
    assert top3_amounts == sorted(top3_amounts, reverse=True)

    assert df.loc[0, "city"] == "New York"
