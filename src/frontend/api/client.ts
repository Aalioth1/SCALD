const API_BASE = 'http://127.0.0.1:8000/api/v1'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function apiBase() {
  return API_BASE
}

async function readError(response: Response) {
  const body = await response.json().catch(() => null)
  const detail = body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => (typeof item?.msg === 'string' ? item.msg : 'Dato inválido'))
    return messages.join('. ')
  }
  return 'No se pudo completar la operación'
}

export async function request<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!response.ok) throw new ApiError(await readError(response), response.status)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
