import pytest
from pathlib import Path
from sqlalchemy.engine import Engine
from unittest.mock import MagicMock

from src.pydough_analytics.commands.generate_json_cmd import (
    get_engine_from_credentials,
    list_all_tables_and_columns,
    generate_metadata_from_config,
)

# get_engine_from_credentials scenarios
engine_cases = [
    pytest.param(
        {"engine": "sqlite", "database": "dummy.db"},
        "sqlite",
        id="valid_sqlite"
    ),
    pytest.param(
        {"database": "dummy.db"},
        pytest.raises(ValueError),
        id="missing_engine"
    ),
]

@pytest.mark.parametrize("config,expected", engine_cases)
def test_get_engine_from_credentials(mocker, config, expected):
    """
    Test get_engine_from_credentials
    """
    mock_engine = MagicMock(spec=Engine)
    mock_connector = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.Connector")
    mock_connector.return_value.get_engine.return_value = mock_engine

    if isinstance(expected, str):
        engine, db_type = get_engine_from_credentials(config.copy())
        assert engine is mock_engine
        assert db_type == expected
    else:
        with expected:
            get_engine_from_credentials(config.copy())


# list_all_tables_and_columns scenarios
tables_cases = [
    pytest.param(["customers", "orders"], "", id="two_tables"),
    pytest.param([], "", id="no_tables"),
    pytest.param(Exception("Inspector error"), pytest.raises(RuntimeError), id="inspector_error"),
]

@pytest.mark.parametrize("mock_result,expected", tables_cases)
def test_list_all_tables_and_columns(mocker, mock_result, expected):
    """
    Test list_all_tables_and_columns
    """
    mock_engine = MagicMock(spec=Engine)
    mock_inspector = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.inspect")

    if isinstance(expected, RuntimeError):
        mock_inspector.side_effect = mock_result
        with expected:
            list_all_tables_and_columns(mock_engine)
    else:
        mock_inspector.return_value.get_table_names.return_value = mock_result
        tables = list_all_tables_and_columns(mock_engine)
        assert tables == mock_result


# generate_metadata_from_config scenarios
metadata_cases = [
    pytest.param(
        dict(engine="sqlite", database="memory.db", graph_name="TestGraph"),
        True,
        id="valid_metadata"
    ),
    pytest.param(
        dict(engine=None, database="memory.db", graph_name="TestGraph"),
        pytest.raises(RuntimeError),
        id="invalid_engine"
    ),
]

@pytest.mark.parametrize("params,expected", metadata_cases)
def test_generate_metadata_from_config(tmp_path, mocker, params, expected):
    """
    Test generate_metadata_from_config
    """
    mock_engine = MagicMock(spec=Engine)
    mock_connector = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.Connector")
    mock_connector.return_value.get_engine.return_value = mock_engine

    mock_inspector = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.inspect")
    mock_inspector.return_value.get_table_names.return_value = ["customers"]

    mock_generate_metadata = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.generate_metadata")
    mock_generate_metadata.return_value = [{"name": "customers"}]

    mock_save_json = mocker.patch("src.pydough_analytics.commands.generate_json_cmd.save_json")

    json_path = tmp_path / "out.json"

    if isinstance(expected, RuntimeError):
        with expected:
            generate_metadata_from_config(
                engine=params.get("engine"),
                database=params.get("database"),
                graph_name=params.get("graph_name"),
                json_path=str(json_path),
            )   
    else:
        metadata = generate_metadata_from_config(
            engine=params.get("engine"),
            database=params.get("database"),
            graph_name=params.get("graph_name"),
            json_path=str(json_path),
        )
        assert metadata == [{"name": "customers"}]
        mock_save_json.assert_called_once_with(Path(json_path), [{"name": "customers"}])
