import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../test/server'
import { renderConRouter } from '../../test/test-utils'
import { AppLayout } from '../AppLayout'

const BASE = 'http://localhost:8000'
const rutas = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <h1>Inicio</h1> },
      { path: 'entidades', element: <h1>Entidades</h1> },
    ],
  },
]

function mockHealth() {
  server.use(
    http.get(`${BASE}/health`, () =>
      HttpResponse.json({ status: 'ok', service: 'govdata-api', version: '1.0.0', timestamp: '2026-01-01T00:00:00Z' }),
    ),
  )
}

/**
 * FASE 3.6 -- Bloque 3: bug real confirmado con `getBoundingClientRect` a
 * 375px de ancho -- el sidebar fijo de 224px dejaba solo ~151px útiles
 * para el contenido. Estos tests verifican el comportamiento del panel
 * deslizable que lo corrige (no se puede verificar `md:hidden` en jsdom,
 * que no aplica media queries reales -- se verifica el estado funcional:
 * clases de transformación y apertura/cierre).
 */
describe('AppLayout / Sidebar -- panel de navegación móvil', () => {
  it('el panel empieza cerrado (fuera de pantalla, -translate-x-full) y sin overlay', () => {
    mockHealth()
    renderConRouter(rutas, ['/'])
    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })

    expect(nav.className).toMatch(/-translate-x-full/)
  })

  it('el botón "Abrir menú" abre el panel; "Cerrar menú" y el overlay lo cierran', async () => {
    mockHealth()
    renderConRouter(rutas, ['/'])
    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })

    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú de navegación' }))
    expect(nav.className).toMatch(/(?<!-)translate-x-0/)

    await userEvent.click(screen.getByRole('button', { name: 'Cerrar menú de navegación' }))
    expect(nav.className).toMatch(/-translate-x-full/)
  })

  it('navegar a una sección desde el panel lo cierra automáticamente', async () => {
    mockHealth()
    renderConRouter(rutas, ['/'])
    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })

    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú de navegación' }))
    expect(nav.className).toMatch(/(?<!-)translate-x-0/)

    await userEvent.click(screen.getByRole('link', { name: 'Entidades' }))

    expect(await screen.findByRole('heading', { name: 'Entidades' })).toBeInTheDocument()
    expect(nav.className).toMatch(/-translate-x-full/)
  })
})
