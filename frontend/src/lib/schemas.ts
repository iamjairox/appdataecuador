import { z } from 'zod'

/**
 * Validación con Zod de las respuestas MÁS críticas (Regla: "no asumir
 * que cualquier JSON recibido es válido"). No se valida cada respuesta
 * del backend en esta fase -- solo la que ya se consume de verdad
 * (listado de entidades); el resto de contratos se valida a medida que
 * se cablean sus pantallas en fases siguientes.
 */

export const entidadSchema = z.object({
  id: z.number(),
  nombre: z.string(),
  tipo: z.string().nullable(),
  provincia: z.string().nullable(),
  ciudad: z.string().nullable(),
  portal_origen: z.string(),
  estado: z.string(),
  ultima_publicacion: z.string().nullable(),
  ultima_actualizacion: z.string().nullable(),
})

export const paginaEntidadSchema = z.object({
  items: z.array(entidadSchema),
  page: z.number(),
  page_size: z.number(),
  total: z.number(),
  pages: z.number(),
})

export const apiErrorBodySchema = z.object({
  error: z.object({
    codigo: z.string(),
    mensaje: z.string(),
    detalle: z.string().nullable(),
    request_id: z.string().nullable(),
  }),
})
