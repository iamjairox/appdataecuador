import axios, { type AxiosError } from 'axios'
import { env } from '../lib/env'
import { ApiError, type ApiErrorBody } from '../types/error'

/**
 * Cliente HTTP único (Regla 9): ninguna otra parte del frontend construye
 * URLs ni configura headers manualmente. Centraliza:
 *  - baseURL (VITE_API_URL)
 *  - X-Request-ID por petición (correlación con logs/errores del backend)
 *  - X-API-Key si está configurada (nunca se imprime)
 *  - normalización de errores al contrato real del backend (Módulo 10)
 */
export const apiClient = axios.create({
  baseURL: env.apiUrl,
  timeout: 120_000, // /entidades/{id}/consulta es sincrono y puede tardar
})

apiClient.interceptors.request.use((config) => {
  config.headers.set('X-Request-ID', crypto.randomUUID())
  if (env.apiKey) {
    config.headers.set('X-API-Key', env.apiKey)
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody | Blob>) => {
    const status = error.response?.status ?? null
    let cuerpo = error.response?.data

    // Peticiones con `responseType: 'blob'` (exportaciones) reciben
    // CUALQUIER respuesta -- también los errores JSON del backend -- como
    // Blob. Sin este paso se perdería el mensaje real y caería al genérico
    // "error de red".
    if (cuerpo instanceof Blob && cuerpo.type.includes('json')) {
      try {
        cuerpo = JSON.parse(await cuerpo.text()) as ApiErrorBody
      } catch {
        cuerpo = undefined
      }
    }

    if (cuerpo && !(cuerpo instanceof Blob) && cuerpo.error) {
      return Promise.reject(
        new ApiError(cuerpo.error.codigo, cuerpo.error.mensaje, cuerpo.error.request_id, status),
      )
    }

    // Sin conexión, timeout, u otra falla antes de llegar al backend --
    // nunca se propaga el error crudo de Axios/red al resto de la app.
    return Promise.reject(
      new ApiError(
        'ERROR_DE_RED',
        'No fue posible comunicarse con el servidor GovData. Verifica tu conexión.',
        null,
        status,
      ),
    )
  },
)
