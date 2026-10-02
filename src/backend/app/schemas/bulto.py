from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BultoCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=100)
    hoja_ruta_id: int
    estado: Literal["PENDIENTE", "OK", "FALTANTE", "DUPLICADO", "SIN LISTA", "SIN HOJA", "REASIGNADO"] = "PENDIENTE"
    pistoleado: bool = False
    fecha: date | None = None
    info_adicional: str | None = None

    @field_validator("codigo")
    @classmethod
    def normalize_codigo(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_state(self):
        if self.pistoleado and self.estado == "PENDIENTE":
            raise ValueError("Un bulto pistoleado no puede permanecer PENDIENTE")
        return self


class BultoOut(BaseModel):
    id: int
    usuario_id: int
    codigo: str
    hoja_ruta_id: int
    estado: str
    pistoleado: bool
    fecha: date | None = None
    info_adicional: str | None = None

    model_config = {"from_attributes": True}
