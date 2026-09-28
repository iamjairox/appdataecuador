import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../../test/server'
import { renderConRouter } from '../../../test/test-utils'
import { crearErrorBody, crearFuncionarioListado, crearPaginaFuncionarios } from '../../../test/fixtures'
import { FuncionariosDeEntidadSection } from '../FuncionariosDeEntidadSection'
import { FuncionarioPerfilPage } from '../../funcionarios/FuncionarioPerfilPage'

const BASE = 'http://localhost:8000'
const rutas = [
  { path: '/entidades/:entidadId', element: <FuncionariosDeEntidadSection entidadId={1} /> },
  { path: '/funcionarios/:personaMasterId', element: <FuncionarioPerfilPage /> },
]

/** Contenedor mutable para capturar la última URL pedida por un test (evita reasignar un `let` directamente desde el resolver de MSW). */
interface Capturado {
  url: URL | null
}

function mockListado(resolver: (url: URL) => ReturnType<typeof HttpResponse.json>) {
  server.use(
    http.get(`${BASE}/api/v1/entidades/1/funcionarios`, ({ request }) => resolver(new URL(request.url))),
  )
}

function mockListadoCapturando(respuesta: (url: URL) => ReturnType<typeof HttpResponse.json>): Capturado {
  const capturado: Capturado = { url: null }
  mockListado((url) => {
    capturado.url = url
    return respuesta(url)
  })
  return capturado
}

// La tabla (desktop) y las tarjetas (mobile) del mismo funcionario están
// AMBAS en el DOM en jsdom (no hay layout real que oculte una vía CSS),
// así que cada nombre aparece 2 veces -- se toma la primera coincidencia
// real en vez de asumir que solo existe un elemento.
async function primerEnlace(nombre: string) {
  const enlaces = await screen.findAllByRole('link', { name: nombre })
  return enlaces[0] as HTMLElement
}

