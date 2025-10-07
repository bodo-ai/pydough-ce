import re
import pytest
from pathlib import Path
from sqlalchemy.engine import Engine
from unittest.mock import MagicMock

# Target under test
from src.pydough_analytics.commands.generate_json_cmd import (
    get_engine_from_credentials,
    list_all_tables_and_columns,
    generate_metadata_from_config,
)


# ---------------------------
# get_engine_from_credentials
# ---------------------------

engine_cases = [
    pytest.param(
        "sqlite:///dummy.db",
        "sqlite",
        id="valid_sqlite",
    ),
    pytest.param(
        {"database": "dummy.db"},
        pytest.raises(ValueError),
        id="missing_engine",
    ),
]


@pytest.mark.parametrize("url,expected", engine_cases)
def test_get_engine_from_credentials(mocker, url, expected):
    """
    Ensure get_engine_from_credentials
    """
    mock_engine = MagicMock(spec=Engine)

    # Patch Connector in the module under test
    mock_connector_cls = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.Connector"
    )
    mock_connector_cls.return_value.get_engine.return_value = mock_engine

    if isinstance(expected, str):
        # Happy path
        engine, db_type, _ = get_engine_from_credentials(url)
        assert engine is mock_engine
        assert db_type == expected
        mock_connector_cls.assert_called_once()
    else:
        # Error path (missing `engine` key)
        with expected:
            get_engine_from_credentials(url)


# ---------------------------
# list_all_tables_and_columns
# ---------------------------

tables_cases = [
    pytest.param(["customers", "orders"], "sqlite", "", None, id="two_tables"),
    pytest.param([], "sqlite", "", None, id="no_tables"),
    pytest.param(Exception("Inspector error"), "sqlite", "", pytest.raises(RuntimeError), id="inspector_error"),
]


@pytest.mark.parametrize("mock_result,db_type,schema,expected", tables_cases)
def test_list_all_tables_and_columns(mocker, mock_result, db_type, schema, expected):
    """
    Ensure list_all_tables_and_columns
    """
    mock_engine = MagicMock(spec=Engine)
    mock_inspect = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.inspect"
    )

    if isinstance(mock_result, Exception):
        # Simulate failure in `inspect(engine)`
        mock_inspect.side_effect = mock_result
        with expected:
            list_all_tables_and_columns(mock_engine, db_type, schema)
    else:
        # Normal behavior
        mock_inspect.return_value.get_table_names.return_value = mock_result
        tables = list_all_tables_and_columns(mock_engine, db_type, schema)
        assert tables == mock_result


# ---------------------------
# generate_metadata_from_config (success)
# ---------------------------

md_success_cases = [
    pytest.param(
        dict(url="sqlite:///memory.db", graph_name="TestGraph"),
        [{"name": "customers"}],
        id="valid_metadata",
    ),
]


@pytest.mark.parametrize("params,expected_metadata", md_success_cases)
def test_generate_metadata_from_config_success(tmp_path, mocker, capsys, params, expected_metadata):
    """
    Success flow for generate_metadata_from_config
    """
    mock_engine = MagicMock(spec=Engine)

    # Patch dependencies used inside the module under test
    mock_connector_cls = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.Connector"
    )
    mock_connector_cls.return_value.get_engine.return_value = mock_engine

    mock_inspect = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.inspect"
    )
    mock_inspect.return_value.get_table_names.return_value = ["customers"]

    mock_generate_metadata = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.generate_metadata",
        return_value=expected_metadata,
    )

    mock_save_json = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.save_json"
    )

    json_path = tmp_path / "out.json"

    # Execute
    result = generate_metadata_from_config(
        url=params["url"],
        graph_name=params["graph_name"],
        json_path=str(json_path),
    )

    # Validate returned metadata
    assert result == expected_metadata

    # Validate save_json call (first arg must be Path)
    mock_save_json.assert_called_once_with(Path(json_path), expected_metadata)

    # Validate generate_metadata call signature
    gm_args, gm_kwargs = mock_generate_metadata.call_args
    # (engine_obj, graph_name, db_type, table_list)
    assert gm_args[0] is mock_engine
    assert gm_args[1] == params["graph_name"]
    assert gm_args[3] == ["customers"]
    assert gm_args[2] == "sqlite"  # db_type from get_engine_from_credentials

    # Validate stdout messages and ensure no stderr
    captured = capsys.readouterr()
    assert f"Connecting to '{params['graph_name']}'..." in captured.out
    assert "Generating metadata for 1 tables..." in captured.out
    assert f"Metadata for '{params['graph_name']}' written to: {json_path}" in captured.out
    assert captured.err == ""


