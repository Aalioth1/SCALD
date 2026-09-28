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
    repository = BultoRepository(db)
    codigo = payload.codigo_bulto.strip().upper()
    bulto = repository.get_by_codigo_and_hoja(codigo, payload.hoja_ruta_id)
    bulto_en_otra_hoja = None
    if bulto is None and payload.hoja_ruta_id is not None:
        bulto_en_otra_hoja = repository.get_by_codigo(codigo)
    if bulto is None and payload.hoja_ruta_id is None:
        bulto = repository.get_by_codigo(codigo)

    auditoria = AuditoriaService(db)
    pistoleo = auditoria.registrar_pistoleo(
        codigo_bulto=codigo,
        hoja_ruta_id=payload.hoja_ruta_id,
        usuario_id=current_user.id,
        bulto=bulto,
        bulto_en_otra_hoja=bulto_en_otra_hoja,
    )
    return pistoleo
