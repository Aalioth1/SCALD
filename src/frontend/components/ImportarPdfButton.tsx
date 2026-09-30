import { useRef, useState } from 'react'
import { importPdfs } from '../api/services'
import type { ImportResult } from '../api/types'

type Props = {
  token: string
  onImported: () => void
}

export default function ImportarPdfButton({ token, onImported }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const elegir = () => {
    setError('')
    inputRef.current?.click()
  }

  const cargar = (files: File[]) => {
    const pdfs = files.filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
    if (!pdfs.length) {
      setError('Selecciona al menos un PDF de hoja de ruta')
      return
    }
    setBusy(true)
    setError('')
    setMessage('')
    importPdfs(token, pdfs)
      .then((result) => {
        setMessage(resumen(result))
        onImported()
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false))
  }

  return (
    <div className="import-action">
      <button className="button primary" disabled={busy} onClick={elegir} type="button">
        {busy ? 'Importando…' : '+ Nueva Hoja de Ruta'}
      </button>
      <input
        accept=".pdf,application/pdf"
        hidden
        multiple
        onChange={(event) => {
          const files = Array.from(event.target.files ?? [])
          event.target.value = ''
          if (files.length) cargar(files)
        }}
        ref={inputRef}
        type="file"
      />
      {message && <p className="notice">{message}</p>}
      {error && <p className="form-error">{error}</p>}
    </div>
  )
}

function resumen(result: ImportResult) {
  return `${result.archivos_exitosos} PDF importado(s) · ${result.hojas_creadas} hoja(s) nueva(s) · ${result.bultos_creados} bulto(s)`
}
