from datetime import date

from pydantic import BaseModel, Field, field_validator


class HojaRutaCreate(BaseModel):
    codigo: str = Field(..., min_length=5, max_length=50)
    tipo: str = Field(..., min_length=2, max_length=20)
    fecha: date
    ruta: str = Field(..., min_length=2, max_length=200)
    transporte: str | None = None
    cantidad_declarada: int = Field(..., ge=0)
    estado: str = "ACTIVA"

    @field_validator("codigo")
    @classmethod
    def validate_codigo(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if "-" not in cleaned:
            raise ValueError("El código debe seguir el formato TIPO-AÑO-NÚMERO")
        tipo, anio, numero = cleaned.split("-", 2)
        if not tipo or not anio.isdigit() or not numero.isdigit():
            raise ValueError("Formato de hoja de ruta inválido")
        return cleaned


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
