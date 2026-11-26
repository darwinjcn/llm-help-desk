"""Reglas de negocio deterministas.

El LLM clasifica, pero las reglas de negocio MANDAN sobre el modelo:
si el texto indica caída total / facturación / producción, la prioridad
se fuerza a "critica" sin importar lo que diga el modelo.
"""
import unicodedata

# Palabras/frases que implican impacto total para la organización
PALABRAS_CRITICAS = (
    "caida total",
    "sin servicio",
    "fuera de servicio",
    "no funciona nada",
    "produccion",
    "facturacion",
    "paralizado",
    "nadie tiene",
    "toda la oficina",
    "toda la sede",
    "toda la empresa",
)


def _normalizar(texto: str) -> str:
    """Minúsculas + sin acentos, para que la regla sea robusta al tipeo."""
    return (
        unicodedata.normalize("NFKD", texto.lower())
        .encode("ascii", "ignore")
        .decode()
    )


def prioridad_forzada(texto: str) -> bool:
    t = _normalizar(texto)
    return any(_normalizar(palabra) in t for palabra in PALABRAS_CRITICAS)
