import { apiClient } from './client'
import { paginaEntidadSchema } from '../lib/schemas'
import { ApiError } from '../types/error'
import { extraerNombreArchivo } from '../lib/content-disposition'
import type {
  AlertaEntidad,
  CambioEntidad,
  ConsultaEntidadResultado,
  Entidad,
  FiltrosCambio,
  FiltrosEntidad,
  FiltrosFuncionario,
  FormatoExportacion,
  Funcionario,
  FuncionarioConsultado,
  Pagina,
  PoliticaConsulta,
} from '../types'

/**
 * `GET /api/v1/entidades` -- listado paginado y filtrado. Valida la
 * forma real de la respuesta con Zod: si el backend cambiara de
 * contrato de forma incompatible, esto falla de manera controlada en
 * vez de propagar datos con forma inesperada al resto de la UI.
 */
export function listarEntidades(filtros: FiltrosEntidad = {}) {
  return apiClient.get('/api/v1/entidades', { params: filtros }).then((r) => {
    const resultado = paginaEntidadSchema.safeParse(r.data)
    if (!resultado.success) {
      throw new ApiError(
        'RESPUESTA_INVALIDA',
        'El servidor respondió con datos en un formato inesperado.',
        null,
        r.status,
      )
    }
    return resultado.data
  })
}

/** `GET /api/v1/entidades/{id}` -- detalle. */
export function obtenerEntidad(entidadId: number) {
  return apiClient.get<Entidad>(`/api/v1/entidades/${entidadId}`).then((r) => r.data)
}

/**
 * `GET /api/v1/entidades/{id}/consulta` -- operación principal ("un clic").
 * SÍNCRONA: la petición permanece abierta hasta que el
 * GovDataPipelineOrchestrator termina. No hay progreso intermedio real.
 */
export function consultarEntidad(entidadId: number, politica?: PoliticaConsulta) {
  return apiClient
    .get<ConsultaEntidadResultado>(`/api/v1/entidades/${entidadId}/consulta`, {
      params: politica ? { politica } : undefined,
    })
    .then((r) => r.data)
}

// Los directorios nacionales pueden contener decenas de miles de filas. Esta
// operación no debe heredar el timeout de 120 s del resto de consultas.
const TIMEOUT_LISTADO_INSTITUCIONAL_MS = 30 * 60_000

/** Actualiza únicamente el directorio de Transparencia, sin enriquecimiento externo. */
export function actualizarListadoInstitucional(entidadId: number) {
  return apiClient
    .post(`/api/v1/entidades/${entidadId}/funcionarios/actualizar-listado`, undefined, {
      timeout: TIMEOUT_LISTADO_INSTITUCIONAL_MS,
    })
    .then((r) => r.data)
}

export interface ProgresoListadoInstitucional {
  estado: 'inactivo' | 'preparando' | 'extrayendo' | 'completado' | 'error'
  total_filas: number | null
  filas_procesadas: number
  funcionarios_extraidos: number
  mensaje: string | null
}

export interface EstadoListadoInstitucional {
  funcionarios_persistidos: number
  profesionales_juridicos: number
  funcionarios_consultados: number
  periodo_publicacion: string | null
  fecha_extraccion: string | null
  ultima_verificacion_dpe: string | null
  estado_verificacion_dpe: string
  requiere_actualizacion: boolean
  mensaje: string
}

export interface ComprobacionPublicacionDpe {
  estado: 'vigente' | 'hay_publicacion_mas_reciente' | 'no_se_pudo_comprobar'
  periodo_local: string | null
  periodo_dpe: string | null
  mensaje: string
}

/** Resumen del directorio persistido y la última publicación conocida. */
export function obtenerEstadoListadoInstitucional(entidadId: number) {
  return apiClient
    .get<EstadoListadoInstitucional>(`/api/v1/entidades/${entidadId}/funcionarios/estado-listado`)
    .then((r) => r.data)
}

