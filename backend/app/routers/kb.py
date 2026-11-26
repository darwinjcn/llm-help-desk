"""Base de conocimiento: artículos e ingesta de embeddings (roles agente/admin)."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import requiere_rol
from app.models import KnowledgeArticle, Usuario
from app.schemas import ArticleIn, ArticleOut, KbListOut, ReingestaOut
from app.services import rag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kb", tags=["kb"])


@router.get("/articles", response_model=KbListOut)
def listar_articulos(
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    items = db.query(KnowledgeArticle).order_by(KnowledgeArticle.updated_at.desc()).all()
    return {"items": [ArticleOut.model_validate(a) for a in items]}


@router.post("/articles", response_model=ArticleOut, status_code=201)
def crear_articulo(
    datos: ArticleIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    articulo = KnowledgeArticle(
        titulo=datos.titulo,
        contenido=datos.contenido,
        categoria=datos.categoria,
        etiquetas=datos.etiquetas,
        created_by=user.id,
    )
    db.add(articulo)
    db.commit()
    db.refresh(articulo)

    # Ingesta de embeddings. Si Ollama no responde, el artículo queda guardado
    # y la ingesta se puede reintentar con POST /kb/articles/{id}/reingesta.
    try:
        rag.ingesta_articulo(db, articulo)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ingesta diferida del artículo %s: %s", articulo.id, exc)

    return articulo


@router.post("/articles/{article_id}/reingesta", response_model=ReingestaOut)
def reingestar_articulo(
    article_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(requiere_rol("agente", "admin")),
):
    articulo = db.get(KnowledgeArticle, article_id)
    if articulo is None:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    articulo.version += 1
    db.commit()
    try:
        n_chunks = rag.ingesta_articulo(db, articulo)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"La ingesta falló (¿Ollama está corriendo con el modelo de embeddings?): {exc}",
        ) from exc
    return {"article_id": articulo.id, "chunks": n_chunks}
