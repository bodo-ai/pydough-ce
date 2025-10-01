import builtins
import keyword
import re
from itertools import product
from collections import defaultdict
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine, CursorResult
from .metadata_constants import TYPE_MAPS, RESERVED_KEYWORDS, CHAR_REPLACEMENTS

def make_valid_identifier(db_type: str, name: str) -> str:
    """
    Clean column/table name to be a valid identifier.
    """
    try:
        original_name: str = name.lower()
        suffix: str = ""
        if "%" in original_name:
            suffix = "_percentage"
        elif "#" in original_name:
            suffix = "_number"

        for char, replacement in CHAR_REPLACEMENTS.items():
            original_name = original_name.replace(char, replacement)

        name = re.sub(r'\W', '_', original_name)
        name = re.sub(r'_+', '_', name).strip('_')

        if name and name[0].isdigit():
            name = "_" + name
        if not name.isidentifier() or keyword.iskeyword(name) or hasattr(builtins, name):
            name += "_"
        reserved: set[str] = (
            RESERVED_KEYWORDS.get(db_type, set()) |
            RESERVED_KEYWORDS.get("general", set()))
        if name.upper() in reserved:
            name += "_"

        return name + suffix
    except Exception as e:
        raise ValueError(f"Error making valid identifier from '{name}': {e}")

def escape_identifier(db_type: str, name: str) -> str:
    """
    Escapes an identifier if it is a reserved keyword or contains spaces.
    """
    try:
        upper_name: str = name.upper()
        reserved: set[str] = RESERVED_KEYWORDS.get(db_type, set()) | RESERVED_KEYWORDS.get("general", set())
        has_special_chars: bool = bool(re.search(r'[^a-zA-Z0-9_]', name))
        starts_with_number: bool = name[0].isdigit()
        is_reserved: bool = upper_name in reserved
        needs_quotes: bool = is_reserved or has_special_chars or starts_with_number

        safe_name: str = name.replace('"', '""')

        if needs_quotes or name != safe_name:
            return f'"{safe_name}"'

        return name
    except Exception as e:
            raise ValueError(f"Error escaping identifier '{name}': {e}")

def resolve_type(db_type: str, raw_type: str) -> str:
    """
    Map a raw column type into one of our standardized types.
    """
    try:
        rt: str = raw_type.upper()
        for key, std in TYPE_MAPS.get(db_type, {}).items():
            if key in rt:
                return std
        return "string"
    except Exception as e:
            raise ValueError(f"Error resolving type for '{raw_type}' in {db_type}: {e}")

def get_all_columns(engine: Engine, table: str, db_type: str) -> list[dict[str, object]]:
    """
    Return a list of column metadata dicts for the given table.
    """
    try:
        insp = inspect(engine)
        cols: list[dict[str, object]] = []

        if db_type == "sqlite":
            with engine.connect() as conn:
                test: str = escape_identifier(db_type, table)
                rows: CursorResult = conn.execute(text(f"PRAGMA table_info({test})"))
                for r in rows:
                    col_type: str = resolve_type("sqlite", r[2])
                    cols.append({
                        "name": r[1],
                        "column name": r[1],
                        "type": col_type,
                        "description": "",
                        "sample values": [],
                        "synonyms": []
                    })
        else:
            schema: str = insp.default_schema_name
            for col in insp.get_columns(table_name=table, schema=schema):
                col_type: str = resolve_type(db_type, col["type"].__class__.__name__)
                cols.append({
                    "name": col["name"],
                    "column name": col["name"],
                    "type": col_type,
                    "description": "",
                    "sample values": [],
                    "synonyms": []
                })

        return cols
    except Exception as e:
            raise ValueError(f"Error retrieving columns for table '{table}': {e}")

def get_primary_keys(engine: Engine, table: str, db_type: str) -> list[str]:
    """
    Retrieve primary key column names for a table.
    """
    try:
        insp = inspect(engine)
        pks: list[str] = []
        if db_type == "sqlite":
            with engine.connect() as conn:
                rows: CursorResult = conn.execute(text(f"PRAGMA table_info({escape_identifier(db_type, table)})"))
                pks = [r[1] for r in rows if r[5] > 0]
        else:
            schema: str = insp.default_schema_name
            pk_info: dict[str, object] = insp.get_pk_constraint(table_name=table, schema=schema)
            pks = pk_info.get("constrained_columns", [])

        return pks
    except Exception as e:
        raise ValueError(f"Error retrieving primary keys for table '{table}': {e}")

