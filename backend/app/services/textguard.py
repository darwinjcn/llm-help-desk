"""Guardia determinista contra salidas repetitivas del LLM.

Los modelos pequeños (3B en CPU) pueden entrar en bucle y repetir la misma
frase muchas veces, sobre todo con temperatura baja y salidas JSON largas.
Este guardia detecta el patrón en código; la salida se rechaza y se reintenta.
"""
import re
from collections import Counter

# Frases más cortas que esto no cuentan (títulos, pasos "1.", etc.)
_MIN_LARGO = 20
# Más de esta cantidad de apariciones de la misma frase => salida repetitiva
_MAX_REPES = 2


def salida_repetitiva(texto: str) -> bool:
    """True si alguna frase (>= _MIN_LARGO caracteres) aparece más de _MAX_REPES veces."""
    if not texto:
        return False
    fragmentos = [
        f.strip().lower()
        for f in re.split(r"[.!?\n;]+", texto)
        if len(f.strip()) >= _MIN_LARGO
    ]
    if not fragmentos:
        return False
    _, repes = Counter(fragmentos).most_common(1)[0]
    return repes > _MAX_REPES
