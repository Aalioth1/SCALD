import { type FormEvent, useState } from 'react'
import logo from '../assets/logo.png'
import { ApiError } from '../api/client'
import { getMe, login } from '../api/services'
import type { UserPublic } from '../api/types'

type Props = {
  onSuccess: (token: string, user: UserPublic) => void
}

export default function LoginPage({ onSuccess }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    login(email, password)
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
        <h1>Entrar al control de despachos</h1>
        <form className="login-form" onSubmit={handleSubmit}>
          <label>Correo<input autoComplete="username" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} /></label>
          <label>Contraseña<input autoComplete="current-password" minLength={8} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} /></label>
          {error && <p className="form-error">{error}</p>}
          <button className="button primary" disabled={loading} type="submit">{loading ? 'Ingresando…' : 'Iniciar sesión'}</button>
        </form>
      </section>
    </main>
  )
}
