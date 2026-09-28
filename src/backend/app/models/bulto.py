from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Bulto(Base):
    __tablename__ = "bultos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), nullable=False, index=True)
    hoja_ruta_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=False)
    estado = Column(String(50), nullable=False, default="PENDIENTE")
    pistoleado = Column(Boolean, default=False, nullable=False)
    fecha = Column(Date, nullable=True, default=date.today)
    info_adicional = Column(String(500), nullable=True)

    hoja_ruta = relationship("HojaRuta", back_populates="bultos")
    pistoleos = relationship("Pistoleo", back_populates="bulto")
    incidencias = relationship("Incidencia", back_populates="bulto")
    reasignaciones = relationship("Reasignacion", back_populates="bulto")

    __table_args__ = (
        UniqueConstraint("hoja_ruta_id", "codigo", name="uq_bultos_hoja_codigo"),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'OK', 'FALTANTE', 'DUPLICADO', 'SIN LISTA', 'SIN HOJA', 'REASIGNADO')",
            name="ck_bultos_estado",
        ),
    )
