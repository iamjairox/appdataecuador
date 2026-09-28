import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearEntidad, crearErrorBody, crearPaginaEntidades, crearPaginaFuncionarios } from '../../../test/fixtures'
import { EntidadesListPage } from '../EntidadesListPage'
import { EntidadDetallePage } from '../EntidadDetallePage'

const BASE = 'http://localhost:8000'
const rutas = [
  { path: '/entidades', element: <EntidadesListPage /> },
  { path: '/entidades/:entidadId', element: <EntidadDetallePage /> },
]

describe('EntidadesListPage', () => {
  it('1. lista las entidades devueltas por GET /api/v1/entidades', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, () =>
        HttpResponse.json(crearPaginaEntidades({ items: [crearEntidad({ nombre: 'Ministerio de Prueba' })] })),
      ),
    )
    renderConRouter(rutas, ['/entidades'])

    expect(await screen.findByRole('link', { name: 'Ministerio de Prueba' })).toBeInTheDocument()
  })

  it('2. muestra el estado de carga antes de recibir la respuesta', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, async () => {
        await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(crearPaginaEntidades())
      }),
    )
    renderConRouter(rutas, ['/entidades'])

    expect(screen.getByText(/cargando entidades/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText(/cargando entidades/i)).not.toBeInTheDocument())
  })

  it('3. muestra el empty state cuando items está vacío', async () => {
    server.use(http.get(`${BASE}/api/v1/entidades`, () => HttpResponse.json(crearPaginaEntidades({ items: [], total: 0, pages: 0 }))))
    renderConRouter(rutas, ['/entidades'])

    expect(await screen.findByText('Sin resultados')).toBeInTheDocument()
  })

  it('4. muestra un error legible cuando el backend responde 500', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, () =>
        HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }),
      ),
    )
    renderConRouter(rutas, ['/entidades'])

    expect(await screen.findByText('No se pudieron cargar las entidades')).toBeInTheDocument()
    expect(screen.queryByText(/AxiosError/i)).not.toBeInTheDocument()
  })

  it('5. paginación: pedir la página siguiente vuelve a consultar al backend server-side', async () => {
    let paginaSolicitada: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/entidades`, ({ request }) => {
        const url = new URL(request.url)
        paginaSolicitada = url.searchParams.get('page')
        const page = Number(paginaSolicitada ?? '1')
        return HttpResponse.json(
          crearPaginaEntidades({
            items: [crearEntidad({ id: page, nombre: `Entidad página ${page}` })],
            page,
            pages: 2,
            total: 2,
          }),
        )
      }),
    )
    renderConRouter(rutas, ['/entidades'])

    expect(await screen.findByRole('link', { name: 'Entidad página 1' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(await screen.findByRole('link', { name: 'Entidad página 2' })).toBeInTheDocument()
    expect(paginaSolicitada).toBe('2')
  })

  it('7. FASE 3.6: mantiene visible la página anterior mientras llega la siguiente, sin spinner de pantalla completa', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, async ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get('page') ?? '1')
        if (page === 2) await new Promise((r) => setTimeout(r, 50))
        return HttpResponse.json(
          crearPaginaEntidades({ items: [crearEntidad({ id: page, nombre: `Entidad página ${page}` })], page, pages: 2, total: 2 }),
        )
      }),
    )
    renderConRouter(rutas, ['/entidades'])
    expect(await screen.findByRole('link', { name: 'Entidad página 1' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    // Mientras llega la página 2, la tabla de la página 1 sigue visible
    // (keepPreviousData) -- nunca un spinner de pantalla completa que la
    // reemplace, solo el indicador discreto "Actualizando…".
    expect(screen.getByRole('link', { name: 'Entidad página 1' })).toBeInTheDocument()
    expect(screen.queryByText(/cargando entidades/i)).not.toBeInTheDocument()
    expect(screen.getByText('Actualizando…')).toBeInTheDocument()

    expect(await screen.findByRole('link', { name: 'Entidad página 2' })).toBeInTheDocument()
  })

  it('6. navega al detalle de la entidad al hacer clic en "Ver detalle"', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, () => HttpResponse.json(crearPaginaEntidades({ items: [crearEntidad({ id: 7, nombre: 'Entidad Siete' })] }))),
      http.get(`${BASE}/api/v1/entidades/7`, () => HttpResponse.json(crearEntidad({ id: 7, nombre: 'Entidad Siete' }))),
      http.get(`${BASE}/api/v1/entidades/7/funcionarios`, () => HttpResponse.json(crearPaginaFuncionarios({ items: [] }))),
    )
    renderConRouter(rutas, ['/entidades'])

    const fila = (await screen.findByRole('link', { name: 'Entidad Siete' })).closest('tr')
    expect(fila).not.toBeNull()
    await userEvent.click(within(fila as HTMLElement).getByRole('link', { name: 'Ver detalle' }))

    expect(await screen.findByRole('heading', { name: 'Entidad Siete' })).toBeInTheDocument()
  })
})
