from datetime import datetime

from pydantic import BaseModel, Field


class PistoleoCreate(BaseModel):
    codigo_bulto: str = Field(..., min_length=3, max_length=100)
    hoja_ruta_id: int | None = None
    observacion: str | None = None


class PistoleoOut(BaseModel):
    id: int
    codigo_bulto: str
    hoja_ruta_id: int | None = None
    bulto_id: int | None = None
    usuario_id: int
    fecha_hora: datetime
    estado: str
    observacion: str | None = None

    model_config = {"from_attributes": True}
