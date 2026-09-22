from datetime import datetime

from pydantic import BaseModel, Field


class IncidenciaCreate(BaseModel):
    tipo: str = Field(..., min_length=2, max_length=60)
    hoja_ruta_id: int | None = None
    bulto_id: int | None = None
    observaciones: str | None = None
    nueva_hoja_ruta_id: int | None = None


class IncidenciaOut(BaseModel):
    id: int
    tipo: str
    hoja_ruta_id: int | None = None
    bulto_id: int | None = None
    usuario_id: int | None = None
    estado: str
    observaciones: str | None = None
    nueva_hoja_ruta_id: int | None = None
    fecha_creacion: datetime
    fecha_resolucion: datetime | None = None

    model_config = {"from_attributes": True}
