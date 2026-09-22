from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.hoja_ruta_repository import HojaRutaRepository
from app.schemas.hoja_ruta import HojaRutaCreate, HojaRutaUpdate


class HojaRutaService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = HojaRutaRepository(db)

    def create(self, payload: HojaRutaCreate):
        if self.repository.get_by_codigo(payload.codigo.upper()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La hoja de ruta ya existe")
        data = payload.model_dump()
        data["codigo"] = data["codigo"].upper()
        return self.repository.create(data)

    def get_all(self):
        return self.repository.get_all()

    def get_by_id(self, hoja_id: int):
        hoja = self.repository.get_by_id(hoja_id)
        if not hoja:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        return hoja

    def update(self, hoja_id: int, payload: HojaRutaUpdate):
        hoja = self.get_by_id(hoja_id)
        if hoja.codigo != payload.codigo.upper() and self.repository.get_by_codigo(payload.codigo.upper()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código ya está asociado a otra hoja")
        data = payload.model_dump()
        data["codigo"] = data["codigo"].upper()
        return self.repository.update(hoja, data)

    def delete(self, hoja_id: int):
        hoja = self.get_by_id(hoja_id)
        self.repository.delete(hoja)
        return {"message": "Hoja de ruta eliminada"}
