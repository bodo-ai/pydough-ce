import sys
import json
from pathlib import Path
from ..utils.database_connectors.connector import Connector
from ..metadata.generate_knowledge_graph import generate_metadata
from ..utils.storage.file_service import save_json
from sqlalchemy.engine import Engine
from sqlalchemy import inspect


def get_engine_from_credentials(config: dict) -> tuple[Engine, str]:
    """
    Extracts connection parameters and builds SQLAlchemy engine.
    """
    try:
        db_type: str = config.pop("engine")
        connector: Connector = Connector(db_type, **config)
        return connector.get_engine(), db_type
    except Exception as e:
        raise ValueError(f"Failed to create engine: {e}") from e


def list_all_tables_and_columns(engine: Engine) -> list[str]:
    """
    Get all tables and columns from the database before metadata generation.
    """
    try:
        inspector = inspect(engine)
        tables: list[str] = inspector.get_table_names()
        return tables
    except Exception as e:
        raise RuntimeError(f"Failed to inspect tables: {e}") from e


def generate_metadata_from_config(engine: str, database: str, graph_name: str, json_path: str):
    """
    Generate metadata from a database.
    """
    try:
        config: dict = {
            "engine": engine,
            "database": database,
            "graph_name": graph_name,
            "json_path": json_path
        }

        # Take config and connect to a database
        print(f"Connecting to '{graph_name}' using engine '{engine}'...")
        engine_obj, db_type = get_engine_from_credentials(config)

        # Get the table list
        table_list: list[str] = list_all_tables_and_columns(engine_obj)

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
