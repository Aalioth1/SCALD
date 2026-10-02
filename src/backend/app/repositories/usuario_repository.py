from sqlalchemy.orm import Session, joinedload

from app.models.rol import Rol
from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Usuario | None:
        return self.db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.email == email).first()

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario_id).first()

    def list_all(self) -> list[Usuario]:
        return (
            self.db.query(Usuario)
            .options(joinedload(Usuario.rol))
            .order_by(Usuario.apellido, Usuario.nombre)
            .all()
        )

    def create(self, *, nombre: str, apellido: str, email: str, password_hash: str, rol: Rol, activo: bool = True) -> Usuario:
        user = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password_hash,
            rol_id=rol.id,
            activo=activo,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: Usuario) -> Usuario:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: Usuario) -> None:
        self.db.delete(user)
        self.db.commit()
