import { useEffect, useState } from 'react'
import { listBultos, listHojas, listIncidencias, resolverIncidencia } from '../api/services'
import type { Bulto, HojaRuta, Incidencia } from '../api/types'
import ResolverIncidencia from '../components/ResolverIncidencia'
import { formatDate } from '../format'

type Props = {
  token: string
  onOpenHoja: (hojaId: number) => void
}

type SortKey = 'hoja' | 'estado' | 'registro'
type SortDir = 'asc' | 'desc'

export default function IncidenciasPage({ token, onOpenHoja }: Props) {
  const [incidencias, setIncidencias] = useState<Incidencia[]>([])
  const [bultos, setBultos] = useState<Bulto[]>([])
  const [hojas, setHojas] = useState<HojaRuta[]>([])
  const [soloPendientes, setSoloPendientes] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [resolviendo, setResolviendo] = useState<Incidencia | null>(null)
  const [resolverError, setResolverError] = useState('')
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir } | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([listIncidencias(token, soloPendientes ? 'PENDIENTE' : undefined), listBultos(token), listHojas(token)])
      .then(([nextIncidencias, nextBultos, nextHojas]) => {
        if (!active) return
        setIncidencias(nextIncidencias)
        setBultos(nextBultos)
        setHojas(nextHojas)
        setError('')
      })
      .catch((reason: Error) => {
        if (active) setError(reason.message)
      })
    return () => {
      active = false
    }
  }, [token, soloPendientes, busy])

  const cerrarResolver = () => {
    if (busy) return
    setResolviendo(null)
    setResolverError('')
  }

  const confirmarResolucion = (accion: 'ELIMINAR_PISTOLEO' | 'ANADIR_BULTO') => {
    if (!resolviendo) return
    setBusy(true)
    setResolverError('')
    resolverIncidencia(token, resolviendo.id, accion)
      .then(() => setResolviendo(null))
      .catch((reason: Error) => setResolverError(reason.message))
      .finally(() => setBusy(false))
  }

  const bultoPorId = new Map(bultos.map((bulto) => [bulto.id, bulto.codigo]))
  const hojaPorId = new Map(hojas.map((hoja) => [hoja.id, hoja]))
  const ordenar = (key: SortKey) => {
    setSort((current) => {
      if (current?.key !== key) return { key, dir: 'asc' }
      return { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
    })
  }
  const visibles = [...incidencias].sort((a, b) => {
    if (!sort) return Number(b.estado === 'PENDIENTE') - Number(a.estado === 'PENDIENTE')
    const factor = sort.dir === 'asc' ? 1 : -1
    return valorIncidencia(a, sort.key, hojaPorId).localeCompare(valorIncidencia(b, sort.key, hojaPorId), 'es', { sensitivity: 'base' }) * factor
  })

  return (
    <div className="stack incidencias-view">
      <div className="page-heading">
        <h1>Incidencias</h1>
        <button className="button" onClick={() => setSoloPendientes((value) => !value)} type="button">
          {soloPendientes ? 'Ver todas' : 'Solo pendientes'}
        </button>
      </div>
      <section className="card incidencias-card">
        {error && <p className="form-error incidencias-error">{error}</p>}
        <div className="table-wrap incidencias-table">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Bulto</th>
                <SortHeader column="hoja" label="Hoja de ruta" onSort={ordenar} sort={sort} />
                <SortHeader column="registro" label="Registro" onSort={ordenar} sort={sort} />
                <SortHeader column="estado" label="Estado" onSort={ordenar} sort={sort} />
                <th />
              </tr>
            </thead>
            <tbody>
              {visibles.map((item) => (
                <tr key={item.id}>
                  <td>{item.tipo}</td>
                  <td className="code">{bultoPorId.get(item.bulto_id ?? -1) ?? '—'}</td>
                  <td className="code">{hojaPorId.get(item.hoja_ruta_id ?? -1)?.codigo ?? '—'}</td>
                  <td>{formatDate(hojaPorId.get(item.hoja_ruta_id ?? -1)?.fecha_registro)}</td>
                  <td><span className={`badge ${item.estado === 'PENDIENTE' ? 'warn' : 'ok'}`}>{item.estado}</span></td>
                  <td className="actions">
                    {item.hoja_ruta_id && <button className="button tiny sheet" onClick={() => onOpenHoja(item.hoja_ruta_id as number)} type="button">Ver hoja</button>}
                    {item.estado === 'PENDIENTE' && (
                      <button className="button tiny primary" disabled={busy} onClick={() => { setResolverError(''); setResolviendo(item) }} type="button">Resolver</button>
                    )}
                  </td>
                </tr>
              ))}
              {!visibles.length && <tr><td colSpan={6}>No hay incidencias para este filtro.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
      {resolviendo && (
        <ResolverIncidencia
          busy={busy}
          codigo={bultoPorId.get(resolviendo.bulto_id ?? -1) ?? 'este bulto'}
          duplicado={resolviendo.tipo === 'DUPLICADO'}
          error={resolverError}
          onAdd={() => confirmarResolucion('ANADIR_BULTO')}
          onClose={cerrarResolver}
          onDelete={() => confirmarResolucion('ELIMINAR_PISTOLEO')}
        />
      )}
    </div>
  )
}

function SortHeader({
  label,
  column,
  sort,
  onSort,
}: {
  label: string
  column: SortKey
  sort: { key: SortKey; dir: SortDir } | null
  onSort: (key: SortKey) => void
}) {
  const active = sort?.key === column
  return (
    <th aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <button className="sort-header" onClick={() => onSort(column)} type="button">
        {label}
        <span aria-hidden="true">{active ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'}</span>
      </button>
    </th>
  )
}

function valorIncidencia(item: Incidencia, key: SortKey, hojaPorId: Map<number, HojaRuta>) {
  const hoja = hojaPorId.get(item.hoja_ruta_id ?? -1)
  if (key === 'hoja') return hoja?.codigo ?? ''
  if (key === 'registro') return hoja?.fecha_registro ?? ''
  return item.estado
}
