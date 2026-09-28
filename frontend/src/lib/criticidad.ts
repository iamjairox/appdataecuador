import type { Tono } from '../components/ui/Badge'

/**
 * `prioridad` de una alerta (`NivelCriticidad`, dominio -- confirmado en
 * `domain/value_objects/nivel_criticidad.py` y reutilizado tal cual por
 * `Alerta` (Módulo 5), `AlertaAcademica` (Módulo 7), `AlertaForo` (Módulo 8)
 * y `AlertaPerfil` (Módulo 6)) es SIEMPRE uno de estos 4 valores reales:
 * `"critico" | "alto" | "medio" | "bajo"`. Nunca "critica"/"alta"/"media"
 * (adjetivo femenino) -- esa forma no existe en el backend.
 */
export function tonoPorPrioridad(prioridad: string): Tono {
  switch (prioridad) {
    case 'critico':
      return 'danger'
    case 'alto':
      return 'warning'
    case 'medio':
      return 'info'
    default:
      return 'neutral'
  }
}

/**
 * `estado` de una alerta (`EstadoAlerta` y sus 3 variantes por fuente,
 * todas con los mismos 3 valores reales): `"pendiente" | "enviada" | "descartada"`.
 */
export function tonoPorEstadoAlerta(estado: string): Tono {
  switch (estado) {
    case 'pendiente':
      return 'warning'
    case 'enviada':
      return 'success'
    case 'descartada':
      return 'neutral'
    default:
      return 'neutral'
  }
}
