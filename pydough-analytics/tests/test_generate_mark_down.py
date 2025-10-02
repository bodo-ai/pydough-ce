import pytest
from unittest.mock import MagicMock

# Target under test
from src.pydough_analytics.metadata.generate_mark_down import (
    generate_collections_and_subcollections,
    generate_additional_definitions_section,
    generate_verified_analysis_section,
    generate_functions_section,
    generate_markdown_from_metadata,
)

# ---------------------------
# Helpers to build mock graph
# ---------------------------

def make_mock_property(
    name: str,
    *,
    is_subcollection: bool = False,
    description: str | None = None,
    synonyms: list[str] | None = None,
    sample_values: list[object] | None = None,
    with_rel_ref: bool = False,
    parent_name: str = "Parent",
    child_name: str = "Child",
):
    """
    Build a PropertyMetadata-like mock.
    """
    prop = MagicMock()
    prop.name = name
    prop.is_subcollection = is_subcollection
    prop.description = description
    prop.synonyms = synonyms or []
    prop.sample_values = sample_values or []

    # Relationship reference lines only if requested
    if with_rel_ref:
        prop.collection = MagicMock()
        prop.collection.name = parent_name
        prop.child_collection = MagicMock()
        prop.child_collection.name = child_name
    else:
        # Ensure attributes may not exist
        if hasattr(prop, "collection"):
            delattr(prop, "collection")
        if hasattr(prop, "child_collection"):
            delattr(prop, "child_collection")
    return prop


def make_mock_collection(
    name: str,
    *,
    description: str | None = None,
    synonyms: list[str] | None = None,
    scalar_props: list[MagicMock] | None = None,
    relation_props: list[MagicMock] | None = None,
):
    """
    Build a CollectionMetadata-like mock.
    """
    col = MagicMock()
    col.name = name
    col.description = description
    col.synonyms = synonyms or []

    # Property storage
    props = {}
    scalar_props = scalar_props or []
    relation_props = relation_props or []

    for p in scalar_props + relation_props:
        props[p.name] = p

    # API used by the generator
    col.get_property_names.return_value = list(props.keys())
    col.get_property.side_effect = lambda n: props.get(n)

    return col


def make_mock_graph(
    *,
    name: str = "TestGraph",
    collections: dict[str, MagicMock] | None = None,
    additional_definitions: list[str] | None = None,
    verified_pydough_analysis: list[dict] | None = None,
    functions: dict[str, MagicMock] | None = None,
):
    """
    Build a GraphMetadata-like mock.
    """
    graph = MagicMock()
    graph.name = name

    collections = collections or {}
    graph.get_collection_names.return_value = list(collections.keys())
    graph.get_collection.side_effect = lambda n: collections.get(n)

    # Optional sections
    if additional_definitions is not None:
        graph.additional_definitions = additional_definitions
    if verified_pydough_analysis is not None:
        graph.verified_pydough_analysis = verified_pydough_analysis

    # Functions
    functions = functions or {}
    graph.get_function_names.return_value = list(functions.keys())
    graph.get_function.side_effect = lambda n: functions.get(n)

    return graph


# ---------------------------
# generate_collections_and_subcollections
# ---------------------------

def test_generate_collections_and_subcollections_basic_success():
    """
    Should list collections, descriptions, synonyms, scalar props, and relationships.
    """
    # Scalar prop
    p_id = make_mock_property(
        "id",
        is_subcollection=False,
        description="Primary identifier.",
        synonyms=["identifier", "key"],
        sample_values=[1, 2, 3],
    )
    # Relationship prop with related collection reference
    p_orders = make_mock_property(
        "orders",
        is_subcollection=True,
        description="Orders of the customer.",
        synonyms=["purchases"],
        with_rel_ref=True,
        parent_name="customers",
        child_name="orders",
    )

    customers = make_mock_collection(
        "customers",
        description="Customers table.",
        synonyms=["clients", "buyers"],
        scalar_props=[p_id],
        relation_props=[p_orders],
    )

    graph = make_mock_graph(collections={"customers": customers})

    out_lines = generate_collections_and_subcollections([], graph)

    text = "\n".join(out_lines)
    # Section header
    assert "## Collections" in text
    # Collection header
    assert "### Collection: `customers`" in text
    # Collection description
    assert "- **Description**: Customers table." in text
    # Synonyms at collection level
    assert "- **Synonyms**: clients, buyers" in text
    # Scalar section
    assert "#### Contains the following scalar properties or columns" in text
    assert "- **id**: Primary identifier." in text
    assert "  - Synonyms: identifier, key" in text
    assert "  - Sample values: 1, 2, 3" in text
    # Relationship section
    assert "#### Contains the following sub-collections or relationships" in text
    assert "- **orders**: Orders of the customer." in text
    assert "  - Related to: `customers.orders`" in text
    assert "  - Synonyms: purchases" in text


def test_generate_collections_and_subcollections_missing_descriptions():
    """
    When descriptions are missing, it should print the 'No description available.' placeholder.
    """
    # No description in collection and property
    p_no_desc = make_mock_property("x", is_subcollection=False, description=None)
    c_no_desc = make_mock_collection("c1", description=None, scalar_props=[p_no_desc])
    graph = make_mock_graph(collections={"c1": c_no_desc})

    out_lines = generate_collections_and_subcollections([], graph)
    text = "\n".join(out_lines)

    assert "- **Description**: No description available." in text
    assert "- **x**: No description available." in text


def test_generate_collections_and_subcollections_exception_wrapped(mocker):
    """
    If an unexpected error occurs, it should raise with 'Error processing collections: {e}'.
    """
    graph = make_mock_graph()
    # Force an error inside implementation by making get_collection_names blow up
    graph.get_collection_names.side_effect = RuntimeError("boom")
    with pytest.raises(Exception) as e:
        generate_collections_and_subcollections([], graph)
    assert "Error processing collections: boom" in str(e.value)


