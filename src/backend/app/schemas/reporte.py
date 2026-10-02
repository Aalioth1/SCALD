from datetime import date, datetime

from pydantic import BaseModel


class ReporteResumen(BaseModel):
    total_hojas: int
    total_bultos_esperados: int
    total_pistoleos: int
    ok: int
    faltantes: int
    duplicados: int
    sin_lista_esperada: int
    no_pertenece: int
    reasignados: int
    incidencias_pendientes: int
    incidencias_regularizadas: int


class ReporteHojaRuta(ReporteResumen):
    hoja_ruta_id: int
    codigo: str
    tipo: str
    fecha: date
    ruta: str
    estado: str


class ReporteOperativoHoja(BaseModel):
    codigo: str
    tipo: str
    registro: date
    ruta: str
    transporte: str | None = None
    estado: str
    esperados: int
    pistoleados: int
    faltantes: int
    incidencias: int


class ReporteOperativoFaltante(BaseModel):
    codigo: str
    hoja: str
    ruta: str
    registro: date


class ReporteOperativoIncidencia(BaseModel):
    registro: datetime
    hoja: str
    bulto: str
    tipo: str
    estado: str
    observaciones: str


class ReporteOperativo(BaseModel):
    resumen: ReporteResumen
    hojas: list[ReporteOperativoHoja]
    faltantes: list[ReporteOperativoFaltante]
    incidencias: list[ReporteOperativoIncidencia]
    pendientes: int
    regularizadas: int


class ReporteIncidencia(BaseModel):
    id: int
    tipo: str
    estado: str
    hoja_ruta_id: int | None = None
    bulto_id: int | None = None
    usuario_id: int | None = None
    fecha_creacion: datetime
    fecha_resolucion: datetime | None = None
    observaciones: str | None = None

    model_config = {"from_attributes": True}
