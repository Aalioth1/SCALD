import type { ComponentType, ReactNode } from 'react'
import { IconAlertTriangle, IconClipboardList, IconLayoutDashboard, IconReportAnalytics, IconRoute, IconUsers } from '@tabler/icons-react'
import logo from '../assets/logo.png'

const navIcons: Record<string, ComponentType<{ size?: number; stroke?: number; className?: string }>> = {
  dashboard: IconLayoutDashboard,
  hojas: IconRoute,
  incidencias: IconAlertTriangle,
  reporte: IconReportAnalytics,
  usuarios: IconUsers,
  registros: IconClipboardList,
}

export type NavItem = { id: string; label: string }

type Props = {
  view: string
  crumb: string
  userName: string
  onNavigate: (view: string) => void
  onLogout: () => void
  actions?: ReactNode
  items?: NavItem[]
  children: ReactNode
}

const defaultItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'hojas', label: 'Hojas de Ruta' },
  { id: 'incidencias', label: 'Incidencias' },
]

export default function AppShell({ view, crumb, userName, onNavigate, onLogout, actions, items = defaultItems, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img alt="SCALD, Control y Auditoría Logística de Despachos" className="brand-logo" src={logo} />
        </div>
        <nav className="nav-group" aria-label="Navegación principal">
          {items.map((item) => {
            const Icon = navIcons[item.id] ?? IconLayoutDashboard
            return (
              <button
                className={`nav-item ${view === item.id ? 'active' : ''}`}
                key={item.id}
                onClick={() => onNavigate(item.id)}
                type="button"
              >
                <Icon className="nav-icon" size={18} stroke={1.75} aria-hidden />
                {item.label}
              </button>
            )
          })}
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
