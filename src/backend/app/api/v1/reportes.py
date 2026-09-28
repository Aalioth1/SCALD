from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.reporte import ReporteHojaRuta, ReporteIncidencia, ReporteResumen
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])


@router.get("/resumen", response_model=ReporteResumen)
def resumen(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    hoja_ruta_id: int | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReporteService(db).resumen(fecha_desde, fecha_hasta, hoja_ruta_id, usuario_id)


@router.get("/hoja-ruta/{hoja_ruta_id}", response_model=ReporteHojaRuta)
def detalle_hoja(
    hoja_ruta_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReporteService(db).detalle_hoja(hoja_ruta_id)


@router.get("/incidencias", response_model=list[ReporteIncidencia])
def reporte_incidencias(
    estado: str | None = Query(default=None),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    hoja_ruta_id: int | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReporteService(db).incidencias(estado, fecha_desde, fecha_hasta, hoja_ruta_id, usuario_id)
