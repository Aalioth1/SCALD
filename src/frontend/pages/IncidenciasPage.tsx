import { useEffect, useState } from 'react'
import { listBultos, listIncidencias, regularizarIncidencia } from '../api/services'
import type { Bulto, Incidencia } from '../api/types'
import { formatDate } from '../format'

type Props = {
  token: string
  onOpenHoja: (hojaId: number) => void
}

export default function IncidenciasPage({ token, onOpenHoja }: Props) {
  const [incidencias, setIncidencias] = useState<Incidencia[]>([])
  const [bultos, setBultos] = useState<Bulto[]>([])
  const [soloPendientes, setSoloPendientes] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let active = true
    Promise.all([listIncidencias(token, soloPendientes ? 'PENDIENTE' : undefined), listBultos(token)])
      .then(([nextIncidencias, nextBultos]) => {
        if (!active) return
        setIncidencias(nextIncidencias)
        setBultos(nextBultos)
        setError('')
      })
      .catch((reason: Error) => {
        if (active) setError(reason.message)
      })
    return () => {
      active = false
    }
  }, [token, soloPendientes, busy])

  const resolver = (id: number) => {
    setBusy(true)
    regularizarIncidencia(token, id, 'Regularizada desde incidencias')
      .then(() => setBusy(false))
      .catch((reason: Error) => {
        setError(reason.message)
        setBusy(false)
      })
  }

  const bultoPorId = new Map(bultos.map((bulto) => [bulto.id, bulto.codigo]))

  return (
    <div className="stack">
      <div className="page-heading">
        <h1>Incidencias</h1>
        <button className="button" onClick={() => setSoloPendientes((value) => !value)} type="button">
          {soloPendientes ? 'Ver todas' : 'Solo pendientes'}
        </button>
      </div>
      {error && <p className="form-error">{error}</p>}
      <section className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Bulto</th>
                <th>Estado</th>
                <th>Fecha</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {incidencias.map((item) => (
                <tr key={item.id}>
                  <td>{item.tipo}</td>
                  <td className="code">{bultoPorId.get(item.bulto_id ?? -1) ?? '—'}</td>
                  <td><span className={`badge ${item.estado === 'PENDIENTE' ? 'warn' : 'ok'}`}>{item.estado}</span></td>
                  <td>{formatDate(item.fecha_creacion)}</td>
                  <td className="actions">
                    {item.hoja_ruta_id && <button className="text-link" onClick={() => onOpenHoja(item.hoja_ruta_id as number)} type="button">Ver hoja</button>}
                    {item.estado === 'PENDIENTE' && <button className="button tiny" disabled={busy} onClick={() => resolver(item.id)} type="button">Resolver</button>}
                  </td>
                </tr>
              ))}
              {!incidencias.length && <tr><td colSpan={5}>No hay incidencias para este filtro.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
