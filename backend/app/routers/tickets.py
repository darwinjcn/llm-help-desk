"""Tickets: CRUD, máquina de estados, comentarios y decisión de la sugerencia IA."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import orchestrator, resolution
from app.database import get_db
from app.deps import requiere_rol, usuario_actual
from app.models import AgentRun, Ticket, TicketEvent, Usuario
from app.schemas import (
    ComentarioIn,
    DetalleTicketOut,
    EventoOut,
    SugerenciaDecisionIn,
    SugerenciaOut,
    SuggestionOutput,
    TicketIn,
    TicketListOut,
    TicketOut,
    TicketPatchEstadoIn,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Máquina de estados del ciclo de vida del ticket
TRANSICIONES: dict[str, set[str]] = {
    "nuevo": {"en_triage", "abierto", "resuelto", "cerrado"},
    "en_triage": {"abierto", "nuevo"},
    "abierto": {"en_resolucion", "resuelto", "cerrado"},
    "en_resolucion": {"resuelto", "abierto", "cerrado"},
    "resuelto": {"cerrado", "abierto"},
    "cerrado": {"abierto"},
}


def _obtener_ticket_con_permiso(
    ticket_id: int, db: Session, user: Usuario
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if user.rol == "cliente" and ticket.usuario_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes ver este ticket")
    return ticket


@router.get("", response_model=TicketListOut)
def listar_tickets(
    estado: Optional[str] = None,
    categoria: Optional[str] = None,
    prioridad: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: Usuario = Depends(usuario_actual),
):
    consulta = db.query(Ticket)
    if user.rol == "cliente":
        consulta = consulta.filter(Ticket.usuario_id == user.id)
    if estado:
        consulta = consulta.filter(Ticket.estado == estado)
    if categoria:
        consulta = consulta.filter(Ticket.categoria == categoria)
    if prioridad:
        consulta = consulta.filter(Ticket.prioridad == prioridad)

    total = consulta.count()
    items = (
        consulta.order_by(Ticket.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(limit, 100))
        .all()
    )
    return {"items": [TicketOut.model_validate(t) for t in items], "total": total}


@router.post("", response_model=TicketOut, status_code=201)
def crear_ticket(
    datos: TicketIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: Usuario = Depends(usuario_actual),
):
    ticket = Ticket(
        titulo=datos.titulo,
        descripcion=datos.descripcion,
        servicio_afectado=datos.servicio_afectado,
        usuario_id=user.id,
        estado="nuevo",
        etiquetas=[],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            autor_id=user.id,
            tipo="creado",
            contenido="Ticket creado por el usuario.",
        )
    )
    db.commit()
    # El pipeline de agente corre en segundo plano (triage ~2s + resolución ~5s en CPU)
    background.add_task(orchestrator.procesar_ticket_nuevo, ticket.id)
    return ticket


@router.get("/{ticket_id}", response_model=DetalleTicketOut)
def detalle_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(usuario_actual),
):
    ticket = _obtener_ticket_con_permiso(ticket_id, db, user)

    eventos = (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket_id)
        .order_by(TicketEvent.created_at)
        .all()
    )
    ids_autores = {e.autor_id for e in eventos if e.autor_id is not None}
    autores = {}
    if ids_autores:
        autores = {
            u.id: u.nombre
            for u in db.query(Usuario).filter(Usuario.id.in_(ids_autores)).all()
        }
    eventos_out = [
        EventoOut(
            id=e.id,
            tipo=e.tipo,
            contenido=e.contenido,
            datos_agente=e.datos_agente,
            autor_nombre=autores.get(e.autor_id) if e.autor_id else None,
            created_at=e.created_at,
        )
        for e in eventos
    ]

    # Última sugerencia válida del agente de resolución (si existe)
    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.ticket_id == ticket_id,
            AgentRun.tipo_agente == "resolucion",
            AgentRun.salida_validada.isnot(None),
        )
        .order_by(AgentRun.id.desc())
        .first()
    )
    sugerencia = None
    if run is not None:
        sugerencia = SugerenciaOut(
            id=run.id,
            salida=SuggestionOutput.model_validate(run.salida_validada),
            aceptado=run.aceptado,
            editado_por_humano=run.editado_por_humano,
        )

    return DetalleTicketOut(
        ticket=TicketOut.model_validate(ticket),
        eventos=eventos_out,
        sugerencia=sugerencia,
    )


@router.patch("/{ticket_id}/estado", response_model=TicketOut)
def cambiar_estado(
    ticket_id: int,
    datos: TicketPatchEstadoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if datos.estado not in TRANSICIONES.get(ticket.estado, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Transición no permitida: de '{ticket.estado}' a '{datos.estado}'",
        )
    estado_anterior = ticket.estado
    ticket.estado = datos.estado
    if ticket.agente_asignado_id is None:
        ticket.agente_asignado_id = user.id
    if datos.estado == "cerrado":
        ticket.closed_at = datetime.now(timezone.utc)
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            autor_id=user.id,
            tipo="cambio_estado",
            contenido=f"Estado cambiado de '{estado_anterior}' a '{datos.estado}'.",
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/comentarios", response_model=EventoOut, status_code=201)
def agregar_comentario(
    ticket_id: int,
    datos: ComentarioIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(usuario_actual),
):
    ticket = _obtener_ticket_con_permiso(ticket_id, db, user)
    evento = TicketEvent(
        ticket_id=ticket.id,
        autor_id=user.id,
        tipo="comentario",
        contenido=datos.contenido,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return EventoOut(
        id=evento.id,
        tipo=evento.tipo,
        contenido=evento.contenido,
        datos_agente=None,
        autor_nombre=user.nombre,
        created_at=evento.created_at,
    )


@router.post("/{ticket_id}/sugerencia/regenerar", response_model=SugerenciaOut, status_code=200)
def regenerar_sugerencia(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    """Re-ejecuta el agente de resolución incluyendo los comentarios del ticket.

    Uso típico: el cliente agregó información nueva, o el agente rechazó la
    sugerencia anterior y quiere una segunda opinión con más contexto.
    Cada reconsulta queda auditada como un AgentRun nuevo.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.estado == "cerrado":
        raise HTTPException(
            status_code=400, detail="No se puede reconsultar la IA en un ticket cerrado"
        )

    comentarios = [
        ev.contenido
        for ev in db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket_id, TicketEvent.tipo == "comentario")
        .order_by(TicketEvent.created_at)
        .all()
    ]

    # Síncrono a propósito: el agente humano está esperando esta respuesta
    # (latencia típica en CPU: ~5-20 s con qwen2.5:3b-instruct).
    r_res = resolution.redactar(db, ticket, textos_extra=comentarios)
    run = AgentRun(
        ticket_id=ticket.id,
        tipo_agente="resolucion",
        prompt_version="v1",
        modelo=r_res["modelo"],
        entrada={
            "fuentes_recuperadas": r_res["fuentes_recuperadas"],
            "con_comentarios": bool(comentarios),
            "num_comentarios": len(comentarios),
        },
        salida_bruta=(str(r_res["salida_bruta"]) if r_res["salida_bruta"] else None),
        salida_validada=(
            r_res["sugerencia"].model_dump()
            if r_res["ok"] and r_res["sugerencia"]
            else None
        ),
        latencia_ms=r_res["latencia_ms"],
        tokens_entrada=r_res["meta"].get("tokens_entrada"),
        tokens_salida=r_res["meta"].get("tokens_salida"),
    )
    db.add(run)

    if r_res["ok"] and r_res["sugerencia"]:
        db.add(
            TicketEvent(
                ticket_id=ticket.id,
                autor_id=None,
                tipo="sugerencia_agente",
                contenido=r_res["sugerencia"].respuesta_borrador,
                datos_agente=r_res["sugerencia"].model_dump(),
            )
        )
        db.commit()
        db.refresh(run)
        return SugerenciaOut(
            id=run.id,
            salida=SuggestionOutput.model_validate(run.salida_validada),
            aceptado=False,
            editado_por_humano=False,
        )

    motivo = r_res["motivo"]
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            autor_id=None,
            tipo="resolucion_fallida",
            contenido=(
                "La reconsulta del agente de resolución no generó una "
                f"sugerencia válida (motivo: {motivo})."
            ),
        )
    )
    db.commit()
    raise HTTPException(
        status_code=502,
        detail=(
            "El agente no generó una sugerencia válida "
            f"(motivo: {motivo}). El intento quedó registrado en la auditoría."
        ),
    )


