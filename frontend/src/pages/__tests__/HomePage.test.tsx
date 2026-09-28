import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen, within } from '@testing-library/react'
import { server } from '../../test/server'
import { renderConRouter } from '../../test/test-utils'
import { crearEntidad, crearErrorBody, crearPaginaEntidades } from '../../test/fixtures'
import { HomePage } from '../HomePage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/', element: <HomePage /> }]

describe('HomePage', () => {
  it('carga inicial y muestra el total real de entidades (sin inventar estadísticas globales)', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('page_size')).toBe('100')
        return HttpResponse.json(crearPaginaEntidades({ total: 7 }))
      }),
    )
    renderConRouter(rutas, ['/'])

    expect(await screen.findByText('7')).toBeInTheDocument()
    expect(screen.getByText('Entidades registradas')).toBeInTheDocument()
    expect(
      screen.getByText(/no expone estadísticas globales de funcionarios jurídicos, alertas ni cambios/i),
    ).toBeInTheDocument()
  })

  it('muestra las entidades con actualización más reciente usando datos reales ya obtenidos', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, () =>
        HttpResponse.json(
          crearPaginaEntidades({
            items: [
              crearEntidad({ id: 1, nombre: 'Entidad Antigua', ultima_actualizacion: '2026-01-01T00:00:00Z' }),
              crearEntidad({ id: 2, nombre: 'Entidad Reciente', ultima_actualizacion: '2026-06-01T00:00:00Z' }),
            ],
            total: 2,
          }),
        ),
      ),
    )
    renderConRouter(rutas, ['/'])

    const heading = await screen.findByText('Entidades con actualización más reciente')
    const seccion = heading.closest('div') as HTMLElement
    const nombres = within(seccion).getAllByRole('link').map((l) => l.textContent)
    expect(nombres.indexOf('Entidad Reciente')).toBeLessThan(nombres.indexOf('Entidad Antigua'))
  })

  it('error: no rompe la página -- muestra el estado de error y el resto del panel sigue disponible', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades`, () =>
        HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }),
      ),
    )
    renderConRouter(rutas, ['/'])

    expect(await screen.findByText('No se pudieron cargar las entidades')).toBeInTheDocument()
    // El resto del panel (accesos rápidos) sigue disponible aunque la
    // lista de entidades falle -- el nombre accesible del link incluye
    // también su descripción, por eso se usa una coincidencia parcial.
    expect(screen.getByRole('link', { name: /^Entidades/ })).toBeInTheDocument()
  })
})
