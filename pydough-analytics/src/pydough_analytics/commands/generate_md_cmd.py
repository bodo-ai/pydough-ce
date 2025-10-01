import sys
from pathlib import Path
from ..metadata.generate_mark_down import generate_markdown_from_metadata
from ..utils.storage.file_service import save_markdown
from pydough import parse_json_metadata_from_file
from pydough.metadata import GraphMetadata

def generate_markdown_from_config(graph_name: str, json_path: str, md_path: str) -> None:
    """
    Generates Markdown documentation from a metadata JSON file.
    """
    try:
        json_input_path: Path = Path(json_path)
        md_output_path: Path = Path(md_path)

        # Parse metadata using PyDough
        graph: GraphMetadata = parse_json_metadata_from_file(json_input_path, graph_name)

        # Generate Markdown
        markdown_content: str = generate_markdown_from_metadata(graph)

        # Write output
        save_markdown(md_output_path, markdown_content)
        print(f"Markdown written to {md_output_path}")

    except Exception as e:
        print(f"[ERROR] Failed to generate Markdown: {e}", file=sys.stderr)
        sys.exit(1)
