from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.reasignacion import Reasignacion
from app.schemas.reporte import (
    ReporteHojaRuta,
    ReporteIncidencia,
    ReporteOperativo,
    ReporteOperativoFaltante,
    ReporteOperativoHoja,
    ReporteOperativoIncidencia,
    ReporteResumen,
)
from app.services.reporte_pdf import (
    BultoPendiente,
    IncidenciaPdf,
    LineaHoja,
    _conteo_incidencias,
    _estado_incidencia,
    _observacion_incidencia,
    generar_pdf_operativo,
)


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
        hojas = self._hojas(fecha_desde, fecha_hasta, hoja_ruta_id, usuario_id)
        hoja_ids = [hoja.id for hoja in hojas]

        bultos = self.db.query(Bulto)
        pistoleos = self.db.query(Pistoleo)
        if usuario_id is not None:
            bultos = bultos.filter(Bulto.usuario_id == usuario_id)
            pistoleos = pistoleos.filter(Pistoleo.usuario_id == usuario_id)
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
        incidencias = self.db.query(Incidencia)
        if usuario_id is not None:
            incidencias = incidencias.filter(Incidencia.usuario_id == usuario_id)
        if hoja_ruta_id is not None:
            incidencias = incidencias.filter(Incidencia.hoja_ruta_id.in_(hoja_ids))
        elif fecha_desde is not None or fecha_hasta is not None:
            if hoja_ids:
                incidencias = incidencias.filter(Incidencia.hoja_ruta_id.in_(hoja_ids))
            else:
                incidencias = incidencias.filter(False)
        reasignaciones = self.db.query(Reasignacion)
        if usuario_id is not None:
            reasignaciones = reasignaciones.filter(Reasignacion.usuario_id == usuario_id)
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

    def vista_operativa(
        self,
        fecha_desde: date | None,
        fecha_hasta: date | None,
        usuario_id: int,
    ) -> ReporteOperativo:
        hojas = self._hojas(fecha_desde, fecha_hasta, None, usuario_id)
        incidencias = self._incidencias_pdf(fecha_desde, fecha_hasta, usuario_id)
        pendientes, regularizadas = _conteo_incidencias(incidencias)
        return ReporteOperativo(
            resumen=self.resumen(fecha_desde, fecha_hasta, None, usuario_id),
            hojas=[
                ReporteOperativoHoja(
                    codigo=linea.codigo,
                    tipo=linea.tipo,
                    registro=linea.fecha,
                    ruta=linea.ruta,
                    transporte=linea.transporte,
                    estado=linea.estado,
                    esperados=linea.esperados,
                    pistoleados=linea.pistoleados,
                    faltantes=linea.faltantes,
                    incidencias=linea.incidencias,
                )
                for linea in self._lineas_hojas(hojas, usuario_id)
            ],
            faltantes=[
                ReporteOperativoFaltante(
                    codigo=item.codigo,
                    hoja=item.hoja,
                    ruta=item.ruta,
                    registro=item.fecha,
                )
                for item in self._bultos_faltantes(hojas, usuario_id, fecha_desde, fecha_hasta)
            ],
            incidencias=[
                ReporteOperativoIncidencia(
                    registro=item.fecha,
                    hoja=item.hoja,
                    bulto=item.bulto,
                    tipo=item.tipo,
                    estado=_estado_incidencia(item.estado),
                    observaciones=_observacion_incidencia(item),
                )
                for item in incidencias
            ],
            pendientes=pendientes,
            regularizadas=regularizadas,
        )

    def pdf_operativo(
        self,
        fecha_desde: date | None,
        fecha_hasta: date | None,
        usuario_id: int,
        autor: str,
    ) -> tuple[bytes, str]:
        hojas = self._hojas(fecha_desde, fecha_hasta, None, usuario_id)
        resumen = self.resumen(fecha_desde, fecha_hasta, None, usuario_id)
        return generar_pdf_operativo(
            resumen=resumen,
            autor=autor,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            hojas=self._lineas_hojas(hojas, usuario_id),
            faltantes=self._bultos_faltantes(hojas, usuario_id, fecha_desde, fecha_hasta),
            incidencias=self._incidencias_pdf(fecha_desde, fecha_hasta, usuario_id),
        )

    def detalle_hoja(self, hoja_ruta_id: int, usuario_id: int | None = None) -> ReporteHojaRuta:
        query = self.db.query(HojaRuta).filter(
            HojaRuta.id == hoja_ruta_id,
            HojaRuta.activo.is_(True),
            HojaRuta.situacion == "VIGENTE",
        )
        if usuario_id is not None:
            query = query.filter(HojaRuta.usuario_id == usuario_id)
        hoja = query.first()
        if hoja is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        resumen = self.resumen(hoja_ruta_id=hoja.id, usuario_id=usuario_id)
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
            query = query.filter(Incidencia.fecha_creacion >= _inicio_dia(fecha_desde))
        if fecha_hasta:
            query = query.filter(Incidencia.fecha_creacion < _fin_dia(fecha_hasta))
        if hoja_ruta_id:
            query = query.filter(Incidencia.hoja_ruta_id == hoja_ruta_id)
        if usuario_id:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        return [ReporteIncidencia.model_validate(item) for item in query.all()]

    def _hojas(
        self,
        fecha_desde: date | None,
        fecha_hasta: date | None,
        hoja_ruta_id: int | None,
        usuario_id: int | None = None,
    ):
        query = self.db.query(HojaRuta).filter(HojaRuta.activo.is_(True), HojaRuta.situacion == "VIGENTE")
        if usuario_id is not None:
            query = query.filter(HojaRuta.usuario_id == usuario_id)
        if fecha_desde:
            query = query.filter(HojaRuta.created_at >= fecha_desde)
        if fecha_hasta:
            query = query.filter(HojaRuta.created_at <= fecha_hasta)
        if hoja_ruta_id:
            query = query.filter(HojaRuta.id == hoja_ruta_id)
        return query.all()

    def _lineas_hojas(self, hojas: list[HojaRuta], usuario_id: int | None) -> list[LineaHoja]:
        if not hojas:
            return []
        ids = [hoja.id for hoja in hojas]
        esperados = dict(self._contar_bultos(ids, usuario_id).all())
        pistoleados = dict(self._contar_bultos(ids, usuario_id, pistoleado=True).all())
        incidencias = dict(self._contar_incidencias(ids, usuario_id).all())
        lineas = []
        for hoja in sorted(hojas, key=lambda item: (item.created_at, item.codigo)):
            total = int(esperados.get(hoja.id, 0) or 0)
            listos = int(pistoleados.get(hoja.id, 0) or 0)
            lineas.append(
                LineaHoja(
                    codigo=hoja.codigo,
                    tipo=hoja.tipo,
                    fecha=hoja.created_at,
                    ruta=hoja.ruta,
                    transporte=hoja.transporte,
                    estado=hoja.estado,
                    esperados=total,
                    pistoleados=listos,
                    faltantes=max(total - listos, 0),
                    incidencias=int(incidencias.get(hoja.id, 0) or 0),
                )
            )
        return lineas

    def _contar_bultos(self, hoja_ids: list[int], usuario_id: int | None, pistoleado: bool | None = None):
        query = self.db.query(Bulto.hoja_ruta_id, func.count(Bulto.id)).filter(Bulto.hoja_ruta_id.in_(hoja_ids))
        if usuario_id is not None:
            query = query.filter(Bulto.usuario_id == usuario_id)
        if pistoleado is not None:
            query = query.filter(Bulto.pistoleado.is_(pistoleado))
        return query.group_by(Bulto.hoja_ruta_id)

    def _contar_incidencias(self, hoja_ids: list[int], usuario_id: int | None):
        query = self.db.query(Incidencia.hoja_ruta_id, func.count(Incidencia.id)).filter(
            Incidencia.hoja_ruta_id.in_(hoja_ids)
        )
        if usuario_id is not None:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        return query.group_by(Incidencia.hoja_ruta_id)

    def _bultos_faltantes(
        self,
        hojas: list[HojaRuta],
        usuario_id: int | None,
        fecha_desde: date | None,
        fecha_hasta: date | None,
    ) -> list[BultoPendiente]:
        if (fecha_desde is not None or fecha_hasta is not None) and not hojas:
            return []
        query = self.db.query(Bulto, HojaRuta).join(HojaRuta, Bulto.hoja_ruta_id == HojaRuta.id).filter(
            Bulto.pistoleado.is_(False),
            HojaRuta.activo.is_(True),
            HojaRuta.situacion == "VIGENTE",
        )
        if usuario_id is not None:
            query = query.filter(Bulto.usuario_id == usuario_id, HojaRuta.usuario_id == usuario_id)
        if hojas and (fecha_desde is not None or fecha_hasta is not None):
            query = query.filter(Bulto.hoja_ruta_id.in_([hoja.id for hoja in hojas]))
        filas = query.order_by(HojaRuta.created_at, HojaRuta.codigo, Bulto.codigo).all()
        return [
            BultoPendiente(codigo=bulto.codigo, hoja=hoja.codigo, ruta=hoja.ruta, fecha=hoja.created_at)
            for bulto, hoja in filas
        ]

    def _incidencias_pdf(
        self,
        fecha_desde: date | None,
        fecha_hasta: date | None,
        usuario_id: int | None,
    ) -> list[IncidenciaPdf]:
        hojas = self._hojas(fecha_desde, fecha_hasta, None, usuario_id)
        query = self.db.query(Incidencia).order_by(Incidencia.fecha_creacion.desc())
        if usuario_id is not None:
            query = query.filter(Incidencia.usuario_id == usuario_id)
        if fecha_desde is not None or fecha_hasta is not None:
            if not hojas:
                return []
            query = query.filter(Incidencia.hoja_ruta_id.in_([hoja.id for hoja in hojas]))
        items = query.all()
        hoja_ids = {item.hoja_ruta_id for item in items if item.hoja_ruta_id}
        bulto_ids = {item.bulto_id for item in items if item.bulto_id}
        hojas_codigo = {
            hoja.id: hoja.codigo
            for hoja in self.db.query(HojaRuta).filter(HojaRuta.id.in_(hoja_ids or [-1])).all()
        }
        bultos_codigo = {
            bulto.id: bulto.codigo
            for bulto in self.db.query(Bulto).filter(Bulto.id.in_(bulto_ids or [-1])).all()
        }
        return [
            IncidenciaPdf(
                fecha=item.fecha_creacion,
                hoja=hojas_codigo.get(item.hoja_ruta_id, "—"),
                bulto=bultos_codigo.get(item.bulto_id, "—"),
                tipo=item.tipo,
                estado=item.estado,
                observaciones=item.observaciones,
            )
            for item in items
        ]


def _inicio_dia(valor: date) -> datetime:
    return datetime.combine(valor, time.min, tzinfo=timezone.utc)


def _fin_dia(valor: date) -> datetime:
    return datetime.combine(valor + timedelta(days=1), time.min, tzinfo=timezone.utc)
