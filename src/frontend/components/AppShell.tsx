import type { ReactNode } from 'react'
import logo from '../assets/logo.png'

type NavId = 'dashboard' | 'hojas' | 'incidencias'

type Props = {
  view: NavId
  crumb: string
  userName: string
  onNavigate: (view: NavId) => void
  onLogout: () => void
  actions?: ReactNode
  children: ReactNode
}

const items: Array<{ id: NavId; label: string }> = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'hojas', label: 'Hojas de Ruta' },
  { id: 'incidencias', label: 'Incidencias' },
]

export default function AppShell({ view, crumb, userName, onNavigate, onLogout, actions, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img alt="SCALD, Control y Auditoría Logística de Despachos" className="brand-logo" src={logo} />
        </div>
        <nav className="nav-group" aria-label="Navegación principal">
          {items.map((item) => (
            <button
              className={`nav-item ${view === item.id ? 'active' : ''}`}
              key={item.id}
              onClick={() => onNavigate(item.id)}
              type="button"
            >
              <span className={`nav-swatch swatch-${item.id}`} aria-hidden="true" />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <strong>{userName}</strong>
          <button className="link-button" onClick={onLogout} type="button">Cerrar sesión</button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">SCALD <span>›</span> {crumb}</div>
          <div className="top-actions">{actions}</div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  )
}
