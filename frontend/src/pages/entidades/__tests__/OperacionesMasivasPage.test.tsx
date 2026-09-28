import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearEntidad, crearErrorBody, crearPaginaEntidades, crearResultadoConsulta } from '../../../test/fixtures'
import { OperacionesMasivasPage } from '../OperacionesMasivasPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/operaciones', element: <OperacionesMasivasPage /> }]

function mockEntidades(activas = 3) {
  server.use(
    http.get(`${BASE}/api/v1/entidades`, () =>
      HttpResponse.json(
        crearPaginaEntidades({
          items: Array.from({ length: activas }, (_, i) => crearEntidad({ id: i + 1, estado: 'activa' })),
          total: activas,
          pages: 1,
        }),
      ),
    ),
  )
}

async function irAConsultaMasivaConfirmando() {
  await userEvent.click(await screen.findByRole('button', { name: 'Ejecutar consulta masiva' }))
  await screen.findByText(/¿Deseas ejecutar consulta masiva sobre/)
}

describe('OperacionesMasivasPage', () => {
  it('avisa explícitamente que no se puede seleccionar un subconjunto de entidades y muestra el conteo real de activas', async () => {
    mockEntidades(5)
    renderConRouter(rutas, ['/operaciones'])

    expect(
      await screen.findByText(/El backend no permite seleccionar un subconjunto de entidades/),
    ).toBeInTheDocument()
    expect(await screen.findByText('5')).toBeInTheDocument()
    expect(screen.getByText('Entidades activas')).toBeInTheDocument()
  })

  it('consulta masiva: confirmación → ejecución (POST sin body, política como query param) → resultado con Job', async () => {
    mockEntidades(2)
    let politicaRecibida: string | null = null
    let cuerpoRecibido: string
    server.use(
      http.post(`${BASE}/api/v1/entidades/consulta-masiva`, async ({ request }) => {
        politicaRecibida = new URL(request.url).searchParams.get('politica')
        cuerpoRecibido = await request.text()
        return HttpResponse.json([
          crearResultadoConsulta({ entidad: { id: 1, nombre: 'Entidad Uno' } }),
          crearResultadoConsulta({ entidad: { id: 2, nombre: 'Entidad Dos' }, job: { id: 'job-2' } }),
        ])
      }),
    )
    renderConRouter(rutas, ['/operaciones'])

    await irAConsultaMasivaConfirmando()
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByText('2 entidades procesadas.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Entidad Uno' })).toHaveAttribute('href', '/entidades/1')
    expect(screen.getByRole('link', { name: 'Entidad Dos' })).toHaveAttribute('href', '/entidades/2')
    const enlacesJob = screen.getAllByRole('link', { name: /Ver/ }).map((el) => el.getAttribute('href'))
    expect(enlacesJob).toContain('/jobs/job-2')
    expect(politicaRecibida).toBeNull() // predeterminada: no se envía si no se eligió una
    expect(cuerpoRecibido!).toBe('') // SIN body -- confirmado en la auditoría
  })

  it('consulta masiva: error 500 muestra el error real, sin bloquear la tarjeta de actualización masiva', async () => {
    mockEntidades(1)
    server.use(
      http.post(`${BASE}/api/v1/entidades/consulta-masiva`, () =>
        HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }),
      ),
    )
    renderConRouter(rutas, ['/operaciones'])

    await irAConsultaMasivaConfirmando()
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByText('La consulta masiva no se pudo completar')).toBeInTheDocument()
    // La otra tarjeta sigue disponible de forma independiente.
    expect(screen.getByRole('button', { name: 'Ejecutar actualización masiva' })).toBeEnabled()
  })

  it('actualización masiva: confirmación → ejecución (POST sin body ni query params) → resultado', async () => {
    mockEntidades(1)
    let query: string
    let cuerpoRecibido: string
    server.use(
      http.post(`${BASE}/api/v1/entidades/actualizar-masivo`, async ({ request }) => {
        query = new URL(request.url).search
        cuerpoRecibido = await request.text()
        return HttpResponse.json([crearResultadoConsulta()])
      }),
    )
    renderConRouter(rutas, ['/operaciones'])

    await userEvent.click(await screen.findByRole('button', { name: 'Ejecutar actualización masiva' }))
    await screen.findByText(/¿Deseas forzar la actualización de/)
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(await screen.findByText('1 entidad procesada.')).toBeInTheDocument()
    expect(query!).toBe('')
    expect(cuerpoRecibido!).toBe('')
  })

  it('errores parciales: una entidad con errores[] no oculta las demás filas del resultado', async () => {
    mockEntidades(1)
    server.use(
      http.post(`${BASE}/api/v1/entidades/consulta-masiva`, () =>
        HttpResponse.json([
          crearResultadoConsulta({ entidad: { id: 1, nombre: 'Entidad Uno' }, errores: [] }),
          crearResultadoConsulta({ entidad: { id: 2, nombre: 'Entidad Dos' }, errores: ['Foro no disponible.'] }),
        ]),
      ),
    )
    renderConRouter(rutas, ['/operaciones'])

    await irAConsultaMasivaConfirmando()
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    await screen.findByText('2 entidades procesadas.')
    const filaDos = screen.getByText('Entidad Dos').closest('tr') as HTMLElement
    // El badge de conteo de errores es un <span>; se distingue de la celda
    // "Funcionarios jurídicos" (texto plano, también "1" por defecto en la fixture).
    expect(within(filaDos).getByText('1', { selector: 'span' })).toBeInTheDocument()
    expect(screen.getByText('Entidad Uno')).toBeInTheDocument()
  })

  it('seguridad: la petición pasa por el interceptor centralizado (X-Request-ID) y nunca expone la API key en el DOM', async () => {
    mockEntidades(1)
    let headerRequestId: string | null = null
    server.use(
      http.post(`${BASE}/api/v1/entidades/consulta-masiva`, ({ request }) => {
        headerRequestId = request.headers.get('X-Request-ID')
        return HttpResponse.json([crearResultadoConsulta()])
      }),
    )
    renderConRouter(rutas, ['/operaciones'])

    await irAConsultaMasivaConfirmando()
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    await screen.findByText('1 entidad procesada.')

    expect(headerRequestId).not.toBeNull()
    expect(document.body.innerHTML).not.toMatch(/x-api-key/i)
  })

  it('accesibilidad: el selector de política tiene un label asociado y es alcanzable por teclado', async () => {
    mockEntidades(1)
    renderConRouter(rutas, ['/operaciones'])

    const selector = await screen.findByLabelText('Política')
    expect(selector.tagName).toBe('SELECT')
    selector.focus()
    expect(selector).toHaveFocus()
  })
})
