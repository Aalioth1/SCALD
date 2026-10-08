# SCALD

Sistema de Control y Auditoría Logística de Despachos. Este repositorio contiene un frontend inicial en React/Vite y un backend en FastAPI para transformar progresivamente el sistema legado `Control Auditor`, basado en Excel y PDF, en una plataforma centralizada.

## Estado actual

### Frontend

La vista inicial permite seleccionar uno o varios PDF y validar localmente que sean archivos PDF. Actualmente muestra el flujo de prueba; todavía no envía los archivos al backend porque el endpoint de importación está pendiente.

### Backend implementado

- FastAPI con documentación OpenAPI en `/docs` y `/redoc`.
- Configuración por variables de entorno.
- SQLAlchemy con SQLite por defecto para desarrollo local.
- Autenticación JWT y contraseñas con bcrypt.
- Roles básicos `ADMIN` y `AUDITOR`.
- CRUD inicial de hojas de ruta.
- Alta y consulta de bultos esperados.
- Registro básico de pistoleos.
- Consulta, regularización y anulación de incidencias.
- Parser CMK inicial e importación múltiple de PDF con resultados parciales.
- Bitácora de auditoría para operaciones críticas y consulta administrativa.
- Reportes backend de resumen, hoja de ruta e incidencias.
- Pruebas funcionales con `pytest`.

### Pendiente para alcanzar el alcance del legado

- OCR para PDFs escaneados y validación avanzada de layouts CMK.
- Persistencia de OV, factura, cliente y origen.
- Incidencias y estados de seguimiento.
- Reasignación transaccional de bultos.
- Auditoría completa de CRUD y permisos.
- Procedimientos y triggers PostgreSQL para operaciones críticas.

## Estructura

```text
src/
├── App.tsx                 # Vista inicial de carga PDF
├── main.tsx
└── backend/
	├── app/
	│   ├── api/v1/         # Controladores REST
	│   ├── core/           # Configuración, seguridad y BD
	│   ├── models/         # Entidades SQLAlchemy
	│   ├── repositories/   # Persistencia
	│   ├── schemas/        # Validación Pydantic
	│   └── services/       # Lógica de negocio
	├── alembic/              # Migraciones versionadas
	├── alembic.ini
	├── docker-compose.yml    # PostgreSQL 16
	├── tests/
	├── requirements.txt
	└── README.md
```

## Ejecutar frontend

```bash
npm install
npm run dev
```

## Preparar PostgreSQL y Alembic

Docker debe estar instalado y ejecutándose. Desde el backend:

```bash
cd src/backend
copy .env.example .env
docker compose up -d postgres
python -m alembic upgrade head
```

La migración inicial crea las tablas actuales y los roles `ADMIN` y `AUDITOR`. No se deben crear tablas manualmente en pgAdmin.

Para comprobar la revisión aplicada:

```bash
python -m alembic current
```

Para detener PostgreSQL sin eliminar sus datos:

```bash
docker compose stop postgres
```

Para eliminar también el volumen local de desarrollo:

```bash
docker compose down -v
```

> Docker no estaba disponible en el entorno donde se preparó esta configuración. La migración sí fue verificada sobre una base SQLite temporal y llegó a la revisión `20260928_0001`.

## Ejecutar backend

Desde la raíz del repositorio:

```bash
cd src/backend
python -m uvicorn app.main:app --reload
```

Luego abrir `http://127.0.0.1:8000/docs`.

## Desplegar frontend y backend en Vercel

El repositorio está preparado para desplegarse como un único proyecto Vercel:

- El frontend Vite se publica desde `dist`.
- FastAPI se ejecuta como la función Python `api/index.py`.
- Las rutas `/api/*` se redirigen internamente a FastAPI.

La base de datos debe ser PostgreSQL persistente (por ejemplo, Neon o Supabase).
No se debe usar SQLite en Vercel porque el sistema de archivos de las funciones
es efímero.

En Vercel, configurar estas variables de entorno:

```env
DATABASE_URL=postgresql+psycopg://usuario:contraseña@host/base
SECRET_KEY=una-clave-larga-y-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=https://tu-proyecto.vercel.app
ENVIRONMENT=production
DEBUG=false
```

Después de crear la base PostgreSQL, ejecutar las migraciones desde un entorno
que tenga acceso a ella:

```bash
cd src/backend
python -m alembic upgrade head
```

Para crear las cuentas iniciales sin guardar contraseñas en el repositorio,
ejecutar desde la raíz con las variables de conexión y contraseñas configuradas:

```bash
set SCALD_ADMIN_PASSWORD=una-contraseña-segura
set SCALD_AUDITOR_PASSWORD=otra-contraseña-segura
python src/backend/scripts/seed_users.py
```

El script usa por defecto `admin@scald.com` con rol `ADMIN` y
`moises@scald.com` con rol `AUDITOR`. También permite cambiar los correos
mediante `SCALD_ADMIN_EMAIL` y `SCALD_AUDITOR_EMAIL`.

El plan Hobby de Vercel tiene límites de ejecución y las funciones no deben
usarse como almacenamiento persistente. El procesamiento de reportes PDF debe
validarse en el despliegue porque `weasyprint` depende de librerías nativas.

### Demo académica sin PostgreSQL

Para una presentación académica, `vercel.json` activa un modo demo que usa
SQLite en `/tmp` y crea automáticamente estas cuentas:

```text
admin@scald.com  / scald123  (Administrador)
moises@scald.com / scald123  (Auditor)
```

La base es temporal y puede reiniciarse cuando Vercel recicle la función. Esta
configuración no debe usarse para datos reales. Para desactivar el modo demo,
eliminar `SCALD_DEMO_MODE` y configurar una base PostgreSQL persistente.

## Configuración local

Copiar `.env.example` como `.env` dentro de `src/backend`:

```env
SECRET_KEY=change-me-in-production
DATABASE_URL=postgresql+psycopg://scald:scald_dev_password@localhost:5433/scald
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Endpoints disponibles

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/hojas-ruta
GET  /api/v1/hojas-ruta
GET  /api/v1/hojas-ruta/{id}
PUT  /api/v1/hojas-ruta/{id}
DELETE /api/v1/hojas-ruta/{id}
POST /api/v1/bultos
GET  /api/v1/bultos
GET  /api/v1/bultos/{id}
POST /api/v1/pistoleos
POST /api/v1/importaciones/hojas-ruta
GET  /api/v1/auditoria
GET  /api/v1/reportes/resumen
GET  /api/v1/reportes/hoja-ruta/{id}
GET  /api/v1/reportes/incidencias
GET  /api/v1/incidencias
GET  /api/v1/incidencias/{id}
PATCH /api/v1/incidencias/{id}/regularizar
PATCH /api/v1/incidencias/{id}/anular
GET  /health
```

## Pruebas

```bash
cd src/backend
python -m pytest -q
```

Las pruebas usan datos únicos por ejecución para no depender de una base persistente previa.
