import { request, requestBlob } from './client'
import type {
  Auditoria,
  AuthSession,
  Bulto,
  HojaRuta,
  HojaRutaInput,
  ImportResult,
  Incidencia,
  Pistoleo,
  Reasignacion,
  ReporteHoja,
  ReporteOperativo,
  ReporteResumen,
  UserPublic,
  UsuarioAdmin,
  UsuarioInput,
  ActividadUsuario,
  Acceso,
} from './types'

export function login(email: string, password: string, rol: Acceso) {
  return request<AuthSession>('/auth/login', null, {
    method: 'POST',
    body: JSON.stringify({ email, password, rol }),
  })
}

export function getMe(token: string) {
  return request<UserPublic>('/auth/me', token)
}

export function listHojas(token: string) {
  return request<HojaRuta[]>('/hojas-ruta', token)
}

export function getHoja(token: string, hojaId: number) {
  return request<HojaRuta>(`/hojas-ruta/${hojaId}`, token)
}

export function createHoja(token: string, payload: HojaRutaInput) {
  return request<HojaRuta>('/hojas-ruta', token, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateHoja(token: string, hojaId: number, payload: HojaRutaInput) {
  return request<HojaRuta>(`/hojas-ruta/${hojaId}`, token, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function listBultos(token: string) {
  return request<Bulto[]>('/bultos', token)
}

export function listPistoleos(token: string, limite = 30) {
  return request<Pistoleo[]>(`/pistoleos?limite=${limite}`, token)
}

export function registrarPistoleo(token: string, codigoBulto: string, hojaRutaId: number) {
  return request<Pistoleo>('/pistoleos', token, {
    method: 'POST',
    body: JSON.stringify({ codigo_bulto: codigoBulto, hoja_ruta_id: hojaRutaId }),
  })
}

export function reasignarBulto(token: string, bultoId: number, hojaDestinoId: number, motivo: string) {
  return request<Reasignacion>('/reasignaciones', token, {
    method: 'POST',
    body: JSON.stringify({
      bulto_id: bultoId,
      hoja_destino_id: hojaDestinoId,
      motivo,
    }),
  })
}

export function listIncidencias(token: string, estado?: string) {
  const query = estado ? `?estado=${encodeURIComponent(estado)}` : ''
  return request<Incidencia[]>(`/incidencias${query}`, token)
}

export function resolverIncidencia(token: string, incidenciaId: number, accion: 'ELIMINAR_PISTOLEO' | 'ANADIR_BULTO') {
  return request<Incidencia>(`/incidencias/${incidenciaId}/resolver`, token, {
    method: 'POST',
    body: JSON.stringify({ accion }),
  })
}

export function regularizarIncidencia(token: string, incidenciaId: number, observaciones: string) {
  return request<Incidencia>(`/incidencias/${incidenciaId}/regularizar`, token, {
    method: 'PATCH',
    body: JSON.stringify({ observaciones: observaciones || null }),
  })
}

export function getOperativo(token: string, fechaDesde?: string, fechaHasta?: string) {
  const params = new URLSearchParams()
  if (fechaDesde) params.set('fecha_desde', fechaDesde)
  if (fechaHasta) params.set('fecha_hasta', fechaHasta)
  const query = params.toString()
  return request<ReporteOperativo>(`/reportes/operativo${query ? `?${query}` : ''}`, token)
}

export function getResumen(token: string, fechaDesde?: string, fechaHasta?: string) {
  const params = new URLSearchParams()
  if (fechaDesde) params.set('fecha_desde', fechaDesde)
  if (fechaHasta) params.set('fecha_hasta', fechaHasta)
  const query = params.toString()
  return request<ReporteResumen>(`/reportes/resumen${query ? `?${query}` : ''}`, token)
}

export function downloadReportePdf(token: string, fechaDesde?: string, fechaHasta?: string, usuarioId?: number) {
  const params = new URLSearchParams()
  if (fechaDesde) params.set('fecha_desde', fechaDesde)
  if (fechaHasta) params.set('fecha_hasta', fechaHasta)
  if (usuarioId) params.set('usuario_id', String(usuarioId))
  const query = params.toString()
  return requestBlob(`/reportes/pdf${query ? `?${query}` : ''}`, token)
}

export function getDetalleHoja(token: string, hojaId: number) {
  return request<ReporteHoja>(`/reportes/hoja-ruta/${hojaId}`, token)
}

export function listAuditoria(token: string, limite = 8) {
  return request<Auditoria[]>(`/auditoria?limite=${limite}`, token)
}

export function listUsuarios(token: string) {
  return request<UsuarioAdmin[]>('/usuarios', token)
}

export function createUsuario(token: string, payload: UsuarioInput) {
  return request<UsuarioAdmin>('/usuarios', token, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateUsuario(token: string, usuarioId: number, payload: UsuarioInput) {
  return request<UsuarioAdmin>(`/usuarios/${usuarioId}`, token, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function setUsuarioActivo(token: string, usuarioId: number, activo: boolean) {
  return request<UsuarioAdmin>(`/usuarios/${usuarioId}/estado`, token, {
    method: 'PATCH',
    body: JSON.stringify({ activo }),
  })
}

export function deleteUsuario(token: string, usuarioId: number) {
  return request<{ message: string }>(`/usuarios/${usuarioId}`, token, { method: 'DELETE' })
}

export function archivarRegistrosUsuario(token: string, usuarioId: number) {
  return request<{ archivadas: number }>(`/usuarios/${usuarioId}/archivar`, token, { method: 'POST' })
}

export function eliminarRegistrosHoja(token: string, usuarioId: number, hojaId: number) {
  return request<{ message: string }>(`/usuarios/${usuarioId}/hojas/${hojaId}`, token, { method: 'DELETE' })
}

export function getActividadUsuario(token: string, usuarioId: number, fechaDesde?: string, fechaHasta?: string) {
  const params = new URLSearchParams()
  if (fechaDesde) params.set('fecha_desde', fechaDesde)
  if (fechaHasta) params.set('fecha_hasta', fechaHasta)
  const query = params.toString()
  return request<ActividadUsuario>(`/usuarios/${usuarioId}/actividad${query ? `?${query}` : ''}`, token)
}

export function importPdfs(token: string, files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append('archivos', file))
  return request<ImportResult>('/importaciones/hojas-ruta', token, {
    method: 'POST',
    body: formData,
  })
}
