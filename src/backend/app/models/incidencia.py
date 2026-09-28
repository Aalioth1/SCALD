from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(60), nullable=False)
    hoja_ruta_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=True)
    bulto_id = Column(Integer, ForeignKey("bultos.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    estado = Column(String(30), nullable=False, default="PENDIENTE")
    observaciones = Column(String(500), nullable=True)
    nueva_hoja_ruta_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)

    hoja_ruta = relationship(
        "HojaRuta",
        foreign_keys=[hoja_ruta_id],
        back_populates="incidencias",
    )
    bulto = relationship("Bulto", back_populates="incidencias")
    usuario = relationship("Usuario")
    nueva_hoja_ruta = relationship(
        "HojaRuta",
        foreign_keys=[nueva_hoja_ruta_id],
    )
    reasignaciones = relationship("Reasignacion", back_populates="incidencia")

    __table_args__ = (
        CheckConstraint(
            "estado IN ('PENDIENTE', 'REGULARIZADO', 'REASIGNADO', 'ANULADO')",
            name="ck_incidencias_estado",
        ),
    )