# ---------------------------
# generate_metadata_from_config (errors)
# ---------------------------

md_error_cases = [
    pytest.param(
        dict(url="memory.db", graph_name="TestGraph"),
        "connector_error",
        r"\[ERROR\] Failed to generate Metadata: .*",
        id="invalid_engine_connector_fail",
    ),
    pytest.param(
        dict(url="sqlite:///memory.db", graph_name="TestGraph"),
        "inspect_error",
        r"\[ERROR\] Failed to generate Metadata: Failed to inspect tables: boom on inspect",
        id="inspect_failure",
    ),
    pytest.param(
        dict(url="sqlite:///memory.db", graph_name="TestGraph"),
        "generate_metadata_error",
        r"\[ERROR\] Failed to generate Metadata: gen failed",
        id="generation_failure",
    ),
    pytest.param(
        dict(url="sqlite:///memory.db", graph_name="TestGraph"),
        "save_error",
        r"\[ERROR\] Failed to generate Metadata: disk full",
        id="save_failure",
    ),
]


@pytest.mark.parametrize("params,fail_type,stderr_pattern", md_error_cases)
def test_generate_metadata_from_config_errors(tmp_path, mocker, capsys, params, fail_type, stderr_pattern):
    """
    Error flows for generate_metadata_from_config
    """
    mock_engine = MagicMock(spec=Engine)
    json_path = tmp_path / "out.json"

    # Common patches for successful parts unless overridden by a failing branch
    mock_connector_cls = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.Connector"
    )
    mock_connector_cls.return_value.get_engine.return_value = mock_engine

    mock_inspect = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.inspect"
    )
    mock_inspect.return_value.get_table_names.return_value = ["customers"]

    mock_generate_metadata = mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.generate_metadata",
        return_value=[{"name": "customers"}],
    )
    mocker.patch(
        "src.pydough_analytics.commands.generate_json_cmd.save_json",
        side_effect=None,
    )

    # Inject specific failures per branch
    if fail_type == "connector_error":
        # Failure happens right after the initial "Connecting..." print
        mock_connector_cls.side_effect = Exception("bad engine")
    elif fail_type == "inspect_error":
        # list_all_tables_and_columns wraps this into RuntimeError("Failed to inspect tables: ...")
        mock_inspect.side_effect = Exception("boom on inspect")
    elif fail_type == "generate_metadata_error":
        # Failure occurs after printing "Generating metadata for N tables..."
        mock_generate_metadata.side_effect = Exception("gen failed")
    elif fail_type == "save_error":
        # Failure occurs after metadata generation succeeded
        mocker.patch(
            "src.pydough_analytics.commands.generate_json_cmd.save_json",
            side_effect=Exception("disk full"),
        )

    # Execute and assert SystemExit(1)
    with pytest.raises(SystemExit) as e:
        generate_metadata_from_config(
            url=params.get("url"),
            graph_name=params.get("graph_name"),
            json_path=str(json_path),
        )
    assert e.value.code == 1

    # Validate stderr contains the formatted error
    captured = capsys.readouterr()
    assert re.search(stderr_pattern, captured.err), (
        f"Expected stderr to match: {stderr_pattern}\nGot:\n{captured.err}"
    )

    # Validate stdout by phase — progress logs can legitimately appear before the crash
    if fail_type == "connector_error":
        # Only the initial "Connecting..." is expected
        assert f"Connecting to '{params['graph_name']}'..." in captured.out
    elif fail_type == "inspect_error":
        # We printed "Connecting..." before attempting inspection
        assert f"Connecting to '{params['graph_name']}'..." in captured.out
    elif fail_type == "generate_metadata_error":
        # We printed both "Connecting..." and "Generating metadata..." before failing
        assert f"Connecting to '{params['graph_name']}'..." in captured.out
        assert "Generating metadata for 1 tables..." in captured.out
    elif fail_type == "save_error":
        # We printed both "Connecting..." and "Generating metadata..." before failing on save
        assert f"Connecting to '{params['graph_name']}'..." in captured.out
        assert "Generating metadata for 1 tables..." in captured.out
