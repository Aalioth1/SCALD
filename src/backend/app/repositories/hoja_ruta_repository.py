from sqlalchemy.orm import Session

from app.models.hoja_ruta import HojaRuta


class HojaRutaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_codigo(self, codigo: str) -> HojaRuta | None:
        return self.db.query(HojaRuta).filter(HojaRuta.codigo == codigo).first()

    def get_all(self):
        return self.db.query(HojaRuta).filter(HojaRuta.activo.is_(True)).all()

    def get_by_id(self, hoja_id: int) -> HojaRuta | None:
        return self.db.query(HojaRuta).filter(HojaRuta.id == hoja_id, HojaRuta.activo.is_(True)).first()

    def create(self, payload: dict) -> HojaRuta:
        hoja = HojaRuta(**payload)
        self.db.add(hoja)
        self.db.commit()
        self.db.refresh(hoja)
        return hoja

    def update(self, hoja: HojaRuta, payload: dict) -> HojaRuta:
        for key, value in payload.items():
            setattr(hoja, key, value)
        self.db.commit()
        self.db.refresh(hoja)
        return hoja

    def delete(self, hoja: HojaRuta) -> None:
        hoja.activo = False
        self.db.commit()
