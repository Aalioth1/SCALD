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
- Dashboard frontend y exportación avanzada de reportes.
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
