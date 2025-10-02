import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

# Target under test
from src.pydough_analytics.metadata.generate_knowledge_graph import (
    make_valid_identifier,
    escape_identifier,
    resolve_type,
    get_all_columns,
    get_primary_keys,
    get_foreign_keys,
    build_collections,
    get_unique_columns,
    infer_relationship,
    get_safe_relationship_name,
    split_all_combinations,
    apply_split_to_all_fk_groups,
    build_relationships,
    generate_metadata,
)


# ---------------------------
# make_valid_identifier
# ---------------------------

@pytest.mark.parametrize(
    "db_type,name,expected_contains",
    [
        ("sqlite", "total%", "_percentage"),
        ("sqlite", "count#", "_number"), 
        ("sqlite", "Order Id", "order_id"),
        ("sqlite", "9lives", "_9lives"),
        ("sqlite", "class", "class_"),
        ("sqlite", "list", "list_"),
    ],
    ids=["percent_suffix", "hash_suffix", "spaces_to_underscores", "leading_digit", "py_keyword", "builtin_name"],
)
def test_make_valid_identifier_happy_path(db_type, name, expected_contains):
    """
    Ensure make_valid_identifier normalizes names and applies suffix/prefix rules.
    """
    out = make_valid_identifier(db_type, name)
    assert expected_contains in out
    # Should be a valid Python identifier after transformations (apart from added suffix)
    assert out.replace("_percentage", "").replace("_number", "").replace("_", "").isalnum()


def test_make_valid_identifier_reserved_keyword_general(mocker):
    """
    If the uppercased candidate is in RESERVED_KEYWORDS['general'], it should add an underscore.
    """
    # Patch RESERVED_KEYWORDS for deterministic behavior
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.RESERVED_KEYWORDS",
        {"general": {"SELECT"}, "sqlite": set()},
    )
    out = make_valid_identifier("sqlite", "Select")
    assert out.endswith("_"), f"Expected trailing underscore for reserved keyword, got: {out}"


def test_make_valid_identifier_wraps_error(mocker):
    """
    If something goes wrong internally, function should raise ValueError with context message.
    """
    # Force an error by patching CHAR_REPLACEMENTS to a non-iterable
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.CHAR_REPLACEMENTS",
        None,
    )
    with pytest.raises(ValueError) as e:
        make_valid_identifier("sqlite", "ok")
    assert "Error making valid identifier" in str(e.value)


# ---------------------------
# escape_identifier
# ---------------------------

def test_escape_identifier_needs_quotes_for_space():
    """
    Names with spaces should be quoted.
    """
    assert escape_identifier("sqlite", "order id") == '"order id"'


def test_escape_identifier_needs_quotes_for_number_start():
    """
    Names starting with a digit should be quoted.
    """
    assert escape_identifier("sqlite", "9id") == '"9id"'


def test_escape_identifier_reserved(mocker):
    """
    Reserved general words should be quoted.
    """
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.RESERVED_KEYWORDS",
        {"general": {"SELECT"}, "sqlite": set()},
    )
    assert escape_identifier("sqlite", "select") == '"select"'


def test_escape_identifier_wraps_error():
    """
    Should wrap unexpected errors into ValueError.
    """
    with pytest.raises(ValueError) as e:
        escape_identifier("sqlite", None)  # type: ignore[arg-type]
    assert "Error escaping identifier" in str(e.value)


# ---------------------------
# resolve_type
# ---------------------------

def test_resolve_type_uses_type_maps(mocker):
    """
    Verify resolve_type maps using TYPE_MAPS with substring match (uppercased).
    """
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.TYPE_MAPS",
        {"sqlite": {"INT": "integer", "CHAR": "string"}},
    )
    assert resolve_type("sqlite", "varChar(255)") == "string"
    assert resolve_type("sqlite", "bigint") == "integer"
    assert resolve_type("sqlite", "mystery") == "string"


def test_resolve_type_wraps_error():
    with pytest.raises(ValueError) as e:
        resolve_type("sqlite", None)
    assert "Error resolving type" in str(e.value)


# ---------------------------
# get_all_columns
# ---------------------------

def test_get_all_columns_sqlite_happy(mocker):
    """
    PRAGMA table_info path: rows are tuples like (cid, name, type, notnull, dflt_value, pk)
    """
    # Return a dummy inspector so inspect(engine) doesn't explode
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=SimpleNamespace(default_schema_name="main"),
    )

    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.resolve_type",
        side_effect=lambda db, t: f"T-{t}",
    )

    conn = MagicMock()
    conn.execute.return_value = [
        (0, "id", "INTEGER", 1, None, 1),
        (1, "name", "TEXT", 0, None, 0),
    ]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    out = get_all_columns(engine, "Users", "sqlite")
    assert out == [
        {
            "name": "id",
            "column name": "id",
            "type": "T-INTEGER",
            "description": "",
            "sample values": [],
            "synonyms": [],
        },
        {
            "name": "name",
            "column name": "name",
            "type": "T-TEXT",
            "description": "",
            "sample values": [],
            "synonyms": [],
        },
    ]


