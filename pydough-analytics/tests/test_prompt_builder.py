from __future__ import annotations

from pydough_analytics.prompting.builder import PromptBuilder


def test_prompt_contains_question_and_metadata():
    metadata = {
        "collections": [
            {
                "name": "customers",
                "properties": [
                    {"name": "id", "type": "table column"},
                    {"name": "name", "type": "table column"},
                ],
            }
        ]
    }
    builder = PromptBuilder(metadata)
    prompt = builder.build("List customers")
    assert "List customers" in prompt.user
    assert "customers" in prompt.user