/** Comprueba DPE sin descargar ni extraer el directorio institucional. */
export function comprobarPublicacionDpe(entidadId: number) {
  return apiClient
    .post<ComprobacionPublicacionDpe>(`/api/v1/entidades/${entidadId}/funcionarios/comprobar-publicacion-dpe`, undefined, {
      timeout: TIMEOUT_LISTADO_INSTITUCIONAL_MS,
    })
    .then((r) => r.data)
}

export type EstadoConsultaExterna = 'pendiente' | 'en_proceso' | 'completada' | 'sin_coincidencia' | 'error'
export function obtenerEstadosConsultaExterna(entidadId: number) {
  return apiClient.get<{ items: Record<string, { estado: EstadoConsultaExterna; fecha: string | null; error?: string | null }> }>(
    `/api/v1/entidades/${entidadId}/funcionarios/estado-consulta`,
  ).then((r) => r.data)
}

/** Crea o reutiliza la identidad local solo del funcionario que se seleccionó. */
export function prepararFuncionarioParaConsulta(entidadId: number, funcionarioId: number) {
  return apiClient
    .post<{ funcionario_id: number; persona_master_id: number }>(
      `/api/v1/entidades/${entidadId}/funcionarios/${funcionarioId}/preparar-consulta`,
    )
    .then((r) => r.data)
}

/** Guarda una selección humana como profesional jurídico o afín, sin consultar fuentes externas. */
export function marcarFuncionarioComoProfesional(entidadId: number, funcionarioId: number) {
  return apiClient
    .post(`/api/v1/entidades/${entidadId}/funcionarios/${funcionarioId}/marcar-profesional`)
    .then((r) => r.data)
}

/** Guarda varios funcionarios seleccionados como profesionales jurídicos o afines. */
export function marcarFuncionariosComoProfesionales(entidadId: number, funcionarioIds: number[]) {
  return apiClient
    .post(`/api/v1/entidades/${entidadId}/funcionarios/marcar-profesionales`, { funcionario_ids: funcionarioIds })
    .then((r) => r.data)
}

/** Avance real del procesamiento del directorio institucional en curso. */
export function obtenerProgresoListadoInstitucional(entidadId: number) {
  return apiClient
    .get<ProgresoListadoInstitucional>(`/api/v1/entidades/${entidadId}/funcionarios/progreso-listado`)
    .then((r) => r.data)
}

/** `POST /api/v1/entidades/{id}/actualizar` -- fuerza `actualizacion_completa`. Síncrona. */
export function actualizarEntidad(entidadId: number) {
  return apiClient
    .post<ConsultaEntidadResultado>(`/api/v1/entidades/${entidadId}/actualizar`)
    .then((r) => r.data)
}

/**
 * Timeout extendido para las operaciones MASIVAS -- a diferencia de
 * `consultarEntidad`/`actualizarEntidad` (UNA entidad), estas corren el
 * pipeline síncronamente sobre TODAS las entidades activas
 * (`GovDataPipelineOrchestrator.consultar_masivo`/`actualizar_masivo`,
 * confirmado en el código real -- ninguna acepta una lista de
 * `entidad_id`). El timeout global de `apiClient` (120s) está pensado
 * para una sola entidad; aquí se sobreescribe por petición.
 */
const TIMEOUT_MASIVA_MS = 10 * 60_000

/**
 * `POST /api/v1/entidades/consulta-masiva` -- SIN body. Solo admite
 * `politica` como query param (`Query(default="consulta_rapida")`,
 * `routes/entidades.py`). Ejecuta `consultar_masivo()`, que SIEMPRE opera
 * sobre `EntidadRepositoryPort.listar_activas()` -- el backend no expone
 * ningún parámetro para acotar a un subconjunto de entidades.
 */
