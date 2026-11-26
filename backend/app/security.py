"""Hash de contraseñas (bcrypt) y tokens JWT."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    return pwd_context.verify(password, hash_guardado)


def crear_token(usuario_id: int) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(usuario_id), "exp": expira}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def leer_token(token: str) -> int | None:
    """Devuelve el id de usuario si el token es válido; None en caso contrario."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
