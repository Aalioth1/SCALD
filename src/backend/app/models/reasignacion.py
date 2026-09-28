from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Reasignacion(Base):
    __tablename__ = "reasignaciones"

    id = Column(Integer, primary_key=True, index=True)
    bulto_id = Column(Integer, ForeignKey("bultos.id"), nullable=False)
    hoja_origen_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=False)
    hoja_destino_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=False)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    motivo = Column(String(200), nullable=False)
    observaciones = Column(String(500), nullable=True)
    estado = Column(String(30), nullable=False, default="COMPLETADA")

    bulto = relationship("Bulto", back_populates="reasignaciones")
    hoja_origen = relationship("HojaRuta", foreign_keys=[hoja_origen_id], back_populates="reasignaciones_origen")
    hoja_destino = relationship("HojaRuta", foreign_keys=[hoja_destino_id], back_populates="reasignaciones_destino")
    incidencia = relationship("Incidencia", back_populates="reasignaciones")
    usuario = relationship("Usuario")

    __table_args__ = (
        CheckConstraint("hoja_origen_id <> hoja_destino_id", name="ck_reasignaciones_hojas_distintas"),
        CheckConstraint("estado IN ('COMPLETADA', 'ANULADA')", name="ck_reasignaciones_estado"),
    )
