from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.auditoria import Auditoria
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.reasignacion import Reasignacion
from app.schemas.reasignacion import ReasignacionCreate
from app.services.hoja_ruta_service import cerrar_hoja_si_completa


class ReasignacionService:
    def __init__(self, db: Session):
        self.db = db

    def reasignar(self, payload: ReasignacionCreate, usuario_id: int, *, cerrar_origen_vacia: bool = True) -> Reasignacion:
        bulto = (
            self.db.query(Bulto)
            .filter(Bulto.id == payload.bulto_id)
            .with_for_update()
            .first()
        )
        if bulto is None or bulto.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulto no encontrado")

        origen_id = bulto.hoja_ruta_id
        if origen_id == payload.hoja_destino_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La hoja origen y destino no pueden ser iguales",
            )

        destino = (
            self.db.query(HojaRuta)
            .filter(
                HojaRuta.id == payload.hoja_destino_id,
                HojaRuta.activo.is_(True),
                HojaRuta.usuario_id == usuario_id,
            )
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
                .filter(Incidencia.id == payload.incidencia_id, Incidencia.usuario_id == usuario_id)
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

        codigo_bulto = bulto.codigo
        pistoleos = (
            self.db.query(Pistoleo)
            .filter(Pistoleo.bulto_id == bulto.id, Pistoleo.hoja_ruta_id == origen_id)
            .all()
        )
        for pistoleo in pistoleos:
            pistoleo.hoja_ruta_id = destino.id
        bulto.hoja_ruta_id = destino.id
        bulto.estado = "OK" if bulto.pistoleado else "REASIGNADO"
        self.db.add(reasignacion)
        self.db.flush()
        cerrar_hoja_si_completa(self.db, destino.id)
        if origen_id != destino.id:
            cerrar_hoja_si_completa(self.db, origen_id)
        if cerrar_origen_vacia:
            origen_inhabilitada, codigo_origen = self._inhabilitar_origen_si_queda_vacia(origen_id)
        else:
            origen = self.db.query(HojaRuta).filter(HojaRuta.id == origen_id).first()
            origen_inhabilitada, codigo_origen = False, origen.codigo if origen else None
        self.db.add(
            Auditoria(
                usuario_id=usuario_id,
                entidad="REASIGNACION",
                entidad_id=reasignacion.id,
                accion="CREAR",
                datos_anteriores={"hoja_ruta_id": origen_id},
                datos_nuevos={
                    "hoja_ruta_id": destino.id,
                    "bulto_id": bulto.id,
                    "codigo_bulto": codigo_bulto,
                    "codigo_hoja_origen": codigo_origen,
                    "codigo_hoja_destino": destino.codigo,
                    "hoja_origen_inhabilitada": origen_inhabilitada,
                },
            )
        )

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

    def _inhabilitar_origen_si_queda_vacia(self, origen_id: int | None) -> tuple[bool, str | None]:
        if origen_id is None:
            return False, None
        origen = self.db.query(HojaRuta).filter(HojaRuta.id == origen_id).first()
        if origen is None:
            return False, None
        restantes = self.db.query(Bulto).filter(Bulto.hoja_ruta_id == origen_id).count()
        if restantes > 0 or origen.estado != "ACTIVA":
            return False, origen.codigo
        origen.estado = "INACTIVA"
        return True, origen.codigo