def get_foreign_keys(engine: Engine, table: str, db_type: str) -> list[dict[str, object]]:
    """
    Retrieve foreign key relationships for a table.
    """
    try:
        insp = inspect(engine)
        fks: list[dict[str, object]] = []
        if db_type == "sqlite":
            with engine.connect() as conn:
                rows: CursorResult = conn.execute(text(f"PRAGMA foreign_key_list({escape_identifier(db_type, table)})"))
                for r in rows:
                    fks.append({
                        "id": r[0],
                        "child_table": table,
                        "parent_table": r[2],
                        "from_col": r[3],
                        "to_col": r[4]
                    })
        else:
            schema: str = insp.default_schema_name
            raw: list[dict[str, object]] = insp.get_foreign_keys(table_name=table, schema=schema)
            fk_counter: int = 0
            for fk in raw:
                if fk["referred_table"] and fk["constrained_columns"] and fk["referred_columns"]:
                    for from_col, to_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                        fks.append({
                            "id": fk_counter,
                            "child_table": table,
                            "parent_table": fk["referred_table"],
                            "from_col": from_col,
                            "to_col": to_col
                        })
                    fk_counter += 1

        return fks
    except Exception as e:
        raise ValueError(f"Error retrieving foreign keys for table '{table}': {e}")

