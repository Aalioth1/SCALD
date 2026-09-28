import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.rol import Rol  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.create_all(bind=TEST_ENGINE)
    with TestSessionLocal() as session:
        session.add_all(
            [
                Rol(nombre="ADMIN", descripcion="Administrador del sistema"),
                Rol(nombre="AUDITOR", descripcion="Auditor logístico"),
            ]
        )
        session.commit()
        admin_role = session.query(Rol).filter(Rol.nombre == "ADMIN").one()
        session.add(
            Usuario(
                nombre="Admin",
                apellido="Pruebas",
                email="admin-fixture@example.com",
                password_hash=hash_password("SecurePass123!"),
                rol_id=admin_role.id,
            )
        )
        session.commit()

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TEST_ENGINE)
