import { Alert, Button } from './ui'
import { ApiError } from '../types/error'
import { mensajeAmigable } from '../lib/error-messages'

interface ErrorStateProps {
  error: unknown
  title?: string
  /** Si se provee, muestra un botón "Reintentar" -- centraliza el patrón `ErrorState` + botón que se repetía en cada pantalla. */
  onRetry?: () => void
}

/**
 * Traduce cualquier error capturado por React Query a un mensaje
 * comprensible (Regla: nunca stack traces/SQL/rutas internas). Muestra
 * `request_id` solo como referencia de soporte, nunca detalle técnico.
 */
export function ErrorState({ error, title = 'No se pudo completar la solicitud', onRetry }: ErrorStateProps) {
  const apiError = error instanceof ApiError ? error : null
  const mensaje = apiError ? mensajeAmigable(apiError) : 'Ocurrió un error inesperado.'

  return (
    <div className="flex flex-col items-start gap-3">
      <Alert tone="danger" title={title}>
        <p>{mensaje}</p>
        {apiError?.requestId && (
          <p className="mt-1 text-xs text-red-700/70">
            Referencia para soporte: <span className="font-mono">{apiError.requestId}</span>
          </p>
        )}
      </Alert>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </div>
  )
}
