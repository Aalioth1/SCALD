export function formatDate(value: string | null | undefined) {
  if (!value) return '—'
  const [year, month, day] = value.slice(0, 10).split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat('es-CL').format(value)
}

export function formatPercent(part: number, total: number) {
  if (!total) return '0%'
  return `${((part / total) * 100).toFixed(1)}%`
}

export function formatRoute(ruta: string) {
  return ruta.replace(/\s+-\s+/g, ' → ')
}

export function formatTime(value: string | null | undefined) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
}
