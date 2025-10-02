import pytest
from unittest.mock import MagicMock

from src.pydough_analytics.commands.generate_md_cmd import generate_markdown_from_config

# Success scenarios
md_success_cases = [
    pytest.param(
        dict(graph_name="TestGraph", json_path="graph.json", md_path="graph.md"),
        "# Test Markdown",
        id="valid_markdown"
    ),
]

@pytest.mark.parametrize("params,expected_output", md_success_cases)
def test_generate_markdown_success_cases(tmp_path, mocker, params, expected_output):
    """
    Success cases for generate_markdown_from_config.
    """
    mock_graph = MagicMock()
    # Patch dependencies for a successful run
    mocker.patch(
        "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file", 
        return_value=mock_graph
    )
    mocker.patch(
        "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata", 
        return_value=expected_output
    )
    mock_save = mocker.patch("src.pydough_analytics.commands.generate_md_cmd.save_markdown")

    md_path = tmp_path / params.get("md_path")

    # Execute function
    generate_markdown_from_config(
        params.get("graph_name"),
        str(tmp_path / params.get("json_path")), 
        str(md_path)
    )

    # Validate calls
    mock_save.assert_called_once_with(md_path, expected_output)


# Error scenarios
md_error_cases = [
    pytest.param(
        dict(graph_name="Graph", json_path="bad.json", md_path="graph.md"),
        "parse_error",
        id="parse_failure"
    ),
    pytest.param(
        dict(graph_name="Graph", json_path="graph.json", md_path="graph.md"),
        "generation_error",
        id="generation_failure"
    ),
    pytest.param(
        dict(graph_name="Graph", json_path="graph.json", md_path="graph.md"),
        "save_error",
        id="save_failure"
    ),
]

@pytest.mark.parametrize("params,fail_type", md_error_cases)
def test_generate_markdown_error_cases(tmp_path, mocker, params, fail_type):
    """
    Error cases for generate_markdown_from_config.
    """
    if fail_type == "parse_error":
        # Simulate parse failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            side_effect=Exception("invalid JSON")
        )
    elif fail_type == "generation_error":
        # Simulate markdown generation failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            return_value=MagicMock()
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata",
            side_effect=Exception("generation fail")
        )
    elif fail_type == "save_error":
        # Simulate save failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            return_value=MagicMock()
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata",
            return_value="# Markdown"
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.save_markdown",
            side_effect=Exception("disk full")
        )

    md_path = tmp_path / params["md_path"]

    # Function should exit with code 1 on any failure
    with pytest.raises(SystemExit) as e:
        generate_markdown_from_config(
            params["graph_name"], str(tmp_path / params["json_path"]), str(md_path)
        )

    assert e.value.code == 1
