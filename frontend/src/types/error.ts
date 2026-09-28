/**
 * Contrato de error real del backend (Módulo 10,
 * `infrastructure/api/exception_handlers.py`):
 *
 *   { "error": { "codigo", "mensaje", "detalle", "request_id" } }
 *
 * Confirmado en vivo contra `/ready` (500) y `/entidades/{id inexistente}` (404).
 */
export interface ApiErrorBody {
  error: {
    codigo: string
    mensaje: string
    detalle: string | null
    request_id: string | null
  }
}

/** Error normalizado que usa el resto del frontend -- nunca se propaga un stack trace. */
export class ApiError extends Error {
  readonly codigo: string
  readonly requestId: string | null
  readonly status: number | null

  constructor(codigo: string, mensaje: string, requestId: string | null, status: number | null) {
    super(mensaje)
    this.name = 'ApiError'
    this.codigo = codigo
    this.requestId = requestId
    this.status = status
  }
}
