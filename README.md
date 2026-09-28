# GovData Intelligence Platform

Plataforma modular de automatizacion e inteligencia de datos publicos del
Estado ecuatoriano. Arquitectura Hexagonal (Ports & Adapters) + Clean
Architecture + SOLID + Repository Pattern + Service Layer + DI.

Fuente inicial: `transparencia.dpe.gob.ec`. Disenada para agregar SENESCYT,
Funcion Judicial, SERCOP, Registro Mercantil, SRI, Contraloria, etc. como
nuevos adaptadores sin modificar el dominio ni los casos de uso.

## Estado del proyecto

- **Modulo 1 -- Foundation: COMPLETO.**
  Config Manager multi-entorno, logging centralizado, jerarquia de
  excepciones, Value Objects y Entidades de dominio (incluyendo el modelo
  `Persona` / `Funcionario` desacoplado y `HistorialCambios`), todos los
  puertos (interfaces) de `application`, retry policy, modelos SQLAlchemy +
  migracion inicial de Alembic, DI Container, Docker (Postgres + Redis +
  MinIO), y tests unitarios verdes.
- **Modulo 2 -- Adaptador DPE (descubrimiento): COMPLETO.**
  Descubre automaticamente todas las entidades de `transparencia.dpe.gob.ec`,
  detecta la ultima publicacion mensual de Transparencia Activa por
  entidad, localiza el numeral "Directorio y distributivo del personal"
  (matching difuso) y su archivo de datos, identifica el tipo de archivo
  (PDF/XLS/XLSX/CSV) -- **sin descargar nada**. Pool de contextos
  Playwright + reutilizacion de navegador, concurrencia y rate limiting
  configurables, retry con backoff exponencial, auditoria persistida
  (`Ejecucion`) y logging estructurado. 114 tests (unitarios + integracion
  con Playwright real contra fixtures offline), 91% cobertura, Ruff y
  MyPy limpios. Ver `docs/modulo-2.md` (si se solicita) o el resumen
  entregado en la conversacion de diseno.
- **Modulo 3 -- Descarga de Documentos: COMPLETO.**
  Descarga los documentos ya descubiertos (Modulo 2) via una cola
  persistida en BD (claim atomico, reanudable tras interrupcion),
  concurrencia configurable, retry con backoff exponencial, validacion
  cruzada Content-Type -> Magic Bytes -> Extension (detecta paginas de
  error HTML disfrazadas de PDF), calculo de SHA-256/tamano/ETag/Last-Modified,
  deduplicacion GLOBAL por hash (storage content-addressable), storage
  local o MinIO configurable, y auditoria completa en dos tablas nuevas
  (`Descarga` = cada intento, `Manifest` = cada version efectivamente
  almacenada). `Documento` ahora es una maquina de estados versionada
  (DESCUBIERTO/DESCARGANDO/DESCARGADO/ERROR/OBSOLETO) que detecta cuando
  el archivo publicado cambio sin depender del nombre. NUNCA parsea
  contenido. 215 tests totales (unitarios + integracion con servidor HTTP
  real y storage real), 94% cobertura, Ruff y MyPy limpios.
- Modulos 4-9 (extraccion PDF/XLS/XLSX/CSV, historial/monitoreo continuo,
  Identity Resolution, SENESCYT, Foro de Abogados, Orquestador Maestro):
  **COMPLETOS** -- ver `docs/` o los informes de cierre de cada modulo.
- **Modulo 10 -- API REST: COMPLETO.** Capa de acceso HTTP sobre los
  Modulos 1-9 (congelados, sin modificar) -- ver seccion dedicada abajo.
- Modulo 11 (frontend) -- **no iniciado**.

## Arquitectura

