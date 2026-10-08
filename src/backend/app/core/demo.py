"""Ephemeral demo database initialization for academic presentations."""

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.rol import Rol
from app.models.usuario import Usuario

DEMO_USERS = (
    {
        "email": "admin@scald.com",
        "password": "scald123",
        "nombre": "Administrador",
        "apellido": "SCALD",
        "role": "ADMIN",
        "description": "Administrador del sistema",
    },
    {
        "email": "moises@scald.com",
        "password": "scald123",
        "nombre": "Moises",
        "apellido": "SCALD",
        "role": "AUDITOR",
        "description": "Auditor logístico",
    },
)


def initialize_demo_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        _ensure_roles(session)
        _ensure_users(session)
        session.commit()


def _ensure_roles(session: Session) -> None:
    for role_name, description in (
        ("ADMIN", "Administrador del sistema"),
        ("AUDITOR", "Auditor logístico"),
    ):
        role = session.query(Rol).filter(Rol.nombre == role_name).one_or_none()
        if role is None:
            session.add(Rol(nombre=role_name, descripcion=description))
    session.flush()


def _ensure_users(session: Session) -> None:
    roles = {role.nombre: role for role in session.query(Rol).all()}
    for demo_user in DEMO_USERS:
        role = roles[demo_user["role"]]
        user = session.query(Usuario).filter(Usuario.email == demo_user["email"]).one_or_none()
        if user is None:
            session.add(
                Usuario(
                    nombre=demo_user["nombre"],
                    apellido=demo_user["apellido"],
                    email=demo_user["email"],
                    password_hash=hash_password(demo_user["password"]),
                    rol=role,
                    activo=True,
                )
            )
