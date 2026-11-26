"""Punto de entrada de Vercel: expone el servidor Flask del tablero Dash (dashboard/app.py) como `app`.

Vercel detecta el preset de Flask (flask está en requirements.txt) y entrega aquí cada petición con su ruta real,
sin reescrituras. El tablero lee el modelo, cargar_y_predecir.py y la carpeta resultados/ desde esta raíz.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "dashboard"))

from app import server as app  # noqa: E402,F401
