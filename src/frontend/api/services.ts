import { request } from './client'
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
  ReporteResumen,
  UserPublic,
} from './types'

export function login(email: string, password: string) {
  return request<AuthSession>('/auth/login', null, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
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

export function regularizarIncidencia(token: string, incidenciaId: number, observaciones: string) {
  return request<Incidencia>(`/incidencias/${incidenciaId}/regularizar`, token, {
    method: 'PATCH',
    body: JSON.stringify({ observaciones: observaciones || null }),
  })
}

export function getResumen(token: string) {
  return request<ReporteResumen>('/reportes/resumen', token)
}

export function getDetalleHoja(token: string, hojaId: number) {
  return request<ReporteHoja>(`/reportes/hoja-ruta/${hojaId}`, token)
}

export function listAuditoria(token: string, limite = 8) {
  return request<Auditoria[]>(`/auditoria?limite=${limite}`, token)
}

export function importPdfs(token: string, files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append('archivos', file))
  return request<ImportResult>('/importaciones/hojas-ruta', token, {
    method: 'POST',
    body: formData,
  })
}
