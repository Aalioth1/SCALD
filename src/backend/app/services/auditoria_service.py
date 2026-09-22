from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo


class AuditoriaService:
    def __init__(self, db: Session):
        self.db = db

    def determinar_estado_bulto(self, bulto: Bulto) -> str:
        if bulto.pistoleado:
            return "OK"
        return "FALTANTE"

    def registrar_pistoleo(self, *, codigo_bulto: str, hoja_ruta_id: int | None, usuario_id: int, bulto: Bulto | None) -> Pistoleo:
        if bulto is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulto no encontrado")

        if bulto.hoja_ruta_id != hoja_ruta_id and hoja_ruta_id is not None:
            estado = "REASIGNADO"
        else:
            estado = "OK"

        bulto.pistoleado = True
        bulto.estado = estado
        self.db.add(bulto)

        pistoleo = Pistoleo(
            codigo_bulto=bulto.codigo,
            hoja_ruta_id=bulto.hoja_ruta_id,
            bulto_id=bulto.id,
            usuario_id=usuario_id,
            estado=estado,
            observacion="Pistoleo registrado",
            fecha_hora=datetime.utcnow(),
        )
        self.db.add(pistoleo)
        self.db.commit()
        self.db.refresh(pistoleo)
        return pistoleo

    def crear_incidencia_si_corresponde(self, *, bulto: Bulto, tipo: str, usuario_id: int, hoja_ruta_id: int | None = None, observaciones: str | None = None):
        incidencia = Incidencia(
            tipo=tipo,
            hoja_ruta_id=hoja_ruta_id or bulto.hoja_ruta_id,
            bulto_id=bulto.id,
            usuario_id=usuario_id,
            estado="PENDIENTE",
            observaciones=observaciones,
            fecha_creacion=datetime.utcnow(),
        )
        self.db.add(incidencia)
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia
