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
- Pruebas funcionales con `pytest`.

### Pendiente para alcanzar el alcance del legado

- Parser CMK para PDF HRD/HRE.
- Importación simple y masiva de PDF.
- Persistencia de OV, factura, cliente y origen.
- Incidencias y estados de seguimiento.
- Reasignación transaccional de bultos.
- Auditoría de cambios.
- Reportes y dashboard.
- Migraciones Alembic y configuración PostgreSQL 16.

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
	├── tests/
	├── requirements.txt
	└── README.md
```

## Ejecutar frontend

```bash
npm install
npm run dev
```

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
DATABASE_URL=sqlite:///./scald.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
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
GET  /health
```

## Pruebas

```bash
cd src/backend
python -m pytest -q
```

Las pruebas usan datos únicos por ejecución para no depender de una base persistente previa.
