import { type FormEvent, useEffect, useState } from 'react'
import { importPdfs, login, type AuthSession } from './api'
import './styles.css'

const navItems = [
  ['▦', 'Resumen'],
  ['▤', 'Hojas de ruta'],
  ['◌', 'Pistoleo'],
  ['!', 'Incidencias'],
  ['↥', 'Importación'],
]

const routes = [
  { code: 'HRD-2026-1638', type: 'HRD', route: 'Norte', expected: 124, scanned: 119, status: 'Pendiente' },
  { code: 'HRE-2026-0775', type: 'HRE', route: 'Centro', expected: 86, scanned: 86, status: 'Cerrada' },
  { code: 'HRD-2026-1641', type: 'HRD', route: 'Sur', expected: 52, scanned: 49, status: 'Pendiente' },
]

function formatBytes(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(() => {
    const saved = localStorage.getItem('scald-session')
    return saved ? JSON.parse(saved) : null
  })
  const [activeView, setActiveView] = useState('Resumen')
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState('Conectando con SCALD API...')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then((response) => {
        if (!response.ok) throw new Error('API no disponible')
        return response.json()
      })
      .then(() => setStatus('API conectada'))
      .catch(() => setStatus('Modo local · API no conectada'))
  }, [])

  const addFiles = (incoming: File[]) => {
    const pdfs = incoming.filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
    setFiles(pdfs)
    setStatus(pdfs.length ? `${pdfs.length} PDF(s) preparado(s) para importar` : 'Selecciona archivos PDF válidos')
  }

  const handleImport = () => {
    if (!files.length) {
      setStatus('Selecciona al menos una hoja de ruta PDF')
      return
    }
    if (!session) {
      setStatus('Inicia sesión para enviar los archivos al backend')
      return
    }
    importPdfs(files, session.access_token)
      .then((result) => setStatus(`${result.archivos_exitosos} archivo(s) importado(s) · ${result.bultos_creados} bulto(s) creados`))
      .catch((error: Error) => setStatus(error.message))
  }

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoginError('')
    login(email, password)
      .then((nextSession) => {
        localStorage.setItem('scald-session', JSON.stringify(nextSession))
        setSession(nextSession)
        setStatus('Sesión iniciada · API conectada')
      })
      .catch((error: Error) => setLoginError(error.message))
  }

  if (!session) {
    return (
      <main className="login-page">
        <section className="login-card">
          <div className="brand"><div className="brand-mark">S</div><div><div className="brand-name">SCALD</div><div className="brand-subtitle">Control logístico</div></div></div>
          <p className="eyebrow">Acceso operativo</p>
          <h1>Entrar al control de despachos</h1>
          <p className="page-copy">Usa una cuenta del backend para consultar la operación e importar hojas de ruta.</p>
          <form className="login-form" onSubmit={handleLogin}>
            <label>Correo<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Contraseña<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
            {loginError && <p className="form-error">{loginError}</p>}
            <button className="button primary" type="submit">Iniciar sesión</button>
          </form>
          <p className="login-hint">API: 127.0.0.1:8000 · PostgreSQL: 5433</p>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div className="brand-copy">
            <div className="brand-name">SCALD</div>
            <div className="brand-subtitle">Control logístico</div>
          </div>
        </div>

        <nav className="nav-group" aria-label="Navegación principal">
          <div className="nav-label">Operación</div>
          {navItems.map(([icon, label]) => (
            <button
              className={`nav-item ${activeView === label ? 'active' : ''}`}
              key={label}
              onClick={() => setActiveView(label)}
            >
              <span className="nav-icon" aria-hidden="true">{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">Semana 6 · Backend en construcción<br />Ambiente local</div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">SCALD / <strong>{activeView}</strong></div>
          <div className="top-actions">
            <span className="status-dot">{status}</span>
            <button className="user-chip" onClick={() => { localStorage.removeItem('scald-session'); setSession(null) }}>Cerrar sesión</button>
          </div>
        </header>

        <div className="content">
          <section className="page-heading">
            <div>
              <p className="eyebrow">Control de despachos</p>
              <h1>{activeView}</h1>
              <p className="page-copy">Una lectura clara del estado operativo: hojas activas, bultos esperados y excepciones que necesitan seguimiento.</p>
            </div>
            <button className="button primary" onClick={() => setActiveView('Importación')}>+ Cargar hoja de ruta</button>
          </section>

          <section className="metrics" aria-label="Indicadores operativos">
            <article className="metric"><span className="metric-label">Hojas activas</span><strong className="metric-value">12</strong><span className="metric-note">3 requieren revisión</span></article>
            <article className="metric"><span className="metric-label">Bultos esperados</span><strong className="metric-value">1.284</strong><span className="metric-note">+86 desde ayer</span></article>
            <article className="metric"><span className="metric-label">Pistoleados</span><strong className="metric-value">1.219</strong><span className="metric-note">94,9% del total</span></article>
            <article className="metric"><span className="metric-label">Incidencias abiertas</span><strong className="metric-value">18</strong><span className="metric-note">6 duplicados</span></article>
          </section>

          <div className="workspace-grid">
            <section className="card">
              <div className="card-header">
                <div><h2 className="card-title">Hojas de ruta recientes</h2><p className="card-subtitle">Seguimiento del turno actual</p></div>
                <button className="button">Ver todas</button>
              </div>
              <div className="card-body table-wrap">
                <table>
                  <thead><tr><th>Hoja</th><th>Ruta</th><th>Esperados</th><th>Pistoleados</th><th>Estado</th></tr></thead>
                  <tbody>{routes.map((item) => <tr key={item.code}><td>{item.code}<br /><small>{item.type}</small></td><td>{item.route}</td><td>{item.expected}</td><td>{item.scanned}</td><td><span className={`badge ${item.status === 'Cerrada' ? 'muted' : ''}`}>{item.status}</span></td></tr>)}</tbody>
                </table>
              </div>
            </section>

            <section className="card">
              <div className="card-header"><div><h2 className="card-title">Actividad reciente</h2><p className="card-subtitle">Últimas operaciones registradas</p></div></div>
              <div className="card-body activity-list">
                <div className="activity"><div><strong>Importación preparada</strong><span>2 hojas listas para procesar · ahora</span></div></div>
                <div className="activity"><div><strong>Incidencia pendiente</strong><span>BU12345678 · duplicado · hace 8 min</span></div></div>
                <div className="activity"><div><strong>Reasignación completada</strong><span>HRE-2026-0775 → HRD-2026-1641 · hace 21 min</span></div></div>
              </div>
            </section>
          </div>

          <section className="card import-card">
            <div className="card-header"><div><h2 className="card-title">Importar hojas de ruta</h2><p className="card-subtitle">Carga PDFs CMK HRD/HRE para crear esperados</p></div><span className="badge muted">Máx. 10 MB</span></div>
            <div className="card-body">
              <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragEnter={(event) => { event.preventDefault(); setDragging(true) }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); addFiles(Array.from(event.dataTransfer.files)) }}>
                <p className="drop-title">Arrastra tus PDFs aquí</p>
                <p className="drop-copy">También puedes seleccionarlos desde tu equipo. El backend validará cada archivo y devolverá el resultado individual.</p>
                <label className="button primary" htmlFor="pdf-input">Seleccionar PDFs</label>
                <input id="pdf-input" type="file" accept=".pdf,application/pdf" multiple onChange={(event) => addFiles(Array.from(event.target.files ?? []))} />
              </div>
              {files.length > 0 && <div className="file-list">{files.map((file) => <div className="file-row" key={`${file.name}-${file.size}`}><strong>{file.name}</strong><span>{formatBytes(file.size)}</span></div>)}</div>}
              <p className="notice">{status}</p>
              <button className="button primary" onClick={handleImport} disabled={!files.length}>Preparar importación</button>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