describe('FuncionariosDeEntidadSection', () => {
  it('1-2. carga inicial y muestra los resultados reales', async () => {
    mockListado(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])

    expect(screen.getByText(/cargando funcionarios/i)).toBeInTheDocument()
    expect(await primerEnlace('Ana Pérez')).toBeInTheDocument()
  })

  it.each([
    ['Nombres', 'nombre', 'Ana'],
    ['Apellidos', 'apellido', 'Pérez'],
    ['Cédula (exacta)', 'cedula', '1712345678'],
    ['Cargo', 'cargo', 'Abogada'],
    ['Dependencia', 'dependencia', 'Jurídica'],
    ['Correo', 'correo', 'ana@ejemplo.gob.ec'],
    ['Teléfono (exacto)', 'telefono', '022345678'],
  ])('3. filtro real por %s: envía el parámetro %s con el valor tecleado', async (label, param, valor) => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Ana Pérez')

    await userEvent.type(screen.getByLabelText(label), valor)
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get(param)).toBe(valor)
  })

  it('3. filtro real de Área: envía el valor exacto del enum', async () => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Ana Pérez')

    await userEvent.selectOptions(screen.getByLabelText('Área'), 'Jurídica')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('area')).toBe('juridica')
  })

  it('3. filtro real de Vigencia: por defecto pide solo vigentes; "Todos" envía solo_vigentes=false', async () => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Ana Pérez')

    // Por defecto (coincide con el default real del backend, Sección 10).
    expect(capturado.url?.searchParams.get('solo_vigentes')).toBe('true')

    await userEvent.selectOptions(screen.getByLabelText('Vigencia'), 'Todos (vigentes y no vigentes)')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('solo_vigentes')).toBe('false')
  })

  it('4. combinación de filtros: varios parámetros reales viajan juntos en la misma petición', async () => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Ana Pérez')

    await userEvent.type(screen.getByLabelText('Nombres'), 'Ana')
    await userEvent.type(screen.getByLabelText('Cargo'), 'Abogada')
    await userEvent.selectOptions(screen.getByLabelText('Área'), 'Jurídica')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('nombre')).toBe('Ana')
    expect(capturado.url?.searchParams.get('cargo')).toBe('Abogada')
    expect(capturado.url?.searchParams.get('area')).toBe('juridica')
  })

  it('5. limpiar filtros: quita todos los parámetros de la URL y vuelve a consultar sin filtros', async () => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1?nombre=Ana&cargo=Abogada'])
    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('nombre')).toBe('Ana')

    await userEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }))

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('nombre')).toBeNull()
    expect(capturado.url?.searchParams.get('cargo')).toBeNull()
    expect(screen.getByLabelText('Nombres')).toHaveValue('')
  })

  it('6. cambio de página: usa page/pages reales del backend y deshabilita los límites', async () => {
    const capturado = mockListadoCapturando((url) => {
      const page = Number(url.searchParams.get('page') ?? '1')
      return HttpResponse.json(
        crearPaginaFuncionarios({ page, pages: 2, total: 2, items: [crearFuncionarioListado({ nombre_completo: `Pagina${page}` })] }),
      )
    })
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Pagina1')
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()

    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    await primerEnlace('Pagina2')
    expect(capturado.url?.searchParams.get('page')).toBe('2')
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
  })

  it('7. cambio de page_size: reinicia a la página 1 y envía el tamaño real elegido', async () => {
    const capturado = mockListadoCapturando(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1?page=2'])
    await primerEnlace('Ana Pérez')

    await userEvent.selectOptions(screen.getByLabelText('Funcionarios por página'), '100')

    await primerEnlace('Ana Pérez')
    expect(capturado.url?.searchParams.get('page_size')).toBe('100')
    expect(capturado.url?.searchParams.get('page')).toBe('1')
  })

  it('8. sin resultados con filtros activos: ofrece limpiar filtros (no una tabla vacía muda)', async () => {
    mockListado(() => HttpResponse.json(crearPaginaFuncionarios({ items: [], total: 0, pages: 0 })))
    renderConRouter(rutas, ['/entidades/1?nombre=Inexistente'])

    expect(await screen.findByText('Sin resultados')).toBeInTheDocument()
    expect(screen.getByText('No se encontraron funcionarios con estos filtros.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Limpiar filtros' })).toBeInTheDocument()
  })

  it('9. error: muestra el mensaje real del backend', async () => {
    mockListado(() => HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 }))
    renderConRouter(rutas, ['/entidades/1'])

    expect(await screen.findByText('No se pudieron cargar los funcionarios')).toBeInTheDocument()
  })

  it('10. retry: el botón "Reintentar" vuelve a pedir los datos y puede recuperarse', async () => {
    const intentos: { total: number } = { total: 0 }
    mockListado(() => {
      intentos.total += 1
      if (intentos.total === 1) {
        return HttpResponse.json(crearErrorBody('ERROR_INTERNO', 'Ocurrio un error interno.'), { status: 500 })
      }
      return HttpResponse.json(crearPaginaFuncionarios())
    })
    renderConRouter(rutas, ['/entidades/1'])

    await screen.findByText('No se pudieron cargar los funcionarios')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await primerEnlace('Ana Pérez')).toBeInTheDocument()
    expect(intentos.total).toBe(2)
  })

  it('11. navega al perfil real usando persona_master_id (nunca un ID inventado)', async () => {
    mockListado(() => HttpResponse.json(crearPaginaFuncionarios({ items: [crearFuncionarioListado({ persona_master_id: 30 })] })))
    server.use(
      http.get(`${BASE}/api/v1/funcionarios/30`, () =>
        HttpResponse.json({ persona: { nombre_completo: 'Ana Pérez' }, transparencia: {}, senescyt: {}, foro: {}, generado_en: '2026-01-01' }),
      ),
    )
    renderConRouter(rutas, ['/entidades/1'])

    await userEvent.click(await primerEnlace('Ana Pérez'))

    expect(await screen.findByRole('heading', { name: 'Ana Pérez' })).toBeInTheDocument()
  })

  it('12. accesibilidad: cada filtro tiene un label real asociado (no solo placeholder)', async () => {
    mockListado(() => HttpResponse.json(crearPaginaFuncionarios()))
    renderConRouter(rutas, ['/entidades/1'])
    await primerEnlace('Ana Pérez')

    for (const label of ['Nombres', 'Apellidos', 'Cédula (exacta)', 'Cargo', 'Dependencia', 'Correo', 'Teléfono (exacto)', 'Área', 'Vigencia']) {
      expect(screen.getByLabelText(label)).toBeInTheDocument()
    }
  })
})
