"""LLM Help Desk — API FastAPI con agente IA local (Qwen vía Ollama)."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401 — importa los modelos para create_all
    AgentRun,
    KbChunk,
    KnowledgeArticle,
    Ticket,
    TicketEvent,
    Usuario,
)
from app.routers import agent_runs, auth, evals, kb, tickets
from app.security import hashear_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Help Desk API",
    version="0.1.0",
    description="Help desk con triage y resolución por agente IA 100% local",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción: restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, tickets.router, kb.router, agent_runs.router, evals.router):
    app.include_router(router, prefix="/api")


@app.get("/api/health")
def salud():
    return {
        "estado": "ok",
        "modelo_triage": settings.triage_model,
        "modelo_resolucion": settings.resolution_model,
        "embedding_model": settings.embedding_model,
    }


@app.on_event("startup")
def al_arrancar():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Usuario).filter(Usuario.email == settings.admin_email).first():
            db.add(
                Usuario(
                    email=settings.admin_email,
                    password_hash=hashear_password(settings.admin_password),
                    nombre="Administrador",
                    rol="admin",
                )
            )
            db.commit()
            logger.info("Usuario admin inicial creado: %s", settings.admin_email)
    finally:
        db.close()
