from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from .metadata.generator import MetadataGenerationError, generate_metadata, write_metadata
from .pipeline.analytics import AnalyticsEngine, AnalyticsPipelineError
from .prompting.markdown import metadata_to_markdown

console = Console()

app = typer.Typer(help="PyDough Analytics Community Edition tooling.")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show pydough-analytics version and exit",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR).",
    ),
):
    """Global options for the CLI."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )
    if version:
        from ._version import __version__

        console.print(f"pydough-analytics {__version__}")
        raise typer.Exit()


@app.command("init-metadata")
def init_metadata(
    url: str = typer.Argument(..., help="SQLAlchemy database URL, e.g. sqlite:///tpch.db"),
    output: Path = typer.Option(..., "--output", "-o", help="Destination JSON file."),
    graph_name: str = typer.Option("DATABASE", help="Name assigned to the metadata graph."),
    schema: Optional[str] = typer.Option(None, help="Optional schema to reflect."),
    no_reverse: bool = typer.Option(
        False,
        help="Disable emitting reverse relationships (parent <- child).",
    ),
    write_markdown: bool = typer.Option(
        True,
        "--write-markdown/--no-write-markdown",
        help="Also generate a Markdown schema summary.",
    ),
    markdown_path: Optional[Path] = typer.Option(
        None,
        "--markdown-path",
        help="Path for the Markdown summary (defaults to JSON path with .md).",
    ),
) -> None:
    """Generate a PyDough metadata knowledge graph for a database."""

    console.print(f"Generating metadata for [bold]{url}[/bold] ...")
    try:
        metadata = generate_metadata(
            url,
            graph_name=graph_name,
            schema=schema,
            include_reverse_relationships=not no_reverse,
        )
    except MetadataGenerationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    target = write_metadata(metadata, output)
    console.print(f"[green]Success:[/green] wrote metadata to {target}")

    if write_markdown:
        md_target = markdown_path or target.with_suffix('.md')
        md_target.parent.mkdir(parents=True, exist_ok=True)
        md_target.write_text(metadata_to_markdown(metadata), encoding='utf-8')
        console.print(f"[green]Success:[/green] wrote markdown summary to {md_target}")


@app.command("ask")
def ask(
    question: str = typer.Argument(..., help="Natural language analytics question."),
    metadata: Path = typer.Option(..., "--metadata", "-m", help="Path to metadata JSON."),
    graph_name: str = typer.Option("DATABASE", help="PyDough graph name."),
    url: str = typer.Option(..., "--url", help="Database connection URL (SQLAlchemy format)."),
    model: str = typer.Option("gemini-2.0-flash", help="Gemini model identifier."),
    temperature: float = typer.Option(0.2, help="Sampling temperature."),
    attempts: int = typer.Option(2, help="Maximum LLM attempts."),
    max_rows: int = typer.Option(100, help="Maximum rows to return."),
    timeout: float = typer.Option(10.0, help="Execution timeout in seconds."),
    show_sql: bool = typer.Option(False, help="Print the generated SQL."),
    show_code: bool = typer.Option(False, help="Print the generated PyDough code."),
    as_json: bool = typer.Option(False, "--json", help="Emit result as JSON."),
) -> None:
    """Run the end-to-end text to analytics pipeline."""

    console.print(f"[bold]Question:[/bold] {question}")
    try:
        engine = AnalyticsEngine(
            metadata_path=metadata,
            graph_name=graph_name,
            database_url=url,
            model=model,
            temperature=temperature,
            execution_timeout=timeout,
        )
        result = engine.ask(
            question,
            max_attempts=attempts,
            max_rows=max_rows,
        )
    except (AnalyticsPipelineError, FileNotFoundError, ValueError) as exc:
        if as_json:
            console.print_json(
                data={"question": question, "error": str(exc)},
            )
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if as_json:
        _print_json(result, question)
        return

    if show_code:
        console.rule("PyDough code")
        console.print(f"```python\n{result.code}\n```")

    if show_sql:
        console.rule("SQL")
        console.print(result.sql)

    console.rule("Result preview")
    _print_dataframe(result.dataframe)
    console.print(f"Attempts: {result.attempts}")
    if result.explanation:
        console.print(f"Explanation: {result.explanation}")


def _print_dataframe(df) -> None:
    if df.empty:
        console.print("[yellow]No rows returned.[/yellow]")
        return

    table = Table(show_lines=False)
    for column in df.columns:
        table.add_column(str(column))

    for _, row in df.iterrows():
        table.add_row(*("" if pd.isna(value) else str(value) for value in row))

    console.print(table)


def _print_json(result, question: str) -> None:
    data = {
        "question": question,
        "code": result.code,
        "sql": result.sql,
        "attempts": result.attempts,
        "explanation": result.explanation,
        "rows": result.dataframe.to_dict(orient="records"),
    }
    console.print_json(data=data)


if __name__ == "__main__":  # pragma: no cover
    app()
