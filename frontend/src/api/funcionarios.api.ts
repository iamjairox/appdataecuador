import { apiClient } from './client'
import type {
  AlertaFuncionario,
  PerfilAcademico,
  PerfilConsolidado,
  Timeline,
  VersionHistorial,
} from '../types'

export type RegistroForo = {
  nombre_completo?: string | null
  registro?: string | null
  estado?: string | null
  provincia?: string | null
  correo?: string | null
  celular?: string | null
}

export type PerfilForo = { registros?: RegistroForo[] }

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
    .get<PerfilForo>(`/api/v1/funcionarios/${personaMasterId}/foro`)
    .then((r) => r.data)
}

export type ResultadoValidacionAbogado = {
  estado_consulta_externa: 'error' | 'completada' | 'sin_coincidencia'
  job_id: string
  estado: string
  estado_identificacion: string
  confianza: number
  institucion: string
  tipo_institucion?: string
  provincia?: string
  mes_transparencia?: string
  nombre_completo: string
  cargo: string
  dependencia: string
  area_normalizada?: string
  correo_institucional: string | null
  telefono_institucional: string | null
  ciudad: string | null
  registro_foro: string | null
  estado_foro: string | null
  provincia_foro: string | null
  correo_personal: string | null
  celular_personal: string | null
  fuente: string | null
  fecha_consulta: string | null
  detalle: string | null
}

/** Inicia una validación individual y trazable; el job se consulta en `/jobs/{id}`. */
export function validarAbogado(personaMasterId: number) {
  return apiClient
    .post<ResultadoValidacionAbogado>(`/api/v1/funcionarios/${personaMasterId}/validar-abogado`)
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
