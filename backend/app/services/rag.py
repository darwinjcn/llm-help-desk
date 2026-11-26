"""RAG sobre la base de conocimiento: chunking, ingesta y búsqueda pgvector."""
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import KbChunk, KnowledgeArticle
from app.services.ollama_client import embed

CHUNK_CHARS = 1800
OVERLAP_CHARS = 200


def chunk_text(contenido: str) -> list[str]:
    """Divide el artículo en fragmentos de ~1800 caracteres con solapamiento.

    Corta en fin de oración o salto de línea para no romper frases.
    """
    contenido = contenido.strip()
    if len(contenido) <= CHUNK_CHARS:
        return [contenido]

    trozos: list[str] = []
    inicio = 0
    while inicio < len(contenido):
        fin = min(inicio + CHUNK_CHARS, len(contenido))
        if fin < len(contenido):
            corte = max(
                contenido.rfind("\n", inicio, fin),
                contenido.rfind(". ", inicio, fin),
            )
            if corte > inicio + CHUNK_CHARS // 2:
                fin = corte + 1
        trozos.append(contenido[inicio:fin].strip())
        if fin >= len(contenido):
            break
        inicio = fin - OVERLAP_CHARS
    return [t for t in trozos if t]


def ingesta_articulo(db: Session, articulo: KnowledgeArticle) -> int:
    """Re-genera los embeddings de un artículo. Devuelve el nº de chunks.

    Requiere Ollama corriendo con el modelo de embeddings descargado.
    """
    db.query(KbChunk).filter(KbChunk.article_id == articulo.id).delete()
    trozos = chunk_text(articulo.contenido)
    for indice, texto in enumerate(trozos):
        db.add(
            KbChunk(
                article_id=articulo.id,
                chunk_index=indice,
                chunk_text=texto,
                embedding=embed(texto),
            )
        )
    db.commit()
    return len(trozos)


def buscar_chunks(
    db: Session,
    consulta: str,
    k: int | None = None,
    categoria: str | None = None,
) -> list[tuple[KbChunk, float]]:
    """Búsqueda semántica top-k (distancia coseno) solo sobre artículos activos.

    Si se indica `categoria`, restringe la búsqueda a artículos de esa
    categoría (mejora la relevancia: el triage ya clasificó el ticket).
    Devuelve pares (chunk, distancia) ordenados de más a menos relevante.
    """
    k = k or settings.kb_top_k
    qvec = embed(consulta)
    distancia = KbChunk.embedding.cosine_distance(qvec).label("dist")
    stmt = (
        select(KbChunk, distancia)
        .join(KnowledgeArticle, KbChunk.article_id == KnowledgeArticle.id)
        .filter(KnowledgeArticle.activo.is_(True))
    )
    if categoria:
        stmt = stmt.filter(KnowledgeArticle.categoria == categoria)
    stmt = stmt.order_by(asc(distancia)).limit(k)
    return [(fila[0], float(fila[1])) for fila in db.execute(stmt).all()]
