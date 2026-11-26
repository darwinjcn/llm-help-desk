"""Cliente para Ollama: chat con salida JSON estructurada y embeddings.

Patrón clave del proyecto: el LLM SOLO devuelve JSON que se valida con un
esquema Pydantic; el código determinista decide y ejecuta.
"""
import json

import requests

from app.config import settings


class OllamaError(RuntimeError):
    """Error al contactar Ollama o al interpretar su salida."""


def chat_json(
    model: str,
    messages: list[dict],
    json_schema: dict,
    temperature: float = 0.1,
    num_ctx: int = 4096,
    num_predict: int | None = None,
    repeat_penalty: float = 1.15,
) -> tuple[dict, dict]:
    """Ejecuta un chat en Ollama forzando salida JSON según `json_schema`.

    Ollama soporta "format": <json-schema> (structured outputs). Devuelve
    (contenido_parseado, meta con tokens y latencia). Lanza OllamaError si el
    servicio no responde o el contenido no es JSON válido.

    `repeat_penalty` y `num_predict` mitigan el modo de fallo típico de los
    modelos 3B en CPU: repetir la misma frase en bucle.
    """
    opciones: dict = {
        "temperature": temperature,
        "num_ctx": num_ctx,
        "repeat_penalty": repeat_penalty,
    }
    if num_predict:
        opciones["num_predict"] = num_predict
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": json_schema,
        "options": opciones,
    }
    try:
        r = requests.post(
            f"{settings.ollama_base_url}/api/chat", json=payload, timeout=300
        )
        r.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(f"No se pudo contactar a Ollama: {exc}") from exc

    data = r.json()
    contenido = data.get("message", {}).get("content", "")
    meta = {
        "tokens_entrada": data.get("prompt_eval_count"),
        "tokens_salida": data.get("eval_count"),
        "latencia_ms_total": int(data.get("total_duration", 0) / 1e6),
    }
    try:
        return json.loads(contenido), meta
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Salida JSON inválida: {contenido[:200]!r}") from exc


def embed(texto: str) -> list[float]:
    """Embedding de un texto con el modelo de embeddings configurado."""
    try:
        r = requests.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={"model": settings.embedding_model, "prompt": texto[:2000]},
            timeout=120,
        )
        r.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(f"No se pudo generar el embedding: {exc}") from exc
    return r.json()["embedding"]
