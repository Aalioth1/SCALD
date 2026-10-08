"""Create or update the initial SCALD users in the configured database.

Run this script once after applying the Alembic migrations. Passwords are
read from environment variables and are never stored in the repository.
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.rol import Rol
from app.models.usuario import Usuario


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value


def upsert_user(
    session,
    *,
    email: str,
    password: str,
    nombre: str,
    apellido: str,
    role_name: str,
) -> None:
    role = session.query(Rol).filter(Rol.nombre == role_name).one_or_none()
    if role is None:
        raise RuntimeError(f"No existe el rol requerido: {role_name}")

    user = session.query(Usuario).filter(Usuario.email == email).one_or_none()
    if user is None:
        user = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=hash_password(password),
            rol=role,
            activo=True,
        )
        session.add(user)
    else:
        user.nombre = nombre
        user.apellido = apellido
        user.password_hash = hash_password(password)
        user.rol = role
        user.activo = True


def main() -> None:
    admin_email = os.getenv("SCALD_ADMIN_EMAIL", "admin@scald.com")
    auditor_email = os.getenv("SCALD_AUDITOR_EMAIL", "moises@scald.com")

    with SessionLocal() as session:
        upsert_user(
            session,
            email=admin_email,
            password=required_env("SCALD_ADMIN_PASSWORD"),
            nombre=os.getenv("SCALD_ADMIN_NOMBRE", "Administrador"),
            apellido=os.getenv("SCALD_ADMIN_APELLIDO", "SCALD"),
            role_name="ADMIN",
        )
        upsert_user(
            session,
            email=auditor_email,
            password=required_env("SCALD_AUDITOR_PASSWORD"),
            nombre=os.getenv("SCALD_AUDITOR_NOMBRE", "Moises"),
            apellido=os.getenv("SCALD_AUDITOR_APELLIDO", "SCALD"),
            role_name="AUDITOR",
        )
        session.commit()

    print(f"Usuarios iniciales configurados: {admin_email}, {auditor_email}")


if __name__ == "__main__":
    main()
