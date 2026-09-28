from datetime import datetime

from pydantic import BaseModel


class AuditoriaOut(BaseModel):
    id: int
    usuario_id: int | None = None
    entidad: str
    entidad_id: int | None = None
    accion: str
    datos_anteriores: dict | None = None
    datos_nuevos: dict | None = None
    fecha_hora: datetime
    origen: str
    correlation_id: str | None = None

    model_config = {"from_attributes": True}
