"""Prompt construction utilities for the text-to-PyDough workflow."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Mapping, Optional

from .config import PromptConfig
from .guide import PYDOUGH_GUIDE
from .schema import render_schema


CHEAT_SHEET = """PyDough reminders:
- Use collection methods: `Collection.CALCULATE(...)`, `Collection.WHERE(...)`, `Collection.TOP_K(k, by=expression)`.
- Call `TOP_K` on the collection returned from your calculation (example: `nation.CALCULATE(...).TOP_K(5, by=total_revenue.DESC())`).
- Relationships are attributes (no parentheses): `orders.customer`, `nation.suppliers`.
- Aggregations act on plural sub-collections: `SUM(lines.L_EXTENDEDPRICE * (1 - lines.L_DISCOUNT))`.
- Filters must be called on collections (e.g., `orders.WHERE(order_date.YEAR() == 1994)`).
- Chain methods (e.g., `collection.WHERE(...).CALCULATE(...)`) and assign the final result to `result`.

Example:
```python
orders_1994 = orders.WHERE(YEAR(o_orderdate) == 1994)
result = nation.CALCULATE(
    n_name,
    total_revenue=SUM(orders_1994.lineitem.l_extendedprice * (1 - orders_1994.lineitem.l_discount))
).TOP_K(5, by=total_revenue.DESC())
```
- Identifier case matters: use collection/property names exactly as shown in the metadata section.
- When ranking, reference the calculated field directly (for example `by=total_revenue.DESC()`), without prefixing it with the collection name.
- Avoid reusing a collection name for a calculated field; give result columns unique names like `city_name`.
- Inside `CALCULATE`, reference properties directly (use `amount`, not `payment.amount`).
"""

def _default_system_instruction() -> str:
    return dedent(
    """
    You translate natural language analytics questions into executable PyDough code.
    PyDough is a Python DSL that operates on the metadata provided.

    Rules you must follow:
    - Return only valid Python code that uses the PyDough DSL and assigns the final analytic expression to a variable named `result`.
    - Use CALCULATE to project scalar fields. Use aggregation functions (SUM, COUNT, AVG, etc.) when iterating over plural sub-collections.
    - Use WHERE for filtering, TOP_K for ordered top-k results, and HAS/HASNOT to test existence of sub-collections.
    - Do not emit SQL, raw pandas code, or plain English.
    - Respect the metadata; do not invent collections or properties that are not listed.
    - Keep calculations declarative—avoid Python loops or conditionals outside PyDough constructs.
    - When provided with previous code and an error message, update the code to fix the issue rather than returning a brand new analysis.

    Your response must be JSON with fields `code` (required) and `explanation` (optional).
    """
    ).strip()


@dataclass
class Prompt:
    system: str
    user: str


class PromptBuilder:
    """Builds prompts for the LLM based on metadata and conversation context."""

    def __init__(self, metadata: Mapping[str, object], config: Optional[PromptConfig] = None) -> None:
        self._metadata = metadata
        self._config = config or PromptConfig.from_env()
        self._metadata_text = render_schema(
            metadata,
            style=self._config.schema_style,
            max_collections=self._config.schema_max_collections,
            max_columns=self._config.schema_max_columns,
        )
        self._guide = self._config.guide_text or PYDOUGH_GUIDE
        self._system_instruction = self._config.system_instruction or _default_system_instruction()

    def build(
        self,
        question: str,
        *,
        previous_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Prompt:
        parts = [f"Question:\n{question.strip()}\n"]
        if previous_code:
            parts.append("Previous attempt:\n")
            parts.append(f"```python\n{previous_code.strip()}\n```\n")
        if error_message:
            parts.append("Runtime feedback:\n")
            parts.append(f"{error_message.strip()}\n")

        if self._metadata_text:
            parts.append("Metadata:\n")
            parts.append(self._metadata_text)
        parts.append("Guidance:\n")
        parts.append(CHEAT_SHEET)
        parts.append("\nReference:\n")
        parts.append(self._guide)

        user_content = "\n".join(parts)
        return Prompt(system=self._system_instruction, user=user_content)


__all__ = ["Prompt", "PromptBuilder"]
