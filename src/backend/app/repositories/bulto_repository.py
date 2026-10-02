from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta


class BultoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_codigo_and_hoja(self, codigo: str, hoja_ruta_id: int | None, usuario_id: int) -> Bulto | None:
        query = self.db.query(Bulto).filter(Bulto.codigo == codigo, Bulto.usuario_id == usuario_id)
        if hoja_ruta_id is not None:
            query = query.filter(Bulto.hoja_ruta_id == hoja_ruta_id)
        return query.first()

    def get_by_codigo(self, codigo: str, usuario_id: int) -> Bulto | None:
        return (
            self.db.query(Bulto)
            .join(HojaRuta, Bulto.hoja_ruta_id == HojaRuta.id)
            .filter(
                Bulto.codigo == codigo,
                Bulto.usuario_id == usuario_id,
                HojaRuta.situacion == "VIGENTE",
            )
            .first()
        )

    def create(self, payload: dict) -> Bulto:
        bulto = Bulto(**payload)
        self.db.add(bulto)
        self.db.commit()
        self.db.refresh(bulto)
        return bulto

    def get_all(self, usuario_id: int):
        return (
            self.db.query(Bulto)
            .join(HojaRuta, Bulto.hoja_ruta_id == HojaRuta.id)
            .filter(Bulto.usuario_id == usuario_id, HojaRuta.situacion == "VIGENTE")
            .all()
        )

    def get_by_id(self, bulto_id: int, usuario_id: int) -> Bulto | None:
        return (
            self.db.query(Bulto)
            .filter(Bulto.id == bulto_id, Bulto.usuario_id == usuario_id)
            .first()
        )

    def update(self, bulto: Bulto, payload: dict) -> Bulto:
        for key, value in payload.items():
            setattr(bulto, key, value)
        self.db.commit()
        self.db.refresh(bulto)
        return bulto
