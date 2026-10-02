import { type FormEvent, useState } from 'react'
import logo from '../assets/logo.png'
import { ApiError } from '../api/client'
import { getMe, login } from '../api/services'
import type { Acceso, UserPublic } from '../api/types'

type Props = {
  onSuccess: (token: string, user: UserPublic) => void
}

const accesos: Array<{ id: Acceso; label: string }  > = [
  { id: 'AUDITOR', label: 'Auditor' },
  { id: 'ADMIN', label: 'Administrador' },
]

export default function LoginPage({ onSuccess }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [acceso, setAcceso] = useState<Acceso>('AUDITOR')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    login(email, password, acceso)
      .then((session) => getMe(session.access_token).then((user) => onSuccess(session.access_token, user)))
      .catch((reason: Error) => setError(reason instanceof ApiError ? reason.message : 'No se pudo iniciar sesión'))
      .finally(() => setLoading(false))
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="brand">
          <img alt="SCALD, Control y Auditoría Logística de Despachos" className="brand-logo" src={logo} />
        </div>
        <h2>Ingresar al sistema</h2>
        <p className="login-description">Selecciona el tipo de usuario y ingresa tus credenciales para continuar</p>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="role-switch" role="radiogroup" aria-label="Tipo de usuario">
            {accesos.map((item) => (
              <button
                aria-checked={acceso === item.id}
                className={acceso === item.id ? 'active' : ''}
                key={item.id}
                onClick={() => setAcceso(item.id)}
                role="radio"
                type="button"
              >
                <span className="role-mark" aria-hidden="true" />
                <strong>{item.label}</strong>
              </button>
            ))}
          </div>
          <label>Correo<input autoComplete="username" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} /></label>
          <label>Contraseña<input autoComplete="current-password" minLength={8} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} /></label>
          {error && <p className="form-error">{error}</p>}
          <button className="button primary" disabled={loading} type="submit">{loading ? 'Ingresando…' : 'Iniciar sesión'}</button>
        </form>
      </section>
    </main>
  )
}
