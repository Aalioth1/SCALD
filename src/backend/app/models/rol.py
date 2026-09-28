from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.core.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("nombre", name="uq_roles_nombre"),)
