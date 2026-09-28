import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearErrorBody, crearEtapaJob, crearJob } from '../../../test/fixtures'
import { JobDetallePage } from '../JobDetallePage'
import { EntidadDetallePage } from '../../entidades/EntidadDetallePage'
import type { EstadoJob } from '../../../types'

const BASE = 'http://localhost:8000'
const JOB_ID = '11111111-1111-4111-8111-111111111111'
const rutas = [
  { path: '/jobs/:jobId', element: <JobDetallePage /> },
  { path: '/entidades/:entidadId', element: <EntidadDetallePage /> },
]

describe('JobDetallePage', () => {
  it.each<EstadoJob>(['pendiente', 'en_cola', 'ejecutando', 'pausado', 'reintentando', 'completado', 'cancelado', 'error'])(
    'muestra el estado real "%s" -- nunca un estado inventado',
    async (estado) => {
      // `etapas: []` evita que el `estado_paso` de la etapa por defecto
      // ("completado") choque con el propio estado del job bajo prueba.
      server.use(http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () => HttpResponse.json(crearJob({ estado, etapas: [] }))))
      renderConRouter(rutas, [`/jobs/${JOB_ID}`])

      expect(await screen.findByText(estado)).toBeInTheDocument()
    },
  )

  it('datos completos: muestra entidad_id (con enlace), tipo, prioridad, política, intentos y parámetros', async () => {
    server.use(
      http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () =>
        HttpResponse.json(crearJob({ entidad_id: 7, parametros: { politica: 'consulta_rapida' } })),
      ),
    )
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    await screen.findByText('consulta_entidad')
    expect(screen.getByText('1 / 3')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /#7/ })).toHaveAttribute('href', '/entidades/7')
    expect(screen.getByText('politica')).toBeInTheDocument()
  })

  it('campos null: entidad_id/fechas/último error null se muestran como "—", nunca inventados', async () => {
    server.use(
      http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () =>
        HttpResponse.json(
          crearJob({
            entidad_id: null,
            iniciado_en: null,
            finalizado_en: null,
            ultimo_error: null,
            parametros: {},
          }),
        ),
      ),
    )
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    await screen.findByText('consulta_entidad')
    const guiones = screen.getAllByText('—')
    expect(guiones.length).toBeGreaterThanOrEqual(3)
  })

  it('etapas: muestra tipo_paso/estado_paso/duración reales', async () => {
    server.use(
      http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () =>
        HttpResponse.json(crearJob({ etapas: [crearEtapaJob({ tipo_paso: 'foro', estado_paso: 'completado', duracion_segundos: 1.5 })] })),
      ),
    )
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    expect(await screen.findByText('foro')).toBeInTheDocument()
    expect(screen.getByText('1.5')).toBeInTheDocument()
  })

  it('sin etapas y job no terminal: mensaje honesto, nunca rellena etapas artificialmente', async () => {
    server.use(http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () => HttpResponse.json(crearJob({ estado: 'ejecutando', etapas: [] }))))
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    expect(await screen.findByText('El backend aún no ha registrado etapas finalizadas.')).toBeInTheDocument()
  })

  it('error: job inexistente (404) muestra el mensaje real, sin stack trace', async () => {
    server.use(
      http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () =>
        HttpResponse.json(crearErrorBody('HTTP_404', `Job no encontrado: ${JOB_ID}`), { status: 404 }),
      ),
    )
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    expect(await screen.findByText('No se pudo cargar el trabajo')).toBeInTheDocument()
    expect(screen.queryByText(/traceback|axioserror/i)).not.toBeInTheDocument()
  })

  it('navegación: el enlace a la entidad usa entidad_id real, no un ID inventado', async () => {
    server.use(
      http.get(`${BASE}/api/v1/jobs/${JOB_ID}`, () => HttpResponse.json(crearJob({ entidad_id: 7 }))),
      http.get(`${BASE}/api/v1/entidades/7`, () =>
        HttpResponse.json({
          id: 7,
          nombre: 'Entidad Siete',
          tipo: null,
          provincia: null,
          ciudad: null,
          portal_origen: 'DPE',
          estado: 'activa',
          ultima_publicacion: null,
          ultima_actualizacion: null,
        }),
      ),
      http.get(`${BASE}/api/v1/entidades/7/funcionarios`, () =>
        HttpResponse.json({ items: [], page: 1, page_size: 50, total: 0, pages: 0 }),
      ),
    )
    renderConRouter(rutas, [`/jobs/${JOB_ID}`])

    await userEvent.click(await screen.findByRole('link', { name: /#7/ }))

    expect(await screen.findByRole('heading', { name: 'Entidad Siete' })).toBeInTheDocument()
  })
})
