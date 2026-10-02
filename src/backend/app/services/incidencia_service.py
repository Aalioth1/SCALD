from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria
from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.schemas.reasignacion import ReasignacionCreate
from app.services.reasignacion_service import ReasignacionService


class IncidenciaService:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, estado: str | None = None, usuario_id: int | None = None):
        query = (
            self.db.query(Incidencia)
            .outerjoin(HojaRuta, Incidencia.hoja_ruta_id == HojaRuta.id)
            .filter(or_(Incidencia.hoja_ruta_id.is_(None), HojaRuta.situacion == "VIGENTE"))
            .order_by(Incidencia.fecha_creacion.desc())
        )
        if usuario_id is not None:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        if estado:
            query = query.filter(Incidencia.estado == estado.upper())
        return query.all()

    def obtener(self, incidencia_id: int, usuario_id: int | None = None) -> Incidencia:
        query = self.db.query(Incidencia).filter(Incidencia.id == incidencia_id)
        if usuario_id is not None:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        incidencia = query.first()
        if incidencia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidencia no encontrada",
            )
        return incidencia

    def resolver(self, incidencia_id: int, usuario_id: int, observaciones: str | None = None) -> Incidencia:
        incidencia = self.obtener(incidencia_id, usuario_id)
        self._validar_pendiente(incidencia)
        incidencia.estado = "REGULARIZADO"
        incidencia.usuario_id = usuario_id
        incidencia.fecha_resolucion = datetime.now(timezone.utc)
        if observaciones:
            incidencia.observaciones = observaciones
        self.db.add(
            Auditoria(
                usuario_id=usuario_id,
                entidad="INCIDENCIA",
                entidad_id=incidencia.id,
                accion="REGULARIZAR",
                datos_anteriores={"estado": "PENDIENTE"},
                datos_nuevos=self._contexto_incidencia(incidencia),
            )
        )
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    def eliminar_pistoleo(self, incidencia_id: int, usuario_id: int) -> Incidencia:
        incidencia = self.obtener(incidencia_id, usuario_id)
        self._validar_pendiente(incidencia)
        if incidencia.hoja_ruta_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La incidencia no está asociada a una hoja de ruta",
            )

        consulta = self.db.query(Pistoleo).filter(
            Pistoleo.hoja_ruta_id == incidencia.hoja_ruta_id,
            Pistoleo.usuario_id == usuario_id,
            Pistoleo.estado == incidencia.tipo,
        )
        if incidencia.bulto_id is None:
            consulta = consulta.filter(Pistoleo.bulto_id.is_(None))
        else:
            consulta = consulta.filter(Pistoleo.bulto_id == incidencia.bulto_id)
        pistoleos = consulta.order_by(Pistoleo.fecha_hora.desc()).all()
        if incidencia.bulto_id is None:
            pistoleos = pistoleos[:1]
        if not pistoleos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el pistoleo de esta incidencia",
            )

        for pistoleo in pistoleos:
            self.db.add(
                Auditoria(
                    usuario_id=usuario_id,
                    entidad="PISTOLEO",
                    entidad_id=pistoleo.id,
                    accion="ELIMINAR",
                    datos_anteriores={"estado": pistoleo.estado, "codigo_bulto": pistoleo.codigo_bulto},
                    datos_nuevos={"incidencia_id": incidencia.id},
                )
            )
            self.db.delete(pistoleo)
        self.db.flush()
        self._ajustar_bulto_tras_eliminar(incidencia)
        incidencia.estado = "ANULADO"
        incidencia.usuario_id = usuario_id
        incidencia.fecha_resolucion = datetime.now(timezone.utc)
        incidencia.observaciones = "Pistoleo eliminado"
        self.db.add(
            Auditoria(
                usuario_id=usuario_id,
                entidad="INCIDENCIA",
                entidad_id=incidencia.id,
                accion="ANULAR",
                datos_anteriores={"estado": "PENDIENTE"},
                datos_nuevos=self._contexto_incidencia(incidencia),
            )
        )
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    def anadir_bulto(self, incidencia_id: int, usuario_id: int) -> Incidencia:
        incidencia = self.obtener(incidencia_id, usuario_id)
        self._validar_pendiente(incidencia)
        if incidencia.bulto_id is None or incidencia.hoja_ruta_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay un bulto para añadir a esta hoja de ruta",
            )
        bulto = incidencia.bulto
        if bulto is None or bulto.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulto no encontrado")
        if bulto.hoja_ruta_id == incidencia.hoja_ruta_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El bulto ya pertenece a esta hoja de ruta",
            )

        tipo = incidencia.tipo
        hoja_id = incidencia.hoja_ruta_id
        bulto_id = incidencia.bulto_id
        codigo = bulto.codigo
        ReasignacionService(self.db).reasignar(
            ReasignacionCreate(
                bulto_id=bulto_id,
                hoja_destino_id=hoja_id,
                incidencia_id=incidencia.id,
                motivo="Añadido a la hoja desde la resolución de la incidencia",
            ),
            usuario_id,
            cerrar_origen_vacia=False,
        )
        self._quitar_copias_en_otras_hojas(codigo, usuario_id, hoja_id, conservar_id=bulto_id)

        bulto = self.db.query(Bulto).filter(Bulto.id == bulto_id, Bulto.usuario_id == usuario_id).one()
        bulto.pistoleado = True
        bulto.estado = "OK"
        pistoleos = (
            self.db.query(Pistoleo)
            .filter(
                Pistoleo.bulto_id == bulto_id,
                Pistoleo.hoja_ruta_id == hoja_id,
                Pistoleo.usuario_id == usuario_id,
                Pistoleo.estado == tipo,
            )
            .all()
        )
        for pistoleo in pistoleos:
            pistoleo.estado = "OK"
            pistoleo.observacion = "Bulto añadido a la hoja de ruta"
        incidencia_actual = self.obtener(incidencia_id, usuario_id)
        incidencia_actual.observaciones = "El bulto se cambió a esta ruta"
        self.db.commit()
        return self.obtener(incidencia_id, usuario_id)

    def anular(self, incidencia_id: int, usuario_id: int, observaciones: str | None = None) -> Incidencia:
        incidencia = self.obtener(incidencia_id, usuario_id)
        self._validar_pendiente(incidencia)
        incidencia.estado = "ANULADO"
        incidencia.usuario_id = usuario_id
        incidencia.fecha_resolucion = datetime.now(timezone.utc)
        if observaciones:
            incidencia.observaciones = observaciones
        self.db.add(
            Auditoria(
                usuario_id=usuario_id,
                entidad="INCIDENCIA",
                entidad_id=incidencia.id,
                accion="ANULAR",
                datos_anteriores={"estado": "PENDIENTE"},
                datos_nuevos=self._contexto_incidencia(incidencia),
            )
        )
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    @staticmethod
    def _contexto_incidencia(incidencia: Incidencia) -> dict:
        return {
            "estado": incidencia.estado,
            "tipo": incidencia.tipo,
            "codigo_bulto": incidencia.bulto.codigo if incidencia.bulto else None,
            "codigo_hoja": incidencia.hoja_ruta.codigo if incidencia.hoja_ruta else None,
        }

    def _quitar_copias_en_otras_hojas(self, codigo: str, usuario_id: int, hoja_destino_id: int, conservar_id: int) -> None:
        copias = (
            self.db.query(Bulto)
            .filter(
                Bulto.codigo == codigo,
                Bulto.usuario_id == usuario_id,
                Bulto.id != conservar_id,
                Bulto.hoja_ruta_id != hoja_destino_id,
            )
            .all()
        )
        for copia in copias:
            for pistoleo in list(copia.pistoleos):
                pistoleo.bulto_id = conservar_id
            for otra in list(copia.incidencias):
                otra.bulto_id = conservar_id
                if otra.estado == "PENDIENTE":
                    otra.estado = "ANULADO"
                    otra.fecha_resolucion = datetime.now(timezone.utc)
                    otra.observaciones = "El bulto se añadió a otra hoja de ruta"
            for reasignacion in list(copia.reasignaciones):
                reasignacion.bulto_id = conservar_id
        if not copias:
            return
        self.db.flush()
        for copia in copias:
            self.db.delete(copia)
        self.db.flush()

    def _ajustar_bulto_tras_eliminar(self, incidencia: Incidencia) -> None:
        bulto = incidencia.bulto
        if bulto is None or bulto.hoja_ruta_id != incidencia.hoja_ruta_id:
            return
        restantes = self.db.query(Pistoleo).filter(Pistoleo.bulto_id == bulto.id).count()
        if restantes == 0:
            bulto.pistoleado = False
            bulto.estado = "FALTANTE"
        elif restantes == 1:
            bulto.pistoleado = True
            bulto.estado = "OK"

    @staticmethod
    def _validar_pendiente(incidencia: Incidencia) -> None:
        if incidencia.estado != "PENDIENTE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Solo se pueden modificar incidencias PENDIENTES",
            )