def build_collections(
    engine: Engine,
    tables: list[str],
    db_type: str
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """
    Build the 'collections' JSON entries and a lookup map of table -> collection_name.
    Raises ValueError if any table lacks a primary key.
    """
    insp = inspect(engine)
    default_schema: str = insp.default_schema_name
    collections: list[dict[str, object]] = []
    collection_names: dict[str, str] = {}
    try:
        for table in tables:
            # Extract column and primary key info
            cols: list[dict[str, object]] = get_all_columns(engine, table, db_type)
            pk: list[str] = get_primary_keys(engine, table, db_type)

            # Track used property names to avoid duplicates
            used_names: set[str] = set()
            properties: list[dict[str, object]] = []
            for i, c in enumerate(cols):
                raw_name: str = c["name"]
                valid_name: str = make_valid_identifier(db_type, raw_name)

                # Handle empty or duplicate property names
                if not valid_name:
                    valid_name = f"unknown_column_{i}"
                elif valid_name in used_names:
                    valid_name = f"{valid_name}__{i}"

                used_names.add(valid_name)
                properties.append({
                    "name": valid_name,
                    "type": "table column",
                    "column name": escape_identifier(db_type, c["column name"]),
                    "data type": c["type"],
                    "description": "",
                    "sample values": [],
                    "synonyms": []
                })

            # Determine unique properties from PK or fallback to first column
            unique_props: list[str] = []
            if pk:
                unique_props = [make_valid_identifier(db_type, c) for c in pk]
            else:
                fallback_col: str = cols[0]["name"]
                unique_props = [make_valid_identifier(db_type, fallback_col)]

            collection_names[table] = table.lower()
            
            # Table path using schema rules
            formated_table: str = escape_identifier(db_type, table)
            path: str = ""
            if db_type == "sqlite":
                path = f"main.{formated_table}"
            else:
                path = f"{default_schema}.{formated_table}"

            collections.append({
                "name": make_valid_identifier(db_type, table),
                "type": "simple table",
                "table path": path,
                "unique properties": unique_props,
                "properties": properties,
                "description": "",
                "synonyms": []
            })

        return collections, collection_names
    except Exception as e:
        raise ValueError(f"Error building collections from tables: {e}")

def get_unique_columns(engine: Engine, table: str, db_type: str) -> set[str]:
    """
    Detects columns that are part of UNIQUE constraints in a SQLite table.
    Uses PRAGMA index_list + PRAGMA index_info.
    """
    try:
        unique_cols: set[str] = set()
        if db_type == "sqlite":
            def clean_sqlite_identifier(name: str) -> str:
                name = name.strip()
                return re.sub(r'^(["\']+)(.*?)(\1)$', r'\2', name)

            table_clean: str = clean_sqlite_identifier(table)

            with engine.connect() as conn:
                index_list: list[object] = conn.execute(text(f"PRAGMA index_list('{table_clean}')")).fetchall()

                for index in index_list:
                    index_name: str = index[1]
                    is_unique: bool = index[2] == 1

                    if is_unique:
                        index_info: list[object] = conn.execute(text(f"PRAGMA index_info('{index_name}')")).fetchall()
                        for col in index_info:
                            unique_cols.add(col[2])
        else:
            inspector = inspect(engine)
            schema: str = inspector.default_schema_name
            indexes: list[dict[str, object]] = inspector.get_indexes(table_name=table, schema=schema)

            for idx in indexes:
                if idx.get("unique", False):
                    for col in idx.get("column_names", []):
                        unique_cols.add(col)

        return unique_cols
    except Exception as e:
        raise ValueError(f"Error retrieving unique columns for table '{table}': {e}")

def infer_relationship(
    engine: Engine,
    child_table: str,
    child_col: str,
    db_type: str
) -> tuple[dict[str, bool], dict[str, bool]]:
    """
    Returns inferred singular and always_matches flags based on column constraints.
    """
    try:
        inspector = inspect(engine)
        child_pk: set[str] = set()
        child_nullable: set[str] = set()
        if db_type == "sqlite":
            with engine.connect() as conn:
                pragma_result: list[object] = conn.execute(text(f"PRAGMA table_info({child_table})")).fetchall()
                child_pk = {row[1] for row in pragma_result if row[5] > 0}
                child_nullable = {row[1] for row in pragma_result if row[3] == 0}
        else:
            schema: str = inspector.default_schema_name
            child_pk = set(get_primary_keys(engine, child_table, db_type))
            columns: list[dict[str, object]] = inspector.get_columns(table_name=child_table, schema=schema)
            child_nullable = {col["name"] for col in columns if col.get("nullable", True)}

        child_uniques: set[str] = get_unique_columns(engine, child_table, db_type)

        is_fk_pk: bool = child_col in child_pk
        is_fk_unique: bool = is_fk_pk or child_col in child_uniques
        is_fk_nullable: bool = (child_col in child_nullable) and not is_fk_pk

        direct_singular: bool = is_fk_unique
        direct_always_matches: bool = False

        reverse_singular: bool = True
        reverse_always_matches: bool = not is_fk_nullable

        return (
            {"singular": direct_singular, "always matches": direct_always_matches},
            {"singular": reverse_singular, "always matches": reverse_always_matches}
        )
    except Exception as e:
            raise ValueError(f"Error inferring relationship for column '{child_col}' in table '{child_table}': {e}")

def get_safe_relationship_name(
    base_name: str,
    used_names: dict[str, int],
    conflicting_names: set[str]
) -> str:
    """
    Generates a unique relationship name avoiding collisions with property names.
    """
    try:
        candidate: str = ""
        if base_name not in used_names:
            candidate = base_name
            used_names[base_name] = 1
        else:
            used_names[base_name] += 1
            candidate = f"{base_name}_{used_names[base_name]}"

        while candidate in conflicting_names:
            used_names[base_name] += 1
            candidate = f"{base_name}_{used_names[base_name]}"

        return candidate
    except Exception as e:
        raise ValueError(f"Error get safe relationship name for '{base_name}': {e}")
    
def split_all_combinations(fk_group: list[dict]) -> list[list[dict]]:
    """
    Generate all combinations of valid FK mappings to avoid JSON key collisions.
    """
    to_col_map: dict[str, list] = defaultdict(list)
    for fk in fk_group:
        to_col_map[fk["to_col"]].append(fk)
    groups: list[tuple] = list(product(*to_col_map.values()))
    return [list(group) for group in groups]

def apply_split_to_all_fk_groups(
    fk_groups: dict[int, list]
) -> dict[int, list]:
    """
    Take dict of fk groups and apply split_all_combinations for each group,
    generating new groups with unique IDs.
    """
    new_fk_groups: dict[int, list] = {}
    next_id: int = 0

    for _, fk_group in fk_groups.items():
        combinations: list[list[dict]] = split_all_combinations(fk_group)
        for combo in combinations:
            new_group: list = []
            for fk in combo:
                new_fk: dict = fk.copy()
                new_fk["id"] = next_id
                new_group.append(new_fk)
                new_fk_groups[next_id] = new_group
            next_id += 1

    return new_fk_groups

def build_relationships(
    engine: Engine,
    tables: list[str],
    collection_names: dict[str, str],
    db_type: str,
    split_groups: bool
) -> list[dict[str, object]]:
    """
    Build both simple joins and reverse relationships from foreign keys.
    """
    try:
        relationships: list[dict[str, object]] = []
        seen: set[tuple[str, str, int]] = set()
        forward_name_counts: dict[str, int] = {}
        reverse_name_counts: dict[str, int] = {}

        property_name_map: dict[str, set[str]] = {
            table: {
                make_valid_identifier(db_type, col["name"])
                for col in get_all_columns(engine, table, db_type)
            }
            for table in tables
        }

        for table in tables:
            fks: list[dict[str, object]] = get_foreign_keys(engine, table, db_type)

            # Group FKs by ID
            fk_groups: dict[int, list[dict[str, object]]] = defaultdict(list)
            for fk in fks:
                fk_groups[fk["id"]].append(fk)
            if fk_groups and split_groups:
                fk_groups = apply_split_to_all_fk_groups(fk_groups)
            for fk_id, fk_group in fk_groups.items():
                first: dict[str, object] = fk_group[0]
                parent_raw: str | None = collection_names.get(first["parent_table"])
                child_raw: str | None  = collection_names.get(first["child_table"])
                if not parent_raw or not child_raw:
                    continue
                parent: str = make_valid_identifier(db_type, parent_raw)
                child: str  = make_valid_identifier(db_type, child_raw)
                
                # Map parent to child keys
                keys: dict[str, list[str]] = {}
                for fk in fk_group:
                    parent_col: str = make_valid_identifier(db_type, fk["to_col"])
                    child_col: str  = make_valid_identifier(db_type, fk["from_col"])
                    keys.setdefault(parent_col, []).append(child_col)

                direct_flags, reverse_flags = infer_relationship(
                    engine,
                    escape_identifier(db_type, fk["child_table"]),
                    escape_identifier(db_type, fk["from_col"]),
                    db_type 
                )

                # Forward relationships
                key_pair: tuple[str, str, int] = (parent, child, fk_id)
                if key_pair not in seen:
                    parent_props: set[str] = property_name_map.get(first["parent_table"], set())
                    rel_name: str = get_safe_relationship_name(child, forward_name_counts, parent_props)

                    relationships.append({
                        "type": "simple join",
                        "name": rel_name,
                        "parent collection": parent,
                        "child collection": child,
                        "singular": direct_flags["singular"],
                        "always matches": direct_flags["always matches"],
                        "keys": keys,
                        "description": "",
                        "synonyms": []
                    })
                    seen.add(key_pair)

                # Reverse relationship
                rev_pair: tuple[str, str, int] = (child, parent, fk_id)
                if rev_pair not in seen:
                    child_props: set[str] = property_name_map.get(first["child_table"], set())
                    reverse_name: str = get_safe_relationship_name(parent, reverse_name_counts, child_props)
                    
                    relationships.append({
                        "type": "reverse",
                        "name": reverse_name,
                        "original parent": parent,
                        "original property": rel_name,
                        "singular": reverse_flags["singular"],
                        "always matches": reverse_flags["always matches"],
                        "description": "",
                        "synonyms": []
                    })
                    seen.add(rev_pair)

        return relationships
    except Exception as e:
            raise ValueError(f"Error building relationships from foreign keys: {e}")

def generate_metadata(
    engine: Engine,
    graph_name: str,
    db_type: str,
    tables: list[str],
    split_groups: bool = True
) -> list[dict[str, object]]:
    """
    Orchestrates the creation of collections and relationships into the final graph.
    Propagates any ValueError from missing keys as a failure.
    """
    try:
        collections, collection_names = build_collections(engine, tables, db_type)
        relationships: list[dict[str, object]] = build_relationships(engine, tables, collection_names, db_type, split_groups)

        return [{
            "name": graph_name,
            "version": "V2",
            "collections": collections,
            "relationships": relationships
        }]
    except Exception as e:
        raise ValueError(f"Error generating metadata: {e}")
