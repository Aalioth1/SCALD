from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.bulto import Bulto
from app.models.auditoria import Auditoria
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.reasignacion import Reasignacion
from app.services.hoja_ruta_service import cerrar_hoja_si_completa
from app.schemas.auditoria import AuditoriaOut


class AuditoriaService:
    def __init__(self, db: Session):
        self.db = db

    def determinar_estado_bulto(self, bulto: Bulto) -> str:
        if bulto.pistoleado:
            return "OK"
        return "FALTANTE"

    def listar_registros(self, entidad: str | None = None, limite: int = 100):
        query = self.db.query(Auditoria).order_by(Auditoria.fecha_hora.desc())
        if entidad:
            query = query.filter(Auditoria.entidad == entidad.upper())
        registros = query.limit(limite).all()
        referencias = self._referencias(registros)
        salida: list[AuditoriaOut] = []
        for registro in registros:
            item = AuditoriaOut.model_validate(registro)
            extra = referencias.get((registro.entidad, registro.entidad_id), {})
            datos = dict(item.datos_nuevos or {})
            for clave, valor in extra.items():
                if valor not in (None, "") and not datos.get(clave):
                    datos[clave] = valor
            item.datos_nuevos = datos
            salida.append(item)
        return salida

    def registrar_pistoleo(
        self,
        *,
        codigo_bulto: str,
        hoja_ruta_id: int | None,
        usuario_id: int,
        bulto: Bulto | None,
        bulto_en_otra_hoja: Bulto | None = None,
    ) -> Pistoleo:
        codigo = codigo_bulto.strip().upper()
        hoja_efectiva = hoja_ruta_id or (bulto.hoja_ruta_id if bulto else None)

        if bulto is None:
            estado = "NO PERTENECE" if bulto_en_otra_hoja else "SIN LISTA ESPERADA"
            incidencia_bulto = bulto_en_otra_hoja
            observacion = "El bulto pertenece a otra hoja" if bulto_en_otra_hoja else "No existe en la lista esperada"
        else:
            pistoleos_previos = self.db.query(Pistoleo).filter(
                Pistoleo.bulto_id == bulto.id,
                Pistoleo.hoja_ruta_id == hoja_efectiva,
            ).count()
            estado = "DUPLICADO" if pistoleos_previos else "OK"
            incidencia_bulto = bulto
            observacion = "Pistoleo duplicado" if pistoleos_previos else "Pistoleo registrado"

        pistoleo = Pistoleo(
            codigo_bulto=codigo,
            hoja_ruta_id=hoja_efectiva,
            bulto_id=bulto.id if bulto else (bulto_en_otra_hoja.id if bulto_en_otra_hoja else None),
            usuario_id=usuario_id,
            estado=estado,
            observacion=observacion,
            fecha_hora=datetime.now(timezone.utc),
        )

        try:
            self.db.add(pistoleo)
            if bulto is not None:
                bulto.pistoleado = True
                bulto.estado = estado
                self.db.add(bulto)
            self.db.flush()
            hoja = (
                self.db.query(HojaRuta).filter(HojaRuta.id == hoja_efectiva).first()
                if hoja_efectiva
                else None
            )
            codigo_hoja = hoja.codigo if hoja else None
            if estado != "OK":
                incidencia = self._crear_incidencia_en_transaccion(
                    tipo=estado,
                    hoja_ruta_id=hoja_efectiva,
                    bulto=incidencia_bulto,
                    usuario_id=usuario_id,
                    observaciones=observacion,
                )
                self.db.flush()
                self.db.add(
                    Auditoria(
                        usuario_id=usuario_id,
                        entidad="INCIDENCIA",
                        entidad_id=incidencia.id,
                        accion="CREAR",
                        datos_nuevos={
                            "tipo": estado,
                            "estado": "PENDIENTE",
                            "codigo_bulto": incidencia_bulto.codigo if incidencia_bulto else codigo,
                            "codigo_hoja": codigo_hoja,
                        },
                    )
                )
            if estado in ("OK", "DUPLICADO") and bulto is not None and bulto.hoja_ruta_id == hoja_efectiva:
                cerrar_hoja_si_completa(self.db, hoja_efectiva)
            self.db.add(
                Auditoria(
                    usuario_id=usuario_id,
                    entidad="PISTOLEO",
                    entidad_id=pistoleo.id,
                    accion="CREAR",
                    datos_nuevos={
                        "codigo_bulto": codigo,
                        "estado": estado,
                        "codigo_hoja": codigo_hoja,
                    },
                )
            )
            self.db.commit()
            self.db.refresh(pistoleo)
            return pistoleo
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo registrar el pistoleo por un conflicto de datos",
            )

    def _crear_incidencia_en_transaccion(
        self,
        *,
        tipo: str,
        hoja_ruta_id: int | None,
        bulto: Bulto | None,
        usuario_id: int,
        observaciones: str,
    ) -> Incidencia:
        incidencia = Incidencia(
            tipo=tipo,
            hoja_ruta_id=hoja_ruta_id,
            bulto_id=bulto.id if bulto else None,
            usuario_id=usuario_id,
            estado="PENDIENTE",
            observaciones=observaciones,
            fecha_creacion=datetime.now(timezone.utc),
        )
        self.db.add(incidencia)
        return incidencia

    def crear_incidencia_si_corresponde(self, *, bulto: Bulto, tipo: str, usuario_id: int, hoja_ruta_id: int | None = None, observaciones: str | None = None):
        incidencia = Incidencia(
            tipo=tipo,
            hoja_ruta_id=hoja_ruta_id or bulto.hoja_ruta_id,
            bulto_id=bulto.id,
            usuario_id=usuario_id,
            estado="PENDIENTE",
            observaciones=observaciones,
            fecha_creacion=datetime.now(timezone.utc),
        )
        self.db.add(incidencia)
        self.db.commit()
        self.db.refresh(incidencia)
        return incidencia

    def _referencias(self, registros: list[Auditoria]) -> dict[tuple[str, int | None], dict]:
        pistoleo_ids = [item.entidad_id for item in registros if item.entidad == "PISTOLEO" and item.entidad_id]
        incidencia_ids = [item.entidad_id for item in registros if item.entidad == "INCIDENCIA" and item.entidad_id]
        reasignacion_ids = [item.entidad_id for item in registros if item.entidad == "REASIGNACION" and item.entidad_id]
        hoja_ids = [item.entidad_id for item in registros if item.entidad == "HOJA_RUTA" and item.entidad_id]
        refs: dict[tuple[str, int | None], dict] = {}

        if pistoleo_ids:
            pistoleos = self.db.query(Pistoleo).filter(Pistoleo.id.in_(pistoleo_ids)).all()
            for pistoleo in pistoleos:
                refs[("PISTOLEO", pistoleo.id)] = {
                    "codigo_bulto": pistoleo.codigo_bulto,
                    "estado": pistoleo.estado,
                    "codigo_hoja": pistoleo.hoja_ruta.codigo if pistoleo.hoja_ruta else None,
                }
        if incidencia_ids:
            incidencias = self.db.query(Incidencia).filter(Incidencia.id.in_(incidencia_ids)).all()
            for incidencia in incidencias:
                refs[("INCIDENCIA", incidencia.id)] = {
                    "tipo": incidencia.tipo,
                    "estado": incidencia.estado,
                    "codigo_bulto": incidencia.bulto.codigo if incidencia.bulto else None,
                    "codigo_hoja": incidencia.hoja_ruta.codigo if incidencia.hoja_ruta else None,
                }
        if reasignacion_ids:
            reasignaciones = self.db.query(Reasignacion).filter(Reasignacion.id.in_(reasignacion_ids)).all()
            for reasignacion in reasignaciones:
                refs[("REASIGNACION", reasignacion.id)] = {
                    "codigo_bulto": reasignacion.bulto.codigo if reasignacion.bulto else None,
                    "codigo_hoja_origen": reasignacion.hoja_origen.codigo if reasignacion.hoja_origen else None,
                    "codigo_hoja_destino": reasignacion.hoja_destino.codigo if reasignacion.hoja_destino else None,
                }
        if hoja_ids:
            hojas = self.db.query(HojaRuta).filter(HojaRuta.id.in_(hoja_ids)).all()
            for hoja in hojas:
                refs[("HOJA_RUTA", hoja.id)] = {"codigo": hoja.codigo, "codigo_hoja": hoja.codigo}

        return refs
