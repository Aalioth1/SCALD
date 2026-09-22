from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.bulto_repository import BultoRepository
from app.repositories.hoja_ruta_repository import HojaRutaRepository
from app.schemas.bulto import BultoCreate


class BultoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BultoRepository(db)
        self.hoja_repository = HojaRutaRepository(db)

    def create(self, payload: BultoCreate):
        hoja = self.hoja_repository.get_by_id(payload.hoja_ruta_id)
        if not hoja:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        existing = self.repository.get_by_codigo_and_hoja(payload.codigo.upper(), payload.hoja_ruta_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El bulto ya existe en la hoja de ruta")
        data = payload.model_dump()
        data["codigo"] = data["codigo"].upper()
        return self.repository.create(data)

    def get_all(self):
        return self.repository.get_all()

    def get_by_id(self, bulto_id: int):
        bulto = self.repository.get_by_id(bulto_id)
        if not bulto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulto no encontrado")
        return bulto
