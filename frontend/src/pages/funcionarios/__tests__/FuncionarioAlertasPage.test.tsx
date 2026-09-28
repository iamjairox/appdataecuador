import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearAlertaFuncionario, crearErrorBody } from '../../../test/fixtures'
import { FuncionarioAlertasPage } from '../FuncionarioAlertasPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/alertas', element: <FuncionarioAlertasPage /> }]

describe('FuncionarioAlertasPage', () => {
  it('reconoce la prioridad real ("alto", no "alta") -- regresión del bug encontrado en FASE 3.3', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/alertas`, () =>
        HttpResponse.json([crearAlertaFuncionario({ prioridad: 'alto', estado: 'pendiente' })]),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/alertas'])

    const celdaPrioridad = await screen.findByText('alto')
    // tone="warning" -> Badge.tsx usa bg-amber-100 text-amber-800 (no el
    // gris neutral que salía antes de corregir el bug de FASE 3.3).
    expect(celdaPrioridad.className).toContain('amber')
  })

  it('reconoce el estado real ("pendiente"/"enviada"/"descartada")', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/alertas`, () =>
        HttpResponse.json([crearAlertaFuncionario({ estado: 'enviada' })]),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/alertas'])

    const celdaEstado = await screen.findByText('enviada')
    // tone="success" -> Badge.tsx usa bg-emerald-100.
    expect(celdaEstado.className).toContain('emerald')
  })

  it('empty: muestra el mensaje explícito cuando no hay alertas', async () => {
    server.use(http.get(`${BASE}/api/v1/funcionarios/30/alertas`, () => HttpResponse.json([])))
    renderConRouter(rutas, ['/funcionarios/30/alertas'])

    expect(await screen.findByText('Sin alertas')).toBeInTheDocument()
  })

  it('error + retry: muestra el error real y se recupera', async () => {
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/alertas`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
        }
        return HttpResponse.json([crearAlertaFuncionario()])
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30/alertas'])

    await screen.findByText('No se pudieron cargar las alertas')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Nuevo registro en el Foro de Abogados.')).toBeInTheDocument()
  })
})