```
src/govdata/
  domain/          # Entidades, Value Objects, reglas de negocio, excepciones
                    # (NO depende de nada externo)
  application/      # Puertos (interfaces) + casos de uso (orquestacion)
  infrastructure/    # Adaptadores: Playwright, parsers, SQLAlchemy/Postgres,
                    # storage, cola, logging
  config/           # Settings (pydantic-settings), logging, DI Container
  shared/           # Retry policy, utilidades transversales
```

Regla de dependencia: `infrastructure -> application -> domain`. El dominio
nunca importa Playwright, SQLAlchemy, ni ninguna libreria de infraestructura.

### Modelo de datos clave

`Persona` (identidad unica) se separa de `Funcionario` (vinculo
Persona-Entidad-Cargo con vigencia temporal) para que la misma persona,
detectada en Transparencia, SENESCYT o Funcion Judicial, nunca se duplique.
`HistorialCambios` registra cada transicion de cargo detectada entre
corridas.

## Requisitos

- Python 3.13+
- Docker (para Postgres/Redis/MinIO locales)

## Arranque rapido

```bash
cp .env.example .env.development   # ya viene poblado con defaults locales
pip install -e ".[dev]"
docker compose -f docker/docker-compose.yml up -d postgres redis minio
python scripts/run_pipeline.py
```

## Modulo 2: descubrimiento del portal DPE

```bash
python -m playwright install chromium   # una sola vez
python scripts/descubrir_dpe.py
```

Solo descubre y persiste metadata (entidades, publicacion mensual mas
reciente, documento del directorio de personal encontrado) -- no descarga
archivos. Ver `.env.example` para las variables `SCRAPING_*` (concurrencia,
rate limiting, umbrales de confianza del matching difuso, anios de
lookback).

## Modulo 3: descarga de documentos

```bash
python scripts/descargar_documentos.py
```

Toma los documentos en estado `DESCUBIERTO`/`ERROR` (cola persistida en
BD), los descarga con concurrencia configurable, valida el contenido real
(no solo la extension), calcula su hash y los almacena -- local (default,
`STORAGE_BACKEND=local`) o MinIO (`STORAGE_BACKEND=minio`). Ver
`.env.example` para las variables `DOWNLOAD_*` y `STORAGE_*`. Nunca lee ni
interpreta el contenido de los archivos.

## Modulo 10: API REST

```bash
uvicorn govdata.infrastructure.api.app:app --reload --port 8000
```

Swagger UI en `/docs`, ReDoc en `/redoc`, `/health` y `/ready` para
health/readiness. Todos los endpoints funcionales viven bajo `/api/v1`
(`entidades`, `funcionarios`, `jobs`) y son una CAPA DE ACCESO pura: nunca
reimplementan scraping/extraccion/identidad/SENESCYT/Foro/orquestacion --
siempre delegan en los servicios de aplicacion de los Modulos 1-9 (via
`Container`), nunca acceden a `Session`/ORM directamente. El endpoint
principal, `GET /api/v1/entidades/{id}/consulta`, es la operacion "un
clic": ejecuta `GovDataPipelineOrchestrator` (Modulo 9) completo,
aprovechando cache/monitoreo existentes. Seguridad basica: header
`X-API-Key` (opcional en `development`, obligatorio en `production` via
`.env.production`), CORS configurable, rate limit en memoria por proceso
(`RATE_LIMIT_POR_MINUTO`), `X-Request-ID` en cada respuesta y manejo
global de errores (nunca expone stack traces). Ver `.env.example` para
las variables `APP_HOST`/`APP_PORT`/`API_KEY`/`CORS_ORIGINS`/`RATE_LIMIT_*`.

## Tests

```bash
pytest                                             # suite completa
pytest --cov=src/govdata --cov-report=term-missing # con cobertura
```

Los tests de integracion levantan un Chromium real (headless) contra un
servidor HTTP local que sirve fixtures capturadas del portal DPE
(`tests/fixtures/dpe/`, ver su `README.md`) -- no requieren red ni el
portal real disponible.

## Configuracion multi-entorno

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
