from sqlalchemy.orm import Session

from app.models.bulto import Bulto


class BultoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_codigo_and_hoja(self, codigo: str, hoja_ruta_id: int | None = None) -> Bulto | None:
        query = self.db.query(Bulto).filter(Bulto.codigo == codigo)
        if hoja_ruta_id is not None:
            query = query.filter(Bulto.hoja_ruta_id == hoja_ruta_id)
        return query.first()

    def get_by_codigo(self, codigo: str) -> Bulto | None:
        return self.db.query(Bulto).filter(Bulto.codigo == codigo).first()

    def create(self, payload: dict) -> Bulto:
        bulto = Bulto(**payload)
        self.db.add(bulto)
        self.db.commit()
        self.db.refresh(bulto)
        return bulto

    def get_all(self):
        return self.db.query(Bulto).all()

    def get_by_id(self, bulto_id: int) -> Bulto | None:
        return self.db.query(Bulto).filter(Bulto.id == bulto_id).first()

    def update(self, bulto: Bulto, payload: dict) -> Bulto:
        for key, value in payload.items():
            setattr(bulto, key, value)
        self.db.commit()
        self.db.refresh(bulto)
        return bulto
