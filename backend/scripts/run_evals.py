"""Wrapper para correr la suite de evals desde la línea de comandos.

Uso (desde /backend o dentro del contenedor):
    python scripts/run_evals.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evals.runner import run_evals  # noqa: E402

if __name__ == "__main__":
    reporte = run_evals()
    resumen = {k: v for k, v in reporte.items() if k != "resultados"}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"\nReporte completo guardado en app/evals/reports/latest.json")
