import type { ApiError } from '../types/error'

/**
 * Traduce el `codigo` real del backend (nombre de la excepción de
 * dominio, Módulo 10 -- `exception_handlers.py`) a un mensaje
 * comprensible. Si no hay una traducción específica, se usa el
 * `mensaje` que ya envía el backend (ya pensado para ser legible, nunca
 * un stack trace) -- nunca se inventa texto que contradiga al backend.
 */
const MENSAJES_POR_CODIGO: Record<string, string> = {
  EntidadNoEncontradaError: 'No se encontró la entidad solicitada.',
  PersonaMasterInvalidaError: 'No fue posible identificar de forma confiable a esta persona.',
  PublicacionNoDisponibleError: 'Esta entidad todavía no tiene publicaciones de Transparencia Activa.',
  RecursoNoDisponibleError: 'El recurso solicitado ya no está disponible.',
  BloqueoOptimistaFallidoError: 'Esta operación ya está en curso en otra solicitud. Intenta de nuevo en un momento.',
  TrabajoOrquestadorInvalidoError: 'El trabajo no admite esa operación en su estado actual.',
  // 502 (dependencia externa fallo de forma no reintentable -- exception_handlers.py)
  ConsultaForoPermanenteError: 'El Foro de Abogados rechazó la consulta de forma permanente para esta persona.',
  EnriquecimientoAcademicoFallidoError: 'No fue posible enriquecer la información académica (SENESCYT) en esta consulta.',
  EnriquecimientoForoFallidoError: 'No fue posible enriquecer la información del Foro de Abogados en esta consulta.',
  // 503 (dependencia externa temporalmente no disponible)
  ForoCircuitoAbiertoError: 'El Foro de Abogados no está disponible temporalmente. Intenta de nuevo más tarde.',
  ConsultaForoFallidaError: 'No fue posible consultar el Foro de Abogados en este momento.',
  ConsultaSenescytFallidaError: 'No fue posible consultar SENESCYT en este momento.',
  DescargaFallidaError: 'No fue posible descargar la publicación de la fuente externa en este momento.',
  // 500 (error interno)
  OrquestacionFallidaError: 'Ocurrió un error interno al orquestar la consulta. Intenta de nuevo más tarde.',
  HTTP_401: 'No autorizado. Verifica la configuración de acceso a la API.',
  HTTP_404: 'No se encontró el recurso solicitado.',
  HTTP_422: 'Los parámetros enviados no son válidos.',
  VALIDACION_INVALIDA: 'Los parámetros enviados no son válidos.',
  RATE_LIMIT_EXCEDIDO: 'Se realizaron demasiadas solicitudes. Espera un momento e intenta de nuevo.',
  ERROR_INTERNO: 'Ocurrió un error interno en el servidor. Intenta de nuevo más tarde.',
  ERROR_DE_RED: 'No fue posible comunicarse con el servidor DataOK. Verifica tu conexión.',
  RESPUESTA_INVALIDA: 'El servidor respondió con datos en un formato inesperado.',
}

/**
 * Segundo nivel de traducción por rango de `status` HTTP (Submódulo
 * 10.11: 404/502/503/500 son las familias reales que la API puede
 * devolver). Se usa solo cuando el `codigo` puntual no tiene una
 * traducción específica arriba -- nunca contradice al backend, solo
 * generaliza por familia de estado.
 */
function mensajePorStatus(status: number | null): string | null {
  if (status === 404) return 'No se encontró la entidad o el recurso solicitado.'
  if (status === 502) return 'Una fuente externa no pudo ser consultada correctamente. Intenta de nuevo más tarde.'
  if (status === 503) return 'Una fuente externa no está disponible en este momento. Intenta de nuevo más tarde.'
  if (status !== null && status >= 500) return 'Ocurrió un error interno en el servidor. Intenta de nuevo más tarde.'
  return null
}

export function mensajeAmigable(error: ApiError): string {
  return MENSAJES_POR_CODIGO[error.codigo] ?? mensajePorStatus(error.status) ?? error.message
}
