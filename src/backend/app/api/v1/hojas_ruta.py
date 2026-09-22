from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.hoja_ruta import HojaRutaCreate, HojaRutaOut, HojaRutaUpdate
from app.services.hoja_ruta_service import HojaRutaService

router = APIRouter(prefix="/api/v1/hojas-ruta", tags=["hojas_ruta"])


@router.post("", response_model=HojaRutaOut, status_code=status.HTTP_201_CREATED)
def create_hoja_ruta(
    payload: HojaRutaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    service = HojaRutaService(db)
    return service.create(payload)


@router.get("", response_model=list[HojaRutaOut])
def list_hojas_ruta(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return HojaRutaService(db).get_all()


@router.get("/{hoja_id}", response_model=HojaRutaOut)
def get_hoja_ruta(hoja_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return HojaRutaService(db).get_by_id(hoja_id)


@router.put("/{hoja_id}", response_model=HojaRutaOut)
def update_hoja_ruta(
    hoja_id: int,
    payload: HojaRutaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return HojaRutaService(db).update(hoja_id, payload)


@router.delete("/{hoja_id}")
def delete_hoja_ruta(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return HojaRutaService(db).delete(hoja_id)
