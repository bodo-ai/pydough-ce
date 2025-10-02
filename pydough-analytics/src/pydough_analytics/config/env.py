from __future__ import annotations
from pathlib import Path

def load_env() -> bool:
    """
    Carga variables desde un archivo .env si existe.
    - Prioriza el .env del directorio actual (útil para notebooks en llm/).
    - Si no, busca .env en padres comunes (repo root, src/, paquete, config/).
    No lanza error si python-dotenv no está instalado.
    """
    try:
        from dotenv import load_dotenv, find_dotenv  # pip install python-dotenv
    except Exception:
        return False

    found = find_dotenv(usecwd=True)
    if not found:
        here = Path(__file__).resolve()
        for p in (
            here.parents[3] / ".env",  # <repo>/.env
            here.parents[2] / ".env",  # <repo>/src/.env
            here.parents[1] / ".env",  # <repo>/src/pydough_analytics/.env
            here.parent / ".env",      # <repo>/src/pydough_analytics/config/.env
        ):
            if p.exists():
                found = str(p)
                break

    if found:
        load_dotenv(found, override=False)
        return True
    return False

# Autocarga al importar (puedes comentarlo si prefieres llamarlo manualmente)
load_env()