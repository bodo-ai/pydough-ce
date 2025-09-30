import sys
import argparse
from pathlib import Path
from generate_mark_down import generate_markdown_from_metadata
from pydough import parse_json_metadata_from_file
from pydough.metadata import GraphMetadata

def main():
    """
    Usage:
    python generate_md.py \
        --json_path /path/to/metadata.json \
        --md_path /path/to/output.md
    """
    parser = argparse.ArgumentParser(description="Generate Markdown from existing metadata JSON file.")
    parser.add_argument("--graph_name", required=True, help="Name of the metadata graph")
    parser.add_argument("--json_path", required=True, help="Path to the input metadata JSON file")
    parser.add_argument("--md_path", required=True, help="Path to output the Markdown file")
    args = parser.parse_args()

    try:
        json_path: str = Path(args.json_path)
        md_path: str = Path(args.md_path)
        graph_name: str = args.graph_name

        # Parse metadata using PyDough
        graph: GraphMetadata = parse_json_metadata_from_file(json_path, graph_name)

        # Generate markdown from parsed graph
        markdown_content = generate_markdown_from_metadata(graph)

        # Save markdown to file
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Markdown written to {md_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
