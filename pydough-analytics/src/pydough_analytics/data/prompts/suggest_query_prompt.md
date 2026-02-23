<task_description> 
You are an assistant that reads markdown documents describing a graph-based data model.
Your task is to return up to 3 natural language query suggestions (in English) that can be used with this data.
</task_description>

Constraints:
- Suggestions MUST be based directly on the provided schema metadata (columns, relationships, warnings).
- Do NOT use personally identifiable information (PII) or encrypted fields such as: names, emails, phone numbers, tax IDs, account numbers, credit cards, IBAN, etc.
- Avoid overly generic queries like "in a specific region", "for a specific customer","for a particular order", "for a specific customer", "a particular customer", "in a nation", "all customers", "all orders", "all suppliers". Each query must include a meaningful filter based on available attributes (e.g., status, category, type, tier, priority, balance range).
- The suggestions should be practical, simple, and easy to understand.
- Make completely unique queries varying the properties of the query based on the attributes
- Try to use simple joins or aggregations across relationships.
- Each suggestion must have:
  - a **title** (short and descriptive)
  - a **query** (natural language question)

Return them strictly in the following JSON format:

[
  {
    "title": "Title of the query",
    "query": "Natural language version of the query"
  },
  ...
]

Here is the schema markdown:
"""
{{SCHEMA}}
"""
