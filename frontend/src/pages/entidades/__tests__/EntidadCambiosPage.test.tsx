import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearCambioEntidad, crearEntidad, crearErrorBody, crearPaginaCambios } from '../../../test/fixtures'
import { EntidadCambiosPage } from '../EntidadCambiosPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/entidades/:entidadId/cambios', element: <EntidadCambiosPage /> }]

function mockEntidad() {
  server.use(http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))))
}

interface Capturado {
  url: URL | null
}

function mockCambios(respuesta: (url: URL) => ReturnType<typeof HttpResponse.json>): Capturado {
  const capturado: Capturado = { url: null }
  server.use(
    http.get(`${BASE}/api/v1/entidades/1/cambios`, ({ request }) => {
      const url = new URL(request.url)
      capturado.url = url
      return respuesta(url)
    }),
  )
  return capturado
}

describe('EntidadCambiosPage', () => {
  it('carga y muestra los cambios reales; tipo_cambio/criticidad null se muestran como "—", nunca inventados', async () => {
    mockEntidad()
    mockCambios(() => HttpResponse.json(crearPaginaCambios()))
    renderConRouter(rutas, ['/entidades/1/cambios'])

    expect(screen.getByText(/cargando cambios/i)).toBeInTheDocument()
    expect(await screen.findByText('Directora Jurídica')).toBeInTheDocument()
    const fila = screen.getByText('Directora Jurídica').closest('tr') as HTMLElement
    expect(fila.textContent).toMatch(/—/)
  })

  it('empty: muestra el mensaje explícito cuando no hay cambios', async () => {
    mockEntidad()
    mockCambios(() => HttpResponse.json(crearPaginaCambios({ items: [], total: 0, pages: 0 })))
    renderConRouter(rutas, ['/entidades/1/cambios'])

    expect(await screen.findByText('Sin cambios')).toBeInTheDocument()
  })

  it('error: muestra el error real del backend', async () => {
    mockEntidad()
    mockCambios(() => HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }))
    renderConRouter(rutas, ['/entidades/1/cambios'])

    expect(await screen.findByText('No se pudieron cargar los cambios')).toBeInTheDocument()
  })

  it('filtro real desde/hasta: envía los parámetros reales del backend', async () => {
    mockEntidad()
    const capturado = mockCambios(() => HttpResponse.json(crearPaginaCambios()))
    renderConRouter(rutas, ['/entidades/1/cambios'])
    await screen.findByText('Directora Jurídica')

    await userEvent.type(screen.getByLabelText('Desde'), '2026-01-01')
    await userEvent.type(screen.getByLabelText('Hasta'), '2026-06-01')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar' }))

    await screen.findByText('Directora Jurídica')
    expect(capturado.url?.searchParams.get('desde')).toBe('2026-01-01')
    expect(capturado.url?.searchParams.get('hasta')).toBe('2026-06-01')
  })

  it('paginación: pedir la página siguiente usa page/pages reales', async () => {
    mockEntidad()
    const capturado = mockCambios((url) => {
      const page = Number(url.searchParams.get('page') ?? '1')
      return HttpResponse.json(
        crearPaginaCambios({ page, pages: 2, total: 2, items: [crearCambioEntidad({ cargo: `Cargo página ${page}` })] }),
      )
    })
    renderConRouter(rutas, ['/entidades/1/cambios'])

    await screen.findByText('Cargo página 1')
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(await screen.findByText('Cargo página 2')).toBeInTheDocument()
    expect(capturado.url?.searchParams.get('page')).toBe('2')
  })

  it('FASE 3.6: mantiene visible la tabla de la página anterior mientras llega la siguiente', async () => {
    mockEntidad()
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/cambios`, async ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get('page') ?? '1')
        if (page === 2) await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(
          crearPaginaCambios({ page, pages: 2, total: 2, items: [crearCambioEntidad({ cargo: `Cargo página ${page}` })] }),
        )
      }),
    )
    renderConRouter(rutas, ['/entidades/1/cambios'])
    await screen.findByText('Cargo página 1')

    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(screen.getByText('Cargo página 1')).toBeInTheDocument()
    expect(screen.queryByText(/cargando cambios/i)).not.toBeInTheDocument()
    expect(screen.getByText('Actualizando…')).toBeInTheDocument()

    expect(await screen.findByText('Cargo página 2')).toBeInTheDocument()
  })

  it('FASE 3.7: cambiar de entidad (misma ruta) nunca muestra los cambios de la entidad anterior como placeholder', async () => {
    mockEntidad()
    server.use(
      http.get(`${BASE}/api/v1/entidades/2`, () => HttpResponse.json(crearEntidad({ id: 2 }))),
      http.get(`${BASE}/api/v1/entidades/1/cambios`, () =>
        HttpResponse.json(crearPaginaCambios({ items: [crearCambioEntidad({ cargo: 'Cargo de la entidad 1' })] })),
      ),
      http.get(`${BASE}/api/v1/entidades/2/cambios`, async () => {
        await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(crearPaginaCambios({ items: [crearCambioEntidad({ cargo: 'Cargo de la entidad 2' })] }))
      }),
    )
    const { router } = renderConRouter(rutas, ['/entidades/1/cambios'])
    await screen.findByText('Cargo de la entidad 1')

    // Simula navegación directa entre dos entidades ya visitadas en la
    // misma ruta (URL editada a mano o atrás/adelante del navegador) --
    // el componente NO se desmonta, a diferencia de `EntidadDetallePage`.
    await act(async () => {
      await router.navigate('/entidades/2/cambios')
    })

    expect(screen.queryByText('Cargo de la entidad 1')).not.toBeInTheDocument()
    expect(await screen.findByText('Cargo de la entidad 2')).toBeInTheDocument()
  })
})
