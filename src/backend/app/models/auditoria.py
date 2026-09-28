from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String

from app.core.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    entidad = Column(String(80), nullable=False)
    entidad_id = Column(Integer, nullable=True)
    accion = Column(String(40), nullable=False)
    datos_anteriores = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    origen = Column(String(80), nullable=False, default="API")
    correlation_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_auditoria_entidad", "entidad", "entidad_id"),
        Index("ix_auditoria_fecha_hora", "fecha_hora"),
    )
