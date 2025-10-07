from urllib.parse import urlparse, parse_qs, ParseResult
from collections.abc import Callable

# Registry for parser functions
_DATABASE_PARSERS: dict[str, Callable[[ParseResult], dict]] = {}

def register_parser(name: str):
    """
    Decorator to register a connection string parser by database type.

    Example:
        @register_parser("sqlite")
        def parse_sqlite(parsed): ...
    """
    def decorator(fn: Callable[[ParseResult], dict]):
        _DATABASE_PARSERS[name.lower()] = fn
        return fn
    return decorator

def parse_db_url(url: str) -> dict:
    """
    Factory function that dispatches parsing to the appropriate
    database-specific parser based on the URL scheme.
    """
    parsed: ParseResult = urlparse(url)
    db_type: str = parsed.scheme.lower()

    if db_type not in _DATABASE_PARSERS:
        raise ValueError(f"Unsupported or unregistered engine: {db_type}")

    return _DATABASE_PARSERS[db_type](parsed)

# Parser for SQLite
@register_parser("sqlite")
def parse_sqlite(parsed: ParseResult) -> dict:
    """
    Example: sqlite:///path/to/file.db
    """
    return {
        "engine": "sqlite",
        "database": parsed.path.lstrip("/"),
    }

# Parser for Snowflake
@register_parser("snowflake")
def parse_snowflake(parsed: ParseResult) -> dict:
    """
    Example: snowflake://user:pass@account/db/schema?warehouse=WH&role=PUBLIC
    """
    path_parts = [p for p in parsed.path.split("/") if p]
    query = parse_qs(parsed.query)
    return {
        "engine": "snowflake",
        "user": parsed.username,
        "password": parsed.password,
        "account": parsed.hostname,
        "database": path_parts[0] if len(path_parts) > 0 else "",
        "schema": path_parts[1] if len(path_parts) > 1 else "",
        "warehouse": query.get("warehouse", [""])[0],
        "role": query.get("role", [""])[0],
    }

# Parser for MySQL
@register_parser("mysql")
def parse_mysql(parsed: ParseResult) -> dict:
    """
    Example: mysql://user:pass@host:3306/dbname
    """
    return {
        "engine": "mysql",
        "username": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "database": parsed.path.lstrip("/"),
    }

# Parser for PostgreSQL
@register_parser("postgres")
def parse_postgres(parsed: ParseResult) -> dict:
    """
    Example: postgres://user:pass@localhost:5432/dbname
    """
    return {
        "engine": "postgres",
        "username": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
    }