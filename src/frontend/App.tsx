import { useEffect, useState } from 'react'
import { getMe } from './api/services'
import type { UserPublic } from './api/types'
import AppShell from './components/AppShell'
import LoginPage from './pages/LoginPage'
import AdminPage from './pages/AdminPage'
import DashboardPage from './pages/DashboardPage'
import HojasPage from './pages/HojasPage'
import HojaDetallePage from './pages/HojaDetallePage'
import IncidenciasPage from './pages/IncidenciasPage'
import ReportePage from './pages/ReportePage'
import './styles.css'

type Screen = 'dashboard' | 'hojas' | 'detalle' | 'incidencias' | 'reporte'

type StoredSession = {
  token: string
  user: UserPublic
}

const STORAGE_KEY = 'scald-session'

function readSession(): StoredSession | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Partial<StoredSession> & { access_token?: string }
    if (parsed.token && parsed.user) return { token: parsed.token, user: parsed.user }
    if (parsed.access_token) return { token: parsed.access_token, user: { id: 0, nombre: 'Usuario', apellido: '', email: '', role: null } }
    return null
  } catch {
    return null
  }
}

export default function App() {
  const [session, setSession] = useState<StoredSession | null>(() => readSession())
  const [screen, setScreen] = useState<Screen>('dashboard')
  const [hojaId, setHojaId] = useState<number | null>(null)
  const [focusPistoleo, setFocusPistoleo] = useState(false)

  useEffect(() => {
    if (!session?.token) return
    getMe(session.token)
      .then((user) => {
        const next = { token: session.token, user }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
        setSession(next)
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY)
        setSession(null)
      })
  }, [session?.token])

  const openHoja = (id: number, pistoleo = false) => {
    setHojaId(id)
    setFocusPistoleo(pistoleo)
    setScreen('detalle')
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setSession(null)
    setScreen('dashboard')
  }

  if (!session) {
    return (
      <LoginPage
        onSuccess={(token, user) => {
          const next = { token, user }
          localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
          setSession(next)
        }}
      />
    )
  }

  const userName = `${session.user.nombre} ${session.user.apellido}`.trim() || session.user.email
  if (session.user.role === 'ADMIN') {
    return <AdminPage onLogout={logout} token={session.token} userId={session.user.id} userName={userName} />
  }

  const nav = screen === 'detalle' ? 'hojas' : screen
  const crumb = screen === 'detalle'
    ? 'Hojas de Ruta'
    : screen === 'incidencias'
      ? 'Incidencias'
      : screen === 'reporte'
        ? 'Reporte'
        : screen === 'hojas'
          ? 'Hojas de Ruta'
          : 'Dashboard'

  return (
    <AppShell
      actions={screen === 'dashboard' || screen === 'hojas' ? undefined : null}
      crumb={crumb}
      items={[
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'hojas', label: 'Hojas de Ruta' },
        { id: 'incidencias', label: 'Incidencias' },
        { id: 'reporte', label: 'Reporte' },
      ]}
      onLogout={logout}
      onNavigate={(view) => setScreen(view as Screen)}
      userName={userName}
      view={nav}
    >
      {screen === 'dashboard' && (
        <DashboardPage
          isAdmin={false}
          onIncidencias={() => setScreen('incidencias')}
          onOpenHoja={(id) => openHoja(id)}
          onPistoleo={(id) => openHoja(id, true)}
          onReporte={() => setScreen('reporte')}
          onVerTodas={() => setScreen('hojas')}
          token={session.token}
        />
      )}
      {screen === 'hojas' && (
        <HojasPage onOpenHoja={(id) => openHoja(id)} token={session.token} />
      )}
      {screen === 'detalle' && hojaId !== null && (
        <HojaDetallePage canEdit={false} focusPistoleo={focusPistoleo} hojaId={hojaId} token={session.token} />
      )}
      {screen === 'incidencias' && <IncidenciasPage onOpenHoja={(id) => openHoja(id)} token={session.token} />}
      {screen === 'reporte' && <ReportePage token={session.token} />}
    </AppShell>
  )
}
