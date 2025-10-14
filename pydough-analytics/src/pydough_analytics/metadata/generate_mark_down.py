from pydough.metadata import GraphMetadata, CollectionMetadata, PropertyMetadata
from pydough.pydough_operators import ExpressionFunctionOperator

from typing import Any, Dict, Iterable, List, Optional

class _DictProperty:
    def __init__(self, d: Dict[str, Any]):
        self.name: str = d.get("name", "")
        self.type: str = d.get("type", "")

class _DictRelationship:
    def __init__(self, d: Dict[str, Any]):
        self.name: str = d.get("name", "")
        self.to: str = d.get("to", "")
        self.cardinality: str = d.get("cardinality", "")

class _DictCollection:
    def __init__(self, d: Dict[str, Any]):
        self.name: str = d.get("name", "")
        self._props = [ _DictProperty(p) for p in d.get("properties", []) ]
        self._rels  = [ _DictRelationship(r) for r in d.get("relationships", []) ]

    # Methods some existing markdown generators tend to call:
    def iter_properties(self) -> Iterable[_DictProperty]:
        return iter(self._props)

    def iter_relationships(self) -> Iterable[_DictRelationship]:
        return iter(self._rels)

class _DictGraphAdapter:
    """Adapter so dict-based V2 metadata looks like the rich Graph API."""
    def __init__(self, g: Dict[str, Any]):
        self.name: str = g.get("name", "GRAPH")
        cols = g.get("collections", [])
        self._collections: List[_DictCollection] = [ _DictCollection(c) for c in cols ]
        # Map for quick lookup by name
        self._by_name = { c.name: c for c in self._collections }

    # Common calls used by markdown renderers:
    def get_collection_names(self) -> List[str]:
        return [c.name for c in self._collections]

    def get_collection(self, name: str) -> Optional[_DictCollection]:
        return self._by_name.get(name)

    def iter_collections(self) -> Iterable[_DictCollection]:
        return iter(self._collections)

def _ensure_graph_object(graph: Any) -> Any:
    """If `graph` is a dict (V2), wrap it; otherwise pass through."""
    if isinstance(graph, dict):
        return _DictGraphAdapter(graph)
    return graph


def generate_collections_and_subcollections(markdown: list[str], graph: GraphMetadata) -> list[str]:
    """
    Appends the collections and their properties/relationships to the Markdown output.
    """
    graph = _ensure_graph_object(graph)

    try:
        markdown.append("## Collections")
        for collection_name in graph.get_collection_names():
            collection = graph.get_collection(collection_name)
            markdown.append(f"### Collection: `{collection.name}` ")

            # Si es una colección "rica" (CollectionMetadata) con attrs/métodos:
            if hasattr(collection, "get_property_names"):
                # Description
                if hasattr(collection, 'description') and collection.description:
                    markdown.append(f"- **Description**: {collection.description}")
                else:
                    markdown.append("- **Description**: No description available.")
                # Synonyms
                if hasattr(collection, 'synonyms') and collection.synonyms:
                    markdown.append(f"- **Synonyms**: {', '.join(collection.synonyms)}")

                markdown.append("")
                markdown.append("#### Contains the following scalar properties or columns")
                for prop_name in collection.get_property_names():
                    prop = collection.get_property(prop_name)
                    if not prop or getattr(prop, "is_subcollection", False):
                        continue
                    description_text = getattr(prop, "description", None) or "No description available."
                    markdown.append(f"- **{prop.name}**: {description_text}")
                    if hasattr(prop, 'synonyms') and prop.synonyms:
                        markdown.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                    if hasattr(prop, 'sample_values') and prop.sample_values:
                        sample_values_str = ', '.join(map(str, prop.sample_values))
                        markdown.append(f"  - Sample values: {sample_values_str}")

                markdown.append("")
                # Sub-collections or relationships como propiedades especiales
                relationship_props = [
                    collection.get_property(p)
                    for p in collection.get_property_names()
                    if (collection.get_property(p) and getattr(collection.get_property(p), "is_subcollection", False))
                ]
                if relationship_props:
                    markdown.append(f"#### Contains the following sub-collections or relationships")
                    for prop in relationship_props:
                        description_text = getattr(prop, "description", None) or "No description available."
                        markdown.append(f"- **{prop.name}**: {description_text}")
                        if hasattr(prop, 'collection') and hasattr(prop, 'child_collection'):
                            parent_name = getattr(prop.collection, "name", "?")
                            child_name = getattr(prop.child_collection, "name", "?")
                            markdown.append(f"  - Related to: `{parent_name}.{child_name}`")
                        if hasattr(prop, 'synonyms') and prop.synonyms:
                            markdown.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                    markdown.append("")

            else:
                # ✅ Ruta dict-adaptada: usa tus iteradores simples
                markdown.append("- **Description**: No description available.")
                markdown.append("")
                markdown.append("#### Contains the following scalar properties or columns")
                for prop in collection.iter_properties():
                    markdown.append(f"- **{prop.name}**: type `{prop.type}`")

                markdown.append("")
                rels = list(collection.iter_relationships())
                if rels:
                    markdown.append("#### Contains the following sub-collections or relationships")
                    for r in rels:
                        card = f" ({r.cardinality})" if r.cardinality else ""
                        markdown.append(f"- **{r.name}** → `{r.to}`{card}")
                    markdown.append("")

            markdown.append("")  # espaciado entre colecciones
        return markdown
    except Exception as e:
        raise Exception(f"Error processing collections: {e}")


