from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Pistoleo(Base):
    __tablename__ = "pistoleos"

    id = Column(Integer, primary_key=True, index=True)
    codigo_bulto = Column(String(100), nullable=False, index=True)
    hoja_ruta_id = Column(Integer, ForeignKey("hojas_ruta.id"), nullable=True)
    bulto_id = Column(Integer, ForeignKey("bultos.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_hora = Column(DateTime, nullable=False, default=datetime.utcnow)
    estado = Column(String(50), nullable=False, default="OK")
    observacion = Column(String(500), nullable=True)

    hoja_ruta = relationship("HojaRuta", back_populates="pistoleos")
    bulto = relationship("Bulto", back_populates="pistoleos")
    usuario = relationship("Usuario")
