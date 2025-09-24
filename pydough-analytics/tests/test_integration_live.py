from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from pydough_analytics.metadata.generator import generate_metadata, write_metadata
from pydough_analytics.pipeline.analytics import AnalyticsEngine, AnalyticsPipelineError


LIVE_ENV_FLAG = "PYDOUGH_ANALYTICS_RUN_LIVE"


def _live_enabled() -> bool:
    return os.getenv(LIVE_ENV_FLAG, "").lower() in {"1", "true", "yes"}


@pytest.mark.live_llm
def test_live_sqlite(tmp_path: Path) -> None:
    if not _live_enabled():
        pytest.skip(f"set {LIVE_ENV_FLAG}=1 to run live LLM tests")

    db_path = tmp_path / "sales.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE sales (id INTEGER PRIMARY KEY, city TEXT, amount REAL)"
    )
    cur.executemany(
        "INSERT INTO sales (city, amount) VALUES (?, ?)",
        [
            ("New York", 100.0),
            ("New York", 50.0),
            ("Chicago", 80.0),
            ("San Francisco", 40.0),
        ],
    )
    conn.commit()
    conn.close()

    metadata = generate_metadata(f"sqlite:///{db_path}", graph_name="SALES")
    metadata_path = tmp_path / "sales.json"
    write_metadata(metadata, metadata_path)

    engine = AnalyticsEngine(
        metadata_path=metadata_path,
        graph_name="SALES",
        database_url=f"sqlite:///{db_path}",
        execution_timeout=15.0,
    )

    question = (
        "Respond with the exact PyDough code `result = sales.TOP_K(3, by=amount.DESC())` "
        "and return the result. Do not introduce CALCULATE or aliases."
    )
    try:
        result = engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed: {exc}")

    assert not result.dataframe.empty
    assert "city" in result.dataframe.columns
    assert "amount" in result.dataframe.columns


@pytest.mark.live_llm
def test_live_postgres() -> None:
    pg_url = os.getenv("PYDOUGH_ANALYTICS_LIVE_PG_URL")
    metadata_path = os.getenv("PYDOUGH_ANALYTICS_LIVE_PG_METADATA")
    if not (_live_enabled() and pg_url and metadata_path):
        pytest.skip(
            "set PYDOUGH_ANALYTICS_RUN_LIVE=1, PYDOUGH_ANALYTICS_LIVE_PG_URL, "
            "and PYDOUGH_ANALYTICS_LIVE_PG_METADATA to run"
        )

    engine = AnalyticsEngine(
        metadata_path=metadata_path,
        graph_name=os.getenv("PYDOUGH_ANALYTICS_LIVE_PG_GRAPH", "DATABASE"),
        database_url=pg_url,
        execution_timeout=20.0,
    )

    question = os.getenv(
        "PYDOUGH_ANALYTICS_LIVE_PG_QUESTION",
        "Respond with the exact PyDough code `result = payments.TOP_K(3, by=amount.DESC())` and return the result.",
    )

    try:
        result = engine.ask(question, max_attempts=3, max_rows=10)
    except AnalyticsPipelineError as exc:  # pragma: no cover - depends on LLM
        pytest.fail(f"Live Gemini call failed for Postgres: {exc}")

    assert not result.dataframe.empty
