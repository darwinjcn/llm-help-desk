"""Evals: suite de evaluación del agente y su reporte (roles agente/admin)."""
import json

from fastapi import APIRouter, BackgroundTasks, Depends
from app.evals import runner
from app.models import Usuario
from app.schemas import EvalReportOut, EvalRunOut
from app.deps import requiere_rol

router = APIRouter(prefix="/evals", tags=["evals"])


@router.post("/run", response_model=EvalRunOut)
def correr_evals(
    background: BackgroundTasks,
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    """Lanza la suite de evaluación en segundo plano (tarda varios minutos:
    son 12 tickets x triage + consultas RAG contra Ollama local)."""
    background.add_task(runner.run_evals)
    return EvalRunOut(
        mensaje="Evaluación iniciada; puede tardar varios minutos en CPU. "
        "Consulta el resultado con GET /evals/report."
    )


@router.get("/report", response_model=EvalReportOut)
def reporte_evals(
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    return runner.leer_reporte()
