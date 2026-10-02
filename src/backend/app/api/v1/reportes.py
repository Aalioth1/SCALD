from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.reporte import ReporteHojaRuta, ReporteIncidencia, ReporteOperativo, ReporteResumen
from app.services.reporte_pdf import PdfNoDisponible
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
    _validar_usuario(usuario_id, current_user.id)
    _validar_rango(fecha_desde, fecha_hasta)
    return ReporteService(db).resumen(fecha_desde, fecha_hasta, hoja_ruta_id, current_user.id)


@router.get("/hoja-ruta/{hoja_ruta_id}", response_model=ReporteHojaRuta)
def detalle_hoja(
    hoja_ruta_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReporteService(db).detalle_hoja(hoja_ruta_id, current_user.id)


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
    _validar_usuario(usuario_id, current_user.id)
    _validar_rango(fecha_desde, fecha_hasta)
    return ReporteService(db).incidencias(estado, fecha_desde, fecha_hasta, hoja_ruta_id, current_user.id)


@router.get("/operativo", response_model=ReporteOperativo)
def operativo(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validar_rango(fecha_desde, fecha_hasta)
    return ReporteService(db).vista_operativa(fecha_desde, fecha_hasta, current_user.id)


@router.get("/pdf")
def pdf_operativo(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validar_rango(fecha_desde, fecha_hasta)
    objetivo = _usuario_objetivo(usuario_id, current_user, db)
    autor = f"{objetivo.nombre} {objetivo.apellido}".strip() or objetivo.email
    try:
        contenido, nombre = ReporteService(db).pdf_operativo(
            fecha_desde,
            fecha_hasta,
            objetivo.id,
            autor,
        )
    except PdfNoDisponible as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


def _validar_rango(fecha_desde: date | None, fecha_hasta: date | None) -> None:
    if fecha_desde is not None and fecha_hasta is not None and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha inicial no puede ser posterior a la final",
        )


def _usuario_objetivo(usuario_id: int | None, current_user: Usuario, db: Session) -> Usuario:
    if usuario_id is None or usuario_id == current_user.id:
        return current_user
    rol = current_user.rol.nombre if current_user.rol else None
    if rol != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede consultar registros de otro usuario",
        )
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def _validar_usuario(usuario_id: int | None, current_user_id: int) -> None:
    if usuario_id is not None and usuario_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede consultar registros de otro usuario",
        )
