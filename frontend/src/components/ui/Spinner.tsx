import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'

interface SpinnerProps {
  label?: string
  className?: string
}

/**
 * Indicador de progreso INDETERMINADO -- nunca un porcentaje inventado (ver
 * Regla crítica de progreso). Cuando se pasa `label=""` a propósito (p. ej.
 * dentro de un `StatCard`, para no duplicar visualmente el label de la
 * tarjeta) el texto visible queda vacío, pero `aria-label` sigue anunciando
 * el estado de carga a lectores de pantalla (FASE 3.6 -- Bloque 2).
 */
export function Spinner({ label, className }: SpinnerProps) {
  const texto = label ?? 'Cargando…'
  return (
    <div
      role="status"
      aria-label={texto === '' ? 'Cargando' : undefined}
      className={cn('flex items-center gap-2 text-slate-600', className)}
    >
      <Loader2 className="size-4 animate-spin" aria-hidden="true" />
      <span>{texto}</span>
    </div>
  )
}
