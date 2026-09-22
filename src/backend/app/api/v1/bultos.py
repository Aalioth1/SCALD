from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.bulto import BultoCreate, BultoOut
from app.services.bulto_service import BultoService

router = APIRouter(prefix="/api/v1/bultos", tags=["bultos"])


@router.post("", response_model=BultoOut, status_code=status.HTTP_201_CREATED)
def create_bulto(
    payload: BultoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    return BultoService(db).create(payload)


@router.get("", response_model=list[BultoOut])
def list_bultos(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return BultoService(db).get_all()


@router.get("/{bulto_id}", response_model=BultoOut)
def get_bulto(bulto_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return BultoService(db).get_by_id(bulto_id)
