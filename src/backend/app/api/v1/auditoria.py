from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.auditoria import AuditoriaOut
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoria"])


@router.get("", response_model=list[AuditoriaOut])
def listar_auditoria(
    entidad: str | None = Query(default=None),
    limite: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return AuditoriaService(db).listar_registros(entidad, limite)