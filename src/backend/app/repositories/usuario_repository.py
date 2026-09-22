from sqlalchemy.orm import Session

from app.models.rol import Rol
from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def create(self, *, nombre: str, apellido: str, email: str, password_hash: str, rol: Rol) -> Usuario:
        user = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password_hash,
            rol_id=rol.id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all(self):
        return self.db.query(Usuario).all()
