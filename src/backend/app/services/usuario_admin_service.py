from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.auditoria import Auditoria
from app.models.bulto import Bulto
from app.models.hoja_ruta import HojaRuta
from app.models.incidencia import Incidencia
from app.models.pistoleo import Pistoleo
from app.models.reasignacion import Reasignacion
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.services.reporte_pdf import _estado_incidencia
from app.schemas.usuario import (
    EventoUsuario,
    FaltanteUsuarioResumen,
    HojaUsuarioResumen,
    IncidenciaUsuarioResumen,
    PistoleoUsuarioResumen,
    UsuarioActividadOut,
    UsuarioAdminOut,
    UsuarioCreate,
    UsuarioEstado,
    UsuarioUpdate,
)


class UsuarioAdminService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuarioRepository(db)

    def listar(self) -> list[UsuarioAdminOut]:
        return [self._to_out(user) for user in self.repository.list_all()]

    def crear(self, payload: UsuarioCreate) -> UsuarioAdminOut:
        if self.repository.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")
        user = self.repository.create(
            nombre=payload.nombre.strip(),
            apellido=payload.apellido.strip(),
            email=payload.email,
            password_hash=hash_password(payload.password),
            rol=self._rol(payload.rol),
            activo=True,
        )
        return self._to_out(user)

    def actualizar(self, usuario_id: int, payload: UsuarioUpdate, actor_id: int) -> UsuarioAdminOut:
        user = self._obtener(usuario_id)
        existing = self.repository.get_by_email(payload.email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")
        if user.id == actor_id and payload.rol != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puede quitarse el permiso de administrador",
            )
        if self._es_admin_activo(user) and payload.rol != "ADMIN":
            self._exigir_otro_admin(user.id)
        user.nombre = payload.nombre.strip()
        user.apellido = payload.apellido.strip()
        user.email = payload.email
        user.rol = self._rol(payload.rol)
        if payload.password:
            user.password_hash = hash_password(payload.password)
        return self._to_out(self.repository.save(user))

    def cambiar_estado(self, usuario_id: int, payload: UsuarioEstado, actor_id: int) -> UsuarioAdminOut:
        user = self._obtener(usuario_id)
        if user.id == actor_id and not payload.activo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puede desactivar su propia cuenta",
            )
        if self._es_admin_activo(user) and not payload.activo:
            self._exigir_otro_admin(user.id)
        user.activo = payload.activo
        return self._to_out(self.repository.save(user))

    def archivar_registros(self, usuario_id: int) -> dict[str, int]:
        user = self._obtener(usuario_id)
        hojas = (
            self.db.query(HojaRuta)
            .filter(HojaRuta.usuario_id == user.id, HojaRuta.situacion == "VIGENTE")
            .all()
        )
        for hoja in hojas:
            hoja.situacion = "ARCHIVADO"
        self.db.commit()
        return {"archivadas": len(hojas)}

    def eliminar_registros_hoja(self, usuario_id: int, hoja_id: int) -> dict[str, str]:
        user = self._obtener(usuario_id)
        hoja = (
            self.db.query(HojaRuta)
            .filter(HojaRuta.id == hoja_id, HojaRuta.usuario_id == user.id)
            .first()
        )
        if hoja is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hoja de ruta no encontrada")
        if hoja.situacion == "ELIMINADO":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Los registros de esta hoja ya fueron eliminados")
        bulto_ids = [item.id for item in self.db.query(Bulto.id).filter(Bulto.hoja_ruta_id == hoja.id).all()]
        reasignaciones = [Reasignacion.hoja_origen_id == hoja.id, Reasignacion.hoja_destino_id == hoja.id]
        incidencias = [Incidencia.hoja_ruta_id == hoja.id, Incidencia.nueva_hoja_ruta_id == hoja.id]
        pistoleos = [Pistoleo.hoja_ruta_id == hoja.id]
        if bulto_ids:
            reasignaciones.append(Reasignacion.bulto_id.in_(bulto_ids))
            incidencias.append(Incidencia.bulto_id.in_(bulto_ids))
            pistoleos.append(Pistoleo.bulto_id.in_(bulto_ids))
        self.db.query(Reasignacion).filter(or_(*reasignaciones)).delete(synchronize_session=False)
        self.db.query(Incidencia).filter(or_(*incidencias)).delete(synchronize_session=False)
        self.db.query(Pistoleo).filter(or_(*pistoleos)).delete(synchronize_session=False)
        self.db.query(Bulto).filter(Bulto.hoja_ruta_id == hoja.id).delete(synchronize_session=False)
        hoja.situacion = "ELIMINADO"
        self.db.add(
            Auditoria(
                usuario_id=user.id,
                entidad="HOJA_RUTA",
                entidad_id=hoja.id,
                accion="ELIMINAR_REGISTROS",
                datos_nuevos={"codigo": hoja.codigo},
            )
        )
        self.db.commit()
        return {"message": "Registros de la hoja eliminados"}

    def eliminar(self, usuario_id: int, actor_id: int) -> dict[str, str]:
        user = self._obtener(usuario_id)
        if user.id == actor_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No puede eliminar su propia cuenta")
        if self._es_admin_activo(user):
            self._exigir_otro_admin(user.id)
        if self._tiene_registros(user.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar: el usuario tiene registros. Desactívelo para quitarle el acceso",
            )
        try:
            self.repository.delete(user)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar: el usuario tiene registros. Desactívelo para quitarle el acceso",
            ) from exc
        return {"message": "Usuario eliminado"}

    def actividad(
        self,
        usuario_id: int,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> UsuarioActividadOut:
        user = self._obtener(usuario_id)
        hojas_base = self.db.query(HojaRuta).filter(HojaRuta.usuario_id == user.id, HojaRuta.activo.is_(True))
        if fecha_desde is not None:
            hojas_base = hojas_base.filter(HojaRuta.created_at >= fecha_desde)
        if fecha_hasta is not None:
            hojas_base = hojas_base.filter(HojaRuta.created_at <= fecha_hasta)
        hoja_ids = [row[0] for row in hojas_base.with_entities(HojaRuta.id).all()]
        hojas = hojas_base.order_by(HojaRuta.fecha.desc(), HojaRuta.id.desc()).limit(100).all()
        pistoleos = self.db.query(Pistoleo).filter(Pistoleo.usuario_id == user.id)
        faltantes = (
            self.db.query(Bulto, HojaRuta)
            .join(HojaRuta, Bulto.hoja_ruta_id == HojaRuta.id)
            .filter(
                Bulto.usuario_id == user.id,
                Bulto.pistoleado.is_(False),
                HojaRuta.usuario_id == user.id,
                HojaRuta.activo.is_(True),
                HojaRuta.situacion == "VIGENTE",
            )
        )
        incidencias = (
            self.db.query(Incidencia)
            .options(joinedload(Incidencia.hoja_ruta), joinedload(Incidencia.bulto))
            .filter(Incidencia.usuario_id == user.id)
        )
        if fecha_desde is not None or fecha_hasta is not None:
            if hoja_ids:
                pistoleos = pistoleos.filter(Pistoleo.hoja_ruta_id.in_(hoja_ids))
                faltantes = faltantes.filter(Bulto.hoja_ruta_id.in_(hoja_ids))
                incidencias = incidencias.filter(Incidencia.hoja_ruta_id.in_(hoja_ids))
            else:
                pistoleos = pistoleos.filter(False)
                faltantes = faltantes.filter(False)
                incidencias = incidencias.filter(False)
        pistoleos = pistoleos.order_by(Pistoleo.fecha_hora.desc()).limit(15).all()
        faltantes = faltantes.order_by(HojaRuta.codigo, Bulto.codigo).limit(100).all()
        incidencias = incidencias.order_by(Incidencia.fecha_creacion.desc()).limit(100).all()
        if hoja_ids:
            esperados = self.db.query(Bulto).filter(Bulto.usuario_id == user.id, Bulto.hoja_ruta_id.in_(hoja_ids)).count()
            listos = (
                self.db.query(Bulto)
                .filter(Bulto.usuario_id == user.id, Bulto.hoja_ruta_id.in_(hoja_ids), Bulto.pistoleado.is_(True))
                .count()
            )
        else:
            esperados = 0
            listos = 0
        eventos = (
            self.db.query(Auditoria)
            .filter(Auditoria.usuario_id == user.id)
            .order_by(Auditoria.fecha_hora.desc())
            .limit(20)
            .all()
        )
        return UsuarioActividadOut(
            usuario_id=user.id,
            nombre=user.nombre,
            apellido=user.apellido,
            email=user.email,
            rol=user.rol.nombre if user.rol else "",
            activo=user.activo,
            total_hojas=len(hoja_ids),
            total_bultos=esperados,
            total_pistoleos=self.db.query(Pistoleo).filter(Pistoleo.usuario_id == user.id, Pistoleo.hoja_ruta_id.in_(hoja_ids or [-1])).count(),
            total_incidencias=self.db.query(Incidencia).filter(Incidencia.usuario_id == user.id, Incidencia.hoja_ruta_id.in_(hoja_ids or [-1])).count(),
            bultos_esperados=esperados,
            bultos_pistoleados=listos,
            hojas=[
                HojaUsuarioResumen(
                    id=hoja.id,
                    codigo=hoja.codigo,
                    fecha=hoja.fecha,
                    fecha_registro=hoja.fecha_registro,
                    ruta=hoja.ruta,
                    estado=hoja.estado,
                    situacion=hoja.situacion,
                )
                for hoja in hojas
            ],
            pistoleos=[
                PistoleoUsuarioResumen(
                    id=item.id,
                    codigo_bulto=item.codigo_bulto,
                    estado=item.estado,
                    fecha_hora=item.fecha_hora,
                    observacion=item.observacion,
                )
                for item in pistoleos
            ],
            faltantes=[
                FaltanteUsuarioResumen(id=bulto.id, codigo=bulto.codigo, hoja=hoja.codigo)
                for bulto, hoja in faltantes
            ],
            incidencias=[
                IncidenciaUsuarioResumen(
                    id=item.id,
                    hoja=item.hoja_ruta.codigo if item.hoja_ruta else "—",
                    bulto=item.bulto.codigo if item.bulto else "—",
                    tipo=item.tipo,
                    estado=_estado_incidencia(item.estado),
                )
                for item in incidencias
            ],
            eventos=[
                EventoUsuario(
                    id=item.id,
                    entidad=item.entidad,
                    accion=item.accion,
                    detalle=self._detalle(item),
                    fecha_hora=item.fecha_hora,
                )
                for item in eventos
            ],
        )

    def _obtener(self, usuario_id: int) -> Usuario:
        user = self.repository.get_by_id(usuario_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    def _rol(self, nombre: str) -> Rol:
        rol = self.db.query(Rol).filter(Rol.nombre == nombre).first()
        if rol is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El permiso de acceso no existe")
        return rol

    def _es_admin_activo(self, user: Usuario) -> bool:
        return bool(user.activo and user.rol and user.rol.nombre == "ADMIN")

    def _exigir_otro_admin(self, usuario_id: int) -> None:
        otros = (
            self.db.query(Usuario)
            .join(Rol)
            .filter(Rol.nombre == "ADMIN", Usuario.activo.is_(True), Usuario.id != usuario_id)
            .count()
        )
        if otros == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Debe permanecer al menos un administrador activo",
            )

    def _tiene_registros(self, usuario_id: int) -> bool:
        totales = (
            self._contar(HojaRuta, HojaRuta.usuario_id == usuario_id),
            self._contar(Bulto, Bulto.usuario_id == usuario_id),
            self._contar(Pistoleo, Pistoleo.usuario_id == usuario_id),
            self._contar(Incidencia, Incidencia.usuario_id == usuario_id),
            self._contar(Auditoria, Auditoria.usuario_id == usuario_id),
            self._contar(Reasignacion, Reasignacion.usuario_id == usuario_id),
        )
        return any(totales)

    def _contar(self, model, *filters) -> int:
        query = self.db.query(func.count(model.id))
        for condition in filters:
            query = query.filter(condition)
        return int(query.scalar() or 0)

    @staticmethod
    def _detalle(registro: Auditoria) -> str:
        datos = registro.datos_nuevos or {}
        partes = [str(datos[clave]) for clave in ("codigo", "codigo_hoja", "codigo_bulto", "estado", "tipo", "archivo") if datos.get(clave)]
        return " · ".join(partes) if partes else registro.accion

    @staticmethod
    def _to_out(user: Usuario) -> UsuarioAdminOut:
        return UsuarioAdminOut(
            id=user.id,
            nombre=user.nombre,
            apellido=user.apellido,
            email=user.email,
            rol=user.rol.nombre if user.rol else "",
            activo=user.activo,
        )
