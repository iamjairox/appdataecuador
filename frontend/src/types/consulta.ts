import type { FuncionarioConsolidado } from './funcionario'

/**
 * `ConsultaEntidadResponseSchema` real (Módulo 10) -- resultado de
 * `GET /entidades/{id}/consulta`, `/actualizar`, `/consulta-masiva`,
 * `/actualizar-masivo`. `job`/`entidad`/`estadisticas` son objetos
 * libres (`dict[str, Any]` en el backend) -- se tipan como `Record`
 * para no inventar una forma fija que el backend no garantiza.
 */
export interface ConsultaEntidadResultado {
  job: Record<string, unknown>
  entidad: Record<string, unknown>
  estadisticas: Record<string, unknown>
  funcionarios: FuncionarioConsolidado[]
  alertas: Record<string, unknown>[]
  errores: string[]
  duracion_total: string
  generado_en: string
}

export type PoliticaConsulta =
  | 'consulta_rapida'
  | 'actualizacion_completa'
  | 'solo_cambios'
  | 'masiva_nocturna'
