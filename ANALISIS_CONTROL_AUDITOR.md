# ANÁLISIS CONTROL AUDITOR -> SCALD

## 1. Propósito del sistema original

El sistema original "Control Auditor" es una solución local enfocada en la auditoría logística de despachos. Su funcionamiento se apoya principalmente en hojas de ruta en PDF, archivos Excel, registro de bultos, pistoleo manual o escaneado, comparación entre esperados y pistoleados, seguimiento de incidencias y regularización de discrepancias. La lógica de negocio está codificada en scripts de Python y dentro de un Excel dinámico utilizado como herramienta operativa.

## 2. Funcionalidades detectadas

- Carga de PDF de hojas de ruta.
- Identificación de tipos HRD/HRE.
- Extracción de datos del documento.
- Extracción de bultos esperados.
- Registro de bultos esperados.
- Registro de bultos pistoleados.
- Comparación esperados vs pistoleados.
- Detección de faltantes, duplicados y sin lista.
- Detección de bultos sin hoja de ruta.
- Registro y seguimiento de incidencias.
- Regularización y reasignación de incidencias.
- Corrección de fechas.
- Migración de bultos entre hojas.
- Eliminación de hojas de ruta.
- Generación de indicadores y reportes.
- Mantenimiento de respaldos.
- Trabajo con múltiples registros y auditorías.

## 3. Entidades detectadas

- Usuario / analista.
- Rol / perfil.
- Hoja de ruta.
- Bulto esperado.
- Pistoleo.
- Incidencia.
- Reasignación.
- Transporte / ruta.
- Archivo importado.
- Auditoría / trazabilidad.

## 4. Reglas de negocio

- La hoja de ruta puede ser HRD o HRE.
- El código debe ser validado con formato TIPO-AÑO-NÚMERO.
- No se debe duplicar una hoja de ruta.
- Un bulto esperado pertenece a una hoja de ruta.
- El mismo bulto no debe repetirse dentro de la misma hoja.
- Un pistoleo puede corresponder a un bulto esperado o no.
- Deben detectarse discrepancias: OK, FALTANTE, DUPLICADO, SIN LISTA ESPERADA, SIN HOJA DE RUTA, REASIGNADO.
- Las incidencias deben seguir estados PENDIENTE, REGULARIZADO, REASIGNADO, ANULADO.
- En la reasignación de bultos se debe usar transacción y rollback.
- El sistema debe mantener trazabilidad de acciones.

## 5. Estados

### Estados de hoja de ruta

- ACTIVA
- INACTIVA
- CERRADA

### Estados de bulto

- PENDIENTE
- OK
- FALTANTE
- DUPLICADO
- SIN LISTA
- SIN HOJA
- REASIGNADO

### Estados de incidencia

- PENDIENTE
- REGULARIZADO
- REASIGNADO
- ANULADO

## 6. Casos borde relevantes

- PDF inexistente.
- PDF que no sea válido.
- PDF sin bultos.
- Bultos duplicados.
- Pérdida de fechas, rutas o transporte.
- Bulto sin hoja de ruta.
- Bulto sin lista esperada.
- Reasignación origen = destino.
- Bulto ya existente en destino.
- Eliminación de hoja con registros asociados.
- Operaciones concurrentes.
- Múltiples archivos en la misma importación.

## 7. Mapeo desde Excel hacia SCALD

- "Esperados" -> tabla bultos esperados.
- "Pistoleo" -> tabla pistoleos en conjunto con auditoría.
- "Pendientes" -> vista de incidencias pendientes.
- "Seguimiento" -> incidencias y trazabilidad.
- "Informe" -> reportes agregados.
- "Detalle Observaciones" -> incidencias y comentarios.
- "\_Listas" -> datos maestros relacionados a transports, rutas, lotes y validaciones.

## 8. Propuesta de arquitectura

Se propone un backend FastAPI con capas bien separadas:

- API REST / controladores
- Servicios de negocio
- Repositorios / acceso a datos
- Modelos SQLAlchemy
- Schemas Pydantic
- Seguridad JWT y roles
- PostgreSQL como fuente central
- Capa de procesado PDF independiente

## 9. Propuesta de base de datos

Entidades principales:

- usuarios
- roles
- hojas_ruta
- bultos
- pistoleos
- incidencias
- auditoria
- reasignaciones
- archivos_importados

