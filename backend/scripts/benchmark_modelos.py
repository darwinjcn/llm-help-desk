"""Benchmark de modelos: compara candidatos de Qwen para el agente de triage.

Corre el dataset dorado con cada modelo y muestra una tabla con precisión,
tasa de validación JSON y latencia (p50/p95) EN TU MÁQUINA — la elección del
modelo queda respaldada por datos, no por fichas técnicas.

Uso (desde /backend, con Ollama corriendo y los modelos ya descargados):
    python scripts/benchmark_modelos.py
    python scripts/benchmark_modelos.py --modelos "qwen2.5:3b-instruct,qwen3:4b"
"""
import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.triage import PROMPT_SISTEMA, SCHEMA  # noqa: E402
from app.evals.runner import _cargar_muestras  # noqa: E402
from app.schemas import TriageOutput  # noqa: E402
from app.services import ollama_client  # noqa: E402


def evaluar_modelo(modelo: str, muestras: list[dict]) -> dict:
    ok_json = 0
    aciertos_cat = 0
    aciertos_pri = 0
    latencias: list[int] = []

    for muestra in muestras:
        mensajes = [
            {"role": "system", "content": PROMPT_SISTEMA},
            {
                "role": "user",
                "content": (
                    f"TICKET NUEVO\nTitulo: {muestra['titulo']}\n"
                    f"Descripcion: {muestra['descripcion']}"
                ),
            },
        ]
        inicio = time.perf_counter()
        try:
            bruta, _ = ollama_client.chat_json(modelo, mensajes, SCHEMA, temperature=0.1)
            salida = TriageOutput.model_validate(bruta)
            ok_json += 1
            if salida.categoria == muestra["esperado"]["categoria"]:
                aciertos_cat += 1
            if salida.prioridad == muestra["esperado"]["prioridad"]:
                aciertos_pri += 1
        except Exception:  # noqa: BLE001 — el fallo también se mide
            pass
        latencias.append(int((time.perf_counter() - inicio) * 1000))

    n = len(muestras)
    ordenadas = sorted(latencias)
    return {
        "modelo": modelo,
        "precision_categoria": round(aciertos_cat / n, 3),
        "precision_prioridad": round(aciertos_pri / n, 3),
        "tasa_validacion_json": round(ok_json / n, 3),
        "lat_p50": ordenadas[min(int(0.50 * (n - 1)), n - 1)],
        "lat_p95": ordenadas[min(int(0.95 * (n - 1)), n - 1)],
        "lat_media": round(statistics.mean(latencias)),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark de modelos de triage")
    parser.add_argument(
        "--modelos",
        default="qwen2.5:3b-instruct,qwen3:4b",
        help="Modelos separados por coma (deben estar descargados en Ollama)",
    )
    args = parser.parse_args()

    muestras = _cargar_muestras()
    print(f"Dataset dorado: {len(muestras)} muestras\n")

    resultados = []
    for modelo in [m.strip() for m in args.modelos.split(",") if m.strip()]:
        print(f"Evaluando {modelo} ...", flush=True)
        resultados.append(evaluar_modelo(modelo, muestras))

    encabezado = (
        f"{'modelo':<26}{'cat':>7}{'pri':>7}{'json':>7}"
        f"{'p50(ms)':>10}{'p95(ms)':>10}{'media':>9}"
    )
    print("\n" + encabezado)
    print("-" * len(encabezado))
    for r in resultados:
        print(
            f"{r['modelo']:<26}"
            f"{r['precision_categoria']:>7.3f}"
            f"{r['precision_prioridad']:>7.3f}"
            f"{r['tasa_validacion_json']:>7.3f}"
            f"{r['lat_p50']:>10}"
            f"{r['lat_p95']:>10}"
            f"{r['lat_media']:>9}"
        )
    print(
        "\nConsejo: copia esta tabla al README del proyecto — la elección del "
        "modelo queda respaldada por datos reproducibles en tu máquina."
    )


if __name__ == "__main__":
    main()