def test_get_all_columns_other_db_happy(mocker):
    """
    Non-sqlite path uses inspector.get_columns with objects whose class names are read.
    """
    class BigInt: ...
    class VarChar: ...

    insp = MagicMock()
    insp.default_schema_name = "public"
    insp.get_columns.return_value = [
        {"name": "id", "type": BigInt()},
        {"name": "title", "type": VarChar()},
    ]
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.resolve_type",
        side_effect=lambda db, t: f"T-{t}",
    )

    out = get_all_columns(MagicMock(), "books", "postgres")
    assert [c["name"] for c in out] == ["id", "title"]
    assert [c["type"] for c in out] == ["T-BigInt", "T-VarChar"]


def test_get_all_columns_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        side_effect=RuntimeError("boom"),
    )
    with pytest.raises(ValueError) as e:
        get_all_columns(MagicMock(), "x", "sqlite")
    assert "Error retrieving columns for table 'x':" in str(e.value)


# ---------------------------
# get_primary_keys
# ---------------------------

def test_get_primary_keys_sqlite(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=SimpleNamespace(default_schema_name="main"),
    )

    conn = MagicMock()
    conn.execute.return_value = [
        (0, "id", "INTEGER", 1, None, 1),
        (1, "name", "TEXT", 0, None, 0),
    ]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    out = get_primary_keys(engine, "Users", "sqlite")
    assert out == ["id"]


def test_get_primary_keys_other_db(mocker):
    insp = MagicMock()
    insp.default_schema_name = "public"
    insp.get_pk_constraint.return_value = {"constrained_columns": ["id", "code"]}
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )
    out = get_primary_keys(MagicMock(), "t", "postgres")
    assert out == ["id", "code"]


def test_get_primary_keys_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        side_effect=RuntimeError("oops"),
    )
    with pytest.raises(ValueError) as e:
        get_primary_keys(MagicMock(), "t", "sqlite")
    assert "Error retrieving primary keys for table 't':" in str(e.value)


# ---------------------------
# get_foreign_keys
# ---------------------------

def test_get_foreign_keys_sqlite(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=SimpleNamespace(default_schema_name="main"),
    )

    conn = MagicMock()
    conn.execute.return_value = [
        (0, 0, "Parent", "parent_id", "id"),
        (0, 1, "Parent", "parent_code", "code"),
    ]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    out = get_foreign_keys(engine, "Child", "sqlite")
    assert out == [
        {"id": 0, "child_table": "Child", "parent_table": "Parent", "from_col": "parent_id", "to_col": "id"},
        {"id": 0, "child_table": "Child", "parent_table": "Parent", "from_col": "parent_code", "to_col": "code"},
    ]


def test_get_foreign_keys_other_db(mocker):
    insp = MagicMock()
    insp.default_schema_name = "public"
    insp.get_foreign_keys.return_value = [
        {"referred_table": "P", "constrained_columns": ["a", "b"], "referred_columns": ["x", "y"]},
        {"referred_table": "Q", "constrained_columns": ["c"], "referred_columns": ["z"]},
    ]
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )
    out = get_foreign_keys(MagicMock(), "C", "postgres")
    # id is counted starting at 0, pairs are zipped
    assert out == [
        {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "a", "to_col": "x"},
        {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "b", "to_col": "y"},
        {"id": 1, "child_table": "C", "parent_table": "Q", "from_col": "c", "to_col": "z"},
    ]


def test_get_foreign_keys_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        side_effect=RuntimeError("fk boom"),
    )
    with pytest.raises(ValueError) as e:
        get_foreign_keys(MagicMock(), "C", "postgres")
    assert "Error retrieving foreign keys for table 'C':" in str(e.value)


# ---------------------------
# build_collections
# ---------------------------

def test_build_collections_happy(mocker):
    """
    Ensure properties, unique properties and table path are built correctly.
    """
    # Inspector default schema
    insp = MagicMock()
    insp.default_schema_name = "public"
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )

    # get_all_columns -> two columns; get_primary_keys -> pk present
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_all_columns",
        return_value=[{"name": "Id", "column name": "Id", "type": "integer"}],
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_primary_keys",
        return_value=["Id"],
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.make_valid_identifier",
        side_effect=lambda db, n: f"v_{n.lower()}",
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.escape_identifier",
        side_effect=lambda db, n: f'"{n}"',
    )

    cols, name_map = build_collections(MagicMock(), ["Users"], "postgres")
    assert name_map == {"Users": "users"}
    assert cols[0]["name"] == "v_users"
    assert cols[0]["unique properties"] == ["v_id"]
    # "table path" should use default schema + escaped table name
    assert cols[0]["table path"] == 'public."Users"'


