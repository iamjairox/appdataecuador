/** `EntidadResponseSchema` real (Módulo 10) -- confirmado en OpenAPI en vivo. */
export interface Entidad {
  id: number
  nombre: string
  tipo: string | null
  provincia: string | null
  ciudad: string | null
  portal_origen: string
  estado: string
  ultima_publicacion: string | null
  ultima_actualizacion: string | null
}

/** Filtros de `GET /api/v1/entidades` (query params reales de la ruta). */
export interface FiltrosEntidad {
  nombre?: string
  provincia?: string
  ciudad?: string
  tipo_institucion?: string
  portal_origen?: string
  page?: number
  page_size?: number
}