def generate_additional_definitions_section(markdown: list[str], graph: GraphMetadata) -> list[str]:
    """
    Appends the Additional Definitions section to the Markdown if present.
    """
    try:
        additional_defs: list[str] = getattr(graph, "additional_definitions", None)
        if additional_defs:
            markdown.append("## Additional Definitions")
            for i, definition in enumerate(additional_defs, start=1):
                markdown.append(f"- **Definition {i}**: {definition}")
            markdown.append("") 
        return markdown
    except Exception as e:
        raise Exception(f"Error processing additional definitions: {e}")

def generate_verified_analysis_section(markdown: list[str], graph: GraphMetadata) -> list[str]:
    """
    Appends the Verified PyDough Analysis section to the Markdown if present.
    """
    try:
        analysis_entries: list[dict] = getattr(graph, "verified_pydough_analysis", None)
        if analysis_entries:
            markdown.append("## Verified PyDough Analysis")
            for i, entry in enumerate(analysis_entries, start=1):
                question = entry.get("question")
                code = entry.get("code")
                markdown.append(f"### Analysis #{i}")
                markdown.append(f"- **Question**: {question}")
                markdown.append("```python")
                markdown.append(code)
                markdown.append("```")
                markdown.append("")
        return markdown
    except Exception as e:
        raise Exception(f"Error processing verified analysis: {e}")

def generate_functions_section(markdown: list[str], graph: GraphMetadata) -> list[str]:
    """
    Appends the user-defined functions to the Markdown output.
    """
    # ✅ Acepta dicts y objetos ricos
    graph = _ensure_graph_object(graph)

    try:
        # Si el objeto no expone funciones, salta silenciosamente
        if not hasattr(graph, "get_function_names"):
            return markdown

        names = graph.get_function_names()
        if names:
            markdown.append("## Functions")
        for func_name in names:
            func = graph.get_function(func_name)
            markdown.append(f"### Function: `{func_name}`")

            description = getattr(func, "description", None)
            markdown.append(f"- **Description**: {description if description else 'No description available.'}")
            markdown.append("")
        return markdown
    except Exception as e:
        raise Exception(f"Error processing functions: {e}")


def generate_markdown_from_metadata(graph: GraphMetadata):
    """
    Converts a pydough graph metadata object into a formatted Markdown string..
    """
    try:
        # Ensure we have a GraphMetadata object (wrap dict if needed)
        graph = _ensure_graph_object(graph)
    
        markdown_output: list[str] = []

        markdown_output.append(f"# Metadata Overview: {graph.name} (Graph Name)")
        markdown_output.append("")

        markdown_output = generate_collections_and_subcollections(markdown_output, graph)
        markdown_output.append("")
        markdown_output = generate_functions_section(markdown_output, graph)

        return "\n".join(markdown_output)
    except Exception as e:
        raise Exception(f"Failed to generate Markdown due to error: {e}")
