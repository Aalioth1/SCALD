import type { HojaRuta } from '../api/types'
import { formatDate, formatNumber } from '../format'

type Props = {
  hojas: HojaRuta[]
  pendingByHoja: Map<number, number>
  onOpen: (hojaId: number) => void
}

export default function HojaTable({ hojas, pendingByHoja, onOpen }: Props) {
  if (!hojas.length) {
    return <p className="empty">No hay hojas de ruta cargadas.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Fecha</th>
            <th>Ruta</th>
            <th>Bultos</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody className="clickable">
          {hojas.map((hoja) => {
            const pending = pendingByHoja.get(hoja.id) ?? 0
            const badge = badgeFor(hoja, pending)
            return (
              <tr key={hoja.id} onClick={() => onOpen(hoja.id)}>
                <td className="code">{hoja.codigo}</td>
                <td>{formatDate(hoja.fecha)}</td>
                <td>{hoja.ruta}</td>
                <td>{formatNumber(hoja.cantidad_declarada)}</td>
                <td><span className={`badge ${badge.tone}`}>{badge.label}</span></td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function badgeFor(hoja: HojaRuta, pending: number) {
  if (hoja.estado === 'CERRADA') return { label: 'Cerrada', tone: 'closed' }
  if (pending > 0) return { label: 'Con incidencias', tone: 'warn' }
  if (hoja.estado === 'ACTIVA') return { label: 'Activa', tone: 'ok' }
  return { label: 'Inactiva', tone: 'muted' }
}
