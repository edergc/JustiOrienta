"""Punto de arranque único de Justicia Orienta (backend + frontend, mismo proceso).

Uso:
    python run.py

Puerto configurable con la variable de entorno PORT (por defecto 8743 -- un
puerto poco común, elegido para no chocar con otras apps típicas en la misma
máquina: ni 3000/3001/5173/5174/5180 (Vite/React), ni 8000/8001/4100/8085
(otros backends). Cambia el valor si igual llegara a chocar en tu equipo.
"""
import os

import uvicorn

PORT = int(os.getenv("PORT", "8743"))
HOST = os.getenv("HOST", "127.0.0.1")
RECARGA_AUTOMATICA = os.getenv("RELOAD", "true").lower() == "true"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=RECARGA_AUTOMATICA)
