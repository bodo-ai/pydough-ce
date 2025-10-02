import re
import pytest
from unittest.mock import MagicMock

# Target under test
from src.pydough_analytics.commands.generate_md_cmd import generate_markdown_from_config


# ---------------------------
# Success scenarios
# ---------------------------

md_success_cases = [
    pytest.param(
        dict(graph_name="TestGraph", json_path="graph.json", md_path="graph.md"),
        "# Test Markdown",
        id="valid_markdown",
    ),
]


@pytest.mark.parametrize("params,expected_output", md_success_cases)
def test_generate_markdown_success_cases(tmp_path, mocker, capsys, params, expected_output):
    """
    Verify that generate_markdown_from_config
    """
    mock_graph = MagicMock()

    # Patch dependencies imported inside the module under test
    mocker.patch(
        "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
        return_value=mock_graph,
    )
    mocker.patch(
        "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata",
        return_value=expected_output,
    )
    mock_save = mocker.patch("src.pydough_analytics.commands.generate_md_cmd.save_markdown")

    json_path = tmp_path / params["json_path"]
    md_path = tmp_path / params["md_path"]

    # Execute
    generate_markdown_from_config(
        params["graph_name"],
        str(json_path),
        str(md_path),
    )

    # Ensure the markdown was saved with the expected content
    mock_save.assert_called_once_with(md_path, expected_output)

    # Ensure stdout contains the confirmation message and stderr is empty
    captured = capsys.readouterr()
    assert f"Markdown written to {md_path}" in captured.out
    assert captured.err == ""


# ---------------------------
# Error scenarios
# ---------------------------

md_error_cases = [
    pytest.param(
        dict(graph_name="Graph", json_path="bad.json", md_path="graph.md"),
        "parse_error",
        r"\[ERROR\] Failed to generate Markdown: invalid JSON",
        id="parse_failure",
    ),
    pytest.param(
        dict(graph_name="Graph", json_path="graph.json", md_path="graph.md"),
        "generation_error",
        r"\[ERROR\] Failed to generate Markdown: generation fail",
        id="generation_failure",
    ),
    pytest.param(
        dict(graph_name="Graph", json_path="graph.json", md_path="graph.md"),
        "save_error",
        r"\[ERROR\] Failed to generate Markdown: disk full",
        id="save_failure",
    ),
]


@pytest.mark.parametrize("params,fail_type,stderr_pattern", md_error_cases)
def test_generate_markdown_error_cases(tmp_path, mocker, capsys, params, fail_type, stderr_pattern):
    """
    Verify that generate_markdown_from_config
    """
    if fail_type == "parse_error":
        # Simulate a parsing failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            side_effect=Exception("invalid JSON"),
        )

    elif fail_type == "generation_error":
        # Simulate a markdown generation failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            return_value=MagicMock(),
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata",
            side_effect=Exception("generation fail"),
        )

    elif fail_type == "save_error":
        # Simulate a save-to-disk failure
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.parse_json_metadata_from_file",
            return_value=MagicMock(),
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.generate_markdown_from_metadata",
            return_value="# Markdown",
        )
        mocker.patch(
            "src.pydough_analytics.commands.generate_md_cmd.save_markdown",
            side_effect=Exception("disk full"),
        )

    md_path = tmp_path / params["md_path"]

    # The function should exit with code 1 on any failure
    with pytest.raises(SystemExit) as e:
        generate_markdown_from_config(
            params["graph_name"],
            str(tmp_path / params["json_path"]),
            str(md_path),
        )

    assert e.value.code == 1

    # Ensure stderr matches the expected error pattern and stdout is empty
    captured = capsys.readouterr()
    assert re.search(stderr_pattern, captured.err), (
        f"Expected stderr to match: {stderr_pattern}\nGot:\n{captured.err}"
    )
    assert captured.out == ""
