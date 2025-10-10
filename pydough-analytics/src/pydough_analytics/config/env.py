from __future__ import annotations
from pathlib import Path

def load_env() -> bool:
    try:
        from dotenv import load_dotenv, find_dotenv  # pip install python-dotenv
    except Exception:
        return False

    found = find_dotenv(usecwd=True)
    if not found:
        here = Path(__file__).resolve()
        for p in (
            here.parents[3] / ".env",  
            here.parents[2] / ".env",  
            here.parents[1] / ".env",  
            here.parent / ".env",      
        ):
            if p.exists():
                found = str(p)
                break

    if found:
        load_dotenv(found, override=False)
        return True
    return False

load_env()