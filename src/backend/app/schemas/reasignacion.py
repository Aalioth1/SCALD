from datetime import datetime

from pydantic import BaseModel, Field


class ReasignacionCreate(BaseModel):
    bulto_id: int
    hoja_destino_id: int
    incidencia_id: int | None = None
    motivo: str = Field(..., min_length=3, max_length=200)
    observaciones: str | None = Field(default=None, max_length=500)


class ReasignacionOut(BaseModel):
    id: int
    bulto_id: int
    hoja_origen_id: int
    hoja_destino_id: int
    incidencia_id: int | None = None
    usuario_id: int
    fecha_hora: datetime
    motivo: str
    observaciones: str | None = None
    estado: str

    model_config = {"from_attributes": True}