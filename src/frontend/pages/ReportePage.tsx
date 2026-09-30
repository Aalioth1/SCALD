import { useEffect, useState } from 'react'
import { getResumen } from '../api/services'
import type { ReporteResumen } from '../api/types'
import { formatNumber, formatPercent } from '../format'

type Props = {
  token: string
}

const rows: Array<{ label: string; key: keyof ReporteResumen }> = [
  { label: 'Hojas', key: 'total_hojas' },
  { label: 'Bultos esperados', key: 'total_bultos_esperados' },
  { label: 'Pistoleos', key: 'total_pistoleos' },
  { label: 'OK', key: 'ok' },
  { label: 'Faltantes', key: 'faltantes' },
  { label: 'Duplicados', key: 'duplicados' },
  { label: 'Sin lista esperada', key: 'sin_lista_esperada' },
  { label: 'No pertenece', key: 'no_pertenece' },
  { label: 'Reasignados', key: 'reasignados' },
  { label: 'Incidencias pendientes', key: 'incidencias_pendientes' },
  { label: 'Incidencias regularizadas', key: 'incidencias_regularizadas' },
]

export default function ReportePage({ token }: Props) {
  const [resumen, setResumen] = useState<ReporteResumen | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getResumen(token)
      .then(setResumen)
      .catch((reason: Error) => setError(reason.message))
  }, [token])

  const pistoleados = resumen ? Math.max(resumen.total_bultos_esperados - resumen.faltantes, 0) : 0

  return (
    <div className="stack">
      <div className="page-heading">
        <h1>Reporte operativo</h1>
        <button className="button primary" onClick={() => window.print()} type="button">Imprimir</button>
      </div>
      {error && <p className="form-error">{error}</p>}
      {resumen && (
        <section className="card">
          <div className="card-header">
            <h2>Resumen</h2>
            <span className="badge ok">{formatPercent(pistoleados, resumen.total_bultos_esperados)} eficiencia</span>
          </div>
          <div className="report-grid">
            {rows.map((row) => (
              <div key={row.key}>
                <span>{row.label}</span>
                <strong>{formatNumber(resumen[row.key])}</strong>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
