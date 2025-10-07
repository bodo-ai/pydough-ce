import typer
from rich.console import Console

from .commands.generate_json_cmd import generate_metadata_from_config
from .commands.generate_md_cmd import generate_markdown_from_config
from .commands.ask_cmd import ask_from_cli

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
):
	if version:
		from ._version import __version__

		console.print(f"pydough-analytics {__version__}")
		raise typer.Exit()

@app.command("generate-json")
def generate_json(
    url: str = typer.Option(..., help="Connection string"),
    graph_name: str = typer.Option(..., help="Graph name for the metadata"),
    json_path: str = typer.Option(..., help="Path to save the metadata JSON file")
):
    """
    Generate metadata from a database and export it to JSON.
    """
    generate_metadata_from_config(url, graph_name, json_path)

@app.command("generate-md")
def generate_md(
    graph_name: str = typer.Option(..., help="Name of the metadata graph"),
    json_path: str = typer.Option(..., help="Path to the input metadata JSON file"),
    md_path: str = typer.Option(..., help="Path to the output Markdown file"),
):
    """
    Generate Markdown documentation from a metadata JSON file.
    """
    generate_markdown_from_config(graph_name, json_path, md_path)

@app.command("ask")
def ask(
    question: str = typer.Option(..., help="Natural language question"),
    url: str = typer.Option(..., help="Connection string"),
    db_name: str = typer.Option(..., help="Logical database name (e.g. TPCH)"),
    md_path: str = typer.Option(..., help="Path to DB markdown"),
    kg_path: str = typer.Option(..., help="Path to knowledge graph JSON"),
    provider: str = typer.Option(None, help="LLM provider (optional)"),
    model: str = typer.Option(None, help="LLM model id (optional)"),
    show_sql: bool = typer.Option(False, help="Print generated SQL"),
    show_df: bool = typer.Option(False, help="Print DataFrame as table"),
    show_explanation: bool = typer.Option(False, help="Print explanation"),
    as_json: bool = typer.Option(False, help="Output as JSON instead of table"),
    rows: int = typer.Option(20, help="Number of rows to show from the DataFrame"),
):
    """
    Ask a natural language question to a LLM provider for generate PyDough code.
    """
    ask_from_cli(
        question=question,
        url=url,
        db_name=db_name,
        md_path=md_path,
        kg_path=kg_path,
        provider=provider,
        model=model,
        show_sql=show_sql,
        show_df=show_df,
        show_explanation=show_explanation,
        as_json=as_json,
        rows=rows,
    )
    
if __name__ == "__main__":
	app()