import { type FormEvent, useEffect, useState } from 'react'
import { IconAlertCircle, IconPackages, IconScan, IconFiles } from '@tabler/icons-react'
import { ApiError } from '../api/client'
import {
  createUsuario,
  archivarRegistrosUsuario,
  deleteUsuario,
  downloadReportePdf,
  eliminarRegistrosHoja,
  getActividadUsuario,
  listUsuarios,
  setUsuarioActivo,
  updateUsuario,
} from '../api/services'
import type { Acceso, ActividadUsuario, UsuarioAdmin } from '../api/types'
import AppShell from '../components/AppShell'
import SortHeader, { compareText, nextSort, type SortState } from '../components/SortHeader'
import { formatDate, formatNumber, formatPercent } from '../format'

type Props = {
  token: string
  userId: number
  userName: string
  onLogout: () => void
}

type FormState = {
  nombre: string
  apellido: string
  email: string
  password: string
  rol: Acceso
}

const emptyForm: FormState = { nombre: '', apellido: '', email: '', password: '', rol: 'AUDITOR' }
const adminNav = [
  { id: 'usuarios', label: 'Usuarios' },
  { id: 'registros', label: 'Registros' },
]

type AdminView = 'usuarios' | 'registros'

function ordenarLista<T>(items: T[], sort: { dir: 'asc' | 'desc' } | null, value: (item: T) => string) {
  if (!sort) return items
  return [...items].sort((a, b) => compareText(value(a), value(b), sort.dir))
}

function fechaLocal(valor: Date) {
  const mes = String(valor.getMonth() + 1).padStart(2, '0')
  const dia = String(valor.getDate()).padStart(2, '0')
  return `${valor.getFullYear()}-${mes}-${dia}`
}

function rangoUltimas48Horas() {
  const ahora = new Date()
  const inicio = new Date(ahora.getTime() - 48 * 60 * 60 * 1000)
  return { desde: fechaLocal(inicio), hasta: fechaLocal(ahora) }
}

function descripcionPeriodo(modo: 'periodo' | 'dia', desde: string, hasta: string) {
  if (modo === 'dia') return desde ? `Registro del ${formatDate(desde)}` : 'Elija un día de registro'
  if (desde && hasta) return `Registro del ${formatDate(desde)} al ${formatDate(hasta)}`
  if (desde) return `Registro desde el ${formatDate(desde)}`
  if (hasta) return `Registro hasta el ${formatDate(hasta)}`
  return 'Todo el historial'
}

function etiquetaSituacion(situacion: string) {
  if (situacion === 'ARCHIVADO') return 'Archivado'
  if (situacion === 'ELIMINADO') return 'Eliminado'
  return 'Vigente'
}

function permiso(rol: string) {
  return rol === 'ADMIN' ? 'Administrador' : 'Auditor'
}

