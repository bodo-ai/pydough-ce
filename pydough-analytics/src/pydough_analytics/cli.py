import typer
from rich.console import Console

from .commands.generate_json_cmd import generate_metadata_from_config
from .commands.generate_md_cmd import generate_markdown_from_config

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
    engine: str = typer.Option(..., help="Database engine (e.g., sqlite)"),
    database: str = typer.Option(..., help="Database path or connection string"),
    graph_name: str = typer.Option(..., help="Graph name for the metadata"),
    json_path: str = typer.Option(..., help="Path to save the metadata JSON file")
):
    """
    Generate metadata from a database and export it to JSON.
    """
    generate_metadata_from_config(engine, database, graph_name, json_path)

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


if __name__ == "__main__":
	app()