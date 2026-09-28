/**
 * `CambioResponseSchema` real -- `GET /entidades/{id}/cambios` (Módulo 5,
 * paginado). `tipo_cambio`/`criticidad` casi siempre llegan `null`: esa
 * clasificación no se persiste junto a la versión (ver el propio informe
 * del backend) -- nunca inventar un valor cuando venga `null`.
 */
export interface CambioEntidad {
  persona_id: number
  numero_version: number
  cargo: string
  dependencia: string
  fecha_inicio: string
  fecha_fin: string | null
  tipo_cambio: string | null
  criticidad: string | null
}

export interface FiltrosCambio {
  desde?: string
  hasta?: string
  page?: number
  page_size?: number
}