export default function AdminPage({ token, userId, userName, onLogout }: Props) {
  const [view, setView] = useState<AdminView>('usuarios')
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [actividad, setActividad] = useState<ActividadUsuario | null>(null)
  const [form, setForm] = useState<FormState | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  const [confirmArchiveId, setConfirmArchiveId] = useState<number | null>(null)
  const [hojaAEliminar, setHojaAEliminar] = useState<number | null>(null)
  const [registrosVersion, setRegistrosVersion] = useState(0)
  const periodoInicial = rangoUltimas48Horas()
  const [modo, setModo] = useState<'periodo' | 'dia'>('dia')
  const [desde, setDesde] = useState(periodoInicial.desde)
  const [hasta, setHasta] = useState(periodoInicial.hasta)
  const [dia, setDia] = useState(() => fechaLocal(new Date()))
  const [descargando, setDescargando] = useState(false)
  const [ordenHojas, setOrdenHojas] = useState<SortState<'codigo' | 'historial' | 'registro'> | null>(null)
  const [ordenFaltantes, setOrdenFaltantes] = useState<SortState<'bulto' | 'hoja'> | null>(null)
  const [ordenIncidencias, setOrdenIncidencias] = useState<SortState<'hoja' | 'bulto'> | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)

  const refresh = () => {
    listUsuarios(token)
      .then((items) => {
        setUsuarios(items)
        setSelectedId((current) => current ?? items[0]?.id ?? null)
        setError('')
      })
      .catch((reason: Error) => setError(reason.message))
  }

  useEffect(() => {
    refresh()
  }, [token])

  const fechaDesde = modo === 'dia' ? dia : desde
  const fechaHasta = modo === 'dia' ? dia : hasta
  const rangoInvalido = Boolean(fechaDesde && fechaHasta && fechaDesde > fechaHasta)

  useEffect(() => {
    if (view !== 'registros' || selectedId === null) {
      setActividad(null)
      return
    }
    if (rangoInvalido) {
      setActividad(null)
      setError('La fecha inicial no puede ser posterior a la final')
      return
    }
    let alive = true
    getActividadUsuario(token, selectedId, fechaDesde || undefined, fechaHasta || undefined)
      .then((detail) => {
        if (alive) {
          setActividad(detail)
          setError('')
        }
      })
      .catch((reason: Error) => {
        if (alive) setError(reason.message)
      })
    return () => {
      alive = false
    }
  }, [token, selectedId, usuarios, view, registrosVersion, fechaDesde, fechaHasta, rangoInvalido])

  const seleccionarModo = (siguiente: 'periodo' | 'dia') => {
    if (siguiente === modo) return
    if (siguiente === 'periodo') {
      const rango = rangoUltimas48Horas()
      setDesde(rango.desde)
      setHasta(rango.hasta)
    } else {
      setDia(fechaLocal(new Date()))
    }
    setModo(siguiente)
  }

  const descargarReporte = async () => {
    if (selectedId === null || rangoInvalido || descargando) return
    setDescargando(true)
    setError('')
    try {
      const { blob, filename } = await downloadReportePdf(token, fechaDesde || undefined, fechaHasta || undefined, selectedId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'reporte-operativo.pdf'
      link.click()
      URL.revokeObjectURL(url)
    } catch (reason) {
      setError(messageFrom(reason))
    } finally {
      setDescargando(false)
    }
  }

  useEffect(() => {
    if (!notice) return
    const timer = window.setTimeout(() => setNotice(''), 5000)
    return () => window.clearTimeout(timer)
  }, [notice])

  const messageFrom = (reason: unknown) => (reason instanceof ApiError ? reason.message : 'No se pudo completar la operación')

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyForm)
    setConfirmDeleteId(null)
    setError('')
    setNotice('')
  }

  const openEdit = (usuario: UsuarioAdmin) => {
    setEditingId(usuario.id)
    setSelectedId(usuario.id)
    setForm({
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      email: usuario.email,
      password: '',
      rol: usuario.rol === 'ADMIN' ? 'ADMIN' : 'AUDITOR',
    })
    setConfirmDeleteId(null)
    setError('')
    setNotice('')
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form) return
    if (!editingId && form.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    setLoading(true)
    setError('')
    const payload = {
      nombre: form.nombre,
      apellido: form.apellido,
      email: form.email,
      rol: form.rol,
      ...(form.password ? { password: form.password } : {}),
    }
    const request = editingId
      ? updateUsuario(token, editingId, payload)
      : createUsuario(token, { ...payload, password: form.password })
    request
      .then((usuario) => {
        setNotice(editingId ? 'Usuario actualizado' : 'Usuario creado')
        setForm(null)
        setEditingId(null)
        setSelectedId(usuario.id)
        refresh()
      })
      .catch((reason: unknown) => setError(messageFrom(reason)))
      .finally(() => setLoading(false))
  }

  const toggleActivo = (usuario: UsuarioAdmin) => {
    setError('')
    setNotice('')
    setUsuarioActivo(token, usuario.id, !usuario.activo)
      .then(() => {
        setNotice(usuario.activo ? 'Usuario desactivado' : 'Usuario activado')
        refresh()
      })
      .catch((reason: unknown) => setError(messageFrom(reason)))
  }

  const archivar = (usuario: UsuarioAdmin) => {
    if (confirmArchiveId !== usuario.id) {
      setConfirmArchiveId(usuario.id)
      setConfirmDeleteId(null)
      return
    }
    setError('')
    archivarRegistrosUsuario(token, usuario.id)
      .then((result) => {
        setNotice(result.archivadas ? `Se archivaron ${result.archivadas} hojas` : 'No hay registros vigentes')
        setConfirmArchiveId(null)
        setRegistrosVersion((value) => value + 1)
      })
      .catch((reason: unknown) => setError(messageFrom(reason)))
  }

  const eliminarHoja = (hojaId: number) => {
    if (selectedId === null) return
    setError('')
    eliminarRegistrosHoja(token, selectedId, hojaId)
      .then(() => {
        setNotice('Registros de la hoja eliminados')
        setHojaAEliminar(null)
        setRegistrosVersion((value) => value + 1)
      })
      .catch((reason: unknown) => setError(messageFrom(reason)))
  }

  const remove = (usuario: UsuarioAdmin) => {
    if (confirmDeleteId !== usuario.id) {
      setConfirmDeleteId(usuario.id)
      return
    }
    setError('')
    deleteUsuario(token, usuario.id)
      .then(() => {
        setNotice('Usuario eliminado')
        setConfirmDeleteId(null)
        if (selectedId === usuario.id) setSelectedId(null)
        if (editingId === usuario.id) {
          setEditingId(null)
          setForm(null)
        }
        refresh()
      })
      .catch((reason: unknown) => setError(messageFrom(reason)))
  }

  const selected = usuarios.find((usuario) => usuario.id === selectedId) ?? null

  return (
    <AppShell
      crumb={view === 'registros' ? 'Registros' : 'Usuarios'}
      items={adminNav}
      onLogout={onLogout}
      onNavigate={(next) => setView(next as AdminView)}
      userName={userName}
      view={view}
    >
      <div className="stack">
        {error && <p className="form-error">{error}</p>}
        {view === 'usuarios' && (
        <>
        <div className="page-heading">
          <div>
            <h1>Usuarios</h1>
            <p className="meta">Alta, permisos de acceso y estado de cada cuenta</p>
          </div>
          <button className="button primary" onClick={openCreate} type="button">Nuevo usuario</button>
        </div>
        <div className={form ? 'workspace-grid' : 'stack'}>
          <section className="card">
            <div className="table-wrap users-table">
              <table>
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Permiso</th>
                    <th>Estado</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((usuario) => (
                    <tr key={usuario.id}>
                      <td>
                        <div className="code">{usuario.nombre} {usuario.apellido}</div>
                        <div className="meta">{usuario.email}</div>
                      </td>
                      <td>{permiso(usuario.rol)}</td>
                      <td>
                        <span className={`badge ${usuario.activo ? 'ok' : 'closed'}`}>{usuario.activo ? 'Activo' : 'Inactivo'}</span>
                      </td>
                      <td className="actions" onClick={(event) => event.stopPropagation()}>
                        <button className="button tiny" onClick={() => openEdit(usuario)} type="button">Editar </button>
                        <button className="button tiny" onClick={() => archivar(usuario)} type="button">
                          {confirmArchiveId === usuario.id ? 'Confirmar archivado' : 'Archivar registros'}
                        </button>
                        <button className="button tiny" disabled={usuario.id === userId && usuario.activo} onClick={() => toggleActivo(usuario)} type="button">
                          {usuario.activo ? 'Desactivar' : 'Activar'}
                        </button>
                        <button className="button tiny danger" disabled={usuario.id === userId} onClick={() => remove(usuario)} type="button">
                          {confirmDeleteId === usuario.id ? 'Confirmar' : 'Eliminar'}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {usuarios.length === 0 && (
                    <tr>
                      <td className="empty" colSpan={4}>No hay usuarios cargados</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
          {form && (
          <div className="side-stack">
              <section className="card">
                <div className="card-header"><h2>{editingId ? 'Editar usuario' : 'Nuevo usuario'}</h2></div>
                <form className="panel-form" onSubmit={submit}>
                  <label>Nombre<input onChange={(event) => setForm({ ...form, nombre: event.target.value })} required value={form.nombre} /></label>
                  <label>Apellido<input onChange={(event) => setForm({ ...form, apellido: event.target.value })} required value={form.apellido} /></label>
                  <label>Correo<input onChange={(event) => setForm({ ...form, email: event.target.value })} required type="email" value={form.email} /></label>
                  <label>
                    Contraseña
                    <input
                      minLength={editingId ? undefined : 8}
                      onChange={(event) => setForm({ ...form, password: event.target.value })}
                      placeholder={editingId ? 'Ingresa nueva contraseña' : 'Ingresa una nueva contraseña para el usuario'}
                      required={!editingId}
                      type="password"
                      value={form.password}
                    />
                  </label>
                  <label>
                    Permiso de acceso
                    <select disabled={editingId === userId} onChange={(event) => setForm({ ...form, rol: event.target.value as Acceso })} value={form.rol}>
                      <option value="AUDITOR">Auditor</option>
                      <option value="ADMIN">Administrador</option>
                    </select>
                  </label>
                  <div className="form-actions">
                    <button className="button" onClick={() => { setForm(null); setEditingId(null) }} type="button">Cancelar</button>
                    <button className="button primary" disabled={loading} type="submit">{loading ? 'Guardando…' : 'Guardar'}</button>
                  </div>
                </form>
              </section>
          </div>
          )}
        </div>
        </>
        )}
        {view === 'registros' && (
          <>
            <div className="page-heading record-heading">
              <div>
                <h1>Registros</h1>
                <p className="meta">{descripcionPeriodo(modo, fechaDesde, fechaHasta)}</p>
              </div>
              <div className="record-controls">
                <label className="record-filter">
                  Usuario
                  <select onChange={(event) => setSelectedId(Number(event.target.value))} value={selectedId ?? ''}>
                    {usuarios.map((usuario) => (
                      <option key={usuario.id} value={usuario.id}>{usuario.nombre} {usuario.apellido}</option>
                    ))}
                  </select>
                </label>
                <div className="mode-switch compact" role="group" aria-label="Tipo de periodo">
                  <button className={modo === 'dia' ? 'active' : ''} onClick={() => seleccionarModo('dia')} type="button">Día</button>
                  <button className={modo === 'periodo' ? 'active' : ''} onClick={() => seleccionarModo('periodo')} type="button">Periodo</button>
                </div>
                <div className="report-dates">
                  {modo === 'periodo' ? (
                    <>
                      <label>
                        Desde
                        <input max={hasta || undefined} onChange={(event) => setDesde(event.target.value)} type="date" value={desde} />
                      </label>
                      <label>
                        Hasta
                        <input min={desde || undefined} onChange={(event) => setHasta(event.target.value)} type="date" value={hasta} />
                      </label>
                    </>
                  ) : (
                    <label>
                      Día
                      <input onChange={(event) => setDia(event.target.value)} type="date" value={dia} />
                    </label>
                  )}
                </div>
                <button className="button primary" disabled={selectedId === null || rangoInvalido || descargando} onClick={descargarReporte} type="button">
                  {descargando ? 'Generando PDF…' : 'Descargar PDF'}
                </button>
              </div>
            </div>
            {!selected && <p className="empty">No hay usuarios para consultar.</p>}
            {actividad && (
              <>
                {(() => {
                  const hojas = ordenarLista(actividad.hojas, ordenHojas, (hoja) => {
                    if (ordenHojas?.key === 'registro') return hoja.fecha_registro
                    if (ordenHojas?.key === 'historial') return etiquetaSituacion(hoja.situacion)
                    return hoja.codigo
                  })
                  const faltantes = ordenarLista(actividad.faltantes, ordenFaltantes, (item) => (ordenFaltantes?.key === 'hoja' ? item.hoja : item.codigo))
                  const incidencias = ordenarLista(actividad.incidencias, ordenIncidencias, (item) => (ordenIncidencias?.key === 'bulto' ? item.bulto : item.hoja))
                  return (
              <>
                <section className="metrics record-metrics" aria-label="Totales del usuario">
                  <article className="metric">
                    <div className="metric-top"><span>Hojas cargadas</span><IconFiles className="metric-icon orange" size={18} stroke={1.75} /></div>
                    <strong>{formatNumber(actividad.total_hojas)}</strong>
                    <small>{selected?.email}</small>
                  </article>
                  <article className="metric">
                    <div className="metric-top"><span>Bultos cargados</span><IconPackages className="metric-icon ink" size={18} stroke={1.75} /></div>
                    <strong>{formatNumber(actividad.total_bultos)}</strong>
                    <small>En las hojas de este usuario</small>
                  </article>
                  <article className="metric">
                    <div className="metric-top"><span>Pistoleos</span><IconScan className="metric-icon green" size={18} stroke={1.75} /></div>
                    <strong>{formatNumber(actividad.total_pistoleos)}</strong>
                    <small>{formatNumber(actividad.pistoleos.filter((item) => item.estado === 'OK').length)} OK entre los recientes</small>
                  </article>
                  <article className="metric">
                    <div className="metric-top"><span>Incidencias</span><IconAlertCircle className="metric-icon yellow" size={18} stroke={1.75} /></div>
                    <strong>{formatNumber(actividad.total_incidencias)}</strong>
                    <small>Asociadas a este usuario</small>
                  </article>
                  <article className="metric reporte-efficiency">
                    <div>
                      <span>Eficiencia de pistoleo</span>
                      <strong>{formatPercent(actividad.bultos_pistoleados, actividad.bultos_esperados)}</strong>
                    </div>
                    <div className="reporte-bar" aria-hidden="true">
                      <div style={{ width: formatPercent(actividad.bultos_pistoleados, actividad.bultos_esperados) }} />
                    </div>
                  </article>
                </section>
                <div className="record-grid">
                  <section className="card">
                    <div className="card-header"><h2>Hojas de ruta</h2><span className="meta">{formatNumber(actividad.hojas.length)}</span></div>
                    {hojas.length === 0 ? <p className="empty">Sin hojas cargadas</p> : (
                      <div className="table-wrap record-table">
                        <table>
                          <thead>
                            <tr>
                              <SortHeader column="codigo" label="Código" onSort={(key) => setOrdenHojas((current) => nextSort(current, key))} sort={ordenHojas} />
                              <th>Estado</th>
                              <SortHeader column="historial" label="Historial" onSort={(key) => setOrdenHojas((current) => nextSort(current, key))} sort={ordenHojas} />
                              <SortHeader column="registro" label="Registro" onSort={(key) => setOrdenHojas((current) => nextSort(current, key))} sort={ordenHojas} />
                              <th></th>
                            </tr>
                          </thead>
                          <tbody>
                            {hojas.map((hoja) => (
                              <tr key={hoja.id}>
                                <td className="code">{hoja.codigo}</td>
                                <td><span className={`badge ${hoja.estado === 'ACTIVA' ? 'ok' : 'muted'}`}>{hoja.estado}</span></td>
                                <td><span className={`badge ${hoja.situacion === 'VIGENTE' ? 'ok' : hoja.situacion === 'ARCHIVADO' ? 'warn' : 'closed'}`}>{etiquetaSituacion(hoja.situacion)}</span></td>
                                <td>{formatDate(hoja.fecha_registro)}</td>
                                <td className="icon-cell">
                                  {hoja.situacion !== 'ELIMINADO' && (
                                    <button aria-label={`Eliminar registros de ${hoja.codigo}`} className="button tiny danger icon-button" onClick={() => setHojaAEliminar(hoja.id)} title="Eliminar" type="button">
                                      <svg aria-hidden="true" viewBox="0 0 24 24">
                                        <path d="M9 3h6l1 2h5v2H3V5h5l1-2zm-2 6h10l-.8 12H7.8L7 9z" />
                                      </svg>
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                  <section className="card">
                    <div className="card-header"><h2>Bultos faltantes</h2><span className="meta">{formatNumber(actividad.faltantes.length)}</span></div>
                    {faltantes.length === 0 ? <p className="empty">No hay bultos pendientes de pistoleo.</p> : (
                      <div className="table-wrap record-table">
                        <table>
                          <thead>
                            <tr>
                              <SortHeader column="bulto" label="Bulto" onSort={(key) => setOrdenFaltantes((current) => nextSort(current, key))} sort={ordenFaltantes} />
                              <SortHeader column="hoja" label="Hoja" onSort={(key) => setOrdenFaltantes((current) => nextSort(current, key))} sort={ordenFaltantes} />
                            </tr>
                          </thead>
                          <tbody>
                            {faltantes.map((item) => (
                              <tr key={item.id}>
                                <td className="code">{item.codigo}</td>
                                <td>{item.hoja}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                  <section className="card">
                    <div className="card-header">
                      <h2>Incidencias</h2>
                      <span className="meta">{actividad.incidencias.filter((item) => item.estado === 'PENDIENTE').length} pendientes · {actividad.incidencias.filter((item) => item.estado !== 'PENDIENTE').length} regularizadas</span>
                    </div>
                    {incidencias.length === 0 ? <p className="empty">Sin incidencias</p> : (
                      <div className="table-wrap record-table">
                        <table>
                          <thead>
                            <tr>
                              <SortHeader column="hoja" label="Hoja" onSort={(key) => setOrdenIncidencias((current) => nextSort(current, key))} sort={ordenIncidencias} />
                              <SortHeader column="bulto" label="Bulto" onSort={(key) => setOrdenIncidencias((current) => nextSort(current, key))} sort={ordenIncidencias} />
                              <th>Tipo</th><th>Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {incidencias.map((item) => (
                              <tr key={item.id}>
                                <td>{item.hoja}</td>
                                <td className="code">{item.bulto}</td>
                                <td>{item.tipo}</td>
                                <td><span className={`badge ${item.estado === 'PENDIENTE' ? 'closed' : 'ok'}`}>{item.estado}</span></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </div>
              </>
                  )
                })()}
              </>
            )}
          </>
        )}
      </div>
      {hojaAEliminar !== null && actividad && (
        <div className="modal-backdrop" onClick={() => setHojaAEliminar(null)} role="presentation">
          <section aria-labelledby="eliminar-hoja-title" aria-modal="true" className="modal" onClick={(event) => event.stopPropagation()} role="dialog">
            <h2 id="eliminar-hoja-title">Eliminar registros de la hoja</h2>
            <p>Se perderán los bultos, pistoleos e incidencias de {actividad.hojas.find((hoja) => hoja.id === hojaAEliminar)?.codigo}. El historial de administración conservará la fila como eliminada.</p>
            <div className="modal-actions">
              <button className="button" onClick={() => setHojaAEliminar(null)} type="button">Cancelar</button>
              <button className="button danger" onClick={() => eliminarHoja(hojaAEliminar)} type="button">Eliminar registros</button>
            </div>
          </section>
        </div>
      )}
      {notice && (
        <p className="toast" role="status">
          <svg aria-hidden="true" viewBox="0 0 16 16">
            <path d="M3.5 8.2 6.4 11 12.5 4.5" />
          </svg>
          {notice}
        </p>
      )}
    </AppShell>
  )
}
