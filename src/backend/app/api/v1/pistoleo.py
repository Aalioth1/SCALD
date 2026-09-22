from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.repositories.bulto_repository import BultoRepository
from app.schemas.pistoleo import PistoleoCreate, PistoleoOut
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/api/v1/pistoleos", tags=["pistoleos"])


@router.post("", response_model=PistoleoOut, status_code=status.HTTP_201_CREATED)
def registrar_pistoleo(
    payload: PistoleoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    bulto = BultoRepository(db).get_by_codigo(payload.codigo_bulto)
    auditoria = AuditoriaService(db)
    pistoleo = auditoria.registrar_pistoleo(
        codigo_bulto=payload.codigo_bulto,
        hoja_ruta_id=payload.hoja_ruta_id,
        usuario_id=current_user.id,
        bulto=bulto,
    )
    return pistoleo
