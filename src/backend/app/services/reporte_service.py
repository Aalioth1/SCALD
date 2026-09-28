from datetime import date

from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.reasignacion import Reasignacion
from app.schemas.reporte import ReporteHojaRuta, ReporteIncidencia, ReporteResumen


class ReporteService:
    def __init__(self, db: Session):
        self.db = db

    def resumen(
        self,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        hoja_ruta_id: int | None = None,
        usuario_id: int | None = None,
    ) -> ReporteResumen:
        hojas = self._hojas(fecha_desde, fecha_hasta, hoja_ruta_id)
        hoja_ids = [hoja.id for hoja in hojas]

        bultos = self.db.query(Bulto)
        pistoleos = self.db.query(Pistoleo)
        if hoja_ruta_id is not None:
            bultos = bultos.filter(Bulto.hoja_ruta_id == hoja_ruta_id)
            pistoleos = pistoleos.filter(Pistoleo.hoja_ruta_id == hoja_ruta_id)
        elif fecha_desde is not None or fecha_hasta is not None:
            if hoja_ids:
                bultos = bultos.filter(Bulto.hoja_ruta_id.in_(hoja_ids))
                pistoleos = pistoleos.filter(Pistoleo.hoja_ruta_id.in_(hoja_ids))
            else:
                bultos = bultos.filter(False)
                pistoleos = pistoleos.filter(False)
        if usuario_id is not None:
            pistoleos = pistoleos.filter(Pistoleo.usuario_id == usuario_id)

        incidencias = self.db.query(Incidencia)
        if hoja_ruta_id is not None:
            incidencias = incidencias.filter(Incidencia.hoja_ruta_id.in_(hoja_ids))
        elif fecha_desde is not None or fecha_hasta is not None:
            if hoja_ids:
                incidencias = incidencias.filter(Incidencia.hoja_ruta_id.in_(hoja_ids))
            else:
                incidencias = incidencias.filter(False)
        if usuario_id is not None:
            incidencias = incidencias.filter(Incidencia.usuario_id == usuario_id)
        if fecha_desde is not None:
            incidencias = incidencias.filter(Incidencia.fecha_creacion >= fecha_desde)
        if fecha_hasta is not None:
            incidencias = incidencias.filter(Incidencia.fecha_creacion < fecha_hasta)

        reasignaciones = self.db.query(Reasignacion)
        if hoja_ruta_id is not None:
            reasignaciones = reasignaciones.filter(
                (Reasignacion.hoja_origen_id.in_(hoja_ids))
                | (Reasignacion.hoja_destino_id.in_(hoja_ids))
            )
        elif fecha_desde is not None or fecha_hasta is not None:
            if hoja_ids:
                reasignaciones = reasignaciones.filter(
                    (Reasignacion.hoja_origen_id.in_(hoja_ids))
                    | (Reasignacion.hoja_destino_id.in_(hoja_ids))
                )
            else:
                reasignaciones = reasignaciones.filter(False)
        if usuario_id is not None:
            reasignaciones = reasignaciones.filter(Reasignacion.usuario_id == usuario_id)

        return ReporteResumen(
            total_hojas=len(hojas),
            total_bultos_esperados=bultos.count(),
            total_pistoleos=pistoleos.count(),
            ok=pistoleos.filter(Pistoleo.estado == "OK").count(),
            faltantes=bultos.filter(Bulto.pistoleado.is_(False)).count(),
            duplicados=pistoleos.filter(Pistoleo.estado == "DUPLICADO").count(),
            sin_lista_esperada=pistoleos.filter(Pistoleo.estado == "SIN LISTA ESPERADA").count(),
            no_pertenece=pistoleos.filter(Pistoleo.estado == "NO PERTENECE").count(),
            reasignados=reasignaciones.filter(Reasignacion.estado == "COMPLETADA").count(),
            incidencias_pendientes=incidencias.filter(Incidencia.estado == "PENDIENTE").count(),
            incidencias_regularizadas=incidencias.filter(Incidencia.estado == "REGULARIZADO").count(),
        )

    def detalle_hoja(self, hoja_ruta_id: int) -> ReporteHojaRuta:
        hoja = self.db.query(HojaRuta).filter(HojaRuta.id == hoja_ruta_id, HojaRuta.activo.is_(True)).first()
        if hoja is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        resumen = self.resumen(hoja_ruta_id=hoja.id)
        return ReporteHojaRuta(
            **resumen.model_dump(),
            hoja_ruta_id=hoja.id,
            codigo=hoja.codigo,
            tipo=hoja.tipo,
            fecha=hoja.fecha,
            ruta=hoja.ruta,
            estado=hoja.estado,
        )

    def incidencias(
        self,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        hoja_ruta_id: int | None = None,
        usuario_id: int | None = None,
    ) -> list[ReporteIncidencia]:
        query = self.db.query(Incidencia).order_by(Incidencia.fecha_creacion.desc())
        if estado:
            query = query.filter(Incidencia.estado == estado.upper())
        if fecha_desde:
            query = query.filter(Incidencia.fecha_creacion >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Incidencia.fecha_creacion < fecha_hasta)
        if hoja_ruta_id:
            query = query.filter(Incidencia.hoja_ruta_id == hoja_ruta_id)
        if usuario_id:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        return [ReporteIncidencia.model_validate(item) for item in query.all()]

    def _hojas(self, fecha_desde: date | None, fecha_hasta: date | None, hoja_ruta_id: int | None):
        query = self.db.query(HojaRuta).filter(HojaRuta.activo.is_(True))
        if fecha_desde:
            query = query.filter(HojaRuta.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(HojaRuta.fecha < fecha_hasta)
        if hoja_ruta_id:
            query = query.filter(HojaRuta.id == hoja_ruta_id)
        return query.all()
