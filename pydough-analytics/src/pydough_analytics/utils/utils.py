import re
from re import Match
import json
import textwrap
import traceback
import tempfile
from pydough.unqualified import transform_cell
import pydough
from .storage.file_service import load_json
from .database_connectors.connection_parser import parse_db_url

def read_file(file_path):
    """
    Read a specific file from memory
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def extract_python_code(text):
    """
    Extracts Python code from a given text, looking for code blocks or specific patterns
    """
    if not isinstance(text, str):
        return ""

    matches: list = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()

    answer_match: Match | None = re.search(r"Answer:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()

    return ""

# ---- Connection map declaration----
connection_map: dict[str, dict] = {
    "sqlite": {
        "kwargs": lambda c: {
            "database": c["database"],
            "check_same_thread": False,
        },
    },
    "snowflake": {
        "kwargs": lambda c: {
            "user": c["user"],
            "password": c["password"],
            "account": c["account"],
            "warehouse": c["warehouse"],
            "database": c["database"],
            "schema": c["schema"],
        },
    },
    "mysql": {
        "kwargs": lambda c: {
            "user": c["username"],
            "password": c["password"],
            "host": c["host"],
            "port": c.get("port", 3306),
            "database": c["database"],
            },
    },
    "postgres": {
        "kwargs": lambda c: {
            "user": c["username"],
            "password": c["password"],
            "host": c["host"],
            "port": c.get("port", 5432),
            "dbname": c["database"],
        },
    },
}


def execute_code_and_extract_result(code, env, kg_path=None, db_name=None, url=None):
    """
    Execute a PyDough query using the provided environment, metadata and DB URL.
    The connection logic is dynamically configured per engine.
    """
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

        if engine not in connection_map:
            raise ValueError(f"Unsupported engine: {engine}")
        
        conn_spec = connection_map[engine]
        pydough.active_session.connect_database(engine, **conn_spec["kwargs"](db_config))

    try:
        transformed = transform_cell(code, "pydough.active_session.metadata", set(env))
        exec(transformed, {}, env)
        last_variable = list(env.values())[-1]
        df = pydough.to_df(last_variable)
        sql = pydough.to_sql(last_variable)
        return df, sql
    except Exception as e:
        raise RuntimeError(f"Error executing PyDough code:\n{traceback.format_exc()}")
