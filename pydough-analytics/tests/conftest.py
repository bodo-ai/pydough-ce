from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest

from pydough_analytics.pipeline.analytics import AnalyticsEngine


LIVE_ENV_FLAG = "PYDOUGH_ANALYTICS_RUN_LIVE"


@pytest.fixture
def ensure_live_env() -> Generator[None, None, None]:
    enabled = os.getenv(LIVE_ENV_FLAG, "").lower() in {"1", "true", "yes"}
    if not enabled:
        pytest.skip(f"set {LIVE_ENV_FLAG}=1 to run live LLM tests")
    yield


@pytest.fixture
def live_sales_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    metadata_path = repo_root / "metadata" / "live_sales.json"
    db_path = repo_root / "metadata" / "live_sales.db"
    if not metadata_path.exists() or not db_path.exists():
        pytest.skip("live sales sample metadata/db not found")
    return metadata_path, db_path


@pytest.fixture
def live_sales_engine(ensure_live_env, live_sales_paths) -> AnalyticsEngine:
    metadata_path, db_path = live_sales_paths
    return AnalyticsEngine(
        metadata_path=metadata_path,
        graph_name="SALES",
        database_url=f"sqlite:///{db_path}",
        execution_timeout=15.0,
    )
