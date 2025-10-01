from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from collections.abc import Callable
from pathlib import Path

# Registry to store connection loader functions by database type
_DATABASE_LOADERS: dict[str, Callable[[dict], Engine]] = {}

def register_database(name: str):
    """
    Decorator to register a new database loader by name.
    """
    def decorator(fn: Callable[[dict], Engine]):
        _DATABASE_LOADERS[name.lower()] = fn
        return fn
    return decorator

# Loader for SQLite using a local file path
@register_database("sqlite")
def load_sqlite_engine(params: dict) -> Engine:
    if "database" not in params:
        raise ValueError("SQLite requires a 'database' parameter.")
    db_path = Path(params["database"])

    return create_engine(f"sqlite:///{db_path}")

class Connector:
    """
    Generic database connector that abstracts the process of initializing
    SQLAlchemy engines based on the type of database specified.
    
    Usage:
        connector = Connector("sqlite", database="path/to/db.sqlite")
        engine = connector.get_engine()
    """
    def __init__(self, db_type: str, **params):
        db_type = db_type.lower()
        if db_type not in _DATABASE_LOADERS:
            raise ValueError(f"Unsupported database type: {db_type}")
        # Call the appropriate loader to get the SQLAlchemy engine
        self.engine: Engine = _DATABASE_LOADERS[db_type](params)

    def get_engine(self) -> Engine:
        """
        Returns the SQLAlchemy engine for database operations.
        """
        return self.engine

    def test_connection(self) -> bool:
        """
        Tries to connect to the database to verify connectivity.
        """
        try:
            with self.engine.connect():
                return True
        except Exception as e:
            return False
