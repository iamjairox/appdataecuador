import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { exportarFuncionarios } from '../entidades.api'

const BASE = 'http://localhost:8000'

describe('exportarFuncionarios', () => {
  it('descarga exitosa: usa el formato pedido y el Content-Disposition real cuando el navegador lo expone', async () => {
    let formatoRecibido: string | null = null
    server.use(
      http.get(`${BASE}/api/v1/entidades/1/funcionarios/exportar`, ({ request }) => {
        formatoRecibido = new URL(request.url).searchParams.get('formato')
        return HttpResponse.text('nombre_completo,cedula\nAna Pérez,1712345678', {
          headers: {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=funcionarios_entidad_1.csv',
          },
        })
      }),
    )

    const resultado = await exportarFuncionarios(1, 'csv')

    expect(formatoRecibido).toBe('csv')
    expect(resultado.nombreArchivo).toBe('funcionarios_entidad_1.csv')
    expect(resultado.blob.type).toContain('text/csv')
    expect(await resultado.blob.text()).toContain('Ana Pérez')
  })

  it('nombre de archivo: si el header no está disponible, reconstruye el MISMO patrón real del backend (nunca inventa uno distinto)', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/2/funcionarios/exportar`, () =>
        HttpResponse.text('[]', { headers: { 'Content-Type': 'application/json' } }),
      ),
    )

    const resultado = await exportarFuncionarios(2, 'json')

    expect(resultado.nombreArchivo).toBe('funcionarios_entidad_2.json')
  })

  it('error: propaga el error real del backend (404 entidad no encontrada) como ApiError, no como Blob crudo', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entidades/999/funcionarios/exportar`, () =>
        HttpResponse.json(
          { error: { codigo: 'HTTP_404', mensaje: 'Entidad no encontrada: 999', detalle: null, request_id: 'req-1' } },
          { status: 404 },
        ),
      ),
    )

    await expect(exportarFuncionarios(999, 'csv')).rejects.toMatchObject({
      name: 'ApiError',
      codigo: 'HTTP_404',
      status: 404,
    })
  })
})