# ---------------------------
# generate_additional_definitions_section
# ---------------------------

@pytest.mark.parametrize(
    "additional,expected_snippet",
    [
        (["Revenue = price - cost"], "- **Definition 1**: Revenue = price - cost"),
        ([], None), 
        (None, None),  
    ],
    ids=["one_definition", "empty_list", "none_missing"],
)
def test_generate_additional_definitions_section(additional, expected_snippet):
    graph = make_mock_graph(additional_definitions=additional)
    out_lines = generate_additional_definitions_section([], graph)
    text = "\n".join(out_lines)

    if expected_snippet:
        assert "## Additional Definitions" in text
        assert expected_snippet in text
    elif not isinstance(additional, list):
        assert "## Additional Definitions" in text
    else:
        assert "## Additional Definitions" not in text


def test_generate_additional_definitions_section_exception_wrapped():
    """
    Simula un fallo al acceder a graph.additional_definitions y verifica el wrap del error.
    """
    class BoomGraph:
        def __getattr__(self, name):
            # Forzar que cualquier acceso a atributos falle
            raise RuntimeError("AD boom")

    with pytest.raises(Exception) as e:
        generate_additional_definitions_section([], BoomGraph())

    assert "Error processing additional definitions: AD boom" in str(e.value)



# ---------------------------
# generate_verified_analysis_section
# ---------------------------

def test_generate_verified_analysis_section_success():
    graph = make_mock_graph(
        verified_pydough_analysis=[
            {"question": "Q1?", "code": "return 1"},
            {"question": "Q2?", "code": "return 2"},
        ]
    )
    out_lines = generate_verified_analysis_section([], graph)
    text = "\n".join(out_lines)

    assert "## Verified PyDough Analysis" in text
    # Entry 1
    assert "### Analysis #1" in text
    assert "- **Question**: Q1?" in text
    assert "```python" in text
    assert "return 1" in text
    assert "```" in text
    # Entry 2
    assert "### Analysis #2" in text
    assert "- **Question**: Q2?" in text
    assert "return 2" in text


@pytest.mark.parametrize("entries", [[], None], ids=["empty", "none"])
def test_generate_verified_analysis_section_absent(entries):
	graph = make_mock_graph(verified_pydough_analysis=entries)
	out_lines = generate_verified_analysis_section([], graph)
	text = "\n".join(out_lines)
	if not isinstance(entries, list):
		assert "## Verified PyDough Analysis" in text
	else:
		assert "## Verified PyDough Analysis" not in text


def test_generate_verified_analysis_section_exception_wrapped():
    """Simula un fallo al acceder a graph.verified_pydough_analysis y verifica el wrap del error."""
    class BoomGraph:
        def __getattr__(self, name):
            # Forzar que cualquier acceso a atributos falle
            raise RuntimeError("VA boom")

    with pytest.raises(Exception) as e:
        generate_verified_analysis_section([], BoomGraph())

    assert "Error processing verified analysis: VA boom" in str(e.value)



# ---------------------------
# generate_functions_section
# ---------------------------

def test_generate_functions_section_success():
    f1 = MagicMock()
    f1.description = "Adds two numbers."
    f2 = MagicMock()
    f2.description = None

    graph = make_mock_graph(
        functions={
            "add": f1,
            "noop": f2,
        }
    )
    out_lines = generate_functions_section([], graph)
    text = "\n".join(out_lines)

    assert "## Functions" in text
    assert "### Function: `add`" in text
    assert "- **Description**: Adds two numbers." in text
    assert "### Function: `noop`" in text
    assert "- **Description**: No description available." in text


def test_generate_functions_section_exception_wrapped(mocker):
    graph = make_mock_graph(functions={"x": MagicMock()})
    graph.get_function_names.side_effect = RuntimeError("FN boom")
    with pytest.raises(Exception) as e:
        generate_functions_section([], graph)
    assert "Error processing functions: FN boom" in str(e.value)


# ---------------------------
# generate_markdown_from_metadata (integration)
# ---------------------------

def test_generate_markdown_from_metadata_integration_minimal():
    """
    Top-level should contain the H1 header, collections, and functions sections.
    """
    # Minimal non-empty objects so loops iterate
    dummy_prop = make_mock_property("id", is_subcollection=False, description="ok")
    dummy_col = make_mock_collection("demo", description="Demo.", scalar_props=[dummy_prop])
    dummy_fn = MagicMock()
    dummy_fn.description = "Example fn."

    graph = make_mock_graph(
        name="MyGraph",
        collections={"demo": dummy_col},
        functions={"fn_example": dummy_fn},
    )

    md = generate_markdown_from_metadata(graph)

    # Header
    assert "# Metadata Overview: MyGraph (Graph Name)" in md
    # Collections content
    assert "## Collections" in md
    assert "### Collection: `demo`" in md
    # Functions content
    assert "## Functions" in md
    assert "### Function: `fn_example`" in md


def test_generate_markdown_from_metadata_wraps_exceptions(mocker):
    """
    If a nested function explodes, outer function raises with the literal message (bug in code).
    """
    graph = make_mock_graph()
    # Patch inner function to raise so we go to the except of generate_markdown_from_metadata
    mocker.patch(
        "src.pydough_analytics.metadata.generate_mark_down.generate_collections_and_subcollections",
        side_effect=RuntimeError("INNER BOOM"),
    )
    with pytest.raises(Exception) as e:
        generate_markdown_from_metadata(graph)
        
    assert "Failed to generate Markdown due to error: {e}" in str(e.value)