@router.post("/{ticket_id}/sugerencia/decision", status_code=200)
def decidir_sugerencia(
    ticket_id: int,
    datos: SugerenciaDecisionIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    """Human-in-the-loop: un humano acepta/edita/rechaza la sugerencia del agente."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.ticket_id == ticket_id,
            AgentRun.tipo_agente == "resolucion",
            AgentRun.salida_validada.isnot(None),
        )
        .order_by(AgentRun.id.desc())
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="El ticket no tiene sugerencia del agente")

    run.aceptado = datos.aceptada
    run.editado_por_humano = bool(datos.respuesta_editada)

    if datos.aceptada:
        texto_final = datos.respuesta_editada or run.salida_validada["respuesta_borrador"]
        ticket.estado = "en_resolucion"
        if ticket.agente_asignado_id is None:
            ticket.agente_asignado_id = user.id
        db.add(
            TicketEvent(
                ticket_id=ticket_id,
                autor_id=user.id,
                tipo="respuesta_agente",
                contenido=texto_final,
            )
        )
    else:
        db.add(
            TicketEvent(
                ticket_id=ticket_id,
                autor_id=user.id,
                tipo="sugerencia_rechazada",
                contenido="La sugerencia del agente fue rechazada por un agente humano.",
            )
        )
    db.commit()
    return {
        "ticket_id": ticket_id,
        "aceptada": datos.aceptada,
        "estado": ticket.estado,
        "editada": run.editado_por_humano,
    }
