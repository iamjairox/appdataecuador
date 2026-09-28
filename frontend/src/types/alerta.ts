/** `AlertaResponseSchema` real -- `GET /entidades/{id}/alertas` (Módulo 5, paginado). */
export interface AlertaEntidad {
  id: string
  entidad_id: number
  tipo: string
  prioridad: string
  descripcion: string
  detectado_en: string
  estado: string
  persona_id: number | null
  documento_id: number | null
}
