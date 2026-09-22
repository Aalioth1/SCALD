from datetime import date

from pydantic import BaseModel, Field


class BultoCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=100)
    hoja_ruta_id: int
    estado: str = "PENDIENTE"
    pistoleado: bool = False
    fecha: date | None = None
    info_adicional: str | None = None


class BultoOut(BaseModel):
    id: int
    codigo: str
    hoja_ruta_id: int
    estado: str
    pistoleado: bool
    fecha: date | None = None
    info_adicional: str | None = None

    model_config = {"from_attributes": True}
