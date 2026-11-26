"""Autenticación: registro, login y perfil actual (JWT)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import usuario_actual
from app.models import Usuario
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.security import crear_token, hashear_password, verificar_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def registrar(datos: RegisterIn, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    user = Usuario(
        email=datos.email,
        password_hash=hashear_password(datos.password),
        nombre=datos.nombre,
        rol=datos.rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=crear_token(user.id), user=UserOut.model_validate(user)
    )


@router.post("/login", response_model=TokenOut)
def iniciar_sesion(datos: LoginIn, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if user is None or not verificar_password(datos.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return TokenOut(
        access_token=crear_token(user.id), user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def perfil_actual(user: Usuario = Depends(usuario_actual)):
    return UserOut.model_validate(user)
