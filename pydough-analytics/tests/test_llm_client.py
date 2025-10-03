import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

# Target under test
from src.pydough_analytics.llm.llm_client import LLMClient, Result


# ---------------------------
# Helpers
# ---------------------------

@pytest.fixture(autouse=True)
def _patch_llmclient_default_prompt_read(mocker):
    """
    Patch read_file used by LLMClient.__init__ so tests that only instantiate LLMClient.
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        return_value="DUMMY_PROMPT_CONTENT"
    )

class FakeDF:
    """
    Minimal DataFrame-like object for serialization tests.
    """
    def __init__(self, rows):
        self._rows = rows
    def to_dict(self, orient="records"):
        assert orient == "records"
        return self._rows


# ---------------------------
# Result.to_dict
# ---------------------------

def test_result_to_dict_serializes_df():
    """
    Ensure Result.to_dict() serializes df via to_dict(records).
    """
    df = FakeDF([{"a": 1}])
    r = Result(
        pydough_code="x=1",
        full_explanation="ok",
        df=df,
        exception=None,
        original_question="Q",
        sql_output="SELECT 1"
    )
    out = r.to_dict()
    assert out["code"] == "x=1"
    assert out["sql"] == "SELECT 1"
    assert out["df"] == [{"a": 1}]
    assert out["full_explanation"] == "ok"
    assert out["exception"] is None
    assert out["original_question"] == "Q"


# ---------------------------
# LLMClient.ask (happy path) - provider returns TEXT
# ---------------------------

def test_llmclient_ask_happy_text_only(mocker):
    """
    ask(): extracts python code, executes, and returns Result with df/sql and explanation cleaned.
    """
    # read_file for prompt & script
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=["PROMPT {script_content} {database_content} {similar_queries} {recomendation} {definitions}", "SCRIPTX"],
    )
    # markdown load
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.load_markdown",
        return_value="# DB MARKDOWN",
    )
    # provider
    fake_provider = MagicMock()
    # Response contains code block + explanation
    provider_text = "```python\nx=1\n```\nThis is an explanation."
    fake_provider.ask.return_value = provider_text
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.get_provider",
        return_value=fake_provider,
    )
    # code extraction & execution
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.extract_python_code",
        return_value="x=1",
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.execute_code_and_extract_result",
        return_value=(FakeDF([{"r": 1}]), "SELECT 1"),
    )

    c = LLMClient(provider="google", model="gemini")
    res = c.ask(
        question="How many rows?",
        kg_path="graph.json",
        md_path="docs.md",
        db_name="DB1",
        db_config={"engine": "sqlite", "database": ":memory:"},
    )

    # Validations
    assert isinstance(res, Result)
    assert res.code == "x=1"
    assert res.sql == "SELECT 1"
    assert res.df.to_dict("records") == [{"r": 1}]
    assert "```python" not in res.full_explanation
    assert "This is an explanation." in res.full_explanation
    # DB markdown map is populated
    assert c.db_markdown_map["DB1"] == "# DB MARKDOWN"
    fake_provider.ask.assert_called_once()


# ---------------------------
# LLMClient.ask (happy path) - provider returns (TEXT, usage)
# ---------------------------

def test_llmclient_ask_happy_tuple_response(mocker):
    """
    ask(): handles tuple (raw_text, usage) and still extracts code.
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=["PROMPT {script_content} {database_content}", "SCRIPTY"],
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.load_markdown",
        return_value="DBDOC",
    )
    fake_provider = MagicMock()
    fake_provider.ask.return_value = ("```python\nprint(1)\n```\nDone.", {"usage": 1})
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.get_provider",
        return_value=fake_provider,
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.extract_python_code",
        return_value="print(1)",
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.execute_code_and_extract_result",
        return_value=(FakeDF([{"x": 1}]), "SELECT X"),
    )

    c = LLMClient(provider="google", model="gemini")
    res = c.ask(
        "Q",
        kg_path="kg.json",
        md_path="md.md",
        db_name="DB",
        db_config={"engine": "sqlite", "database": ":memory:"},
    )
    assert res.code == "print(1)"
    assert res.sql == "SELECT X"
    assert res.df.to_dict("records") == [{"x": 1}]
    assert "```python" not in res.full_explanation


# ---------------------------
# LLMClient.ask (error path) - no auto-correct
# ---------------------------

