from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.importacion import ImportacionResponse
from app.services.importacion_service import ImportacionService

router = APIRouter(prefix="/api/v1/importaciones", tags=["importaciones"])


@router.post("/hojas-ruta", response_model=ImportacionResponse)
async def importar_hojas_ruta(
    archivos: list[UploadFile] = File(..., min_length=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "AUDITOR")),
):
    payloads = [
        (archivo.filename or "archivo.pdf", archivo.content_type, await archivo.read())
        for archivo in archivos
    ]
    return ImportacionService(db).importar(payloads, current_user.id)