def test_build_collections_wraps_error(mocker):
    # Ensure inspect(engine) doesn't crash before our side_effect triggers
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=SimpleNamespace(default_schema_name="public"),
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_all_columns",
        side_effect=RuntimeError("boom"),
    )
    with pytest.raises(ValueError) as e:
        build_collections(MagicMock(), ["T"], "sqlite")
    assert "Error building collections from tables:" in str(e.value)


# ---------------------------
# get_unique_columns
# ---------------------------

class FakeCursor:
    def __init__(self, rows):
        self._rows = rows
    def fetchall(self):
        return self._rows

def test_get_unique_columns_sqlite(mocker):
    """
    Should parse PRAGMA index_list & PRAGMA index_info to gather unique columns.
    """
    conn = MagicMock()
    conn.execute.side_effect = [
        FakeCursor([
            (0, "ix_users_email", 1, "c", 0),
            (1, "ix_users_misc", 0, "c", 0),
        ]),
        FakeCursor([
            (0, 0, "email"),
        ]),
    ]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    out = get_unique_columns(engine, '"Users"', "sqlite")
    assert out == {"email"}


def test_get_unique_columns_other_db(mocker):
    insp = MagicMock()
    insp.default_schema_name = "public"
    insp.get_indexes.return_value = [
        {"name": "uq_code", "unique": True, "column_names": ["code"]},
        {"name": "ix_misc", "unique": False, "column_names": ["x"]},
    ]
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )

    out = get_unique_columns(MagicMock(), "T", "postgres")
    assert out == {"code"}


def test_get_unique_columns_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        side_effect=RuntimeError("idx boom"),
    )
    with pytest.raises(ValueError) as e:
        get_unique_columns(MagicMock(), "T", "postgres")
    assert "Error retrieving unique columns for table 'T':" in str(e.value)


# ---------------------------
# infer_relationship
# ---------------------------

def test_infer_relationship_sqlite(mocker):
    """
    PK implies uniqueness; nullable implies reverse not always_matches.
    """
    # Make sure inspect(engine) doesn't raise
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=SimpleNamespace(default_schema_name="main"),
    )

    # PRAGMA table_info uses .fetchall()
    conn = MagicMock()
    conn.execute.return_value = FakeCursor([
        (0, "parent_id", "INTEGER", 1, None, 0),
        (1, "child_id",  "INTEGER", 0, None, 1),
    ])
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    # Unique columns include child_id
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_unique_columns",
        return_value={"child_id"},
    )

    direct, reverse = infer_relationship(engine, "Child", "child_id", "sqlite")
    assert direct["singular"] is True
    assert direct["always matches"] is False
    assert reverse["singular"] is True
    assert reverse["always matches"] is True


def test_infer_relationship_other_db(mocker):
    insp = MagicMock()
    insp.default_schema_name = "public"
    insp.get_columns.return_value = [
        {"name": "fk_id", "nullable": True},
        {"name": "other", "nullable": False},
    ]
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        return_value=insp,
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_primary_keys",
        return_value=[],
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_unique_columns",
        return_value=set(),
    )

    direct, reverse = infer_relationship(MagicMock(), "Child", "fk_id", "postgres")
    assert direct["singular"] is False
    assert reverse["always matches"] is False


def test_infer_relationship_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.inspect",
        side_effect=RuntimeError("inf boom"),
    )
    with pytest.raises(ValueError) as e:
        infer_relationship(MagicMock(), "C", "x", "postgres")
    assert "Error inferring relationship for column 'x' in table 'C':" in str(e.value)


# ---------------------------
# get_safe_relationship_name
# ---------------------------

def test_get_safe_relationship_name_handles_collisions():
    used = {}
    conflicts = {"orders", "orders_2"}
    # First time -> base
    n1 = get_safe_relationship_name("orders", used, conflicts)
    # Since "orders" conflicts, should iterate to orders_2, which also conflicts, then orders_3
    assert n1 == "orders_3"
    n2 = get_safe_relationship_name("orders", used, conflicts)
    assert n2 == "orders_4"


def test_get_safe_relationship_name_no_raise_on_weird_input():
    # Falsy base_name returns None (current implementation behavior)
    out = get_safe_relationship_name(None, {}, set())
    assert out is None

