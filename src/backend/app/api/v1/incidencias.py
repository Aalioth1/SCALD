from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.incidencia import IncidenciaOut, IncidenciaResolution
from app.services.incidencia_service import IncidenciaService

router = APIRouter(prefix="/api/v1/incidencias", tags=["incidencias"])


@router.get("", response_model=list[IncidenciaOut])
def listar_incidencias(
    estado: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return IncidenciaService(db).listar(estado)


@router.get("/{incidencia_id}", response_model=IncidenciaOut)
def obtener_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return IncidenciaService(db).obtener(incidencia_id)


@router.patch("/{incidencia_id}/regularizar", response_model=IncidenciaOut)
def regularizar_incidencia(
    incidencia_id: int,
    payload: IncidenciaResolution,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    return IncidenciaService(db).resolver(
        incidencia_id,
        current_user.id,
        payload.observaciones,
    )


@router.patch("/{incidencia_id}/anular", response_model=IncidenciaOut)
def anular_incidencia(
    incidencia_id: int,
    payload: IncidenciaResolution,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    return IncidenciaService(db).anular(
        incidencia_id,
        current_user.id,
        payload.observaciones,
    )