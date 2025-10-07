import re
from re import Match
import json
import textwrap
import traceback
import tempfile
from pydough.unqualified import transform_cell
import pydough
from .storage.file_service import load_json
from urllib.parse import urlparse, parse_qs, ParseResult

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# This function extracts Python code from a given text, looking for code blocks or specific patterns
def extract_python_code(text):
    if not isinstance(text, str):
        return ""

    matches: list = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()

    answer_match: Match | None = re.search(r"Answer:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()

    return ""

def parse_db_url(url: str) -> dict:
    """
    Parse connection string into a db_config dict compatible with PyDough.
    Supports SQLite and Snowflake (extensible a MySQL/Postgres).
    """
    parsed: ParseResult = urlparse(url)
    db_type: str = parsed.scheme.lower()

    if db_type == "sqlite":
        # sqlite:///path/to/file.db
        return {
            "engine": "sqlite",
            "database": parsed.path.lstrip("/"), 
        }

    elif db_type == "snowflake":
        # snowflake://user:pass@account/database/schema?warehouse=WH&role=ROLE
        path_parts: list[str] = [p for p in parsed.path.split("/") if p]
        sf_database: str = path_parts[0] if len(path_parts) >= 1 else ""
        sf_schema: str = path_parts[1] if len(path_parts) >= 2 else ""

        query_params: dict[str, list[str]] = parse_qs(parsed.query)
        return {
            "engine": "snowflake",
            "user": parsed.username,
            "password": parsed.password,
            "account": parsed.hostname,
            "database": sf_database,
            "schema": sf_schema,
            "warehouse": query_params.get("warehouse", [""])[0],
            "role": query_params.get("role", [""])[0],
        }
    
    elif db_type in ("mysql", "postgres"):
        # Example: mysql://user:pass@host:3306/dbname
        database: str = parsed.path.lstrip("/")
        return {
            "engine": "mysql" if db_type == "mysql" else "postgres",
            "username": parsed.username,
            "password": parsed.password,
            "host": parsed.hostname or "localhost",
            "port": parsed.port or (3306 if db_type == "mysql" else 5432),
            "database": database,
        }

    else:
        raise ValueError(f"Unsupported engine in URL: {db_type}")

# This function executes the provided PyDough code in a controlled environment
def execute_code_and_extract_result(code, env, kg_path=None, db_name=None, url=None):

    if kg_path and db_name and url:
        metadata: list = load_json(kg_path)
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as tmp:
            json.dump(metadata, tmp)
            tmp.flush()
            graph_meta: dict = metadata[0]
            actual_graph_name: str = graph_meta.get("name")
            pydough.active_session.load_metadata_graph(tmp.name, actual_graph_name)
        
        db_config: str = parse_db_url(url)
        engine: str = db_config["engine"]

        if engine == "sqlite":
            pydough.active_session.connect_database(
                "sqlite",
                database=db_config["database"],
                check_same_thread=False
            )
        elif engine == "snowflake":
            pydough.active_session.connect_database(
                "snowflake",
                user=db_config["user"],
                password=db_config["password"],
                account=db_config["account"],
                warehouse=db_config["warehouse"],
                database=db_config["database"],
                schema=db_config["schema"]
            )
        elif engine in ("mysql", "postgres"):
            default_port: int = 3306 if engine == "mysql" else 5432
            db_key: str = "dbname" if engine == "postgres" else "database"
            pydough.active_session.connect_database(
                engine,
                user=db_config["username"],
                password=db_config["password"],
                host=db_config["host"],
                port=db_config.get("port", default_port),
                **{db_key: db_config["database"]}
            )
        else:
            raise ValueError(f"Unsupported engine: {engine}")

    try:
        transformed = transform_cell(code, "pydough.active_session.metadata", set(env))
        exec(transformed, {}, env)
        last_variable = list(env.values())[-1]
        df = pydough.to_df(last_variable)
        sql = pydough.to_sql(last_variable)
        return df, sql
    except Exception as e:
        raise RuntimeError(f"Error executing PyDough code:\n{traceback.format_exc()}")
