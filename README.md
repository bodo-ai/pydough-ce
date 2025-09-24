# pydough-full

Welcome to the `pydough-full` project! This repository contains the `pydough-analytics` toolkit, a powerful system that translates natural language questions into data analytics results.

It combines a custom Domain-Specific Language (DSL) called PyDough with the power of Large Language Models (LLMs) like Gemini to create a seamless text-to-analytics workflow.

## What It Does

At its core, this project empowers you to "ask" questions of your relational database in plain English. The toolkit handles the complex process of converting your question into a safe, executable query and returning the data you asked for.

The primary workflow is:
1.  **Generate Metadata:** First, you point the tool at your database. It analyzes the schema (tables, columns, relationships) and creates a "knowledge graph" representation.
2.  **Ask a Question:** You ask a question in natural language (e.g., "What are the top 5 cities by total sales?").
3.  **Translate to PyDough:** The system uses an LLM to convert your question into a query using the **PyDough DSL**—a simple, safe language designed specifically for data manipulation.
4.  **Execute Safely:** The PyDough code is materialized into SQL, executed against your database, and the results are returned as a structured table (or a DataFrame for developers).

## Key Features

*   **Natural Language Interface:** Query your data without writing SQL.
*   **Automatic Schema Analysis:** Quickly generates the necessary metadata from existing databases like SQLite, PostgreSQL, MySQL, and Snowflake.
*   **Safe and Sandboxed:** The PyDough DSL prevents arbitrary code execution, ensuring that only safe, declarative data operations are run.
*   **Developer Friendly:** Provides both a command-line interface (CLI) for ad-hoc analysis and a Python API for programmatic use.
*   **Extensible:** Allows for custom prompts, different LLM configurations, and even exposing the analytics capabilities as a service.

## Repository Structure

This repository contains everything you need to run and develop the toolkit.

```
/ 
├── metadata/              # Sample metadata files.
├── pydough-analytics/     # The core Python package.
│   ├── src/               # Source code for the pydough_analytics library.
│   ├── tests/             # Unit and integration tests.
│   ├── docs/              # Detailed guides and documentation.
│   └── README.md          # --> In-depth package documentation.
└── README.md              # You are here!
```

## Getting Started

### Prerequisites

1.  **Python:** Version 3.10 or higher.
2.  **Gemini API Key:** You need an API key for the Google Gemini model. Set it as an environment variable:
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    ```
    The application also supports reading this key from a `.env` file in the project root.

### Installation & Usage

The core logic is contained within the `pydough-analytics` package. For detailed instructions on installation, CLI usage, supported databases, and advanced configuration, please refer to the package's dedicated README.

**➡️ See the detailed [pydough-analytics/README.md](pydough-analytics/README.md) for full setup and usage instructions.**

### Quick Example

Once installed, you can immediately start asking questions using the included sample data.

```bash
# Use the CLI to ask a question against the sample sales database
pydough-analytics ask "Top 3 sales by amount" \
  --metadata metadata/live_sales.json \
  --graph-name SALES \
  --url sqlite:///metadata/live_sales.db \
  --show-sql --show-code
```

## The PyDough DSL

The "PyDough" DSL is a simple, Python-like language for expressing data operations. It is designed to be easy for an LLM to generate and safe to execute. It focuses on common analytics tasks like filtering, ordering, and aggregation.

A typical PyDough query looks like this:

```python
# Get the top 3 sales, showing the city and amount
result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())
```

To understand its syntax and capabilities, please read the comprehensive guide.

**➡️ Learn more in the [PyDough DSL Prompt Authoring Guide](pydough-analytics/docs/pydough-prompt-guide.md).**

## What's Next?

This project has a clear roadmap for future enhancements. Contributions and ideas are welcome! Some suggested next steps include:
*   Improving context trimming to send only the most relevant schema information to the LLM.
*   Building a library of few-shot examples to improve query generation accuracy.
*   Adding more intelligent, error-aware retry mechanisms.
