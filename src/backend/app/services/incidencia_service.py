from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.incidencia import Incidencia


class IncidenciaService:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, estado: str | None = None):
        query = self.db.query(Incidencia).order_by(Incidencia.fecha_creacion.desc())
        if estado:
            query = query.filter(Incidencia.estado == estado.upper())
        return query.all()

    def obtener(self, incidencia_id: int) -> Incidencia:
        incidencia = self.db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
        if incidencia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidencia no encontrada",
            )
        return incidencia

    def resolver(self, incidencia_id: int, usuario_id: int, observaciones: str | None = None) -> Incidencia:
        incidencia = self.obtener(incidencia_id)
        self._validar_pendiente(incidencia)
        incidencia.estado = "REGULARIZADO"
        incidencia.usuario_id = usuario_id
        incidencia.fecha_resolucion = datetime.now(timezone.utc)
        if observaciones:
            incidencia.observaciones = observaciones
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    def anular(self, incidencia_id: int, usuario_id: int, observaciones: str | None = None) -> Incidencia:
        incidencia = self.obtener(incidencia_id)
        self._validar_pendiente(incidencia)
        incidencia.estado = "ANULADO"
        incidencia.usuario_id = usuario_id
        incidencia.fecha_resolucion = datetime.now(timezone.utc)
        if observaciones:
            incidencia.observaciones = observaciones
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    @staticmethod
    def _validar_pendiente(incidencia: Incidencia) -> None:
        if incidencia.estado != "PENDIENTE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Solo se pueden modificar incidencias PENDIENTES",
            )
