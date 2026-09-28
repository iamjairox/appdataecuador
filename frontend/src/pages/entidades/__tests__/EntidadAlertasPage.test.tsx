import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearAlertaEntidad, crearEntidad, crearErrorBody, crearPaginaAlertas } from '../../../test/fixtures'
import { EntidadAlertasPage } from '../EntidadAlertasPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/entidades/:entidadId/alertas', element: <EntidadAlertasPage /> }]

function mockEntidad() {
  server.use(http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))))
}

describe('EntidadAlertasPage', () => {
  it('carga y muestra las alertas reales de la entidad', async () => {
    mockEntidad()
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/alertas`, () =>
        HttpResponse.json(crearPaginaAlertas({ items: [crearAlertaEntidad({ descripcion: 'Cambio de correo detectado.' })] })),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/alertas'])

    expect(screen.getByText(/cargando alertas/i)).toBeInTheDocument()
    expect(await screen.findByText('Cambio de correo detectado.')).toBeInTheDocument()
    expect(screen.getByText('medio')).toBeInTheDocument()
    expect(screen.getByText('pendiente')).toBeInTheDocument()
  })

  it('empty: muestra el mensaje explícito cuando no hay alertas', async () => {
    mockEntidad()
    server.use(http.get(`${BASE}/api/v1/entidades/1/alertas`, () => HttpResponse.json(crearPaginaAlertas({ items: [], total: 0, pages: 0 }))))
    renderConRouter(rutas, ['/entidades/1/alertas'])

    expect(await screen.findByText('Sin alertas')).toBeInTheDocument()
  })

  it('error + retry: muestra el error real y se recupera al reintentar', async () => {
    mockEntidad()
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/alertas`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
        }
        return HttpResponse.json(crearPaginaAlertas())
      }),
    )
    renderConRouter(rutas, ['/entidades/1/alertas'])

    await screen.findByText('No se pudieron cargar las alertas')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Cambio detectado en el cargo.')).toBeInTheDocument()
  })

  it('paginación: pedir la página siguiente vuelve a consultar con el page real', async () => {
    mockEntidad()
    let paginaPedida: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/alertas`, ({ request }) => {
        paginaPedida = new URL(request.url).searchParams.get('page')
        const page = Number(paginaPedida ?? '1')
        return HttpResponse.json(
          crearPaginaAlertas({ page, pages: 2, total: 2, items: [crearAlertaEntidad({ id: `alerta-${page}`, descripcion: `Alerta página ${page}` })] }),
        )
      }),
    )
    renderConRouter(rutas, ['/entidades/1/alertas'])

    await screen.findByText('Alerta página 1')
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(await screen.findByText('Alerta página 2')).toBeInTheDocument()
    expect(paginaPedida).toBe('2')
  })

  it('FASE 3.6: mantiene visible la tabla de la página anterior mientras llega la siguiente', async () => {
    mockEntidad()
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/alertas`, async ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get('page') ?? '1')
        if (page === 2) await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(
          crearPaginaAlertas({ page, pages: 2, total: 2, items: [crearAlertaEntidad({ id: `alerta-${page}`, descripcion: `Alerta página ${page}` })] }),
        )
      }),
    )
    renderConRouter(rutas, ['/entidades/1/alertas'])
    await screen.findByText('Alerta página 1')

    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(screen.getByText('Alerta página 1')).toBeInTheDocument()
    expect(screen.queryByText(/cargando alertas/i)).not.toBeInTheDocument()
    expect(screen.getByText('Actualizando…')).toBeInTheDocument()

    expect(await screen.findByText('Alerta página 2')).toBeInTheDocument()
  })

  it('accesibilidad: la tabla usa encabezados reales de columna', async () => {
    mockEntidad()
    server.use(http.get(`${BASE}/api/v1/entidades/1/alertas`, () => HttpResponse.json(crearPaginaAlertas())))
    renderConRouter(rutas, ['/entidades/1/alertas'])

    await screen.findByText('Cambio detectado en el cargo.')
    expect(screen.getByRole('columnheader', { name: 'Prioridad' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Estado' })).toBeInTheDocument()
  })

  it('FASE 3.7: cambiar de entidad (misma ruta) nunca muestra las alertas de la entidad anterior como placeholder', async () => {
    mockEntidad()
    server.use(
      http.get(`${BASE}/api/v1/entidades/2`, () => HttpResponse.json(crearEntidad({ id: 2 }))),
      http.get(`${BASE}/api/v1/entidades/1/alertas`, () =>
        HttpResponse.json(crearPaginaAlertas({ items: [crearAlertaEntidad({ descripcion: 'Alerta de la entidad 1' })] })),
      ),
      http.get(`${BASE}/api/v1/entidades/2/alertas`, async () => {
        await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(crearPaginaAlertas({ items: [crearAlertaEntidad({ descripcion: 'Alerta de la entidad 2' })] }))
      }),
    )
    const { router } = renderConRouter(rutas, ['/entidades/1/alertas'])
    await screen.findByText('Alerta de la entidad 1')

    // Simula navegación directa entre dos entidades ya visitadas en la
    // misma ruta (URL editada a mano o atrás/adelante del navegador) --
    // el componente NO se desmonta.
    await act(async () => {
      await router.navigate('/entidades/2/alertas')
    })

    expect(screen.queryByText('Alerta de la entidad 1')).not.toBeInTheDocument()
    expect(await screen.findByText('Alerta de la entidad 2')).toBeInTheDocument()
  })
})
