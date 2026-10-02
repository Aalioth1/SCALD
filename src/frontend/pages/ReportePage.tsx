import { useEffect, useState } from 'react'
import { downloadReportePdf, getOperativo } from '../api/services'
import type { ReporteOperativo } from '../api/types'
import SortHeader, { compareText, nextSort, type SortState } from '../components/SortHeader'
import { formatDate, formatNumber, formatPercent, formatRoute } from '../format'

type Props = {
  token: string
}

type Modo = 'periodo' | 'dia'

export default function ReportePage({ token }: Props) {
  const periodoInicial = rangoUltimas48Horas()
  const [modo, setModo] = useState<Modo>('dia')
  const [desde, setDesde] = useState(periodoInicial.desde)
  const [hasta, setHasta] = useState(periodoInicial.hasta)
  const [dia, setDia] = useState(() => fechaLocal(new Date()))
  const [reporte, setReporte] = useState<ReporteOperativo | null>(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)
  const [descargando, setDescargando] = useState(false)
  const [ordenHojas, setOrdenHojas] = useState<SortState<'codigo' | 'registro'> | null>(null)
  const [ordenFaltantes, setOrdenFaltantes] = useState<SortState<'bulto' | 'hoja'> | null>(null)
  const [ordenIncidencias, setOrdenIncidencias] = useState<SortState<'hoja' | 'bulto'> | null>(null)

  const fechaDesde = modo === 'dia' ? dia : desde
  const fechaHasta = modo === 'dia' ? dia : hasta
  const rangoInvalido = Boolean(fechaDesde && fechaHasta && fechaDesde > fechaHasta)

  useEffect(() => {
    if (rangoInvalido) {
      setReporte(null)
      setCargando(false)
      setError('La fecha inicial no puede ser posterior a la final')
      return
    }
    let activo = true
    setError('')
    setCargando(true)
    getOperativo(token, fechaDesde || undefined, fechaHasta || undefined)
      .then((data) => {
        if (activo) setReporte(data)
      })
      .catch((reason: Error) => {
        if (activo) {
          setReporte(null)
          setError(reason.message)
        }
      })
      .finally(() => {
        if (activo) setCargando(false)
      })
    return () => {
      activo = false
    }
  }, [token, fechaDesde, fechaHasta, rangoInvalido])

  const seleccionarModo = (siguiente: Modo) => {
    if (siguiente === modo) return
    if (siguiente === 'periodo') {
      const rango = rangoUltimas48Horas()
      setDesde(rango.desde)
      setHasta(rango.hasta)
    } else {
      setDia(fechaLocal(new Date()))
    }
    setModo(siguiente)
  }

  const descargar = async () => {
    if (rangoInvalido || descargando) return
    setDescargando(true)
    setError('')
    try {
      const { blob, filename } = await downloadReportePdf(token, fechaDesde || undefined, fechaHasta || undefined)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'reporte-operativo.pdf'
      link.click()
      URL.revokeObjectURL(url)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo descargar el reporte')
    } finally {
      setDescargando(false)
    }
  }

  const hojas = ordenar(reporte?.hojas ?? [], ordenHojas, (hoja) => (ordenHojas?.key === 'registro' ? hoja.registro : hoja.codigo))
  const faltantes = ordenar(reporte?.faltantes ?? [], ordenFaltantes, (item) => (ordenFaltantes?.key === 'hoja' ? item.hoja : item.codigo))
  const incidencias = ordenar(reporte?.incidencias ?? [], ordenIncidencias, (item) => (ordenIncidencias?.key === 'bulto' ? item.bulto : item.hoja))
  const resumen = reporte?.resumen
  const pistoleados = resumen ? Math.max(resumen.total_bultos_esperados - resumen.faltantes, 0) : 0
  const eficiencia = resumen ? formatPercent(pistoleados, resumen.total_bultos_esperados) : '0%'
  const chips = resumen
    ? [
        ['Pistoleos', resumen.total_pistoleos],
        ['OK', resumen.ok],
        ['Duplicados', resumen.duplicados],
        ['Sin lista', resumen.sin_lista_esperada],
        ['No pertenece', resumen.no_pertenece],
        ['Reasignados', resumen.reasignados],
      ]
    : []

  return (
    <div className="reporte-view">
      <div className="page-heading reporte-head">
        <div>
          <h1>Reporte operativo</h1>
          <p className="meta">{descripcionPeriodo(modo, fechaDesde, fechaHasta)}</p>
        </div>
        <div className="reporte-toolbar">
          <div className="mode-switch" role="group" aria-label="Tipo de periodo">
            <button className={modo === 'dia' ? 'active' : ''} onClick={() => seleccionarModo('dia')} type="button">Día</button>
            <button className={modo === 'periodo' ? 'active' : ''} onClick={() => seleccionarModo('periodo')} type="button">Periodo</button>
          </div>
          <div className="report-dates">
            {modo === 'periodo' ? (
              <>
                <label>
                  Desde
                  <input max={hasta || undefined} onChange={(event) => setDesde(event.target.value)} type="date" value={desde} />
                </label>
                <label>
                  Hasta
                  <input min={desde || undefined} onChange={(event) => setHasta(event.target.value)} type="date" value={hasta} />
                </label>
              </>
            ) : (
              <label>
                Día
                <input onChange={(event) => setDia(event.target.value)} type="date" value={dia} />
              </label>
            )}
          </div>
          <button className="button primary" disabled={rangoInvalido || (cargando && !reporte) || descargando} onClick={descargar} type="button">
            {descargando ? 'Generando PDF…' : 'Descargar PDF'}
          </button>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}
      {cargando && !reporte && <p className="hint">Cargando reporte…</p>}

      {reporte && resumen && (
        <>
          <section className="reporte-kpis" aria-label="Resumen">
            <article><span>Hojas</span><strong>{formatNumber(resumen.total_hojas)}</strong></article>
            <article><span>Bultos esperados</span><strong>{formatNumber(resumen.total_bultos_esperados)}</strong></article>
            <article><span>Pistoleados</span><strong>{formatNumber(pistoleados)}</strong></article>
            <article><span>Faltantes</span><strong>{formatNumber(resumen.faltantes)}</strong></article>
            <article className="reporte-efficiency">
              <div>
                <span>Eficiencia de pistoleo</span>
                <strong>{eficiencia}</strong>
              </div>
              <div className="reporte-bar" aria-hidden="true">
                <div style={{ width: eficiencia }} />
              </div>
            </article>
          </section>
          <ul className="reporte-chips">
            {chips.map(([label, value]) => (
              <li key={label}>
                <span>{label}</span>
                <strong>{formatNumber(Number(value))}</strong>
              </li>
            ))}
          </ul>
          <div className="reporte-boards">
            <section className="card">
              <div className="card-header"><h2>Hojas de ruta</h2><span className="meta">{formatNumber(reporte.hojas.length)}</span></div>
              <div className="table-wrap">
                {hojas.length === 0 ? <p className="empty">No hay hojas de ruta en este periodo.</p> : (
                  <table>
                    <thead>
                      <tr>
                        <SortHeader column="codigo" label="Código" onSort={(key) => setOrdenHojas((current) => nextSort(current, key))} sort={ordenHojas} />
                        <SortHeader column="registro" label="Registro" onSort={(key) => setOrdenHojas((current) => nextSort(current, key))} sort={ordenHojas} />
                        <th>Ruta</th><th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {hojas.map((hoja) => (
                        <tr key={hoja.codigo}>
                          <td className="code">{hoja.codigo}</td>
                          <td>{formatDate(hoja.registro)}</td>
                          <td>{formatRoute(hoja.ruta)}{hoja.transporte ? <span className="muted"> · {hoja.transporte}</span> : null}</td>
                          <td><span className={`badge ${marcaEstado(hoja.estado)}`}>{hoja.estado}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
            <section className="card">
              <div className="card-header"><h2>Bultos faltantes</h2><span className="meta">{formatNumber(reporte.faltantes.length)}</span></div>
              <div className="table-wrap">
                {faltantes.length === 0 ? <p className="empty">No hay bultos pendientes de pistoleo.</p> : (
                  <table>
                    <thead>
                      <tr>
                        <SortHeader column="bulto" label="Bulto" onSort={(key) => setOrdenFaltantes((current) => nextSort(current, key))} sort={ordenFaltantes} />
                        <SortHeader column="hoja" label="Hoja" onSort={(key) => setOrdenFaltantes((current) => nextSort(current, key))} sort={ordenFaltantes} />
                      </tr>
                    </thead>
                    <tbody>
                      {faltantes.map((item) => (
                        <tr key={`${item.hoja}-${item.codigo}`}>
                          <td className="code">{item.codigo}</td>
                          <td>{item.hoja}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
            <section className="card">
              <div className="card-header">
                <h2>Incidencias</h2>
                <span className="meta">{reporte.pendientes} pendientes · {reporte.regularizadas} regularizadas</span>
              </div>
              <div className="table-wrap">
                {incidencias.length === 0 ? <p className="empty">No hay incidencias en este periodo.</p> : (
                  <table>
                    <thead>
                      <tr>
                        <SortHeader column="hoja" label="Hoja" onSort={(key) => setOrdenIncidencias((current) => nextSort(current, key))} sort={ordenIncidencias} />
                        <SortHeader column="bulto" label="Bulto" onSort={(key) => setOrdenIncidencias((current) => nextSort(current, key))} sort={ordenIncidencias} />
                        <th>Tipo</th><th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {incidencias.map((item) => (
                        <tr key={`${item.registro}-${item.bulto}-${item.tipo}`}>
                          <td>{item.hoja}</td>
                          <td className="code">{item.bulto}</td>
                          <td>{item.tipo}</td>
                          <td><span className={`badge ${marcaEstado(item.estado)}`}>{item.estado}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  )
}

function ordenar<T>(items: T[], sort: { dir: 'asc' | 'desc' } | null, value: (item: T) => string) {
  if (!sort) return items
  return [...items].sort((a, b) => compareText(value(a), value(b), sort.dir))
}

function marcaEstado(estado: string) {
  if (estado === 'PENDIENTE' || estado === 'CERRADA' || estado === 'INACTIVA') return 'closed'
  if (estado === 'REGULARIZADO' || estado === 'ACTIVA' || estado === 'OK') return 'ok'
  return 'warn'
}

function fechaLocal(valor: Date) {
  const mes = String(valor.getMonth() + 1).padStart(2, '0')
  const dia = String(valor.getDate()).padStart(2, '0')
  return `${valor.getFullYear()}-${mes}-${dia}`
}

function rangoUltimas48Horas() {
  const ahora = new Date()
  const inicio = new Date(ahora.getTime() - 48 * 60 * 60 * 1000)
  return { desde: fechaLocal(inicio), hasta: fechaLocal(ahora) }
}

function descripcionPeriodo(modo: Modo, desde: string, hasta: string) {
  if (modo === 'dia') return desde ? `Registro del ${formatDate(desde)}` : 'Elija un día de registro'
  if (desde && hasta) return `Registro del ${formatDate(desde)} al ${formatDate(hasta)}`
  if (desde) return `Registro desde el ${formatDate(desde)}`
  if (hasta) return `Registro hasta el ${formatDate(hasta)}`
  return 'Todo el historial'
}
