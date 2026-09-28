import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from '@tanstack/react-query'
import { server } from '../../test/server'
import { crearQueryClientDePrueba } from '../../test/test-utils'
import { anchorClickMock, createObjectURLMock } from '../../test/setup'
import { ExportarFuncionariosButton } from '../ExportarFuncionariosButton'

const BASE = 'http://localhost:8000'

function renderBoton(entidadId = 1) {
  const queryClient = crearQueryClientDePrueba()
  return render(
    <QueryClientProvider client={queryClient}>
      <ExportarFuncionariosButton entidadId={entidadId} />
    </QueryClientProvider>,
  )
}

describe('ExportarFuncionariosButton', () => {
  it('descarga exitosa: pide el formato seleccionado y dispara la descarga real', async () => {
    createObjectURLMock.mockClear()
    anchorClickMock.mockClear()
    let formatoRecibido: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/funcionarios/exportar`, ({ request }) => {
        formatoRecibido = new URL(request.url).searchParams.get('formato')
        return HttpResponse.text('a,b', {
          headers: { 'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=funcionarios_entidad_1.csv' },
        })
      }),
    )
    renderBoton(1)

    await userEvent.click(screen.getByRole('button', { name: /exportar/i }))

    expect(await screen.findByText('Descarga completada')).toBeInTheDocument()
    expect(formatoRecibido).toBe('csv')
    expect(createObjectURLMock).toHaveBeenCalled()
    expect(anchorClickMock).toHaveBeenCalled()
  })

  it('permite elegir JSON y lo envía como parámetro real', async () => {
    let formatoRecibido: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/funcionarios/exportar`, ({ request }) => {
        formatoRecibido = new URL(request.url).searchParams.get('formato')
        return HttpResponse.text('[]', { headers: { 'Content-Type': 'application/json' } })
      }),
    )
    renderBoton(1)

    await userEvent.selectOptions(screen.getByLabelText('Formato de exportación'), 'JSON')
    await userEvent.click(screen.getByRole('button', { name: /exportar/i }))

    await screen.findByText('Descarga completada')
    expect(formatoRecibido).toBe('json')
  })

  it('error: muestra el mensaje real del backend, sin bloquear el botón', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/funcionarios/exportar`, () =>
        HttpResponse.json(
          { error: { codigo: 'HTTP_404', mensaje: 'Entidad no encontrada: 1', detalle: null, request_id: 'req-2' } },
          { status: 404 },
        ),
      ),
    )
    renderBoton(1)

    await userEvent.click(screen.getByRole('button', { name: /exportar/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/no se encontró/i)
    expect(screen.getByRole('button', { name: /exportar/i })).not.toBeDisabled()
  })
})
