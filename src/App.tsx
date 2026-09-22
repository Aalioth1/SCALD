import { useState } from 'react'

export default function App() {
  const [files, setFiles] = useState<FileList | null>(null)
  const [status, setStatus] = useState('Listo para subir PDFs')

  const handleFiles = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files
    setFiles(selected)
    if (selected && selected.length > 0) {
      setStatus(`${selected.length} archivo(s) seleccionado(s)`)
    } else {
      setStatus('No se seleccionaron archivos')
    }
  }

  const handleUpload = () => {
    if (!files || files.length === 0) {
      setStatus('Debe seleccionar al menos un PDF')
      return
    }

    const valid = Array.from(files).every((file) => file.type === 'application/pdf')
    if (!valid) {
      setStatus('Solo se permiten archivos PDF')
      return
    }

    setStatus(`Se recibieron ${files.length} PDF(s) y están listos para procesarse en el backend`)
  }

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: 'linear-gradient(135deg, #0f172a, #111827)',
        color: '#e5e7eb',
        fontFamily: 'Segoe UI, sans-serif',
        padding: '2rem',
      }}
    >
      <section
        style={{
          width: '100%',
          maxWidth: '760px',
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(148, 163, 184, 0.3)',
          borderRadius: '20px',
          padding: '2rem',
          boxShadow: '0 20px 45px rgba(15, 23, 42, 0.35)',
        }}
      >
        <p style={{ margin: 0, color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: '0.12em', fontSize: '12px' }}>
          SCALD
        </p>
        <h1 style={{ margin: '0.75rem 0 1rem', fontSize: '2.3rem' }}>Sistema de Control y Auditoría Logística</h1>

        <div
          style={{
            background: '#111827',
            border: '1px solid #334155',
            borderRadius: '14px',
            padding: '1.25rem',
            marginBottom: '1.25rem',
          }}
        >
          <p style={{ margin: 0, color: '#cbd5e1' }}>Estado del flujo</p>
          <strong style={{ display: 'block', marginTop: '0.5rem', color: '#f8fafc' }}>{status}</strong>
        </div>

        <label
          htmlFor="pdf-input"
          style={{
            display: 'block',
            padding: '1rem 1.2rem',
            border: '2px dashed #38bdf8',
            borderRadius: '12px',
            background: 'rgba(14, 116, 144, 0.12)',
            cursor: 'pointer',
            marginBottom: '1rem',
          }}
        >
          <input
            id="pdf-input"
            type="file"
            accept=".pdf,application/pdf"
            multiple
            onChange={handleFiles}
            style={{ display: 'none' }}
          />
          Seleccionar hojas de ruta PDF
        </label>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            onClick={handleUpload}
            style={{
              background: '#38bdf8',
              color: '#082f49',
              border: 'none',
              borderRadius: '10px',
              padding: '0.85rem 1.25rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Importar PDF
          </button>

          <button
            onClick={() => setStatus('Simulando revisión del backend de SCALD')}
            style={{
              background: 'transparent',
              color: '#e2e8f0',
              border: '1px solid #475569',
              borderRadius: '10px',
              padding: '0.85rem 1.25rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Revisar flujo
          </button>
        </div>

        <div style={{ marginTop: '1.5rem', color: '#94a3b8', fontSize: '0.95rem' }}>
          <p>Backend previsto:</p>
          <ul style={{ margin: '0.5rem 0 0 1.2rem', lineHeight: '1.8' }}>
            <li>Upload de PDFs</li>
            <li>Validación de tipo y tamaño</li>
            <li>Extracción de HRD/HRE</li>
            <li>Comparación de bultos esperados vs pistoleados</li>
            <li>Incidencias y trazabilidad</li>
          </ul>
        </div>
      </section>
    </main>
  )
}