export function consultarMasivo(politica?: PoliticaConsulta) {
  return apiClient
    .post<ConsultaEntidadResultado[]>('/api/v1/entidades/consulta-masiva', undefined, {
      params: politica ? { politica } : undefined,
      timeout: TIMEOUT_MASIVA_MS,
    })
    .then((r) => r.data)
}

/**
 * `POST /api/v1/entidades/actualizar-masivo` -- SIN body y SIN ningún
 * query param (ni siquiera `politica`): fuerza `masiva_nocturna`
 * internamente (`GovDataPipelineOrchestrator.actualizar_masivo`, sin
 * argumentos). Igual que `consulta-masiva`, opera sobre TODAS las
 * entidades activas -- no hay forma de seleccionar un subconjunto.
 */
export function actualizarMasivo() {
  return apiClient
    .post<ConsultaEntidadResultado[]>('/api/v1/entidades/actualizar-masivo', undefined, {
      timeout: TIMEOUT_MASIVA_MS,
    })
    .then((r) => r.data)
}

/** `GET /api/v1/entidades/{id}/funcionarios` -- solo datos ya persistidos, nunca dispara el pipeline. */
export function listarFuncionarios(entidadId: number, filtros: FiltrosFuncionario = {}) {
  return apiClient
    .get<Pagina<Funcionario>>(`/api/v1/entidades/${entidadId}/funcionarios`, { params: filtros })
    .then((r) => r.data)
}

/** Datos externos ya persistidos; esta lectura nunca vuelve a consultar fuentes. */
export function listarFuncionariosConsultados(entidadId: number) {
  return apiClient
    .get<Pagina<FuncionarioConsultado>>(`/api/v1/entidades/${entidadId}/funcionarios/consultados`, {
      params: { page: 1, page_size: 100 },
    })
    .then((r) => r.data)
}

/** `GET /api/v1/entidades/{id}/cambios`. */
export function obtenerCambiosEntidad(entidadId: number, filtros: FiltrosCambio = {}) {
  return apiClient
    .get<Pagina<CambioEntidad>>(`/api/v1/entidades/${entidadId}/cambios`, { params: filtros })
    .then((r) => r.data)
}

/** `GET /api/v1/entidades/{id}/alertas`. */
export function obtenerAlertasEntidad(entidadId: number, page = 1, pageSize = 50) {
  return apiClient
    .get<Pagina<AlertaEntidad>>(`/api/v1/entidades/${entidadId}/alertas`, {
      params: { page, page_size: pageSize },
    })
    .then((r) => r.data)
}

/** Resultado de una exportación ya descargada: el blob y el nombre de archivo a usar. */
export interface ExportacionFuncionarios {
  blob: Blob
  nombreArchivo: string
}

/**
 * `GET /entidades/{id}/funcionarios/exportar` -- exporta desde BD
 * (nunca vuelve a consultar Transparencia/SENESCYT/Foro), streaming en
 * el backend. Usa `responseType: 'blob'` porque el archivo se descarga,
 * no se parsea como JSON de la app. El backend NO expone
 * `Content-Disposition` vía CORS (`expose_headers` no está configurado
 * en `app.py`), así que en un despliegue cross-origin normal el nombre
 * de archivo real es ilegible desde JS -- se reconstruye aquí el MISMO
 * patrón que usa el backend (`funcionarios_entidad_{id}.{formato}`,
 * ver `routes/entidades.py::exportar_funcionarios`) como fallback, y se
 * usa el header real si el navegador llegara a exponerlo.
 */
export function exportarFuncionarios(
  entidadId: number,
  formato: FormatoExportacion,
): Promise<ExportacionFuncionarios> {
  return apiClient
    .get(`/api/v1/entidades/${entidadId}/funcionarios/exportar`, {
      params: { formato },
      responseType: 'blob',
    })
    .then((r) => ({
      blob: r.data as Blob,
      nombreArchivo:
        extraerNombreArchivo(r.headers['content-disposition'] as string | undefined) ??
        `funcionarios_entidad_${entidadId}.${formato}`,
    }))
}
