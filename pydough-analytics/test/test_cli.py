import re
import pytest
import json
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

# Valid CLI usage cases
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
]

@pytest.mark.parametrize("args,expected_code,expected_output_pattern", valid_cli_cases)
def test_general_cli_cases(runner, args, expected_code, expected_output_pattern):
    """
    Tests valid CLI flags and help messages.
    """
    result = runner.invoke(app, args)
    
    # Assert output content
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    )
    if args in (["--version"], ["-V"]):
        assert re.search(expected_output_pattern, result.stdout), (
            f"Expected version pattern not found in:\n{result.stdout}"
        )
    else:
        assert expected_output_pattern in result.stdout, (
            f"Expected output not found in:\n{result.stdout}"
        )


# Invalid CLI usage cases
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
    
    # Assert output content
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.exit_code}. Output:\n{result.stdout}"
    )
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected:{expected_output}\nOriginal Output:\n{result.stderr}"
    )


# Generate json error cases
generate_json_error_cases = [
    pytest.param(
        ["generate-json"],
        2,
        "Missing option '--engine'",
        id="json_missing_all"
    ),
    pytest.param(
        ["generate-json", "--engine", "sqlite"],
        2,
        "Missing option '--database'",
        id="json_missing_database"
    ),
    pytest.param(
        ["generate-json", "--engine", "test", "--database", "test.db", "--graph-name", "Test", "--json-path", "out.json"],
        1,
        "ERROR",
        id="json_invalid_path"
    ),
]

@pytest.mark.parametrize("args,expected_code,expected_output", generate_json_error_cases)
def test_generate_json_errors(runner, args, expected_code, expected_output):
    """
    Tests various invalid cases for generate-json command.
    """
    result = runner.invoke(app, args)
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.stdout}."
    )
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected:{expected_output}\nOriginal Output:\n{result.stderr}"
    )


# Generate md error cases
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
    Tests various invalid cases for generate-md command.
    """
    result = runner.invoke(app, args)
    assert result.exit_code == expected_code, (
        f"Unexpected exit code: {result.exit_code}."
    )
    assert expected_output in result.stderr, (
        f"Expected error message not found.\nExpected:{expected_output}\nOriginal Output:\n{result.stderr}"
    )


def test_generate_json_creates_file(runner, tmp_path):
    output_path = tmp_path / "temp.json"

    result = runner.invoke(app, [
        "generate-json",
        "--engine", "sqlite",
        "--database", "temp.db",
        "--graph-name", "temp",
        "--json-path", str(output_path)
    ], input="\n")

    assert result.exit_code == 0, (
        f"Unexpected exit code: {result.exit_code}."
    )
    content = json.loads(output_path.read_text())
    assert isinstance(content, list), (
        f"Unexpected type: {type(content)}."
    )
    assert len(content) > 0, (
        f"Unexpected length: {len(content)}."
    )


def test_generate_md_from_json(runner, tmp_path):
	json_path = tmp_path / "temp.json"
	md_path = tmp_path / "temp.md"

	result_json = runner.invoke(app, [
        "generate-json",
        "--engine", "sqlite",
        "--database", "temp.db",
        "--graph-name", "temp",
        "--json-path", str(json_path)
    ], input="\n")
    
	assert result_json.exit_code == 0, (
        f"Unexpected json exit code: {result_json.exit_code}."
    )

	result_md = runner.invoke(app, [
        "generate-md",
        "--graph-name", "temp",
        "--json-path", str(json_path),
        "--md-path", str(md_path)
    ])

	assert result_md.exit_code == 0, (
        f"Unexpected md exit code: {result_md.exit_code}."
    )
	content = md_path.read_text(encoding="utf-8")
	assert "# Metadata Overview: temp (Graph Name)" in content, (
        f"Unexpected content: {content}."
    )