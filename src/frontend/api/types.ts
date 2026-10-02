export type AuthSession = {
  access_token: string
  token_type: string
}

export type UserPublic = {
  id: number
  nombre: string
  apellido: string
  email: string
  role: string | null
}

export type HojaEstado = 'ACTIVA' | 'INACTIVA' | 'CERRADA'
export type HojaTipo = 'HRD' | 'HRE'

export type HojaRuta = {
  id: number
  usuario_id: number
  codigo: string
  tipo: HojaTipo
  fecha: string
  fecha_registro: string
  ruta: string
  transporte: string | null
  cantidad_declarada: number
  cantidad_bultos: number
  estado: HojaEstado
  activo: boolean
}

export type HojaRutaInput = {
  codigo: string
  tipo: HojaTipo
  fecha: string
  ruta: string
  transporte: string | null
  cantidad_declarada: number
  estado: HojaEstado
}

export type Bulto = {
  id: number
  usuario_id: number
  codigo: string
  hoja_ruta_id: number
  estado: string
  pistoleado: boolean
  fecha: string | null
  info_adicional: string | null
}

export type Pistoleo = {
  id: number
  codigo_bulto: string
  hoja_ruta_id: number | null
  bulto_id: number | null
  usuario_id: number
  fecha_hora: string
  estado: string
  observacion: string | null
}

export type Incidencia = {
  id: number
  tipo: string
  hoja_ruta_id: number | null
  bulto_id: number | null
  usuario_id: number | null
  estado: string
  observaciones: string | null
  nueva_hoja_ruta_id: number | null
  fecha_creacion: string
  fecha_resolucion: string | null
}

export type Reasignacion = {
  id: number
  bulto_id: number
  hoja_origen_id: number
  hoja_destino_id: number
  incidencia_id: number | null
  usuario_id: number
  fecha_hora: string
  motivo: string
  observaciones: string | null
  estado: string
}

export type ReporteResumen = {
  total_hojas: number
  total_bultos_esperados: number
  total_pistoleos: number
  ok: number
  faltantes: number
  duplicados: number
  sin_lista_esperada: number
  no_pertenece: number
  reasignados: number
  incidencias_pendientes: number
  incidencias_regularizadas: number
}

export type ReporteOperativo = {
  resumen: ReporteResumen
  hojas: Array<{
    codigo: string
    tipo: string
    registro: string
    ruta: string
    transporte: string | null
    estado: string
    esperados: number
    pistoleados: number
    faltantes: number
    incidencias: number
  }>
  faltantes: Array<{
    codigo: string
    hoja: string
    ruta: string
    registro: string
  }>
  incidencias: Array<{
    registro: string
    hoja: string
    bulto: string
    tipo: string
    estado: string
    observaciones: string
  }>
  pendientes: number
  regularizadas: number
}

export type ReporteHoja = ReporteResumen & {
  hoja_ruta_id: number
  codigo: string
  tipo: string
  fecha: string
  ruta: string
  estado: string
}

export type ImportResult = {
  archivos_procesados: number
  archivos_exitosos: number
  archivos_fallidos: number
  hojas_creadas: number
  hojas_actualizadas: number
  bultos_creados: number
  resultados: Array<{
    archivo: string
    exitoso: boolean
    hoja_ruta: string | null
    bultos_creados: number
    bultos_existentes: number
    error: string | null
  }>
}

export type Auditoria = {
  id: number
  entidad: string
  accion: string
  datos_nuevos: Record<string, unknown> | null
  fecha_hora: string
}

export type Acceso = 'ADMIN' | 'AUDITOR'

export type UsuarioAdmin = {
  id: number
  nombre: string
  apellido: string
  email: string
  rol: Acceso | string
  activo: boolean
}

export type UsuarioInput = {
  nombre: string
  apellido: string
  email: string
  password?: string
  rol: Acceso
}

export type ActividadUsuario = {
  usuario_id: number
  nombre: string
  apellido: string
  email: string
  rol: string
  activo: boolean
  total_hojas: number
  total_bultos: number
  total_pistoleos: number
  total_incidencias: number
  bultos_esperados: number
  bultos_pistoleados: number
  hojas: Array<{ id: number; codigo: string; fecha: string; fecha_registro: string; ruta: string; estado: string; situacion: 'VIGENTE' | 'ARCHIVADO' | 'ELIMINADO' }>
  pistoleos: Array<{ id: number; codigo_bulto: string; estado: string; fecha_hora: string; observacion: string | null }>
  faltantes: Array<{ id: number; codigo: string; hoja: string }>
  incidencias: Array<{ id: number; hoja: string; bulto: string; tipo: string; estado: string }>
  eventos: Array<{ id: number; entidad: string; accion: string; detalle: string; fecha_hora: string }>
}
