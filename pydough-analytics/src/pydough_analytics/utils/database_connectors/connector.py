from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from collections.abc import Callable

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

# Loader for SQLite using a connection string
@register_database("sqlite")
def load_sqlite_engine(url: str) -> Engine:
    """
    Example: sqlite:///mydb.sqlite
    """
    if not url.startswith("sqlite:///"):
        raise ValueError("Invalid SQLite connection string.")
    return create_engine(url)

# Loader for Snowflake using a connection string
@register_database("snowflake")
def load_snowflake_engine(url: str) -> Engine:
    """
    Example: snowflake://user:pass@account/db/schema?warehouse=WH&role=PUBLIC
    """
    if not url.startswith("snowflake://"):
        raise ValueError("Invalid Snowflake connection string.")
    return create_engine(url)

# Loader for MySQL using a connection string
@register_database("mysql")
def load_mysql_engine(url: str) -> Engine:
    """
    Example: mysql://user:pass@localhost:3306/mydb
    SQLAlchemy requires: mysql+mysqlconnector://user:pass@localhost:3306/mydb
    """
    if not url.startswith("mysql://"):
        raise ValueError("Invalid MySQL connection string.")

    url: str = url.replace("mysql://", "mysql+mysqlconnector://", 1)
    return create_engine(url)

# Loader for Postgres using a connection string
@register_database("postgres")
def load_postgres_engine(url: str) -> Engine:
    """
    Example: postgres://user:pass@localhost:5432/mydb
    SQLAlchemy requires: postgresql+psycopg2://user:pass@localhost:5432/mydb
    """
    if not url.startswith("postgres://"):
        raise ValueError("Invalid PostgreSQL connection string.")
    # Normalize scheme to 'postgresql+psycopg2'
    url: str = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return create_engine(url)

class Connector:
    """
    Generic database connector that abstracts the process of initializing
    SQLAlchemy engines based on the type of database specified.
    
    Usage:
        connector = Connector("sqlite", database="path/to/db.sqlite")
        engine = connector.get_engine()
    """
    def __init__(self, db_type: str, url: str):
        db_type: str = db_type.lower()
        if db_type not in _DATABASE_LOADERS:
            raise ValueError(f"Unsupported database type: {db_type}")
        # Call the appropriate loader to get the SQLAlchemy engine
        self.engine: Engine = _DATABASE_LOADERS[db_type](url)

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
