# GovData Intelligence Platform

Plataforma modular de automatización e inteligencia de datos públicos del
Estado ecuatoriano. Arquitectura Hexagonal (Ports & Adapters) + Clean
Architecture + SOLID + Repository Pattern + Service Layer + DI.

Fuentes reales integradas:
- **DPE Transparencia** (`transparencia.dpe.gob.ec`): descubrimiento de
  entidades, último mes publicado, numeral "Directorio y distributivo del
  personal", descarga y extracción de funcionarios desde Excel/CSV/PDF.
- **Mis Datos Ecuador** (`misdatosecuador.com`): resolución de identidad por
  nombres y apellidos (cédula como llave técnica transitoria).
- **Función Judicial - Foro de Abogados** (`app.funcionjudicial.gob.ec`):
  validación profesional de abogados.

## Estado del proyecto

- **Módulo 1 -- Foundation: COMPLETO.**
  Config Manager multi-entorno, logging centralizado, jerarquía de
  excepciones, Value Objects y Entidades de dominio, todos los puertos
  (interfaces) de `application`, retry policy, modelos SQLAlchemy +
  migración inicial de Alembic, DI Container, Docker (Postgres + Redis +
  MinIO), y tests unitarios verdes.
- **Módulo 2 -- Adaptador DPE (descubrimiento): COMPLETO.**
  Descubre automáticamente todas las entidades de `transparencia.dpe.gob.ec`,
  detecta la última publicación mensual de Transparencia Activa por
  entidad, localiza el numeral "Directorio y distributivo del personal"
  (matching difuso) y su archivo de datos, identifica el tipo de archivo
  (PDF/XLS/XLSX/CSV) -- **sin descargar nada**. Pool de contextos
  Playwright + reutilización de navegador, concurrencia y rate limiting
  configurables, retry con backoff exponencial, auditoría persistida
  (`Ejecución`) y logging estructurado.
- **Módulo 3 -- Descarga de Documentos: COMPLETO.**
  Descarga los documentos ya descubiertos (Módulo 2) vía una cola
  persistida en BD (claim atómico, reanudable tras interrupción),
  concurrencia configurable, retry con backoff exponencial, validación
  cruzada Content-Type -> Magic Bytes -> Extension (detecta páginas de
  error HTML disfrazadas de PDF), cálculo de SHA-256/tamaño/ETag/Last-Modified,
  deduplicación GLOBAL por hash (storage content-addressable), storage
  local o MinIO configurable, y auditoría completa en dos tablas nuevas
  (`Descarga` = cada intento, `Manifest` = cada versión efectivamente
  almacenada). `Documento` ahora es una máquina de estados versionada
  (DESCUBIERTO/DESCARGANDO/DESCARGADO/ERROR/OBSOLETO) que detecta cuando
  el archivo publicado cambia sin depender del nombre.
- **Módulos 4-9 (extracción PDF/XLS/XLSX/CSV, historial/monitoreo continuo,
  Identity Resolution, SENESCYT, Foro de Abogados, Orquestador Maestro):
  COMPLETOS** -- ver `docs/` o los informes de cierre de cada módulo.
- **Módulo 10 -- API REST: COMPLETO.** Capa de acceso HTTP sobre los
  Módulos 1-9 (congelados, sin modificar) -- ver sección dedicada abajo.
- **Módulo 11 -- Frontend React/TypeScript: COMPLETO.** Aplicación web
  completa con entidades, funcionarios, historial, académico, Foro,
  alertas, timeline, jobs y operaciones masivas.

## Arquitectura

```
src/govdata/
  domain/          # Entidades, Value Objects, reglas de negocio, excepciones
                     # (NO depende de nada externo)
  application/      # Puertos (interfaces) + casos de uso (orquestación)
  infrastructure/    # Adaptadores: Playwright, parsers, SQLAlchemy/Postgres,
                     # storage, cola, logging
  config/           # Settings (pydantic-settings), logging, DI Container
  shared/           # Retry policy, utilidades transversales, seguridad
```

Regla de dependencia: `infrastructure -> application -> domain`. El dominio
nunca importa Playwright, SQLAlchemy, ni ninguna librería de infraestructura.

### Modelo de datos clave

`Persona` (identidad única) se separa de `Funcionario` (vinculo
Persona-Entidad-Cargo con vigencia temporal) para que la misma persona,
detectada en Transparencia, SENESCYT o Función Judicial, nunca se duplique.
`HistorialCambios` registra cada transición de cargo detectada entre
corridas.

### Flujo completo (pipeline real)

```
DPE Transparencia → entidad → último mes publicado → numeral 2
→ archivo real (Excel/PDF) → funcionarios → área jurídica
→ funcionario → resolución de identidad por apellidos en cascada
(ConsultaEcuador → MisDatosEcuador → EcuadorLegalOnline → SENESCYT)
→ validación profesional (Función Judicial / Foro de Abogados)
→ perfil consolidado con cédula persistida
```

## Requisitos

- Python 3.13+
- Docker (para Postgres/Redis/MinIO locales)
- Node.js 18+ (para frontend)

## Arranque rápido

```bash
cp .env.example .env.development   # ya viene poblado con defaults locales
pip install -e ".[dev]"
docker compose -f docker/docker-compose.yml up -d postgres redis minio
python scripts/run_pipeline.py
```

## Módulo 2: descubrimiento del portal DPE

