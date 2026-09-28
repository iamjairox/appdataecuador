import { apiClient } from './client'
import type {
  AlertaFuncionario,
  PerfilAcademico,
  PerfilConsolidado,
  Timeline,
  VersionHistorial,
} from '../types'

/**
 * `GET /api/v1/funcionarios/{persona_master_id}` -- perfil consolidado
 * (persona/transparencia/senescyt/foro). NO existe `/perfil` como sufijo.
 */
export function obtenerFuncionario(personaMasterId: number) {
  return apiClient
    .get<PerfilConsolidado>(`/api/v1/funcionarios/${personaMasterId}`)
    .then((r) => r.data)
}

/** `GET /api/v1/funcionarios/{id}/historial` -- arreglo directo, sin paginar. */
export function obtenerHistorialFuncionario(personaMasterId: number) {
  return apiClient
    .get<VersionHistorial[]>(`/api/v1/funcionarios/${personaMasterId}/historial`)
    .then((r) => r.data)
}

/** `GET /api/v1/funcionarios/{id}/academico`. */
export function obtenerAcademicoFuncionario(personaMasterId: number) {
  return apiClient
    .get<PerfilAcademico>(`/api/v1/funcionarios/${personaMasterId}/academico`)
    .then((r) => r.data)
}

/** `GET /api/v1/funcionarios/{id}/foro` -- recorte `.foro` del perfil consolidado. */
export function obtenerForoFuncionario(personaMasterId: number) {
  return apiClient
    .get<Record<string, unknown>>(`/api/v1/funcionarios/${personaMasterId}/foro`)
    .then((r) => r.data)
}

/** Inicia una validación individual y trazable; el job se consulta en `/jobs/{id}`. */
export function validarAbogado(personaMasterId: number) {
  return apiClient
    .post<{
      job_id: string
      estado: string
      resultado: {
        nombre: string
        puesto: string
        unidad: string
        ciudad: string | null
        telefono: string | null
        celular: string | null
        correo: string | null
      }
    }>(`/api/v1/funcionarios/${personaMasterId}/validar-abogado`)
    .then((r) => r.data)
}

/** `GET /api/v1/funcionarios/{id}/alertas` -- arreglo directo, sin paginar. */
export function obtenerAlertasFuncionario(personaMasterId: number) {
  return apiClient
    .get<AlertaFuncionario[]>(`/api/v1/funcionarios/${personaMasterId}/alertas`)
    .then((r) => r.data)
}

/** `GET /api/v1/funcionarios/{id}/timeline`. */
export function obtenerTimelineFuncionario(personaMasterId: number) {
  return apiClient
    .get<Timeline>(`/api/v1/funcionarios/${personaMasterId}/timeline`)
    .then((r) => r.data)
}
