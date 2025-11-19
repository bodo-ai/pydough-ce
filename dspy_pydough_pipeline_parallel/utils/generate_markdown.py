def render_value(value: object, indent: int = 0) -> list[str]:
    """
    Recursively render a value (str, list, dict) as Markdown lines.
    """
    try:
        prefix: str = " " * indent
        lines: list[str] = []

        if isinstance(value, (str, int, float, bool)):
            lines.append(f"{prefix}- '{str(value)}'")

        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}[]")
            else:
                lines.append(f"{prefix}[")
                for item in value:
                    lines.extend(render_value(item, indent + 2))
                lines.append(f"{prefix}]")

        elif isinstance(value, dict):
            if not value:
                lines.append(f"{prefix}{{}}")
            else:
                lines.append(f"{prefix}{"{"}")
                for subkey, subval in value.items():
                    if isinstance(subval, (str, int, float, bool)):
                        lines.append(f"{prefix+" "*2}- {subkey}: '{str(subval)}'")
                    else:
                        lines.append(f"{prefix+" "*2}- {subkey}:  ")
                        lines.extend(render_value(subval, indent + 2))
                lines.append(f"{prefix}{"}"}")

        else:
            lines.append(f"{prefix}- {str(value)}")

        return lines
    except Exception as e:
        raise Exception(f"Error render the values of extra semantic info: {e}")

def render_extra_semantic_section(
    markdown: list[str],
    extra_info: dict,
    title_line: str,
    key_prefix: str,
    closing_line: str,
    base_indent: int = 0,
) -> list[str]:
    """
    Appends a formatted Markdown block for the extra_semantic_info field.
    """
    # Section title
    markdown.append(f"{title_line}")

    # Render each key-value pair
    for key, value in extra_info.items():
        if isinstance(value, (str, int, float, bool)):
            markdown.append(f"{key_prefix.format(key=key)}'{str(value)}'")
        else:
            markdown.append(f"{key_prefix.format(key=key)}")
            markdown.extend(render_value(value, indent=base_indent))

    # Closing line
    markdown.append(f"{closing_line}")

    return markdown

def generate_collections_and_subcollections(markdown: list[str], graph) -> list[str]:
    """
    Appends the collections and their properties/relationships to the Markdown output.
    """
    try:
        markdown.append("## Collections")
        for collection_name in graph.get_collection_names():
            collection = graph.get_collection(collection_name)
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
                prop = collection.get_property(prop_name)
                if not prop or prop.is_subcollection:
                    continue

                description_text: str = prop.description if prop.description else "No description available."
                markdown.append(f"- **{prop.name}**: {description_text}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    markdown.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                if hasattr(prop, 'sample_values') and prop.sample_values:
                    sample_values_str = ', '.join(map(str, prop.sample_values))
                    markdown.append(f"  - Sample values: {sample_values_str}")
                if hasattr(prop, 'extra_semantic_info') and prop.extra_semantic_info:
                    render_extra_semantic_section(
                        markdown, 
                        prop.extra_semantic_info,
                        "  - Extra semantic info: (",
                        "    - {key}:  ",
                        "  )",
                        6
                    )

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
                    if hasattr(prop, 'extra_semantic_info') and prop.extra_semantic_info:
                        render_extra_semantic_section(
                            markdown, 
                            prop.extra_semantic_info,
                            "  - Extra semantic info: (",
                            "    - {key}:  ",
                            "  )",
                            6
                        )

                markdown.append("")

            # Extra semantic info
            if hasattr(collection, 'extra_semantic_info') and collection.extra_semantic_info:
                render_extra_semantic_section(
                    markdown, 
                    collection.extra_semantic_info,
                    "#### Contains the following extra semantic information",
                    "- **{key}**: ",
                    "",
                    2
                )

            markdown.append("")
        return markdown
    except Exception as e:
        raise Exception(f"Error processing collections: {e}")

def generate_additional_definitions_section(markdown: list[str], graph) -> list[str]:
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

def generate_verified_analysis_section(markdown: list[str], graph) -> list[str]:
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

def generate_functions_section(markdown: list[str], graph) -> list[str]:
    """
    Appends the user-defined functions to the Markdown output.
    """
    try:
        if hasattr(graph, "functions") and graph.functions:
            markdown.append("## Functions")
            for func_name in graph.get_function_names():
                func = graph.get_function(func_name)
                markdown.append(f"### Function: `{func_name}`")

                # Description
                description: str = getattr(func, "description", None)
                markdown.append(f"- **Description**: {description if description else 'No description available.'}")
                markdown.append("")
            markdown.append("")
        return markdown
    except Exception as e:
        raise Exception(f"Error processing functions: {e}")

def generate_markdown_from_metadata(graph):
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
        markdown_output.append("")
        if hasattr(graph, 'extra_semantic_info') and graph.extra_semantic_info:
            render_extra_semantic_section(
                markdown_output, 
                graph.extra_semantic_info,
                "## Extra Semantic Information",
                "- **{key}**: ",
                "",
                1
                )
            markdown_output.append("")

        return "\n".join(markdown_output)
    except Exception as e:
        raise Exception(f"Failed to generate Markdown due to error: {e}")