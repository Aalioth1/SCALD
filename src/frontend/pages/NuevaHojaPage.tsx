import { type FormEvent, useState } from 'react'
import { createHoja, importPdfs } from '../api/services'
import type { HojaEstado, HojaRutaInput, HojaTipo, ImportResult } from '../api/types'

type Props = {
  token: string
  canCreate: boolean
  onCreated: (hojaId: number) => void
}

const emptyForm: HojaRutaInput = {
  codigo: '',
  tipo: 'HRD',
  fecha: new Date().toISOString().slice(0, 10),
  ruta: '',
  transporte: null,
  cantidad_declarada: 0,
  estado: 'ACTIVA',
}

export default function NuevaHojaPage({ token, canCreate, onCreated }: Props) {
  const [form, setForm] = useState<HojaRutaInput>(emptyForm)
  const [files, setFiles] = useState<File[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const crear = (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setBusy(true)
    createHoja(token, {
      ...form,
      codigo: form.codigo.trim().toUpperCase(),
      transporte: form.transporte?.trim() || null,
    })
      .then((hoja) => onCreated(hoja.id))
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false))
  }

  const importar = () => {
    if (!files.length) {
      setError('Selecciona al menos un PDF')
      return
    }
    setError('')
    setBusy(true)
    importPdfs(token, files)
      .then((result) => {
        setMessage(resumenImportacion(result))
        setFiles([])
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false))
  }

  return (
    <div className="stack">
      <h1>Nueva hoja de ruta</h1>
      <div className="workspace-grid">
        <section className="card">
          <div className="card-header"><h2>Crear manualmente</h2></div>
          <form className="edit-grid" onSubmit={crear}>
            <label>Código<input onChange={(event) => setForm({ ...form, codigo: event.target.value })} placeholder="HRD-2026-047" required value={form.codigo} /></label>
            <label>Tipo
              <select onChange={(event) => setForm({ ...form, tipo: event.target.value as HojaTipo })} value={form.tipo}>
                <option value="HRD">HRD</option>
                <option value="HRE">HRE</option>
              </select>
            </label>
            <label>Fecha<input onChange={(event) => setForm({ ...form, fecha: event.target.value })} required type="date" value={form.fecha} /></label>
            <label>Estado
              <select onChange={(event) => setForm({ ...form, estado: event.target.value as HojaEstado })} value={form.estado}>
                <option value="ACTIVA">ACTIVA</option>
                <option value="INACTIVA">INACTIVA</option>
                <option value="CERRADA">CERRADA</option>
              </select>
            </label>
            <label className="span-2">Ruta<input onChange={(event) => setForm({ ...form, ruta: event.target.value })} required value={form.ruta} /></label>
            <label>Transporte<input onChange={(event) => setForm({ ...form, transporte: event.target.value })} value={form.transporte ?? ''} /></label>
            <label>Cantidad declarada<input min={0} onChange={(event) => setForm({ ...form, cantidad_declarada: Number(event.target.value) })} required type="number" value={form.cantidad_declarada} /></label>
            {!canCreate && <p className="hint span-2">Crear una hoja requiere rol ADMIN o AUDITOR.</p>}
            {error && <p className="form-error span-2">{error}</p>}
            <div className="form-actions span-2">
              <button className="button primary" disabled={busy || !canCreate} type="submit">Crear hoja</button>
            </div>
          </form>
        </section>
        <section className="card">
          <div className="card-header"><h2>Importar PDF</h2></div>
          <div className="panel-form">
            <p className="hint">Carga hojas HRD o HRE. El servicio crea la hoja y sus bultos esperados.</p>
            <input accept=".pdf,application/pdf" multiple onChange={(event) => setFiles(Array.from(event.target.files ?? []))} type="file" />
            {files.map((file) => <p className="file-name" key={`${file.name}-${file.size}`}>{file.name}</p>)}
            {message && <p className="notice">{message}</p>}
            <button className="button primary" disabled={busy || !files.length} onClick={importar} type="button">Importar</button>
          </div>
        </section>
      </div>
    </div>
  )
}

function resumenImportacion(result: ImportResult) {
  return `${result.archivos_exitosos} archivo(s) importado(s) · ${result.hojas_creadas} hoja(s) nueva(s) · ${result.bultos_creados} bulto(s)`
}
