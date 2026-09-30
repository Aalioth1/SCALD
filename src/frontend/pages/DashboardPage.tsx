import { useEffect, useState } from 'react'
import { listAuditoria, listIncidencias, getResumen, listHojas } from '../api/services'
import type { Auditoria, HojaRuta, Incidencia, ReporteResumen } from '../api/types'
import { formatDate, formatNumber, formatPercent } from '../format'
import HojaTable from '../components/HojaTable'
import ImportarPdfButton from '../components/ImportarPdfButton'

type Props = {
  token: string
  isAdmin: boolean
  onOpenHoja: (hojaId: number) => void
  onPistoleo: (hojaId: number) => void
  onIncidencias: () => void
  onReporte: () => void
  onVerTodas: () => void
}

export default function DashboardPage({ token, isAdmin, onOpenHoja, onPistoleo, onIncidencias, onReporte, onVerTodas }: Props) {
  const [hojas, setHojas] = useState<HojaRuta[]>([])
  const [resumen, setResumen] = useState<ReporteResumen | null>(null)
  const [incidencias, setIncidencias] = useState<Incidencia[]>([])
  const [actividad, setActividad] = useState<Auditoria[]>([])
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let alive = true
    Promise.all([listHojas(token), getResumen(token), listIncidencias(token)])
      .then(([nextHojas, nextResumen, nextIncidencias]) => {
        if (!alive) return
        setHojas(nextHojas)
        setResumen(nextResumen)
        setIncidencias(nextIncidencias)
      })
      .catch((reason: Error) => {
        if (alive) setError(reason.message)
      })
    if (isAdmin) {
      listAuditoria(token, 30)
        .then((rows) => {
          if (alive) setActividad(rows)
        })
        .catch(() => {
          if (alive) setActividad([])
        })
    }
    return () => {
      alive = false
    }
  }, [token, isAdmin, version])

  const activas = hojas.filter((hoja) => hoja.activo && hoja.estado === 'ACTIVA').length
  const esperados = resumen?.total_bultos_esperados ?? 0
  const pistoleados = Math.max(esperados - (resumen?.faltantes ?? 0), 0)
  const pendingByHoja = new Map<number, number>()
  incidencias.filter((item) => item.estado === 'PENDIENTE' && item.hoja_ruta_id).forEach((item) => {
    pendingByHoja.set(item.hoja_ruta_id as number, (pendingByHoja.get(item.hoja_ruta_id as number) ?? 0) + 1)
  })
  const recientes = [...hojas].sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, 5)
  const actividadVisible = actividad.length
    ? actividad.map((item) => ({
        id: `a-${item.id}`,
        tone: item.entidad === 'PISTOLEO' || item.accion === 'IMPORTAR_PDF' ? 'ok' : item.entidad === 'REASIGNACION' ? 'warn' : 'alert',
        text: actividadTexto(item),
        time: formatDate(item.fecha_hora),
      }))
    : incidencias.slice(0, 30).map((item) => ({
        id: `i-${item.id}`,
        tone: item.estado === 'PENDIENTE' ? 'alert' : 'ok',
        text: `${item.tipo} · ${item.estado.toLowerCase()}`,
        time: formatDate(item.fecha_creacion),
      }))

  return (
    <div className="stack">
      <div className="page-heading">
        <h1>Dashboard</h1>
        <ImportarPdfButton onImported={() => setVersion((value) => value + 1)} token={token} />
      </div>
      {error && <p className="form-error">{error}</p>}
      <section className="metrics" aria-label="Indicadores">
        <article className="metric">
          <div className="metric-top"><span>Hojas Activas</span><i className="dot orange" /></div>
          <strong>{formatNumber(activas)}</strong>
          <small>{formatNumber(resumen?.total_hojas ?? hojas.length)} hojas en el sistema</small>
        </article>
        <article className="metric">
          <div className="metric-top"><span>Pistoleos</span><i className="dot green" /></div>
          <strong>{formatNumber(resumen?.total_pistoleos ?? 0)}</strong>
          <small>{formatNumber(resumen?.ok ?? 0)} en estado OK</small>
        </article>
        <article className="metric">
          <div className="metric-top"><span>Incidencias Pendientes</span><i className="dot yellow" /></div>
          <strong>{formatNumber(resumen?.incidencias_pendientes ?? 0)}</strong>
          <small>{formatNumber(resumen?.incidencias_regularizadas ?? 0)} regularizadas</small>
        </article>
        <article className="metric">
          <div className="metric-top"><span>Eficiencia</span><i className="dot ink" /></div>
          <strong>{formatPercent(pistoleados, esperados)}</strong>
          <small>{formatNumber(pistoleados)} de {formatNumber(esperados)} bultos</small>
        </article>
      </section>
      <div className="workspace-grid">
        <section className="card">
          <div className="card-header">
            <h2>Hojas de Ruta Recientes</h2>
            <button className="text-link" onClick={onVerTodas} type="button">Ver todas</button>
          </div>
          <HojaTable hojas={recientes} onOpen={onOpenHoja} pendingByHoja={pendingByHoja} />
        </section>
        <div className="side-stack">
          <section className="card">
            <div className="card-header">
              <h2>Actividad en Vivo</h2>
              <i className="dot green" />
            </div>
            <ul className="activity-list">
              {actividadVisible.length === 0 && <li className="muted">Sin movimientos registrados.</li>}
              {actividadVisible.map((item) => (
                <li key={item.id}><i className={`dot ${item.tone}`} /> <span>{item.text}</span> <time>{item.time}</time></li>
              ))}
            </ul>
          </section>
          <section className="card">
            <div className="card-header"><h2>Acciones Rápidas</h2></div>
            <div className="quick-actions">
              <button disabled={!recientes.length} onClick={() => recientes[0] && onPistoleo(recientes[0].id)} type="button"><i className="dot orange" /> Registrar Pistoleo</button>
              <button onClick={onIncidencias} type="button"><i className="dot yellow" /> Ver Incidencias</button>
              <button onClick={onReporte} type="button"><i className="dot green" /> Generar Reporte</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

function actividadTexto(item: Auditoria) {
  const datos = item.datos_nuevos ?? {}
  const codigo = typeof datos.codigo === 'string' ? datos.codigo : ''
  if (item.entidad === 'HOJA_RUTA' && item.accion === 'IMPORTAR_PDF') {
    return codigo ? `Hoja de ruta importada · ${codigo}` : 'Hoja de ruta importada'
  }
  if (item.entidad === 'PISTOLEO') return `Pistoleo ${String(datos.estado ?? '').toLowerCase() || 'registrado'}`
  if (item.entidad === 'REASIGNACION') return 'Bulto migrado de hoja'
  if (item.entidad === 'INCIDENCIA') return 'Incidencia registrada'
  return `${item.entidad.toLowerCase()} · ${item.accion.toLowerCase()}`
}
