import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HojaRutaCreate(BaseModel):
    codigo: str = Field(..., min_length=5, max_length=50)
    tipo: Literal["HRD", "HRE"]
    fecha: date
    ruta: str = Field(..., min_length=2, max_length=200)
    transporte: str | None = None
    cantidad_declarada: int = Field(..., ge=0)
    estado: Literal["ACTIVA", "INACTIVA", "CERRADA"] = "ACTIVA"

    @field_validator("codigo")
    @classmethod
    def validate_codigo(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not re.fullmatch(r"HR[DE]-\d{4}-\d+", cleaned):
            raise ValueError("Formato de hoja de ruta inválido")
        return cleaned

    @model_validator(mode="after")
    def validate_tipo_codigo(self):
        if not self.codigo.startswith(self.tipo + "-"):
            raise ValueError("El tipo no coincide con el prefijo del código")
        return self


class HojaRutaUpdate(HojaRutaCreate):
    pass


class HojaRutaOut(BaseModel):
    id: int
    codigo: str
    tipo: str
    fecha: date
    ruta: str
    transporte: str | None = None
    cantidad_declarada: int
    estado: str
    activo: bool = True

    model_config = {"from_attributes": True}
