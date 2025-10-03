from __future__ import annotations
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

# Carga .env si lo tienes (no rompe si no existe)
from ..config import env as _env  # noqa: F401
from ..llm.llm_client import LLMClient

console = Console()


def _df_like(obj) -> bool:
    return all(hasattr(obj, attr) for attr in ("empty", "columns", "iterrows"))


def _print_dataframe(df, limit: int = 20) -> None:
    if df is None:
        console.print("[yellow]No DataFrame returned.[/yellow]")
        return
    if not _df_like(df):
        console.print(df)
        return
    if df.empty:
        console.print("[yellow]No rows returned.[/yellow]")
        return

    table = Table(show_lines=False)
    for col in df.columns:
        table.add_column(str(col))

    try:
        it = df.head(limit).iterrows()
    except Exception:
        it = df.iterrows()

    # Evitar crash si no está pandas: usar comprobación simple de None
    try:
        import pandas as pd  # noqa: F401
        def _is_na(x):  # type: ignore
            import pandas as pd
            return pd.isna(x)
    except Exception:
        def _is_na(x):  # type: ignore
            return x is None

    for _, row in it:
        vals = [("" if _is_na(v) else str(v)) for v in row]
        table.add_row(*vals)

    console.print(table)


def _print_json(result, question: str) -> None:
    rows = None
    if result.df is not None and _df_like(result.df):
        try:
            rows = result.df.to_dict(orient="records")
        except Exception:
            rows = None
    data = {
        "question": question,
        "code": result.code,
        "sql": result.sql,
        "explanation": result.full_explanation,
        "exception": result.exception,
        "rows": rows,
    }
    console.print_json(data=data)


def ask_from_cli(
    *,
    question: str,
    engine: str,
    database: str,
    db_name: str,
    md_path: str,
    kg_path: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    show_sql: bool = False,        
    show_df: bool = False,           
    show_explanation: bool = False,  
    as_json: bool = False,
    rows: int = 20,
) -> None:
    db_config = {"engine": engine, "database": database}

    PKG = Path(__file__).resolve().parents[3]
    prompt_path = PKG / "data" / "prompts" / "prompt.md"
    cheatsheet_path = PKG / "data" / "prompts" / "cheatsheet.md"

    client = LLMClient(
        prompt=str(prompt_path),
        script=str(cheatsheet_path),
        provider=provider or "google",
        model=model or "gemini-2.5-pro",
    )

    res = client.ask(
        question=question,
        kg_path=kg_path,
        db_config=db_config,
        md_path=md_path,
        db_name=db_name,
    )

    if as_json:
        _print_json(res, question)
        return

    console.rule("PyDough code")
    console.print(f"```python\n{res.code or ''}\n```")
    
    if res.exception:
        console.rule("[red]Error[/red]")
        console.print(res.exception)
        return

    if show_sql:
        console.rule("SQL")
        console.print(res.sql or "<no sql>")

    if show_df:
        console.rule("Result preview")
        _print_dataframe(res.df, limit=rows)

    if show_explanation:
        console.rule("Explanation")
        console.print(res.full_explanation or "<no explanation>")