import { useEffect, useState } from 'react'
import HojaTable from '../components/HojaTable'
import ImportarPdfButton from '../components/ImportarPdfButton'
import { listHojas, listIncidencias } from '../api/services'
import type { HojaRuta, Incidencia } from '../api/types'

type Props = {
  token: string
  onOpenHoja: (hojaId: number) => void
}

export default function HojasPage({ token, onOpenHoja }: Props) {
  const [hojas, setHojas] = useState<HojaRuta[]>([])
  const [incidencias, setIncidencias] = useState<Incidencia[]>([])
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let alive = true
    Promise.all([listHojas(token), listIncidencias(token)])
      .then(([nextHojas, nextIncidencias]) => {
        if (!alive) return
        setHojas(nextHojas)
        setIncidencias(nextIncidencias)
      })
      .catch((reason: Error) => {
        if (alive) setError(reason.message)
      })
    return () => {
      alive = false
    }
  }, [token, version])

  const pendingByHoja = new Map<number, number>()
  incidencias.filter((item) => item.estado === 'PENDIENTE' && item.hoja_ruta_id).forEach((item) => {
    pendingByHoja.set(item.hoja_ruta_id as number, (pendingByHoja.get(item.hoja_ruta_id as number) ?? 0) + 1)
  })

  return (
    <div className="stack">
      <div className="page-heading">
        <h1>Hojas de Ruta</h1>
        <ImportarPdfButton onImported={() => setVersion((value) => value + 1)} token={token} />
      </div>
      {error && <p className="form-error">{error}</p>}
      <section className="card">
        <HojaTable hojas={[...hojas].sort((a, b) => b.fecha.localeCompare(a.fecha))} onOpen={onOpenHoja} pendingByHoja={pendingByHoja} />
      </section>
    </div>
  )
}
