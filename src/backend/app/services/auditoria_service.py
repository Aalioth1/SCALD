from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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
            if estado != "OK":
                self._crear_incidencia_en_transaccion(
                    tipo=estado,
                    hoja_ruta_id=hoja_efectiva,
                    bulto=incidencia_bulto,
                    usuario_id=usuario_id,
                    observaciones=observacion,
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
