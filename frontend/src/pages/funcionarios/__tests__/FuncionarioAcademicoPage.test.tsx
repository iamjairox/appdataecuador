import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearErrorBody, crearPerfilAcademico } from '../../../test/fixtures'
import { FuncionarioAcademicoPage } from '../FuncionarioAcademicoPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/academico', element: <FuncionarioAcademicoPage /> }]

describe('FuncionarioAcademicoPage', () => {
  it('títulos: muestra los campos reales de TituloAcademicoDTO', async () => {
    server.use(http.get(`${BASE}/api/v1/funcionarios/30/academico`, () => HttpResponse.json(crearPerfilAcademico())))
    renderConRouter(rutas, ['/funcionarios/30/academico'])

    // Cada campo aparece dos veces a propósito: destacado arriba Y en el
    // volcado genérico `RecordPreview` del mismo objeto (detalle completo).
    expect(await screen.findAllByText('Abogada de los Tribunales de la República')).not.toHaveLength(0)
    expect(screen.getAllByText('Universidad Central del Ecuador').length).toBeGreaterThan(0)
    expect(screen.getAllByText('tercer_nivel').length).toBeGreaterThan(0)
  })

  it('datos incompletos: un título sin `titulo` no rompe la página (usa el fallback honesto)', async () => {
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/academico`, () =>
        HttpResponse.json(crearPerfilAcademico({ titulos: [{ institucion: 'Universidad X' }] })),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/academico'])

    expect(await screen.findByText('Título sin nombre registrado')).toBeInTheDocument()
    expect(screen.getAllByText('Universidad X').length).toBeGreaterThan(0)
  })

  it('vacío: muestra el EmptyState real de títulos', async () => {
    server.use(http.get(`${BASE}/api/v1/funcionarios/30/academico`, () => HttpResponse.json(crearPerfilAcademico({ titulos: [] }))))
    renderConRouter(rutas, ['/funcionarios/30/academico'])

    expect(await screen.findByText('Sin títulos registrados')).toBeInTheDocument()
    expect(screen.getByText('Títulos (0)')).toBeInTheDocument()
  })

  it('error + retry', async () => {
    let intentos = 0
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30/academico`, () => {
        intentos += 1
        if (intentos === 1) {
          return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
        }
        return HttpResponse.json(crearPerfilAcademico())
      }),
    )
    renderConRouter(rutas, ['/funcionarios/30/academico'])

    await screen.findByText('No se pudo cargar el perfil académico')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findAllByText('Abogada de los Tribunales de la República')).not.toHaveLength(0)
  })
})
