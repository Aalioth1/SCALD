const API_BASE = 'http://127.0.0.1:8000/api/v1'

export type AuthSession = {
  access_token: string
  token_type: string
}

export type ImportResult = {
  archivos_procesados: number
  archivos_exitosos: number
  archivos_fallidos: number
  hojas_creadas: number
  hojas_actualizadas: number
  bultos_creados: number
  resultados: Array<{
    archivo: string
    exitoso: boolean
    hoja_ruta: string | null
    bultos_creados: number
    bultos_existentes: number
    error: string | null
  }>
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error('Credenciales inválidas')
  return response.json()
}

export async function importPdfs(files: File[], token: string): Promise<ImportResult> {
  const formData = new FormData()
  files.forEach((file) => formData.append('archivos', file))
  const response = await fetch(`${API_BASE}/importaciones/hojas-ruta`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(detail?.detail ?? 'No se pudo importar el lote')
  }
  return response.json()
}
