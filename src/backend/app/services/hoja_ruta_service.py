from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.repositories.hoja_ruta_repository import HojaRutaRepository
from app.schemas.hoja_ruta import HojaRutaCreate, HojaRutaOut, HojaRutaUpdate


def cerrar_hoja_si_completa(db: Session, hoja_id: int | None) -> None:
    if hoja_id is None:
        return
    hoja = db.query(HojaRuta).filter(HojaRuta.id == hoja_id, HojaRuta.situacion == "VIGENTE").first()
    if hoja is None or hoja.estado == "CERRADA":
        return
    total = db.query(Bulto).filter(Bulto.hoja_ruta_id == hoja.id).count()
    if total == 0:
        return
    pendientes = db.query(Bulto).filter(Bulto.hoja_ruta_id == hoja.id, Bulto.pistoleado.is_(False)).count()
    if pendientes == 0:
        hoja.estado = "CERRADA"


class HojaRutaService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = HojaRutaRepository(db)

    def create(self, payload: HojaRutaCreate, usuario_id: int):
        if self.repository.get_by_codigo(payload.codigo.upper(), usuario_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La hoja de ruta ya existe")
        data = payload.model_dump()
        data["codigo"] = data["codigo"].upper()
        data["usuario_id"] = usuario_id
        data["created_at"] = date.today()
        return self._to_out(self.repository.create(data))

    def get_all(self, usuario_id: int):
        hojas = self.repository.get_all(usuario_id)
        counts = self._contar_bultos([hoja.id for hoja in hojas])
        return [self._to_out(hoja, counts) for hoja in hojas]

    def get_by_id(self, hoja_id: int, usuario_id: int):
        return self._to_out(self._obtener(hoja_id, usuario_id))

    def update(self, hoja_id: int, payload: HojaRutaUpdate, usuario_id: int):
        hoja = self._obtener(hoja_id, usuario_id)
        codigo = payload.codigo.upper()
        if hoja.codigo != codigo and self.repository.get_by_codigo(codigo, usuario_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código ya está asociado a otra hoja")
        data = payload.model_dump()
        data["codigo"] = codigo
        return self._to_out(self.repository.update(hoja, data))

    def _contar_bultos(self, hoja_ids: list[int]) -> dict[int, int]:
        if not hoja_ids:
            return {}
        rows = (
            self.db.query(Bulto.hoja_ruta_id, func.count(Bulto.id))
            .filter(Bulto.hoja_ruta_id.in_(hoja_ids))
            .group_by(Bulto.hoja_ruta_id)
            .all()
        )
        return {hoja_id: total for hoja_id, total in rows}

    def _to_out(self, hoja: HojaRuta, counts: dict[int, int] | None = None) -> HojaRutaOut:
        cantidad = (counts if counts is not None else self._contar_bultos([hoja.id])).get(hoja.id, 0)
        return HojaRutaOut.model_validate(hoja).model_copy(update={"cantidad_bultos": cantidad})

    def delete(self, hoja_id: int, usuario_id: int):
        hoja = self._obtener(hoja_id, usuario_id)
        self.repository.delete(hoja)
        return {"message": "Hoja de ruta eliminada"}

    def _obtener(self, hoja_id: int, usuario_id: int) -> HojaRuta:
        hoja = self.repository.get_by_id(hoja_id, usuario_id)
        if not hoja:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        return hoja
