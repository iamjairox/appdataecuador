/**
 * `JobResponseSchema` real (Módulo 10) -- `GET /jobs/{job_id}`.
 *
 * `estado` es exactamente uno de estos 8 valores (máquina de estados de
 * `TrabajoOrquestador`, Módulo 9) -- NO existen estados intermedios como
 * "Descubriendo"/"Comparando"/"Consultando SENESCYT": esos NO son
 * señales reales del backend y no deben inventarse en la UI.
 */
export type EstadoJob =
  | 'pendiente'
  | 'en_cola'
  | 'ejecutando'
  | 'pausado'
  | 'reintentando'
  | 'completado'
  | 'cancelado'
  | 'error'

export interface EtapaJob {
  tipo_paso: string
  estado_paso: string
  iniciado_en: string
  finalizado_en: string | null
  duracion_segundos: number | null
  razon_omision: string | null
  cantidad_registros: number
  error: string | null
}

export interface Job {
  id: string
  tipo: string
  estado: EstadoJob
  prioridad: string
  politica: string
  parametros: Record<string, unknown>
  intentos: number
  max_intentos: number
  entidad_id: number | null
  creado_en: string | null
  actualizado_en: string | null
  iniciado_en: string | null
  finalizado_en: string | null
  ultimo_error: string | null
  etapas: EtapaJob[]
}
