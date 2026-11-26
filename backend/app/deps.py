"""Dependencias de FastAPI: autenticación y control de roles (RBAC)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.security import leer_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def usuario_actual(
    token: str = Depends(oauth2), db: Session = Depends(get_db)
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    usuario_id = leer_token(token)
    if usuario_id is None:
        raise credenciales_invalidas
    user = db.get(Usuario, usuario_id)
    if user is None:
        raise credenciales_invalidas
    return user


def requiere_rol(*roles: str):
    """Fábrica de dependencia: limita el acceso a los roles indicados."""

    def verificar(user: Usuario = Depends(usuario_actual)) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta acción",
            )
        return user

    return verificar
