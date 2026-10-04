import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { FuncionarioValidarAbogadoPage } from '../FuncionarioValidarAbogadoPage'

const BASE = 'http://localhost:8000'
const rutas = [{ path: '/funcionarios/:personaMasterId/validar-abogado', element: <FuncionarioValidarAbogadoPage /> }]

describe('FuncionarioValidarAbogadoPage (validación POST)', () => {
  // La pantalla pide una confirmación nativa antes de enviar el POST. jsdom
  // no implementa `window.confirm`, por lo que cada caso que ejerce la
  // validación debe aceptar explícitamente esa confirmación.
  beforeEach(() => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra botón para validar y estado pendiente', async () => {
    server.use(
      http.post(`${BASE}/api/v1/funcionarios/30/validar-abogado`, () =>
        HttpResponse.json({
          job_id: 'test-job-id',
          estado: 'match_exact',
          estado_identificacion: 'match_exact',
          confianza: 95.5,
          institucion: 'ENTIDAD DE PRUEBA',
          tipo_institucion: 'GAD MUNICIPAL',
          provincia: 'PICHINCHA',
          mes_transparencia: '2026-09',
          nombre_completo: 'JUAN PEREZ GOMEZ',
          cargo: 'DIRECTOR JURIDICO',
          dependencia: 'DIRECCION DE ASESORIA JURIDICA',
          area_normalizada: 'juridica',
          ciudad: 'QUITO',
          correo_institucional: 'jperez@entidad.gob.ec',
          telefono_institucional: '02-1234567',
          registro_foro: 'REG-12345',
          estado_foro: 'VIGENTE',
          provincia_foro: 'PICHINCHA',
          correo_personal: 'jperez@gmail.com',
          celular_personal: '0991234567',
          fuente: 'foro_abogados',
          fecha_consulta: '2026-09-28T10:00:00Z',
          detalle: 'Identificación: match_exact | Foro: Registro: REG-12345 | Estado: VIGENTE | Provincia: PICHINCHA',
        }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/validar-abogado'])

    // Verificar que está el botón de validar
    const btnValidar = screen.getByRole('button', { name: 'Validar abogado' })
    expect(btnValidar).toBeInTheDocument()

    // Hacer clic en validar
    await userEvent.click(btnValidar)

    // Verificar que se muestra la información
    expect(await screen.findAllByText('Coincidencia exacta')).not.toHaveLength(0)
    expect(await screen.findByText('ENTIDAD DE PRUEBA')).toBeInTheDocument()
    expect(await screen.findByText('DIRECTOR JURIDICO')).toBeInTheDocument()
    expect(await screen.findByText('jperez@entidad.gob.ec')).toBeInTheDocument()
    expect(await screen.findByText('02-1234567')).toBeInTheDocument()
    expect(await screen.findByText('REG-12345')).toBeInTheDocument()
    expect(await screen.findByText('jperez@gmail.com')).toBeInTheDocument()
    expect(await screen.findByText('0991234567')).toBeInTheDocument()
  })

  it('muestra estado ambiguo correctamente', async () => {
    server.use(
      http.post(`${BASE}/api/v1/funcionarios/30/validar-abogado`, () =>
        HttpResponse.json({
          job_id: 'test-job-id',
          estado: 'ambiguous',
          estado_identificacion: 'ambiguous',
          confianza: 85.0,
          institucion: 'ENTIDAD DE PRUEBA',
          tipo_institucion: 'GAD MUNICIPAL',
          provincia: 'PICHINCHA',
          mes_transparencia: '2026-09',
          nombre_completo: 'JUAN PEREZ GOMEZ',
          cargo: 'DIRECTOR JURIDICO',
          dependencia: 'DIRECCION DE ASESORIA JURIDICA',
          area_normalizada: 'juridica',
          ciudad: 'QUITO',
          correo_institucional: 'jperez@entidad.gob.ec',
          telefono_institucional: '02-1234567',
          fuente: 'consultas_ecuador',
          fecha_consulta: '2026-09-28T10:00:00Z',
          detalle: 'Identificación: ambiguous',
        }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/validar-abogado'])

    const btnValidar = screen.getByRole('button', { name: 'Validar abogado' })
    await userEvent.click(btnValidar)

    expect(await screen.findByText('Resultado ambiguo - Revisar manualmente')).toBeInTheDocument()
    expect(screen.queryByText('Información Profesional')).not.toBeInTheDocument()
  })

  it('muestra fuente no disponible', async () => {
    server.use(
      http.post(`${BASE}/api/v1/funcionarios/30/validar-abogado`, () =>
        HttpResponse.json({
          job_id: 'test-job-id',
          estado: 'source_unavailable',
          estado_identificacion: 'source_unavailable',
          confianza: 0,
          institucion: 'ENTIDAD DE PRUEBA',
          tipo_institucion: 'GAD MUNICIPAL',
          provincia: 'PICHINCHA',
          mes_transparencia: '2026-09',
          nombre_completo: 'JUAN PEREZ GOMEZ',
          cargo: 'DIRECTOR JURIDICO',
          dependencia: 'DIRECCION DE ASESORIA JURIDICA',
          area_normalizada: 'juridica',
          ciudad: 'QUITO',
          correo_institucional: 'jperez@entidad.gob.ec',
          telefono_institucional: '02-1234567',
          fuente: 'consultas_ecuador',
          fecha_consulta: '2026-09-28T10:00:00Z',
          detalle: 'Identificación: source_unavailable',
        }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/validar-abogado'])

    const btnValidar = screen.getByRole('button', { name: 'Validar abogado' })
    await userEvent.click(btnValidar)

    expect(await screen.findAllByText('Fuente no disponible')).not.toHaveLength(0)
  })

  it('no muestra cédula en la respuesta', async () => {
    server.use(
      http.post(`${BASE}/api/v1/funcionarios/30/validar-abogado`, () =>
        HttpResponse.json({
          job_id: 'test-job-id',
          estado: 'match_exact',
          estado_identificacion: 'match_exact',
          confianza: 95.5,
          institucion: 'ENTIDAD DE PRUEBA',
          tipo_institucion: 'GAD MUNICIPAL',
          provincia: 'PICHINCHA',
          mes_transparencia: '2026-09',
          nombre_completo: 'JUAN PEREZ GOMEZ',
          cargo: 'DIRECTOR JURIDICO',
          dependencia: 'DIRECCION DE ASESORIA JURIDICA',
          area_normalizada: 'juridica',
          ciudad: 'QUITO',
          correo_institucional: 'jperez@entidad.gob.ec',
          telefono_institucional: '02-1234567',
          fuente: 'foro_abogados',
          fecha_consulta: '2026-09-28T10:00:00Z',
          detalle: 'Identificación: match_exact',
        }),
      ),
    )
    renderConRouter(rutas, ['/funcionarios/30/validar-abogado'])

    const btnValidar = screen.getByRole('button', { name: 'Validar abogado' })
    await userEvent.click(btnValidar)

    // Verificar que NO aparece ninguna cédula (patrón de 10 dígitos)
    const bodyText = document.body.textContent || ''
    expect(bodyText).not.toMatch(/\b\d{10}\b/)
  })
})
