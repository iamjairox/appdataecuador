import { describe, expect, it } from 'vitest'
import { http, HttpResponse, delay } from 'msw'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { clipboardWriteTextMock } from '../../../test/setup'
import { renderConRouter } from '../../../test/test-utils'
import { crearEntidad, crearErrorBody, crearResultadoConsulta } from '../../../test/fixtures'
import { EntidadConsultaPage } from '../EntidadConsultaPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/entidades/:entidadId/consulta', element: <EntidadConsultaPage /> }]

async function llegarAConfirmar() {
  await userEvent.click(await screen.findByRole('button', { name: 'Ejecutar consulta' }))
  expect(await screen.findByText('¿Consultar esta entidad?')).toBeInTheDocument()
}

describe('EntidadConsultaPage', () => {
  it('7. pide confirmación antes de ejecutar la consulta', async () => {
    server.use(http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))))
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Consultar' })).toBeInTheDocument()
  })

  it('8. consulta exitosa: GET /entidades/1/consulta y muestra el resultado real', async () => {
    let peticiones = 0
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () => {
        peticiones += 1
        return HttpResponse.json(crearResultadoConsulta())
      }),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))

    expect(await screen.findByText('Consulta completada')).toBeInTheDocument()
    expect(screen.getAllByText('Ana Pérez').length).toBeGreaterThan(0)
    expect(peticiones).toBe(1)
  })

  it('9. consulta fallida: muestra el mensaje real del backend y el request_id', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () =>
        HttpResponse.json(crearErrorBody('ConsultaSenescytFallidaError', 'No fue posible consultar SENESCYT.', 'req-999'), {
          status: 503,
        }),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))

    expect(await screen.findByText('La consulta no se pudo completar')).toBeInTheDocument()
    expect(screen.getByText(/no fue posible consultar senescyt/i)).toBeInTheDocument()
    expect(screen.getByText(/req-999/)).toBeInTheDocument()
    expect(screen.queryByText(/AxiosError|stack/i)).not.toBeInTheDocument()
  })

  it('10. previene doble ejecución: un solo clic real llega al backend aunque se pulse varias veces', async () => {
    let peticiones = 0
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, async () => {
        peticiones += 1
        await delay(30)
        return HttpResponse.json(crearResultadoConsulta())
      }),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    const boton = screen.getByRole('button', { name: 'Consultar' })
    await userEvent.click(boton)
    // Una vez pendiente, el botón de confirmación ya no está en el DOM
    // (se reemplaza por el estado "Procesando…"), así que un segundo
    // clic no puede repetirse -- se verifica que solo hubo 1 petición.
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Consultar' })).not.toBeInTheDocument())

    await screen.findByText('Consulta completada')
    expect(peticiones).toBe(1)
  })

  it('11. resultado sin funcionarios muestra el mensaje explícito (sin tabla vacía)', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () =>
        HttpResponse.json(crearResultadoConsulta({ funcionarios: [] })),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))

    expect(await screen.findByText('No se encontraron funcionarios jurídicos para esta consulta.')).toBeInTheDocument()
  })

  it('12. errores parciales: con funcionarios Y errores, se muestra "completada con observaciones" (no fracaso total)', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () =>
        HttpResponse.json(
          crearResultadoConsulta({ errores: ['Foro no disponible para la persona X.'] }),
        ),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))

    expect(await screen.findByText('Consulta completada con observaciones')).toBeInTheDocument()
    expect(screen.getByText('Foro no disponible para la persona X.')).toBeInTheDocument()
    // El funcionario sigue visible: un error puntual no oculta el resto del resultado.
    expect(screen.getAllByText('Ana Pérez').length).toBeGreaterThan(0)
  })

  it('14. copia la cédula del funcionario al portapapeles', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () => HttpResponse.json(crearResultadoConsulta())),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))
    await screen.findAllByText('Ana Pérez')

    const escribir = clipboardWriteTextMock
    escribir.mockClear()
    const [botonCedula] = screen.getAllByRole('button', { name: 'Copiar cédula' })
    await userEvent.click(botonCedula!)

    expect(escribir).toHaveBeenCalledWith('1712345678')
    expect(await screen.findAllByText('Copiado')).not.toHaveLength(0)
  })

  it('15. copia el correo del funcionario al portapapeles', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/consulta`, () => HttpResponse.json(crearResultadoConsulta())),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await llegarAConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }))
    await screen.findAllByText('Ana Pérez')

    const escribir = clipboardWriteTextMock
    escribir.mockClear()
    const [botonCorreo] = screen.getAllByRole('button', { name: 'Copiar correo' })
    await userEvent.click(botonCorreo!)

    expect(escribir).toHaveBeenCalledWith('ana.perez@ejemplo.gob.ec')
  })

  // -- FASE 3.5: actualización individual (`POST /entidades/{id}/actualizar`, SIN body) --

  it('16. actualizar: pide confirmación con el texto real (ignora caché) antes de ejecutar', async () => {
    server.use(http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))))
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar (forzar)' }))

    expect(await screen.findByText('¿Forzar actualización completa de esta entidad?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Actualizar' })).toBeInTheDocument()
  })

  it('17. actualizar: ejecución real -- POST sin body a /entidades/1/actualizar', async () => {
    let peticiones = 0
    let cuerpoRecibido: string
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.post(`${BASE}/api/v1/entidades/1/actualizar`, async ({ request }) => {
        peticiones += 1
        cuerpoRecibido = await request.text()
        return HttpResponse.json(crearResultadoConsulta())
      }),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar (forzar)' }))
    await screen.findByText('¿Forzar actualización completa de esta entidad?')
    await userEvent.click(screen.getByRole('button', { name: 'Actualizar' }))

    expect(await screen.findByText('Consulta completada')).toBeInTheDocument()
    expect(peticiones).toBe(1)
    expect(cuerpoRecibido!).toBe('')
  })

  it('18. actualizar: error real muestra mensaje sin stack trace y permite reintentar', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.post(`${BASE}/api/v1/entidades/1/actualizar`, () =>
        HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar (forzar)' }))
    await screen.findByText('¿Forzar actualización completa de esta entidad?')
    await userEvent.click(screen.getByRole('button', { name: 'Actualizar' }))

    expect(await screen.findByText('La actualización no se pudo completar')).toBeInTheDocument()
    expect(screen.queryByText(/AxiosError|stack/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it('19. actualizar: el resultado enlaza al Job real cuando job.id existe', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.post(`${BASE}/api/v1/entidades/1/actualizar`, () =>
        HttpResponse.json(crearResultadoConsulta({ job: { id: 'job-abc-123' } })),
      ),
    )
    renderConRouter(rutas, ['/entidades/1/consulta'])

    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar (forzar)' }))
    await screen.findByText('¿Forzar actualización completa de esta entidad?')
    await userEvent.click(screen.getByRole('button', { name: 'Actualizar' }))

    const enlace = await screen.findByRole('link', { name: /Ver trabajo/ })
    expect(enlace).toHaveAttribute('href', '/jobs/job-abc-123')
  })
})
