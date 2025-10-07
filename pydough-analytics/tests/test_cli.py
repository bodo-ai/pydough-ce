import re
import pytest
import json
from unittest.mock import MagicMock

# Target under test
from src.pydough_analytics.cli import app


# Regex pattern for version output
VERSION_PATTERN = r"pydough-analytics \d+\.\d+\.\d+" 


@pytest.fixture(autouse=True)
def mock_version(mocker):
    """
    Mock the __version__ variable to ensure a consistent version output 
    for the version tests.
    """
    mocker.patch('src.pydough_analytics._version', '1.0.0')


# ---------------------------
# Valid CLI usage
# ---------------------------

valid_cli_cases = [
    pytest.param(
        ["--version"],
        0,
        VERSION_PATTERN,
        id="version_long"
    ),
    pytest.param(
        ["-V"],
        0,
        VERSION_PATTERN,
        id="version_short"
    ),
    pytest.param(
        ["--help"],
        0,
        "PyDough Analytics Community Edition tooling.",
        id="help_root"
    ),
    pytest.param(
        ["generate-json", "--help"],
        0,
        "Generate metadata from a database",
        id="help_generate_json"
    ),
    pytest.param(
        ["generate-md", "--help"],
        0,
        "Generate Markdown documentation",
        id="help_generate_md"
    ),
    pytest.param(
        ["ask", "--help"],
        0,
        "Ask a natural language question",
        id="help_generate_md"
    ),
]

@pytest.mark.parametrize("args,expected_code,expected_output_pattern", valid_cli_cases)
def test_general_cli_cases(runner, args, expected_code, expected_output_pattern):
    """
    Tests valid CLI flags and help messages.
    """
    result = runner.invoke(app, args)
    
    # Exit code must match
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    )

    # For version, use regex; for help, assert substring
    if args in (["--version"], ["-V"]):
        assert re.search(expected_output_pattern, result.stdout), (
            f"Expected version pattern not found in:\n{result.stdout}"
        )
    else:
        assert expected_output_pattern in result.stdout, (
            f"Expected output not found in:\n{result.stdout}"
        )


# ---------------------------
# Invalid CLI usage
# ---------------------------

invalid_cli_cases = [
    pytest.param(
        ["-v"],
        2,
        "No such option: -v",
        id="invalid_version_flag"
    ),
    pytest.param(
        ["-help"],
        2,
        "No such option: -h",
        id="invalid_help_flag"
    ),
    pytest.param(
        ["invalid-command"],
        2,
        "No such command 'invalid-command'",
        id="invalid_command"
    ),
]

@pytest.mark.parametrize("args,expected_code,expected_output", invalid_cli_cases)
def test_invalid_cli_cases(runner, args, expected_code, expected_output):
    """
    Tests invalid CLI arguments, flags, or commands.
    """
    result = runner.invoke(app, args) 
    
    # Typer returns 2 for CLI-usage errors
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    )
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected:{expected_output}\nOriginal Output:\n{result.stderr}"
    )


# ---------------------------
# Required options checks
# ---------------------------

generate_json_error_cases = [
    pytest.param(
        ["generate-json"],
        2,
        "Missing option '--url'",
        id="json_missing_all"
    ),
    pytest.param(
        ["generate-json", "--url", "sqlite:///test.db"],
        2,
        "Missing option '--graph-name'",
        id="json_missing_database"
    ),
    pytest.param(
        ["generate-json", "--url", "sqlite///test.db", "--graph-name", "Test", "--json-path", "out.json"],
        1,
        "ERROR",
        id="json_url_path"
    ),
]

@pytest.mark.parametrize("args,expected_code,expected_output", generate_json_error_cases)
def test_generate_json_errors(runner, args, expected_code, expected_output):
    """
    Validate that 'generate-json' enforces required options and shows Typer errors.
    """
    result = runner.invoke(app, args)
    assert result.exit_code == expected_code, f"Unexpected exit code: {result.exit_code}"
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected: {expected_output}\nGot:\n{result.stderr}"
    )


generate_md_error_cases = [
    pytest.param(
        ["generate-md"],
        2,
        "Missing option '--graph-name'",
        id="md_missing_all"
    ),
    pytest.param(
        ["generate-md", "--graph-name", "Test"],
        2,
        "Missing option '--json-path'",
        id="md_missing_json_path"
    ),
    pytest.param(
        ["generate-md", "--graph-name", "Test", "--json-path", "out.json", "--md-path", "out.md"],
        1,
        "ERROR",
        id="md_missing_json_path"
    ),
]

@pytest.mark.parametrize("args,expected_code,expected_output", generate_md_error_cases)
def test_generate_md_errors(runner, args, expected_code, expected_output):
    """
    Validate that 'generate-md' enforces required options and shows Typer errors.
    """
    result = runner.invoke(app, args)
    assert result.exit_code == expected_code, f"Unexpected exit code: {result.exit_code}"
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected: {expected_output}\nGot:\n{result.stderr}"
    )


# ---------------------------
# Command delegation checks
# ---------------------------

def test_generate_json_creates_file(runner, mocker):
    """
    Ensure 'generate-json' command delegates to generate_metadata_from_config
    with the exact arguments provided by the user.
    """
    mock_impl = mocker.patch(
        "src.pydough_analytics.cli.generate_metadata_from_config", return_value=None
    )

    args = [
        "generate-json",
        "--url", "sqlite:///temp.db",
        "--graph-name", "temp",
        "--json-path", "out.json",
    ]
    result = runner.invoke(app, args)

    assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    mock_impl.assert_called_once_with("sqlite:///temp.db", "temp", "out.json")


def test_generate_md_from_json(runner, mocker):
    """
    Ensure 'generate-json' command delegates to generate_metadata_from_config
    with the exact arguments provided by the user.
    """
    mock_impl = mocker.patch(
        "src.pydough_analytics.cli.generate_metadata_from_config", return_value=None
    )

    args = [
        "generate-json",
        "--url", "sqlite:///temp.db",
        "--graph-name", "temp",
        "--json-path", "out.json",
    ]
    result = runner.invoke(app, args)

    assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    mock_impl.assert_called_once_with("sqlite:///temp.db", "temp", "out.json")

def test_ask_delegates_to_impl(runner, mocker):
    """
    Ensure 'ask' command delegates to ask_from_cli with the correct arguments.
    """
    mock_impl = mocker.patch("src.pydough_analytics.cli.ask_from_cli", return_value=None)

    args = [
        "ask",
        "--question", "How many rows?",
        "--url", "sqlite:///test.db",
        "--db-name", "TestDB",
        "--md-path", "docs.md",
        "--kg-path", "graph.json",
        "--provider", "openai",
        "--model", "gpt-4",
        "--show-sql",
        "--show-df",
        "--show-explanation",
        "--as-json",
        "--rows", "50",
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 0

    mock_impl.assert_called_once_with(
        question="How many rows?",
        url="sqlite:///test.db",
        db_name="TestDB",
        md_path="docs.md",
        kg_path="graph.json",
        provider="openai",
        model="gpt-4",
        show_sql=True,
        show_df=True,
        show_explanation=True,
        as_json=True,
        rows=50,
    )
