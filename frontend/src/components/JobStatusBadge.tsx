import { Badge } from './ui'
import type { Tono } from './ui/Badge'
import type { EstadoJob } from '../types'

/**
 * Mapea EXCLUSIVAMENTE los 8 estados reales de `TrabajoOrquestador`
 * (Módulo 9) -- nunca un estado intermedio inventado ("procesando",
 * "descubriendo", "comparando", ...) que el backend no reporta.
 */
const TONO_POR_ESTADO: Record<EstadoJob, Tono> = {
  pendiente: 'neutral',
  en_cola: 'neutral',
  ejecutando: 'info',
  pausado: 'warning',
  reintentando: 'warning',
  completado: 'success',
  cancelado: 'neutral',
  error: 'danger',
}

interface JobStatusBadgeProps {
  estado: EstadoJob
}

export function JobStatusBadge({ estado }: JobStatusBadgeProps) {
  return <Badge tone={TONO_POR_ESTADO[estado]}>{estado}</Badge>
}