Relaciones principales:

- Rol 1:N Usuario
- HojaRuta 1:N Bulto
- HojaRuta 1:N Pistoleo
- HojaRuta 1:N Incidencia
- Bulto 1:N Pistoleo
- Bulto 1:N Incidencia
- Usuario 1:N Pistoleo
- Usuario 1:N Incidencia

## 10. Endpoints iniciales

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me
- POST /api/v1/hojas-ruta
- GET /api/v1/hojas-ruta
- GET /api/v1/hojas-ruta/{id}
- PUT /api/v1/hojas-ruta/{id}
- DELETE /api/v1/hojas-ruta/{id}
- POST /api/v1/bultos
- GET /api/v1/bultos
- POST /api/v1/pistoleos
- GET /api/v1/reportes/resumen
- POST /api/v1/hojas-ruta/importar

## 11. Revisión del SCALD actual

La implementación existente fue revisada después de incorporar el sistema legado al workspace.

### Funciona actualmente

- El frontend Vite compila y muestra una vista de selección local de PDF.
- El backend FastAPI inicia con SQLite por defecto.
- Registro, login y consulta del usuario autenticado funcionan con JWT y bcrypt.
- El CRUD básico de hojas de ruta valida códigos y duplicados.
- La creación y consulta de bultos funciona.
- El endpoint de pistoleo registra un evento asociado a un bulto existente.
- Las pruebas funcionales existentes pueden ejecutarse con datos aislados por ejecución.

### No está implementado todavía

- El botón del frontend no sube archivos al backend.
- No existe `pdf_parser_service.py` ni un endpoint de importación PDF.
- El parser CMK del legado no fue trasladado todavía.
- El pistoleo repetido no cambia a `DUPLICADO` ni crea automáticamente una incidencia.
- Un bulto inexistente responde `404`, pero el requisito funcional pide representar `SIN LISTA ESPERADA` o `SIN HOJA DE RUTA` según el contexto.
- No existen endpoints operativos de incidencias, reasignación, reportes o auditoría.
- La reasignación no está implementada como transacción de base de datos.
- `Base.metadata.create_all()` se usa como inicialización temporal; todavía no hay migraciones Alembic.
- La configuración por defecto usa SQLite, no PostgreSQL 16.

### Verificaciones ejecutadas

- `npm run build`: correcto.
- `python -m pytest -q`: se ajustaron las pruebas para no depender de registros persistentes de ejecuciones anteriores.

### Prioridad recomendada

1. Extraer el parser CMK a un servicio backend y agregar importación PDF.
2. Separar fecha documental y fecha operativa, y conservar OV, factura, cliente y origen.
3. Implementar el motor de auditoría completo con duplicados, faltantes y bultos sin lista.
4. Agregar incidencias, reasignación transaccional y auditoría.
5. Crear reportes equivalentes a `Pistoleo`, `Pendientes`, `Informe` y `Detalle Observaciones`.
6. Incorporar Alembic, PostgreSQL y pruebas de integración con base aislada.

## 12. Riesgos técnicos

- El Excel legado depende de rangos fijos, fórmulas y recálculo de Excel.
- La fecha que se persiste como operativa puede diferir de la fecha documental del PDF.
- OV, factura y cliente se extraen en el legado, pero el layout compacto actual no los conserva.
- Los PDFs escaneados o con layout distinto pueden producir cero datos porque no existe OCR.
- El legado permite reasignaciones manuales mediante celdas; SCALD debe validar la hoja destino en una transacción.
- Los respaldos protegen el archivo, pero no reemplazan una auditoría de cambios.

## 13. Decisiones de diseño

- No se reemplaza la lógica original por una arquitectura arbitraria.
- Se articula una base mejorada sobre la lógica funcional detectada.
- Se prioriza el backend web y centralizado.
- Se separa la lógica de PDF en un servicio independiente para permitir cambiar el parser sin afectar el resto del sistema.
- Se adopta PostgreSQL y FastAPI para cumplir la necesidad de multiusuario, trazabilidad y seguridad.
- El código legado se conserva como referencia de comportamiento, no como dependencia de ejecución del backend.
- El Excel se utilizará solo como fuente de migración o exportación, nunca como almacenamiento principal.
- La migración será progresiva: primero hojas y bultos, luego pistoleos históricos, incidencias y reportes.
