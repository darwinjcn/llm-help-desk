"""Modelos ORM: las 6 tablas del esquema v1 de llm-help-desk."""
from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[str] = mapped_column(String(20))  # cliente | agente | admin


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="nuevo", index=True)
    categoria: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    prioridad: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    servicio_afectado: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    etiquetas: Mapped[list] = mapped_column(JSON, default=list)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    agente_asignado_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    eventos = relationship(
        "TicketEvent", back_populates="ticket", order_by="TicketEvent.created_at"
    )


class TicketEvent(Base):
    """Auditoría completa del ticket. autor_id NULL = acción del agente IA."""

    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    autor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(40))
    contenido: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datos_agente: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="eventos")


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    contenido: Mapped[str] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(String(40))
    etiquetas: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class KbChunk(Base):
    """Fragmento de artículo con embedding para búsqueda semántica (pgvector)."""

    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("knowledge_articles.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(768))  # nomic-embed-text produce vectores de 768 dim


class AgentRun(Base):
    """Cada decisión del agente queda registrada, medible y auditable."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    tipo_agente: Mapped[str] = mapped_column(String(20))  # triage | resolucion
    prompt_version: Mapped[str] = mapped_column(String(10), default="v1")
    modelo: Mapped[str] = mapped_column(String(60))
    entrada: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    salida_bruta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salida_validada: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    latencia_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens_entrada: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_salida: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aceptado: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    editado_por_humano: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
