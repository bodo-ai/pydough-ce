import re
import json
import textwrap
import traceback
import tempfile
from pydough.unqualified import transform_cell
import pydough
from .storage.file_service import load_json

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    
# Given the JSON string stored in Database.connection_string, return a dict of creds. Raises ValidationError on invalid JSON.
def parse_connection_string(connection_string: str) -> dict:
    normalized: str = connection_string.replace("'", '"')
    try:
        return json.loads(normalized)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in connection_string: {e}")
    
# Parses a connection string that can be in JSON format or key=value pairs.
def parse_key_value_connection_string(connection_string: str) -> dict:
    normalized: str = connection_string.strip().replace("'", '"')
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        pass

    # If JSON parsing fails, try to parse as key=value pairs
    try:
        creds: dict[str, str] = {}
        for pair in normalized.split(';'):
            if '=' not in pair:
                continue
            key, value = pair.split('=', 1)
            value = value.strip().strip('"').strip("'")
            creds[key.strip()] = value
        return creds
    except Exception as e:
        raise ValueError(f"Invalid connection string format: {e}")

# This function extracts Python code from a given text, looking for code blocks or specific patterns
def extract_python_code(text):
    if not isinstance(text, str):
        return ""

    matches = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()

    answer_match = re.search(r"Answer:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()

    return ""

# This function executes the provided PyDough code in a controlled environment
def execute_code_and_extract_result(code, env, kg_path=None, db_name=None, db_config=None):

    if kg_path and db_name and db_config:
        metadata = load_json(kg_path)
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as tmp:
            json.dump(metadata, tmp)
            tmp.flush()
            graph_meta = metadata[0]
            actual_graph_name = graph_meta.get("name")
            pydough.active_session.load_metadata_graph(tmp.name, actual_graph_name)
        engine = db_config.get("engine")

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
            default_port = 3306 if engine == "mysql" else 5432
            db_key = "dbname" if engine == "postgres" else "database"
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

def get_db_config(connection_string: str) -> tuple[dict, str]:
    # Convert connection_string into a flat dict of creds
    db_creds = parse_key_value_connection_string(connection_string)
    engine_type = db_creds.get("engine")

    if engine_type == "sqlite":
        db_config = {
            "engine":   "sqlite",
            "database": db_creds["db_path"]
        }
    elif engine_type == "snowflake":
        db_config = {
            "engine":    "snowflake",
            "user":      db_creds["SF_USERNAME"],
            "account":   db_creds["SF_ACCOUNT"],
            "warehouse": db_creds.get("SF_WH"),
            "database":  db_creds.get("SF_DATABASE"),
            "schema":    db_creds.get("SF_SCHEMA"),
            "role":      db_creds.get("SF_ROLE"),
        }
    elif engine_type in ("mysql", "postgres"):
        default_port = 3306 if engine_type == "mysql" else 5432
        db_config = {
            "engine":   engine_type,
            "username": db_creds["username"],
            "host":     db_creds["host"],
            "port":     db_creds.get("port", default_port),
            "database": db_creds["database"]
        }

    else:
        raise ValueError(f"Unsupported database engine: {engine_type}")

    return db_config

def initialize_pydough_session(metadata_path: str, db_name: str, db_config: dict):

    metadata = load_json(metadata_path)
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as tmp:
        json.dump(metadata, tmp)
        tmp.flush()
        graph_meta = metadata[0]
        actual_graph_name = graph_meta.get("name")
        pydough.active_session.load_metadata_graph(tmp.name, actual_graph_name)
    engine = db_config.get("engine")
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
    else:
        raise ValueError(f"Unsupported engine: {engine}")


