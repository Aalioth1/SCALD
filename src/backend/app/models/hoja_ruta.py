from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class HojaRuta(Base):
    __tablename__ = "hojas_ruta"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    fecha = Column(Date, nullable=False)
    ruta = Column(String(200), nullable=False)
    transporte = Column(String(200), nullable=True)
    cantidad_declarada = Column(Integer, nullable=False, default=0)
    estado = Column(String(30), nullable=False, default="ACTIVA")
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(Date, nullable=False, default=date.today)
    updated_at = Column(Date, nullable=False, default=date.today, onupdate=date.today)

    bultos = relationship("Bulto", back_populates="hoja_ruta")
    incidencias = relationship(
        "Incidencia",
        foreign_keys="[Incidencia.hoja_ruta_id]",
        back_populates="hoja_ruta",
    )
    pistoleos = relationship("Pistoleo", back_populates="hoja_ruta")
    reasignaciones_origen = relationship(
        "Reasignacion",
        foreign_keys="[Reasignacion.hoja_origen_id]",
        back_populates="hoja_origen",
    )
    reasignaciones_destino = relationship(
        "Reasignacion",
        foreign_keys="[Reasignacion.hoja_destino_id]",
        back_populates="hoja_destino",
    )

    __table_args__ = (
        CheckConstraint("tipo IN ('HRD', 'HRE')", name="ck_hojas_ruta_tipo"),
        CheckConstraint("cantidad_declarada >= 0", name="ck_hojas_ruta_cantidad"),
        CheckConstraint("estado IN ('ACTIVA', 'INACTIVA', 'CERRADA')", name="ck_hojas_ruta_estado"),
        UniqueConstraint("codigo", name="uq_hojas_ruta_codigo"),
    )