def test_llmclient_ask_exception_no_autocorrect(mocker):
    """
    ask(): on exception and auto_correct=False, returns Result with .exception populated.
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=["PROMPT {script_content} {database_content}", "S"],
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.load_markdown",
        return_value="MD",
    )
    fake_provider = MagicMock()
    fake_provider.ask.return_value = "```python\nx=boom()\n```\nExplain."
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.get_provider",
        return_value=fake_provider,
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.extract_python_code",
        return_value="x=boom()",
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.execute_code_and_extract_result",
        side_effect=RuntimeError("exec failed"),
    )

    c = LLMClient()
    res = c.ask("Q?", kg_path="kg", md_path="md", db_name="DB", auto_correct=False)
    assert isinstance(res, Result)
    assert res.exception is not None
    assert "exec failed" in res.exception


# ---------------------------
# LLMClient.ask (error path) - WITH auto-correct
# ---------------------------

def test_llmclient_ask_exception_with_autocorrect_calls_correct(mocker):
    """
    ask(): on exception and auto_correct=True, calls .correct() and returns its result.
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=["PROMPT {script_content} {database_content}", "S"],
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.load_markdown",
        return_value="MD",
    )
    fake_provider = MagicMock()
    fake_provider.ask.return_value = "```python\nx=boom()\n```"
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.get_provider",
        return_value=fake_provider,
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.extract_python_code",
        return_value="x=boom()",
    )
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.execute_code_and_extract_result",
        side_effect=RuntimeError("exec failed"),
    )

    c = LLMClient()
    # Patch correct to confirm it's called and to return a sentinel result
    sentinel = Result(pydough_code="fixed", original_question="Q")
    mocker.patch.object(c, "correct", return_value=sentinel)

    res = c.ask(
        "Q",
        kg_path="kg",
        md_path="md",
        db_name="DB",
        auto_correct=True,
        max_corrections=2,
    )
    assert res is sentinel
    c.correct.assert_called_once()
    # Ensure max_corrections was decremented (verified via call kwargs)
    kwargs = c.correct.call_args.kwargs
    assert kwargs.get("max_corrections") == 1


# ---------------------------
# LLMClient.discourse
# ---------------------------

def test_discourse_no_result_returns_followup():
    """
    discourse(): if result is falsy, returns follow-up unchanged.
    """
    c = LLMClient()
    out = c.discourse(None, "Next?")
    assert out == "Next?"


def test_discourse_no_code():
    """
    discourse(): if result exists but no code, include original question, explain lack of code.
    """
    c = LLMClient()
    r = Result(pydough_code=None, original_question="When?", df=None)
    out = c.discourse(r, "Next?")
    assert "original question" in out
    assert "Next?" in out


def test_discourse_with_code_and_df():
    """
    discourse(): if code and df exist, include both in the reformulated prompt.
    """
    c = LLMClient()
    r = Result(pydough_code="x=1", original_question="Q", df=FakeDF([{"a": 1}]))
    out = c.discourse(r, "Follow up?")
    assert "You solved this question:" in out
    assert "x=1" in out
    assert "Follow up?" in out


# ---------------------------
# LLMClient.add_definition
# ---------------------------

def test_add_definition_appends():
    """
    add_definition(): append non-empty definitions.
    """
    c = LLMClient()
    assert c.definitions == []
    c.add_definition("NEW DEF")
    assert c.definitions == ["NEW DEF"]


# ---------------------------
# LLMClient.format_prompt
# ---------------------------

def test_format_prompt_uses_map_and_context(mocker):
    """
    format_prompt(): builds formatted question and prompt using db markdown and context.
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=[
            # prompt template with placeholders expected by the code
            "SCRIPT:{script_content}\nDB:{database_content}\nSIM:{similar_queries}\nREC:{recomendation}\nDEF:{definitions}",
            "SCRIPT-CONTENT",
        ],
    )
    c = LLMClient()
    # Preload db markdown map as if ask() had done it
    c.db_markdown_map["MyDB"] = "## TABLES ..."

    formatted_q, formatted_prompt = c.format_prompt(
        question="How many orders?",
        db_name="MyDB",
        context_data={
            "context_id": "rec-123",
            "similar_queries": "SELECT COUNT(*) FROM orders;",
            "redefined_question": "Count orders in 2024",
        },
    )

    # formatted_q must include database schema text
    assert "Database Schema:" in formatted_q
    assert "## TABLES ..." in formatted_q
    assert "Count orders in 2024" in formatted_q

    # formatted_prompt must resolve placeholders
    assert "SCRIPT:SCRIPT-CONTENT" in formatted_prompt
    assert "DB:## TABLES ..." in formatted_prompt
    assert "SIM:SELECT COUNT(*) FROM orders;" in formatted_prompt
    assert "REC:rec-123" in formatted_prompt
    # Empty definitions by default -> empty string
    assert "DEF:" in formatted_prompt


# ---------------------------
# LLMClient.correct
# ---------------------------

def test_correct_calls_ask_with_corrective_question(mocker):
    """
    correct(): builds a corrective prompt and delegates back to ask().
    """
    mocker.patch(
        "src.pydough_analytics.llm.llm_client.read_file",
        side_effect=["PROMPT T", "SCR"],
    )
    c = LLMClient()
    # Patch format_prompt to avoid re-reading files; return deterministic values
    mocker.patch.object(c, "format_prompt", return_value=("Q-ORIG", "PROMPT-FMT"))
    # Patch ask to capture the corrective_question and return a sentinel
    sentinel = Result(pydough_code="fixed", original_question="orig")
    mocker.patch.object(c, "ask", return_value=sentinel)

    r = Result(pydough_code="x=1", original_question="orig", exception="ZeroDivisionError")
    out = c.correct(
        result=r,
        kg_path="kg",
        db_config={"engine": "sqlite"},
        md_path="md",
        db_name="DB",
        context_data={"x": 1},
    )

    assert out is sentinel
    # Ensure "corrective" question was built and ask() got called
    args, kwargs = c.ask.call_args
    assert "error occurred" in args[0].lower()
    assert "x=1" in args[0]
    assert "zerodivisionerror" in args[0].lower()
    assert kwargs["db_name"] == "DB"
    assert kwargs["kg_path"] == "kg"
    assert kwargs["md_path"] == "md"
