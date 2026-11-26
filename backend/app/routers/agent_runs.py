"""Agent runs: historial auditable de decisiones del agente IA (roles agente/admin)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import requiere_rol
from app.models import AgentRun, Usuario
from app.schemas import AgentRunListOut, AgentRunOut

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/runs", response_model=AgentRunListOut)
def listar_runs(
    limit: int = 50,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    consulta = db.query(AgentRun)
    if tipo:
        consulta = consulta.filter(AgentRun.tipo_agente == tipo)
    items = consulta.order_by(AgentRun.id.desc()).limit(min(limit, 200)).all()
    return {"items": [AgentRunOut.model_validate(r) for r in items]}
