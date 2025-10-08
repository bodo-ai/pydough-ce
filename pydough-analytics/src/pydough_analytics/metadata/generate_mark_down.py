from pydough.metadata import GraphMetadata, CollectionMetadata, PropertyMetadata
from pydough.pydough_operators import ExpressionFunctionOperator

def generate_collections_and_subcollections(markdown: list[str], graph: GraphMetadata) -> list[str]:
    """
    Appends the collections and their properties/relationships to the Markdown output.
    """
    try:
        markdown.append("## Collections")
        for collection_name in graph.get_collection_names():
            collection: CollectionMetadata = graph.get_collection(collection_name)
            markdown.append(f"### Collection: `{collection.name}` ")

            # Collection description
            if hasattr(collection, 'description') and collection.description:
                markdown.append(f"- **Description**: {collection.description}")
            else:
                markdown.append("- **Description**: No description available.")

            # Synonyms
            if hasattr(collection, 'synonyms') and collection.synonyms:
                markdown.append(f"- **Synonyms**: {', '.join(collection.synonyms)}")

            markdown.append("")

            # Scalar properties
            markdown.append("#### Contains the following scalar properties or columns")
            for prop_name in collection.get_property_names():
                prop: PropertyMetadata = collection.get_property(prop_name)
                if not prop or prop.is_subcollection:
                    continue

                description_text: str = prop.description if prop.description else "No description available."
                markdown.append(f"- **{prop.name}**: {description_text}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    markdown.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                if hasattr(prop, 'sample_values') and prop.sample_values:
                    sample_values_str = ', '.join(map(str, prop.sample_values))
                    markdown.append(f"  - Sample values: {sample_values_str}")

            markdown.append("")

            # Sub-collections or relationships
            relationship_props: list = [
                collection.get_property(p) for p in collection.get_property_names()
                if collection.get_property(p) and collection.get_property(p).is_subcollection
            ]

            if relationship_props:
                markdown.append(f"#### Contains the following sub-collections or relationships")
                for prop in relationship_props:
                    description_text: str = prop.description if prop.description else "No description available."
                    markdown.append(f"- **{prop.name}**: {description_text}")

                    # Reference to related collection
                    if hasattr(prop, 'collection') and hasattr(prop, 'child_collection'):
                        parent_name: str = prop.collection.name
                        child_name: str = prop.child_collection.name
                        markdown.append(f"  - Related to: `{parent_name}.{child_name}`")

                    if hasattr(prop, 'synonyms') and prop.synonyms:
                        markdown.append(f"  - Synonyms: {', '.join(prop.synonyms)}")

                markdown.append("")
            markdown.append("")
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
    try:
        if graph.get_function_names():
            markdown.append("## Functions")
        for func_name in graph.get_function_names():
            func: ExpressionFunctionOperator = graph.get_function(func_name)
            markdown.append(f"### Function: `{func_name}`")

            # Description
            description: str = getattr(func, "description", None)
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
        markdown_output: list[str] = []

        markdown_output.append(f"# Metadata Overview: {graph.name} (Graph Name)")
        markdown_output.append("")

        markdown_output = generate_collections_and_subcollections(markdown_output, graph)
        markdown_output.append("")
        markdown_output = generate_functions_section(markdown_output, graph)

        return "\n".join(markdown_output)
    except Exception as e:
        raise Exception(f"Failed to generate Markdown due to error: {e}")
