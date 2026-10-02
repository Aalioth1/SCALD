from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.pistoleo import Pistoleo
from app.repositories.bulto_repository import BultoRepository
from app.repositories.hoja_ruta_repository import HojaRutaRepository
from app.schemas.pistoleo import PistoleoCreate, PistoleoOut
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/api/v1/pistoleos", tags=["pistoleos"])


@router.get("", response_model=list[PistoleoOut])
def listar_pistoleos(
    limite: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    return (
        db.query(Pistoleo)
        .filter(Pistoleo.usuario_id == current_user.id)
        .order_by(Pistoleo.fecha_hora.desc())
        .limit(limite)
        .all()
    )


@router.post("", response_model=PistoleoOut, status_code=status.HTTP_201_CREATED)
def registrar_pistoleo(
    payload: PistoleoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    repository = BultoRepository(db)
    codigo = payload.codigo_bulto.strip().upper()
    if payload.hoja_ruta_id is not None and HojaRutaRepository(db).get_by_id(payload.hoja_ruta_id, current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
    bulto = repository.get_by_codigo_and_hoja(codigo, payload.hoja_ruta_id, current_user.id)
    bulto_en_otra_hoja = None
    if bulto is None and payload.hoja_ruta_id is not None:
        bulto_en_otra_hoja = repository.get_by_codigo(codigo, current_user.id)
    if bulto is None and payload.hoja_ruta_id is None:
        bulto = repository.get_by_codigo(codigo, current_user.id)

    auditoria = AuditoriaService(db)
    pistoleo = auditoria.registrar_pistoleo(
        codigo_bulto=codigo,
        hoja_ruta_id=payload.hoja_ruta_id,
        usuario_id=current_user.id,
        bulto=bulto,
        bulto_en_otra_hoja=bulto_en_otra_hoja,
    )
    return pistoleo
