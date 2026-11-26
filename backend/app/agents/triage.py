"""Agente de triage: clasifica el ticket y devuelve salida JSON validada.

Arquitectura híbrida:
- El LLM (Qwen vía Ollama) clasifica con salida estructurada (JSON Schema).
- Pydantic valida la salida; si falla tras 1 reintento, el triage falla y el
  ticket queda en cola manual (fallback graceful).
- Las reglas deterministas (rules.py) pueden SOBREESCRIBIR al modelo.
"""
import time
from pathlib import Path

from app.config import settings
from app.schemas import TriageOutput
from app.services import ollama_client, textguard
from app.services.rules import prioridad_forzada

PROMPT_SISTEMA = (
    Path(__file__).parent / "prompts" / "triage_v1.md"
).read_text(encoding="utf-8")
SCHEMA = TriageOutput.model_json_schema()


def clasificar(titulo: str, descripcion: str) -> dict:
    """Ejecuta el triage. Devuelve dict con ok/salida/salida_bruta/latencia_ms."""
    mensajes = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": f"TICKET NUEVO\nTitulo: {titulo}\nDescripcion: {descripcion}"},
    ]

    inicio = time.perf_counter()
    salida: TriageOutput | None = None
    bruta: dict | None = None
    error: str | None = None
    meta: dict = {}

    for _ in range(2):  # 1 reintento ante JSON inválido o salida repetitiva
        try:
            bruta, meta = ollama_client.chat_json(
                settings.triage_model,
                mensajes,
                SCHEMA,
                temperature=0.1,
                num_predict=250,
            )
            salida = TriageOutput.model_validate(bruta)
            if textguard.salida_repetitiva(salida.justificacion):
                raise ValueError(
                    "salida_repetitiva: la justificación repite la misma frase en bucle"
                )
            error = None
            break
        except Exception as exc:  # noqa: BLE001 — cualquier fallo invalida la salida
            error = str(exc)
            bruta = None
            salida = None

    latencia_ms = int((time.perf_counter() - inicio) * 1000)

    # Regla determinista de negocio: manda sobre el modelo
    if salida is not None and prioridad_forzada(f"{titulo} {descripcion}"):
        if salida.prioridad != "critica":
            salida.prioridad = "critica"
            salida.justificacion = (
                salida.justificacion
                + " [Prioridad crítica aplicada por regla determinista de negocio]"
            )[:300]

    return {
        "ok": salida is not None,
        "salida": salida,
        "salida_bruta": bruta,
        "latencia_ms": latencia_ms,
        "error": error,
        "meta": meta,
        "modelo": settings.triage_model,
        "prompt_version": "v1",
    }
