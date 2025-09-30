import argparse
import json
from pathlib import Path
from connector import Connector
from generate_knowledge_graph import generate_metadata
from sqlalchemy.engine import Engine
from sqlalchemy import inspect

def get_engine_from_credentials(config: dict) -> tuple[Engine, str]:
    """Extracts connection parameters and builds SQLAlchemy engine."""
    db_type: str = config.pop("engine")

    connector = Connector(db_type, **config)
    return connector.get_engine(), db_type

def list_all_tables_and_columns(engine: Engine) -> list:
    """Prints all tables and columns from the database before metadata generation."""
    try:
        inspector = inspect(engine)
        tables_by_schema: dict = {}

        default_schema = inspector.default_schema_name
        tables = inspector.get_table_names()
        tables_by_schema[default_schema] = tables

        print("Found tables in the database:")
        for schema, tbls in tables_by_schema.items():
            print(f"  • Schema '{schema}':")
            for t in tbls:
                print(f"      - {t}")
                try:
                    columns = inspector.get_columns(t, schema=schema)
                    for col in columns:
                        col_name: str = col["name"]
                        col_type: str = col["type"]
                        nullable: bool = col.get("nullable", True)
                        print(f"          • {col_name} ({col_type}, nullable={nullable})")
                except Exception as e:
                    print(f"Failed to retrieve columns: {e}")
        print("———————————————\n")

        # Return flat list of all table names
        all_tables: list = [t for tbls in tables_by_schema.values() for t in tbls]
        return all_tables
    except Exception as e:
        print(f"Error: {e}")

def ask_for_table_selection(table_list: list[str]) -> list[str]:
    """Prompts the user to select tables by index or partial name."""
    print("# Tables: ")
    print(table_list, "\n")
    print("———————————————\n")
    print("\nYou can now select which tables to use for metadata generation, or empty for all tables.")
    print("Example input: 1, 4, 5 or orders, customers")
    raw_input: str = input("Enter comma-separated table indices or names: ").strip()
    if not raw_input:
        print("No input given, using all tables. \n")
        print("———————————————\n")
        return table_list

    selections: list[str] = [s.strip().lower() for s in raw_input.split(",")]

    selected_tables: list[str] = []
    for idx, table_name in enumerate(table_list, 1):
        if str(idx) in selections or table_name.lower() in selections:
            selected_tables.append(table_name)

    print(f"Selected tables: {selected_tables} \n")
    print("———————————————\n")
    return selected_tables

def main():
    '''
    Usage:
    python generate_json.py \
        --engine sqlite \
        --database /path/to/db.sqlite \
        --graph_name my_graph \
        --json_path /output/metadata.json
    '''
    parser = argparse.ArgumentParser(description="Generate metadata JSON from DB credentials.")
    parser.add_argument("--engine", required=True, help="Database engine (e.g., sqlite)")
    parser.add_argument("--database", required=True, help="Database path or connection string")
    parser.add_argument("--graph_name", required=True, help="Name of the metadata graph")
    parser.add_argument("--json_path", required=True, help="Path to save the output JSON file")
    args = parser.parse_args()

    try:
        config = {
            "engine": args.engine,
            "database": args.database,
            "graph_name": args.graph_name,
            "json_path": args.json_path
        }

        graph_name: str = config["graph_name"]
        json_output_path: str = Path(config["json_path"])
        
        engine, db_type = get_engine_from_credentials(config)
        print(f"Connecting to '{graph_name}' using engine '{db_type}'...")

        table_list: list[str] = list_all_tables_and_columns(engine)
        selected_tables: list[str] = ask_for_table_selection(table_list)

        print(f"Generating metadata for {len(selected_tables )} tables...")
        metadata: list[dict] = generate_metadata(engine, graph_name, db_type, selected_tables)
        print(f"Metadata generation complete.")

        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_output_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"Metadata for '{graph_name}' written to: {json_output_path}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
