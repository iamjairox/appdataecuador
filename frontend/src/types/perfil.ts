/**
 * `PerfilConsolidadoResponseSchema` real (Módulo 10) --
 * `GET /funcionarios/{persona_master_id}` (NO existe sufijo `/perfil`).
 * `persona`/`transparencia`/`senescyt`/`foro` son objetos libres tal
 * como los define el backend (Submódulo 8.10) -- NUNCA se aplanan.
 */
export interface PerfilConsolidado {
  persona: Record<string, unknown>
  transparencia: Record<string, unknown>
  senescyt: Record<string, unknown>
  foro: Record<string, unknown>
  generado_en: string
}

/** `PerfilAcademicoResponseSchema` real -- `GET /funcionarios/{id}/academico`. */
export interface PerfilAcademico {
  persona_master: Record<string, unknown>
  identidad: Record<string, unknown>
  titulos: Record<string, unknown>[]
  historial: Record<string, unknown>[]
  alertas: Record<string, unknown>[]
  eventos: Record<string, unknown>[]
  estadisticas: Record<string, unknown>
  generado_en: string
}

/** UNA versión del historial laboral -- `GET /funcionarios/{id}/historial` (arreglo directo, sin paginar). */
export interface VersionHistorial {
  entidad_id: number
  numero_version: number
  cargo: string
  dependencia: string
  area: string
  fecha_inicio: string
  fecha_fin: string | null
  correo: string | null
  telefono: string | null
}

/** `GET /funcionarios/{id}/timeline` -- forma de `TimelinePersonaDTO`. */
export interface Timeline {
  persona_master_id: number
  puntos: PuntoTimeline[]
}

export interface PuntoTimeline {
  fecha_inicio: string | null
  fecha_fin: string | null
  origen: string
  descripcion: string
  referencia_id: number | null
}

/** `GET /funcionarios/{id}/alertas` -- arreglo directo (agregado de Módulos 6/7/8). */
export interface AlertaFuncionario {
  id: string
  fuente: 'identidad' | 'academico' | 'foro'
  tipo: string
  prioridad: string
  descripcion: string
  detectado_en: string
  estado: string
}
