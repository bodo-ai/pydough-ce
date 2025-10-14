# Inserta /src en sys.path y expone 'server' desde el paquete
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from pydough_analytics.mcp.server import server