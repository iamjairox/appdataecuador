import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearEntidad } from '../../../test/fixtures'
import { EntidadConsultaPage } from '../EntidadConsultaPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/entidades/:entidadId/consulta', element: <EntidadConsultaPage /> }]

describe('EntidadConsultaPage', () => {
  it('expone únicamente el flujo manual y no el pipeline externo automático heredado', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/1`, () => HttpResponse.json(crearEntidad({ id: 1 }))),
      http.get(`${BASE}/api/v1/entidades/1/funcionarios/estado-listado`, () => HttpResponse.json({ funcionarios_persistidos: 0, periodo_publicacion: null, fecha_extraccion: null, requiere_actualizacion: true, mensaje: 'Sin listado.' })),
    )

    renderConRouter(rutas, ['/entidades/1/consulta'])

    expect(await screen.findByText('Consulta controlada de entidad')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /verificar y abrir listado de funcionarios/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ver profesionales jurídicos y afines/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ejecutar consulta' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Actualizar (forzar)' })).not.toBeInTheDocument()
  })
})
