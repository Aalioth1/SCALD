from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.reasignacion import ReasignacionCreate, ReasignacionOut
from app.services.reasignacion_service import ReasignacionService

router = APIRouter(prefix="/api/v1/reasignaciones", tags=["reasignaciones"])


@router.post("", response_model=ReasignacionOut, status_code=status.HTTP_201_CREATED)
def crear_reasignacion(
    payload: ReasignacionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    return ReasignacionService(db).reasignar(payload, current_user.id)
