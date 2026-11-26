"""Agente de resolución de nivel 1: borrador de respuesta con RAG y citas.

Anti-alucinación en código (no en el prompt):
- Recupera fragmentos de la KB con pgvector (servicio determinista).
- El LLM redacta citando [KB-XXX]; si lista fuentes que NO estaban en el
  contexto recuperado, la sugerencia se RECHAZA (fuentes_invalidas).
- Sin artículos relevantes: no se llama al LLM; se escala honestamente.
"""
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Ticket
from app.schemas import SuggestionOutput
from app.services import ollama_client, rag, textguard

PROMPT_SISTEMA = (
    Path(__file__).parent / "prompts" / "resolucion_v1.md"
).read_text(encoding="utf-8")
SCHEMA = SuggestionOutput.model_json_schema()


def _etiqueta(article_id: int) -> str:
    return f"KB-{article_id}"


def redactar(db: Session, ticket: Ticket, textos_extra: list[str] | None = None) -> dict:
    """Redacta una sugerencia para el ticket.

    `textos_extra` son comentarios posteriores del ticket (reconsulta):
    enriquecen la búsqueda RAG y el contexto del LLM. Se limita a los
    últimos 6 para acotar el tamaño del prompt.
    """
    inicio = time.perf_counter()
    extras = (textos_extra or [])[-6:]
    consulta = f"{ticket.titulo}\n{ticket.descripcion}"
    if extras:
        consulta += "\n" + "\n".join(f"- {t}" for t in extras)
    # Búsqueda preferente por categoría del ticket (el triage ya clasificó);
    # si la categoría acota demasiado y no hay resultados, se busca sin filtro.
    fragmentos: list[tuple] = []
    if ticket.categoria:
        fragmentos = rag.buscar_chunks(
            db, consulta, settings.kb_top_k, categoria=ticket.categoria
        )
    if not fragmentos:
        fragmentos = rag.buscar_chunks(db, consulta, settings.kb_top_k)
    fuentes_recuperadas = sorted({_etiqueta(chunk.article_id) for chunk, _ in fragmentos})

    if not fragmentos:
        # Determinista: sin conocimiento indexado, no se improvisa.
        sugerencia = SuggestionOutput(
            puede_resolver=False,
            respuesta_borrador=(
                "No encontré artículos en la base de conocimiento para este "
                "problema, así que escalo el ticket a un agente humano. "
                "Conviene adjuntar capturas del error e indicar desde cuándo "
                "ocurre."
            ),
            fuentes=[],
            confianza="baja",
        )
        return {
            "ok": True,
            "sugerencia": sugerencia,
            "motivo": "sin_articulos",
            "latencia_ms": int((time.perf_counter() - inicio) * 1000),
            "salida_bruta": None,
            "modelo": settings.resolution_model,
            "meta": {},
            "fuentes_recuperadas": [],
        }

    contexto = "\n\n".join(
        f"[{_etiqueta(chunk.article_id)}] {chunk.chunk_text[:900]}"
        for chunk, _ in fragmentos
    )
    contenido_usuario = (
        f"FRAGMENTOS DE LA BASE DE CONOCIMIENTO:\n{contexto}\n\n"
        f"TICKET DEL USUARIO\nTitulo: {ticket.titulo}\n"
        f"Descripcion: {ticket.descripcion}"
    )
    if extras:
        contenido_usuario += (
            "\n\nCOMENTARIOS POSTERIORES DEL TICKET (tenlos en cuenta):\n"
            + "\n".join(f"- {t}" for t in extras)
        )
    mensajes = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": contenido_usuario},
    ]

    salida: SuggestionOutput | None = None
    bruta: dict | None = None
    error: str | None = None
    meta: dict = {}

    for _ in range(2):  # 1 reintento ante JSON inválido o salida repetitiva
        try:
            bruta, meta = ollama_client.chat_json(
                settings.resolution_model,
                mensajes,
                SCHEMA,
                temperature=0.3,
                num_predict=600,
            )
            salida = SuggestionOutput.model_validate(bruta)
            if textguard.salida_repetitiva(salida.respuesta_borrador):
                raise ValueError(
                    "salida_repetitiva: la respuesta repite la misma frase en bucle"
                )
            error = None
            break
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            bruta = None
            salida = None

    latencia_ms = int((time.perf_counter() - inicio) * 1000)

    ok = salida is not None
    motivo = error
    if ok and not set(salida.fuentes).issubset(set(fuentes_recuperadas)):
        # Validación anti-alucinación: fuentes inventadas => se rechaza.
        ok = False
        motivo = "fuentes_invalidas"
        salida = None
    elif not ok and error and "salida_repetitiva" in error:
        motivo = "salida_repetitiva"

    return {
        "ok": ok,
        "sugerencia": salida,
        "motivo": motivo,
        "latencia_ms": latencia_ms,
        "salida_bruta": bruta,
        "modelo": settings.resolution_model,
        "meta": meta,
        "fuentes_recuperadas": fuentes_recuperadas,
    }
