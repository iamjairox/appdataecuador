import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearErrorBody, crearPuntoTimeline, crearTimeline } from '../../../test/fixtures'
import { FuncionarioTimelinePage } from '../FuncionarioTimelinePage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/timeline', element: <FuncionarioTimelinePage /> }]

describe('FuncionarioTimelinePage', () => {
  it('muestra los eventos reales en el orden que entrega el backend', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/timeline`, () =>
        HttpResponse.json(
          crearTimeline({
            puntos: [
              crearPuntoTimeline({ origen: 'transparencia', descripcion: 'Evento uno' }),
              crearPuntoTimeline({ origen: 'foro', descripcion: 'Evento dos' }),
            ],
          }),
        ),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/timeline'])

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Evento uno')
    expect(items[1]).toHaveTextContent('Evento dos')
    expect(screen.getByText('transparencia')).toBeInTheDocument()
    expect(screen.getByText('foro')).toBeInTheDocument()
  })

  it('vacío: muestra el EmptyState real sin inventar eventos', async () => {
    server.use(http.get(`${BASE}/api/v1/funcionarios/30/timeline`, () => HttpResponse.json(crearTimeline({ puntos: [] }))))
    renderConRouter(rutas, ['/funcionarios/30/timeline'])

    expect(await screen.findByText('Sin eventos')).toBeInTheDocument()
  })

  it('error + retry', async () => {
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/timeline`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
        }
        return HttpResponse.json(crearTimeline())
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30/timeline'])

    await screen.findByText('No se pudo cargar la línea de tiempo')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findAllByRole('listitem')).toHaveLength(1)
  })
})