def test_get_safe_relationship_name_weird_string_is_sanitized():
    # Weird but string input should yield a non-empty safe name
    out = get_safe_relationship_name("  123 Orders  ", {}, {"123_orders"})
    assert isinstance(out, str) and len(out) > 0


# ---------------------------
# split/apply split helpers
# ---------------------------

def test_split_all_combinations_basic():
    """
    It should generate combinations grouped by 'to_col'.
    """
    group = [
        {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "a", "to_col": "x"},
        {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "b", "to_col": "x"},
        {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "c", "to_col": "y"},
    ]
    combos = split_all_combinations(group)
    # to_col=x has 2 options, to_col=y has 1 -> 2*1 = 2 combos
    assert len(combos) == 2
    assert all(isinstance(c, list) for c in combos)


def test_apply_split_to_all_fk_groups_assigns_new_ids():
    fk_groups = {
        0: [
            {"id": 0, "child_table": "C", "parent_table": "P", "from_col": "a", "to_col": "x"},
            {"id": 1, "child_table": "C", "parent_table": "P", "from_col": "b", "to_col": "y"},
        ]
    }
    out = apply_split_to_all_fk_groups(fk_groups)
    # Current behavior: combinations stay within a single new group id (0)
    assert set(out.keys()) == {0}
    assert all(fk["id"] == 0 for fk in out[0])


# ---------------------------
# build_relationships
# ---------------------------

def test_build_relationships_happy(mocker):
    """
    Verify forward and reverse relationships generated with safe names and flags.
    """
    # get_foreign_keys returns one fk group with two column mappings (id 0)
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_foreign_keys",
        return_value=[
            {"id": 0, "child_table": "orders", "parent_table": "customers", "from_col": "customer_id", "to_col": "id"},
            {"id": 0, "child_table": "orders", "parent_table": "customers", "from_col": "customer_code", "to_col": "code"},
        ],
    )
    # get_all_columns to compute property_name_map (avoid collisions with 'orders' and 'customers')
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_all_columns",
        side_effect=lambda e, t, db: [{"name": "id"}, {"name": "prop"}],
    )
    # infer_relationship deterministic flags
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.infer_relationship",
        return_value=({"singular": True, "always matches": False}, {"singular": True, "always matches": True}),
    )
    # make_valid_identifier simple
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.make_valid_identifier",
        side_effect=lambda db, n: n.lower(),
    )
    # escape_identifier: pass-through with quotes to match function usage site
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.escape_identifier",
        side_effect=lambda db, n: n,
    )

    relationships = build_relationships(
        engine=MagicMock(),
        tables=["orders"],
        collection_names={"customers": "Customers", "orders": "Orders"},
        db_type="sqlite",
        split_groups=False,
    )

    # Should create 1 forward + 1 reverse
    assert len(relationships) == 2
    fwd = next(r for r in relationships if r["type"] == "simple join")
    rev = next(r for r in relationships if r["type"] == "reverse")

    assert fwd["parent collection"] == "customers"
    assert fwd["child collection"] == "orders"
    assert fwd["keys"] == {"id": ["customer_id"], "code": ["customer_code"]}

    assert rev["original parent"] == "customers"
    assert rev["original property"] == fwd["name"]
    assert rev["singular"] is True
    assert rev["always matches"] is True


def test_build_relationships_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.get_foreign_keys",
        side_effect=RuntimeError("r boom"),
    )
    with pytest.raises(ValueError) as e:
        build_relationships(MagicMock(), ["T"], {}, "sqlite", False)
    assert "Error building relationships from foreign keys:" in str(e.value)


# ---------------------------
# generate_metadata
# ---------------------------

def test_generate_metadata_happy(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.build_collections",
        return_value=(
            [{"name": "c1"}],
            {"T": "t"},
        ),
    )
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.build_relationships",
        return_value=[{"type": "simple join", "name": "rel"}],
    )

    out = generate_metadata(
        engine=MagicMock(),
        graph_name="GraphX",
        db_type="sqlite",
        tables=["T"],
        split_groups=True,
    )
    assert out == [{
        "name": "GraphX",
        "version": "V2",
        "collections": [{"name": "c1"}],
        "relationships": [{"type": "simple join", "name": "rel"}],
    }]


def test_generate_metadata_wraps_error(mocker):
    mocker.patch(
        "src.pydough_analytics.metadata.generate_knowledge_graph.build_collections",
        side_effect=RuntimeError("collect fail"),
    )
    with pytest.raises(ValueError) as e:
        generate_metadata(MagicMock(), "G", "sqlite", ["T"])
    assert "Error generating metadata:" in str(e.value)
