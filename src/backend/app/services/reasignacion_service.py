from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.reasignacion import Reasignacion
from app.schemas.reasignacion import ReasignacionCreate


class ReasignacionService:
    def __init__(self, db: Session):
        self.db = db

    def reasignar(self, payload: ReasignacionCreate, usuario_id: int) -> Reasignacion:
        bulto = (
            self.db.query(Bulto)
            .filter(Bulto.id == payload.bulto_id)
            .with_for_update()
            .first()
        )
        if bulto is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulto no encontrado")

        origen_id = bulto.hoja_ruta_id
        if origen_id == payload.hoja_destino_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La hoja origen y destino no pueden ser iguales",
            )

        destino = (
            self.db.query(HojaRuta)
            .filter(HojaRuta.id == payload.hoja_destino_id, HojaRuta.activo.is_(True))
            .with_for_update()
            .first()
        )
        if destino is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja destino no encontrada")
        if destino.estado != "ACTIVA":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La hoja destino no está activa")

        duplicate = self.db.query(Bulto).filter(
            Bulto.hoja_ruta_id == destino.id,
            Bulto.codigo == bulto.codigo,
        ).first()
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El bulto ya existe en la hoja destino",
            )

        incidencia = None
        if payload.incidencia_id is not None:
            incidencia = (
                self.db.query(Incidencia)
                .filter(Incidencia.id == payload.incidencia_id)
                .with_for_update()
                .first()
            )
            if incidencia is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")
            if incidencia.bulto_id != bulto.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La incidencia no corresponde al bulto",
                )
            if incidencia.estado != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Solo se puede reasignar una incidencia PENDIENTE",
                )

        ahora = datetime.now(timezone.utc)
        reasignacion = Reasignacion(
            bulto_id=bulto.id,
            hoja_origen_id=origen_id,
            hoja_destino_id=destino.id,
            incidencia_id=payload.incidencia_id,
            usuario_id=usuario_id,
            fecha_hora=ahora,
            motivo=payload.motivo,
            observaciones=payload.observaciones,
        )

        if incidencia is None:
            incidencia = Incidencia(
                tipo="REASIGNADO",
                hoja_ruta_id=origen_id,
                bulto_id=bulto.id,
                usuario_id=usuario_id,
                estado="REASIGNADO",
                observaciones=payload.observaciones or payload.motivo,
                nueva_hoja_ruta_id=destino.id,
                fecha_creacion=ahora,
                fecha_resolucion=ahora,
            )
            self.db.add(incidencia)
            self.db.flush()
            reasignacion.incidencia_id = incidencia.id
        else:
            incidencia.estado = "REASIGNADO"
            incidencia.usuario_id = usuario_id
            incidencia.nueva_hoja_ruta_id = destino.id
            incidencia.fecha_resolucion = ahora
            if payload.observaciones:
                incidencia.observaciones = payload.observaciones

        bulto.hoja_ruta_id = destino.id
        bulto.estado = "REASIGNADO"
        self.db.add(reasignacion)

        try:
            self.db.commit()
            self.db.refresh(reasignacion)
            return reasignacion
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo completar la reasignación",
            )
