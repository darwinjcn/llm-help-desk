"""Esquemas Pydantic: contratos de API y salidas obligatorias de los agentes."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ---------------------------------------------------------------------------
# Salidas del LLM (el modelo debe devolver EXACTAMENTE esto; se valida con
# Pydantic y si no cumple, la decisión se rechaza — cero alucinaciones por diseño)
# ---------------------------------------------------------------------------


class TriageOutput(BaseModel):
    categoria: Literal["hardware", "software", "red", "accesos", "otro"]
    prioridad: Literal["baja", "media", "alta", "critica"]
    servicio_afectado: str = Field(description="Nombre corto del servicio o sistema afectado")
    requiere_escalado: bool
    etiquetas: list[str] = Field(max_length=4, description="Máximo 4 etiquetas cortas")
    justificacion: str = Field(max_length=300, description="Explicación breve en español")


class SuggestionOutput(BaseModel):
    puede_resolver: bool
    respuesta_borrador: str = Field(max_length=1500)
    fuentes: list[str] = Field(description="Identificadores KB-XXX usados; deben existir")
    confianza: Literal["alta", "media", "baja"]


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

RolLiteral = Literal["cliente", "agente", "admin"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    nombre: str = Field(min_length=1, max_length=120)
    rol: Literal["cliente", "agente"] = "cliente"  # admin solo por seed


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

EstadoLiteral = Literal[
    "nuevo", "en_triage", "abierto", "en_resolucion", "resuelto", "cerrado"
]


class TicketIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str = Field(min_length=1, max_length=4000)
    servicio_afectado: Optional[str] = Field(default=None, max_length=120)


class TicketPatchEstadoIn(BaseModel):
    estado: EstadoLiteral


class ComentarioIn(BaseModel):
    contenido: str = Field(min_length=1, max_length=2000)


class SugerenciaDecisionIn(BaseModel):
    aceptada: bool
    respuesta_editada: Optional[str] = Field(default=None, max_length=2000)


class TicketOut(BaseModel):
    id: int
    titulo: str
    descripcion: str
    estado: str
    categoria: Optional[str] = None
    prioridad: Optional[str] = None
    servicio_afectado: Optional[str] = None
    etiquetas: list[str] = []
    usuario_id: int
    agente_asignado_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TicketListOut(BaseModel):
    items: list[TicketOut]
    total: int


class EventoOut(BaseModel):
    id: int
    tipo: str
    contenido: Optional[str] = None
    datos_agente: Optional[dict] = None
    autor_nombre: Optional[str] = None
    created_at: datetime


class SugerenciaOut(BaseModel):
    id: int
    salida: SuggestionOutput
    aceptado: Optional[bool] = None
    editado_por_humano: bool = False


class DetalleTicketOut(BaseModel):
    ticket: TicketOut
    eventos: list[EventoOut]
    sugerencia: Optional[SugerenciaOut] = None


# ---------------------------------------------------------------------------
# Base de conocimiento
# ---------------------------------------------------------------------------


class ArticleIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    contenido: str = Field(min_length=1, max_length=20000)
    categoria: str = Field(min_length=1, max_length=40)
    etiquetas: list[str] = []


class ArticleOut(BaseModel):
    id: int
    titulo: str
    contenido: str
    categoria: str
    etiquetas: list[str] = []
    activo: bool
    version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KbListOut(BaseModel):
    items: list[ArticleOut]


class ReingestaOut(BaseModel):
    article_id: int
    chunks: int


# ---------------------------------------------------------------------------
# Agent runs y evals
# ---------------------------------------------------------------------------


class AgentRunOut(BaseModel):
    id: int
    ticket_id: int
    tipo_agente: str
    modelo: str
    prompt_version: str
    latencia_ms: int
    aceptado: Optional[bool] = None
    editado_por_humano: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunListOut(BaseModel):
    items: list[AgentRunOut]


class EvalRunOut(BaseModel):
    mensaje: str


class EvalReportOut(BaseModel):
    disponible: bool
    reporte: Optional[dict] = None
