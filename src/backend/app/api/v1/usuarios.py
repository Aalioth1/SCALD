from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.usuario import UsuarioActividadOut, UsuarioAdminOut, UsuarioCreate, UsuarioEstado, UsuarioUpdate
from app.services.usuario_admin_service import UsuarioAdminService

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioAdminOut])
def listar_usuarios(db: Session = Depends(get_db), current_user=Depends(require_roles("ADMIN"))):
    return UsuarioAdminService(db).listar()


@router.post("", response_model=UsuarioAdminOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).crear(payload)


@router.get("/{usuario_id}/actividad", response_model=UsuarioActividadOut)
def actividad_usuario(
    usuario_id: int,
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).actividad(usuario_id, fecha_desde, fecha_hasta)


@router.put("/{usuario_id}", response_model=UsuarioAdminOut)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).actualizar(usuario_id, payload, current_user.id)


@router.patch("/{usuario_id}/estado", response_model=UsuarioAdminOut)
def cambiar_estado_usuario(
    usuario_id: int,
    payload: UsuarioEstado,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).cambiar_estado(usuario_id, payload, current_user.id)


@router.post("/{usuario_id}/archivar")
def archivar_registros(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).archivar_registros(usuario_id)


@router.delete("/{usuario_id}/hojas/{hoja_id}")
def eliminar_registros_hoja(
    usuario_id: int,
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).eliminar_registros_hoja(usuario_id, hoja_id)


@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return UsuarioAdminService(db).eliminar(usuario_id, current_user.id)
