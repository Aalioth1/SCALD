from datetime import date

from pydantic import BaseModel


class ImportacionArchivoResultado(BaseModel):
    archivo: str
    exitoso: bool
    hoja_ruta: str | None = None
    bultos_creados: int = 0
    bultos_existentes: int = 0
    error: str | None = None


class ImportacionResponse(BaseModel):
    archivos_procesados: int
    archivos_exitosos: int
    archivos_fallidos: int
    hojas_creadas: int
    hojas_actualizadas: int
    bultos_creados: int
    resultados: list[ImportacionArchivoResultado]
