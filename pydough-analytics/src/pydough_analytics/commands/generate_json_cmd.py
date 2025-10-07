import sys
import json
from pathlib import Path
from ..utils.database_connectors.connector import Connector
from ..metadata.generate_knowledge_graph import generate_metadata
from ..utils.storage.file_service import save_json
from sqlalchemy.engine import Engine
from sqlalchemy import inspect
from urllib.parse import urlparse


def get_engine_from_credentials(url: str) -> tuple[Engine, str]:
    """
    Extracts connection parameters and builds SQLAlchemy engine.
    """
    try:
        parsed = urlparse(url)
        db_type = parsed.scheme.lower()
        path_parts = [p for p in parsed.path.split("/") if p]
        sf_schema = ""
        if len(path_parts) >= 2:
            _, sf_schema = path_parts[0], path_parts[1]
        connector: Connector = Connector(db_type, url)
        return connector.get_engine(), db_type, sf_schema
    except Exception as e:
        raise ValueError(f"Failed to create engine: {e}") from e


def list_all_tables_and_columns(engine: Engine, db_type: str, sf_schema: str = "") -> list[str]:
    """
    Get all tables and columns from the database before metadata generation.
    """
    try:
        inspector = inspect(engine)
        tables_by_schema = {}

        if db_type == "snowflake":
            if not sf_schema:
                raise ValueError("Schema is required for Snowflake connections.")
            tables = inspector.get_table_names(schema=sf_schema)
            tables_by_schema[sf_schema] = tables
        else:
            default_schema = inspector.default_schema_name
            tables = inspector.get_table_names()
            tables_by_schema[default_schema] = tables

        all_tables = [t for tbls in tables_by_schema.values() for t in tbls]
        return all_tables
    except Exception as e:
        raise RuntimeError(f"Failed to inspect tables: {e}") from e


def generate_metadata_from_config(url: str, graph_name: str, json_path: str):
    """
    Generate metadata from a database.
    """
    try:
# Take config and connect to a database
        print(f"Connecting to '{graph_name}'...")
        engine_obj, db_type, sf_schema = get_engine_from_credentials(url)

        # Get the table list
        table_list: list[str] = list_all_tables_and_columns(engine_obj, db_type, sf_schema)

        # Generate the metadata
        print(f"Generating metadata for {len(table_list)} tables...")
        metadata: json = generate_metadata(engine_obj, graph_name, db_type, table_list)

        # Save the metadata
        json_output_path: Path = Path(json_path)
        save_json(json_output_path, metadata)
        print(f"Metadata for '{graph_name}' written to: {json_output_path}")

        return metadata

    except Exception as e:
        print(f"[ERROR] Failed to generate Metadata: {e}", file=sys.stderr)
        sys.exit(1)
