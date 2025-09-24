from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from pydough_analytics.llm.client import LLMResponse
from pydough_analytics.metadata.generator import generate_metadata, write_metadata
from pydough_analytics.pipeline.analytics import AnalyticsEngine


class _StubLLM:
    def __init__(self, response: LLMResponse) -> None:
        self._response = response
        self.calls = 0

    def generate(self, prompt):  # pragma: no cover - simple stub
        self.calls += 1
        return self._response


def test_engine_with_stub_llm(tmp_path):
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
        ],
    )
    conn.commit()
    conn.close()

    metadata = generate_metadata(f"sqlite:///{db_path}", graph_name="SALES")
    metadata_path = tmp_path / "sales.json"
    write_metadata(metadata, metadata_path)

    stub_response = LLMResponse(
        code="result = sales.TOP_K(5, by=amount.DESC())",
        explanation="Top rows by amount",
        raw_text="{}",
        usage_metadata=None,
    )

    engine = AnalyticsEngine(
        metadata_path=metadata_path,
        graph_name="SALES",
        database_url=f"sqlite:///{db_path}",
        llm_client=_StubLLM(stub_response),
    )

    result = engine.ask("Top rows by amount", max_attempts=1, max_rows=5)
    expected = pd.DataFrame(
        {"id": [1, 3, 2], "city": ["New York", "Chicago", "New York"], "amount": [100.0, 80.0, 50.0]}
    )
    pd.testing.assert_frame_equal(result.dataframe.reset_index(drop=True), expected)
