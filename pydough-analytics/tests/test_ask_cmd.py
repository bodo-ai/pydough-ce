import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock
from rich.table import Table

# Target under test
import src.pydough_analytics.commands.ask_cmd as ask_cmd
from src.pydough_analytics.commands.ask_cmd import (
    _df_like,
    _print_dataframe,
    _print_json,
    ask_from_cli,
)


# ---------------------------
# Helpers
# ---------------------------

class FakeDF:
    """
    Minimal DataFrame-like object used in tests.
    """
    def __init__(self, rows):
        self._rows = rows
        self.columns = list(rows[0].keys()) if rows else []
        self.empty = len(rows) == 0

    def head(self, n):
        return FakeDF(self._rows[:n])

    def iterrows(self):
        for i, row in enumerate(self._rows):
            # Simular comportamiento de pandas: cada row es un dict-like
            yield i, [row[c] for c in self.columns]

    def to_dict(self, orient="records"):
        assert orient == "records"
        return self._rows


# ---------------------------
# _df_like
# ---------------------------

def test_df_like_true_and_false():
    """
    Ensure _df_like checks for required attrs.
    """
    df_like = SimpleNamespace(empty=False, columns=["a"], iterrows=lambda: iter([]))
    not_df = SimpleNamespace(empty=False, columns=["a"])
    assert _df_like(df_like) is True
    assert _df_like(not_df) is False


# ---------------------------
# _print_dataframe
# ---------------------------

def test_print_dataframe_none(mocker):
    """
    If df is None, print warning.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    _print_dataframe(None, limit=5)
    mock_console.print.assert_called_once()
    args, _ = mock_console.print.call_args
    assert "No DataFrame returned" in args[0]


def test_print_dataframe_not_df_like(mocker):
    """
    Non-df-like objects are printed as-is.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    _print_dataframe("hello", limit=5)
    mock_console.print.assert_called_once_with("hello")


def test_print_dataframe_empty_df(mocker):
    """
    Empty df prints 'No rows returned'.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    df = FakeDF([])
    _print_dataframe(df, limit=5)
    # first print is the yellow message; there might be only one print
    args, _ = mock_console.print.call_args
    assert "No rows returned" in args[0]


def test_print_dataframe_populated_builds_table(mocker):
    """
    Populated df should render a rich Table with headers and rows.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    df = FakeDF([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    _print_dataframe(df, limit=5)

    # Assert that a Table was printed
    printed_args = [c.args[0] for c in mock_console.print.call_args_list]
    assert any(isinstance(arg, Table) for arg in printed_args), "Expected a rich.Table to be printed"


# ---------------------------
# _print_json
# ---------------------------

def test_print_json_happy_with_df(mocker):
    """
    _print_json should serialize df rows and pass structured data to console.print_json.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    res = SimpleNamespace(
        code="x=1",
        sql="SELECT 1",
        full_explanation="ok",
        exception=None,
        df=FakeDF([{"a": 1}]),
    )

    _print_json(res, question="How many?")
    mock_console.print_json.assert_called_once()
    _, kwargs = mock_console.print_json.call_args
    data = kwargs["data"]
    assert data["question"] == "How many?"
    assert data["code"] == "x=1"
    assert data["sql"] == "SELECT 1"
    assert data["explanation"] == "ok"
    assert data["exception"] is None
    assert data["rows"] == [{"a": 1}]


def test_print_json_handles_non_df(mocker):
    """
    If df is not df-like, rows should be None.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    res = SimpleNamespace(code=None, sql=None, full_explanation=None, exception=None, df="not-df")
    _print_json(res, question="Q")
    data = mock_console.print_json.call_args.kwargs["data"]
    assert data["rows"] is None


# ---------------------------
# ask_from_cli
# ---------------------------

def _make_result(code="print('ok')", sql="SELECT 1", df_rows=None, explanation="done", exception=None):
    df = FakeDF(df_rows or [{"x": 1}]) if exception is None else None
    return SimpleNamespace(code=code, sql=sql, df=df, full_explanation=explanation, exception=exception)

def test_ask_from_cli_json_mode(mocker):
    """
    When as_json=True, only print_json is used.
    """
    # Patch console to capture calls
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    # Patch LLMClient to a fake
    fake_client = MagicMock()
    fake_client.ask.return_value = _make_result()
    mocker.patch("src.pydough_analytics.commands.ask_cmd.LLMClient", return_value=fake_client)

    ask_from_cli(
        question="Q?",
        url="sqlite:///:memory:",
        db_name="DB",
        md_path="doc.md",
        kg_path="kg.json",
        as_json=True,
    )

    # Should have printed JSON and not the other sections
    mock_console.print_json.assert_called_once()
    # No code/SQL/Explanation/Result sections
    assert not any("PyDough code" in (c.args[0] if c.args else "") for c in mock_console.rule.call_args_list)


def test_ask_from_cli_error_path_prints_error_and_returns(mocker):
    """
    If result.exception is set, prints error and stops.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    fake_client = MagicMock()
    fake_client.ask.return_value = _make_result(exception="Boom!") 
    mocker.patch("src.pydough_analytics.commands.ask_cmd.LLMClient", return_value=fake_client)

    ask_from_cli(
        question="Q?",
        url="sqlite:///:memory:",
        db_name="DB",
        md_path="doc.md",
        kg_path="kg.json",
        as_json=False,
        show_sql=True,
        show_df=True,
        show_explanation=True,
    )

    # It should show code then error, but NOT SQL / DF / Explanation
    rules = [c.args[0] for c in mock_console.rule.call_args_list]
    assert any("PyDough code" in r for r in rules)
    assert any("Error" in r for r in rules)
    assert not any(r == "SQL" for r in rules)
    assert not any("Result preview" in r for r in rules)
    assert not any("Explanation" in r for r in rules)


def test_ask_from_cli_shows_sql_df_explanation_when_flags_true(mocker):
    """
    If flags are True and no exception, print all sections.
    """
    mock_console = MagicMock()
    mocker.patch.object(ask_cmd, "console", mock_console)

    fake_client = MagicMock()
    # Provide a DF with rows to trigger table rendering
    fake_client.ask.return_value = _make_result(sql="SELECT X", df_rows=[{"a": 1}], explanation="why")
    mocker.patch("src.pydough_analytics.commands.ask_cmd.LLMClient", return_value=fake_client)

    # Spy on _print_dataframe to assert it was called with 'rows'
    spy_print_df = mocker.patch("src.pydough_analytics.commands.ask_cmd._print_dataframe")

    ask_from_cli(
        question="Q?",
        url="sqlite:///:memory:",
        db_name="DB",
        md_path="doc.md",
        kg_path="kg.json",
        as_json=False,
        show_sql=True,
        show_df=True,
        show_explanation=True,
        rows=7,
    )

    rules = [c.args[0] for c in mock_console.rule.call_args_list]
    assert "PyDough code" in rules
    assert "SQL" in rules
    assert "Result preview" in rules
    assert "Explanation" in rules

    # SQL printed
    assert any("SELECT X" in (c.args[0] if c.args else "") for c in mock_console.print.call_args_list)

    # Dataframe preview called with correct limit
    spy_print_df.assert_called_once()
    _, kwargs = spy_print_df.call_args
    assert kwargs.get("limit") == 7
