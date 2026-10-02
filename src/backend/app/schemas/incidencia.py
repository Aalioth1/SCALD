from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidenciaCreate(BaseModel):
    tipo: str = Field(..., min_length=2, max_length=60)
    hoja_ruta_id: int | None = None
    bulto_id: int | None = None
    observaciones: str | None = None
    nueva_hoja_ruta_id: int | None = None


class IncidenciaResolution(BaseModel):
    observaciones: str | None = Field(default=None, max_length=500)


class IncidenciaEleccion(BaseModel):
    accion: Literal["ELIMINAR_PISTOLEO", "ANADIR_BULTO"]


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
