"""Suite de evaluación del agente de triage y del RAG.

Corre el dataset dorado (golden_dataset.jsonl) contra el modelo configurado
y genera un reporte JSON en app/evals/reports/latest.json con:
- precisión de categoría y prioridad
- tasa de validación JSON (salidas que pasan Pydantic)
- recall@3 del RAG (cuando la muestra declara artículos relevantes)
- latencias p50/p95/media en la máquina local

Ejecutar: python scripts/run_evals.py  (requiere Ollama corriendo)
"""
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from app.agents import triage
from app.config import settings
from app.database import SessionLocal
from app.services import rag

DIR_EVALS = Path(__file__).parent
RUTA_DATASET = DIR_EVALS / "golden_dataset.jsonl"
RUTA_REPORTE = DIR_EVALS / "reports" / "latest.json"


def _cargar_muestras() -> list[dict]:
    lineas = RUTA_DATASET.read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in lineas if linea.strip()]


def _percentil(valores: list[int], q: float) -> int:
    ordenados = sorted(valores)
    return ordenados[min(int(q * (len(ordenados) - 1)), len(ordenados) - 1)]


def run_evals() -> dict:
    muestras = _cargar_muestras()
    resultados: list[dict] = []
    latencias: list[int] = []
    ok_json = 0
    aciertos_categoria = 0
    aciertos_prioridad = 0
    rag_evaluadas = 0
    rag_aciertos = 0

    for muestra in muestras:
        r = triage.clasificar(muestra["titulo"], muestra["descripcion"])
        latencias.append(r["latencia_ms"])

        if r["ok"]:
            ok_json += 1
            s = r["salida"]
            if s.categoria == muestra["esperado"]["categoria"]:
                aciertos_categoria += 1
            if s.prioridad == muestra["esperado"]["prioridad"]:
                aciertos_prioridad += 1

        # recall@3 del RAG: ¿algún chunk de los artículos esperados está en el
        # top 3? Se evalúa COMO EN PRODUCCIÓN: búsqueda filtrada por la
        # categoría esperada del ticket, con fallback a búsqueda global.
        rag_detalle = None
        if muestra.get("articulos_relevantes"):
            db = SessionLocal()
            try:
                consulta = f"{muestra['titulo']}\n{muestra['descripcion']}"
                fragmentos = rag.buscar_chunks(
                    db, consulta, 3, categoria=muestra["esperado"]["categoria"]
                )
                if not fragmentos:
                    fragmentos = rag.buscar_chunks(db, consulta, 3)
                ids_obtenidos = sorted({chunk.article_id for chunk, _ in fragmentos})
                rag_evaluadas += 1
                acierto = bool(set(ids_obtenidos) & set(muestra["articulos_relevantes"]))
                rag_aciertos += int(acierto)
                rag_detalle = {
                    "articulos_obtenidos": ids_obtenidos,
                    "articulos_esperados": muestra["articulos_relevantes"],
                    "acierto": acierto,
                }
            finally:
                db.close()

        resultados.append(
            {
                "titulo": muestra["titulo"],
                "esperado": muestra["esperado"],
                "obtenido": r["salida"].model_dump() if r["ok"] else None,
                "triage_ok": r["ok"],
                "latencia_ms": r["latencia_ms"],
                "rag": rag_detalle,
            }
        )

    n = len(muestras)
    reporte = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "modelo_triage": settings.triage_model,
        "n_muestras": n,
        "precision_categoria": round(aciertos_categoria / n, 3),
        "precision_prioridad": round(aciertos_prioridad / n, 3),
        "tasa_validacion_json": round(ok_json / n, 3),
        "recall_rag_top3": (
            round(rag_aciertos / rag_evaluadas, 3) if rag_evaluadas else None
        ),
        "latencia_ms": {
            "p50": _percentil(latencias, 0.50),
            "p95": _percentil(latencias, 0.95),
            "media": round(statistics.mean(latencias)),
        },
        "resultados": resultados,
    }
    RUTA_REPORTE.parent.mkdir(parents=True, exist_ok=True)
    RUTA_REPORTE.write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return reporte


def leer_reporte() -> dict:
    if not RUTA_REPORTE.exists():
        return {"disponible": False, "reporte": None}
    reporte = json.loads(RUTA_REPORTE.read_text(encoding="utf-8"))
    return {"disponible": True, "reporte": reporte}
