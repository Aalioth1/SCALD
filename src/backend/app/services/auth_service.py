from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.rol import Rol
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuarioRepository(db)

    def register(self, payload: RegisterRequest):
        existing = self.repository.get_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

        role = self.db.query(Rol).filter(Rol.nombre == payload.role.upper()).first()
        if role is None:
            role = Rol(nombre=payload.role.upper(), descripcion="Rol asignado por sistema")
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)

        user = self.repository.create(
            nombre=payload.nombre,
            apellido=payload.apellido,
            email=payload.email,
            password_hash=hash_password(payload.password),
            rol=role,
        )
        return user

    def login(self, payload: LoginRequest):
        user = self.repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        token = create_access_token(user.email, extra={"role": user.rol.nombre if user.rol else None, "user_id": user.id})
        return {"access_token": token, "token_type": "bearer"}
