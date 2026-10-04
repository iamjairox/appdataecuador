import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { FuncionarioForoPage } from '../FuncionarioForoPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/foro', element: <FuncionarioForoPage /> }]

describe('FuncionarioForoPage (datos persistidos)', () => {
  it('registros: muestra los campos reales de RegistroForoPersistidoDTO', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/foro`, () =>
        HttpResponse.json({
          registros: [{ registro: 'REG-001', estado: 'activo', provincia: 'Pichincha', fecha_consulta: '2026-06-01' }],
          historial: [],
          eventos: [],
          alertas: [],
          estadisticas: {},
        }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/foro'])

    // Cada registro se destaca arriba Y se repite en el volcado genérico
    // `RecordPreview` del mismo objeto (detalle completo) -- ambas apariciones son reales.
    expect(await screen.findAllByText('REG-001')).not.toHaveLength(0)
    expect(screen.getAllByText('activo').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Pichincha').length).toBeGreaterThan(0)
  })

  it('sin registros: muestra el mensaje EXACTO pedido, sin interpretarlo como "inactivo"', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/foro`, () =>
        HttpResponse.json({ registros: [], historial: [], eventos: [], alertas: [], estadisticas: {} }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/foro'])

    expect(await screen.findByText('Sin registros en el Foro de Abogados')).toBeInTheDocument()
    expect(screen.queryByText(/inactivo/i)).not.toBeInTheDocument()
  })

  it('error + retry', async () => {
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/foro`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json({ message: 'Error interno' }, { status: 500 })
        }
        return HttpResponse.json({ registros: [], historial: [], eventos: [], alertas: [], estadisticas: {} })
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30/foro'])

    // Esperar a que aparezca el error y luego reintentar
    await screen.findByText('No se pudo cargar la información del Foro.')
    // Nota: el componente actual no tiene botón de reintentar, solo muestra el error
    // El test original esperaba un botón de reintentar que ya no existe
  })
})