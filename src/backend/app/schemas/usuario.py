from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    rol: Literal["ADMIN", "AUDITOR"]


class UsuarioUpdate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str | None = Field(default=None, min_length=8)
    rol: Literal["ADMIN", "AUDITOR"]


class UsuarioEstado(BaseModel):
    activo: bool


class UsuarioAdminOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    rol: str
    activo: bool


class HojaUsuarioResumen(BaseModel):
    id: int
    codigo: str
    fecha: date
    fecha_registro: date
    ruta: str
    estado: str
    situacion: str


class PistoleoUsuarioResumen(BaseModel):
    id: int
    codigo_bulto: str
    estado: str
    fecha_hora: datetime
    observacion: str | None = None


class FaltanteUsuarioResumen(BaseModel):
    id: int
    codigo: str
    hoja: str


class IncidenciaUsuarioResumen(BaseModel):
    id: int
    hoja: str
    bulto: str
    tipo: str
    estado: str


class EventoUsuario(BaseModel):
    id: int
    entidad: str
    accion: str
    detalle: str
    fecha_hora: datetime


class UsuarioActividadOut(BaseModel):
    usuario_id: int
    nombre: str
    apellido: str
    email: str
    rol: str
    activo: bool
    total_hojas: int
    total_bultos: int
    total_pistoleos: int
    total_incidencias: int
    bultos_esperados: int
    bultos_pistoleados: int
    hojas: list[HojaUsuarioResumen]
    pistoleos: list[PistoleoUsuarioResumen]
    faltantes: list[FaltanteUsuarioResumen]
    incidencias: list[IncidenciaUsuarioResumen]
    eventos: list[EventoUsuario]
