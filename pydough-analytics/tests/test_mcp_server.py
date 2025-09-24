from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd
import pytest

fastmcp = pytest.importorskip("fastmcp")

import importlib

server_module = importlib.import_module("pydough_analytics.mcp.server")
from pydough_analytics.pipeline.analytics import AnalyticsResult


class _StubEngine:
    def __init__(self, result: AnalyticsResult):
        self._result = result
        self.asks: list[str] = []

    def ask(self, question: str, *, max_attempts: int = 2, max_rows: int = 100):
        self.asks.append(question)
        return self._result


def test_mcp_open_and_ask(monkeypatch, tmp_path):
    # create metadata file
    metadata = [
        {
            "name": "SALES",
            "version": "V2",
            "collections": [
                {
                    "name": "sales",
                    "type": "simple table",
                    "table path": "main.sales",
                    "unique properties": ["id"],
                    "properties": [
                        {"name": "id", "type": "table column", "column name": "id", "data type": "numeric"},
                        {"name": "amount", "type": "table column", "column name": "amount", "data type": "numeric"},
                    ],
                }
            ],
            "relationships": [],
        }
    ]
    metadata_file = tmp_path / "sales.json"
    metadata_file.write_text(json.dumps(metadata), encoding="utf-8")

    result_df = pd.DataFrame({"id": [1], "amount": [100.0]})
    analytics_result = AnalyticsResult(
        dataframe=result_df,
        sql="SELECT 1",
        code="result = ...",
        explanation="stub",
        attempts=1,
        llm_raw="{}",
    )

    stub_engine = _StubEngine(analytics_result)

    def _stub_create_engine(metadata_path, graph_name, database_url, execution_timeout):
        assert Path(metadata_path).exists()
        return stub_engine

    monkeypatch.setattr(server_module, "_create_engine", _stub_create_engine)

    session_resp = asyncio.run(
        server_module.open_session_impl(
            database_url="sqlite:///example.db",
            graph_name="SALES",
            metadata_path=str(metadata_file),
        )
    )
    session_id = session_resp["session_id"]
    assert session_id in server_module._sessions

    ask_resp = asyncio.run(
        server_module.ask_impl(session_id=session_id, question="Top rows")
    )
    assert ask_resp["rows"][0]["amount"] == 100.0
    assert stub_engine.asks == ["Top rows"]

    schema_resp = asyncio.run(server_module.schema_markdown_impl(session_id=session_id))
    assert "sales" in schema_resp["markdown"].lower()

    result_resource = asyncio.run(server_module.result_resource_impl(session_id))
    assert result_resource["sql"] == "SELECT 1"

    asyncio.run(server_module.close_session_impl(session_id=session_id))
    assert session_id not in server_module._sessions

