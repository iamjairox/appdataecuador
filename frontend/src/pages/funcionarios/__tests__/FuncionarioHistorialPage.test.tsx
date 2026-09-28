import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearErrorBody, crearVersionHistorial } from '../../../test/fixtures'
import { FuncionarioHistorialPage } from '../FuncionarioHistorialPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/historial', element: <FuncionarioHistorialPage /> }]

describe('FuncionarioHistorialPage', () => {
  it('loading -> resultados: muestra los campos reales de VersionHistorialSchema, incluido correo/teléfono', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/historial`, () => HttpResponse.json([crearVersionHistorial()])),
    )
    renderConRouter(rutas, ['/funcionarios/30/historial'])

    expect(screen.getByText(/cargando historial/i)).toBeInTheDocument()
    expect(await screen.findByText('Abogada')).toBeInTheDocument()
    expect(screen.getByText('ana.perez@ejemplo.gob.ec')).toBeInTheDocument()
    expect(screen.getByText('022345678')).toBeInTheDocument()
  })

  it('vacío: muestra el EmptyState real', async () => {
    server.use(http.get(`${BASE}/api/v1/funcionarios/30/historial`, () => HttpResponse.json([])))
    renderConRouter(rutas, ['/funcionarios/30/historial'])

    expect(await screen.findByText('Sin historial')).toBeInTheDocument()
  })

  it('error + retry: muestra el error real y se recupera', async () => {
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/historial`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
        }
        return HttpResponse.json([crearVersionHistorial()])
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30/historial'])

    await screen.findByText('No se pudo cargar el historial')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Abogada')).toBeInTheDocument()
  })
})
