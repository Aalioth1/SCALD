from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(payload)
    return UserPublic(
        id=user.id,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        role=user.rol.nombre if user.rol else None,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(payload)


@router.get("/me", response_model=UserPublic)
def me(current_user=Depends(get_current_user)):
    return UserPublic(
        id=current_user.id,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        email=current_user.email,
        role=current_user.rol.nombre if current_user.rol else None,
    )
