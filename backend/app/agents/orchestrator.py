"""Orquestador del pipeline de agente para un ticket nuevo.

Secuencia: triage -> (aplicar resultados deterministas) -> resolución RAG ->
registrar AgentRun + TicketEvent de cada paso. Todo queda auditado.

Se ejecuta como tarea en segundo plano con SU PROPIA sesión de BD (el
BackgroundTasks de FastAPI corre fuera del ciclo request/response).
"""
import logging

from app.agents import resolution, triage
from app.database import SessionLocal
from app.models import AgentRun, Ticket, TicketEvent

logger = logging.getLogger(__name__)


def procesar_ticket_nuevo(ticket_id: int) -> None:
    db = SessionLocal()
    try:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None:
            logger.error("Pipeline de agente: ticket %s no existe", ticket_id)
            return

        # --- Fase 1: triage -------------------------------------------------
        ticket.estado = "en_triage"
        db.commit()

        r_triage = triage.clasificar(ticket.titulo, ticket.descripcion)
        db.add(
            AgentRun(
                ticket_id=ticket.id,
                tipo_agente="triage",
                prompt_version=r_triage["prompt_version"],
                modelo=r_triage["modelo"],
                entrada={"titulo": ticket.titulo, "descripcion": ticket.descripcion},
                salida_bruta=(
                    str(r_triage["salida_bruta"]) if r_triage["salida_bruta"] else None
                ),
                salida_validada=(
                    r_triage["salida"].model_dump() if r_triage["ok"] else None
                ),
                latencia_ms=r_triage["latencia_ms"],
                tokens_entrada=r_triage["meta"].get("tokens_entrada"),
                tokens_salida=r_triage["meta"].get("tokens_salida"),
            )
        )

        if not r_triage["ok"]:
            # Fallback graceful: cola de triage manual.
            db.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    autor_id=None,
                    tipo="triage_fallido",
                    contenido=(
                        "El agente de triage no produjo una salida válida; el "
                        "ticket quedó en cola de triage manual."
                    ),
                )
            )
            ticket.estado = "nuevo"
            db.commit()
            logger.warning("Triage fallido para ticket %s: %s", ticket_id, r_triage["error"])
            return

        salida_triage = r_triage["salida"]
        ticket.categoria = salida_triage.categoria
        ticket.prioridad = salida_triage.prioridad
        if not ticket.servicio_afectado:
            ticket.servicio_afectado = salida_triage.servicio_afectado[:120]
        ticket.etiquetas = salida_triage.etiquetas[:4]
        ticket.estado = "abierto"
        db.add(
            TicketEvent(
                ticket_id=ticket.id,
                autor_id=None,
                tipo="triage_agente",
                contenido=salida_triage.justificacion,
                datos_agente=salida_triage.model_dump(),
            )
        )
        db.commit()

        # --- Fase 2: resolución (RAG + borrador con citas) -------------------
        r_res = resolution.redactar(db, ticket)
        db.add(
            AgentRun(
                ticket_id=ticket.id,
                tipo_agente="resolucion",
                prompt_version="v1",
                modelo=r_res["modelo"],
                entrada={"fuentes_recuperadas": r_res["fuentes_recuperadas"]},
                salida_bruta=str(r_res["salida_bruta"]) if r_res["salida_bruta"] else None,
                salida_validada=(
                    r_res["sugerencia"].model_dump() if r_res["ok"] else None
                ),
                latencia_ms=r_res["latencia_ms"],
                tokens_entrada=r_res["meta"].get("tokens_entrada"),
                tokens_salida=r_res["meta"].get("tokens_salida"),
            )
        )

        if r_res["ok"] and r_res["sugerencia"] is not None:
            db.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    autor_id=None,
                    tipo="sugerencia_agente",
                    contenido=r_res["sugerencia"].respuesta_borrador,
                    datos_agente=r_res["sugerencia"].model_dump(),
                )
            )
        else:
            db.add(
                TicketEvent(
                    ticket_id=ticket.id,
                    autor_id=None,
                    tipo="resolucion_fallida",
                    contenido=(
                        "El agente de resolución no generó una sugerencia "
                        f"válida (motivo: {r_res['motivo']}). El ticket requiere "
                        "atención humana."
                    ),
                )
            )
        db.commit()
        logger.info("Pipeline completado para ticket %s", ticket_id)

    except Exception:
        db.rollback()
        logger.exception("Error del pipeline de agente para ticket %s", ticket_id)
        try:
            db.add(
                TicketEvent(
                    ticket_id=ticket_id,
                    autor_id=None,
                    tipo="error_agente",
                    contenido="Error interno del pipeline de agente; requiere atención humana.",
                )
            )
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
    finally:
        db.close()
