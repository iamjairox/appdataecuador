import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearPerfilConsolidado } from '../../../test/fixtures'
import { FuncionarioPerfilPage } from '../FuncionarioPerfilPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId', element: <FuncionarioPerfilPage /> }]

describe('FuncionarioPerfilPage', () => {
  it('13. abre el perfil consolidado real vía GET /api/v1/funcionarios/{persona_master_id} (sin sufijo /perfil)', async () => {
    let rutaLlamada: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/:id`, ({ params, request }) => {
        rutaLlamada = new URL(request.url).pathname
        expect(params.id).toBe('30')
        return HttpResponse.json(crearPerfilConsolidado())
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30'])

    expect(await screen.findByRole('heading', { name: 'Ana Pérez' })).toBeInTheDocument()
    // Aparece tanto en la tarjeta "Datos de contacto" como en el volcado
    // genérico de "Persona" (RecordPreview) -- ambos son reales, no duplicados por error.
    expect(screen.getAllByText('1712345678').length).toBeGreaterThan(0)
    expect(screen.getAllByText('ana.perez@ejemplo.gob.ec').length).toBeGreaterThan(0)
    expect(rutaLlamada).toBe('/api/v1/funcionarios/30')
  })

  it('no aplana persona/transparencia/senescyt/foro: cada sección se muestra por separado', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/:id`, () =>
        HttpResponse.json(
          crearPerfilConsolidado({ transparencia: { cargos: [{ entidad: 'Ministerio X', cargo: 'Analista' }] } }),
        ),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30'])

    await screen.findByRole('heading', { name: 'Ana Pérez' })
    expect(screen.getByRole('heading', { name: 'Persona' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Transparencia' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'SENESCYT' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Foro de Abogados' })).toBeInTheDocument()
  })
})