```bash
python -m playwright install chromium   # una sola vez
python scripts/descubrir_dpe.py
```

Solo descubre y persiste metadata (entidades, publicación mensual más
reciente, documento del directorio de personal encontrado) -- no descarga
archivos. Ver `.env.example` para las variables `SCRAPING_*` (concurrencia,
rate limiting, umbrales de confianza del matching difuso, años de
lookback).

## Módulo 3: descarga de documentos

```bash
python scripts/descargar_documentos.py
```

Toma los documentos en estado `DESCUBIERTO`/`ERROR` (cola persistida en
BD), los descarga con concurrencia configurable, valida el contenido real
(no solo la extensión), calcula su hash y los almacena -- local (default,
`STORAGE_BACKEND=local`) o MinIO (`STORAGE_BACKEND=minio`). Ver
`.env.example` para las variables `DOWNLOAD_*` y `STORAGE_*`. Nunca lee ni
interpreta el contenido de los archivos.

## Módulo 10: API REST

```bash
uvicorn govdata.infrastructure.api.app:app --reload --port 8000
```

Swagger UI en `/docs`, ReDoc en `/redoc`, `/health` y `/ready` para
health/readiness. Todos los endpoints funcionales viven bajo `/api/v1`
(`entidades`, `funcionarios`, `jobs`) y son una CAPA DE ACCESO pura: nunca
reimplementan scraping/extracción/identidad/SENESCYT/Foro/orquestacion --
siempre delegan en los servicios de aplicación de los Módulos 1-9 (via
`Container`), nunca acceden a `Session`/ORM directamente. El endpoint
principal, `GET /api/v1/entidades/{id}/consulta`, es la operacion "un clic":
ejecuta `GovDataPipelineOrchestrator` (Modulo 9) completo,
aprovechando cache/monitoreo existentes. Seguridad basica: header
`X-API-Key` (opcional en `development`, obligatorio en `production` via
`.env.production`), CORS configurable, rate limit en memoria por proceso
(`RATE_LIMIT_POR_MINUTO`), `X-Request-ID` en cada respuesta y manejo
global de errores (nunca expone stack traces). Ver `.env.example` para
las variables `APP_HOST`/`APP_PORT`/`API_KEY`/`CORS_ORIGINS`/`RATE_LIMIT_*`.

### Endpoint de validación de abogado

```
POST /api/v1/funcionarios/{persona_master_id}/validar-abogado
```

Ejecuta el pipeline completo de validación profesional:
1. Resolución de identidad por apellidos en cascada: ConsultaEcuador →
   MisDatosEcuador → EcuadorLegalOnline → SENESCYT (se usa la
   primera que responda con candidatos)
2. Matching conservador (MATCH_EXACT, MATCH_HIGH_CONFIDENCE, AMBIGUOUS, NO_MATCH)
3. Consulta al Foro de Abogados de la Función Judicial (solo si matching inequívoco)
4. Consolidación del perfil con cédula persistida

La respuesta incluye la cédula persistida, además de campos de estado
suficientemente claros para que el frontend distinga todos los casos.

## Frontend

```bash
cd frontend
npm install
npm run dev      # desarrollo
npm test         # tests
npm run lint     # linting
npm run build    # build de producción
```

El frontend incluye pantallas para entidades, funcionarios, historial,
académico, Foro, alertas, timeline, jobs y operaciones masivas.

## Politica de datos sensibles

La cédula se persiste en la base de datos para que aparezca en todas las consultas
y sea un sistema más confiable y consistente. Se almacena en:
- `personas.cedula` - después del matching de identidad con MisDatosEcuador
- `registro_foro.cedula` - después de la consulta al Foro de Abogados

La cédula **NUNCA**:
- se almacena en logs
- se almacena en errores
- se incluye en URLs registradas
- se incluye en auditoría textual
- aparece en CSV/Excel exportado (redacción automática)

## Tests

```bash
pytest                                             # suite completa
pytest --cov=src/govdata --cov-report=term-missing # con cobertura
ruff check .
mypy src/govdata
```

Los tests de integración levantan un Chromium real (headless) contra un
servidor HTTP local que sirve fixtures capturadas del portal DPE
(`tests/fixtures/dpe/`, ver su `README.md`) -- no requieren red ni el
portal real disponible.

## Configuración multi-entorno

`APP_ENV` (`development` | `test` | `production`) determina cual archivo
`.env.<entorno>` se carga automaticamente (`config/settings.py`). Las
variables ya presentes en el entorno real del proceso siempre tienen
prioridad sobre el archivo, para permitir overrides en CI/Docker.

## Migraciones

```bash
alembic upgrade head
```

## Convenciones

- PEP8, docstrings en espanol explicando el *porque*, no solo el *que*.
- Toda excepcion propia hereda de `GovDataError` (`domain/exceptions`).
- Ningun caso de uso o entidad de dominio importa un adaptador de
  `infrastructure` directamente -- siempre a traves de un puerto.

El rechazo automático al detectar CAPTCHA o challenges se configura con
`SCRAPING_RECHAZAR_CAPTCHA_ANTIBOT` (por defecto `false`). Con `false`,
los adaptadores continúan el flujo normal de consulta y extracción; con
`true`, rechazan la consulta ante esos controles.
Reiniciar el backend después de cambiar esta variable. Esta opción no
resuelve los desafíos que pueda exigir el sitio externo.
