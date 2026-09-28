import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Loader2, Search, Users2, X } from 'lucide-react'
import { useFuncionariosDeEntidad } from '../../hooks/useEntidades'
import { Input, Select, Button, Spinner, EmptyState, Table, Thead, Tbody, Tr, Th, Td, Badge, Card, CardBody } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { ExportarFuncionariosButton } from '../../components/ExportarFuncionariosButton'
import { CopyButton } from '../../components/CopyButton'
import type { AreaFuncionario, FiltrosFuncionario } from '../../types'

const TAMANOS_PAGINA = [10, 20, 50, 100] as const
const PAGE_SIZE_DEFECTO = 50
const CAMPOS_TEXTO = ['nombre', 'apellido', 'cedula', 'cargo', 'dependencia', 'correo', 'telefono'] as const

/**
 * Filtros REALES de `GET /entidades/{id}/funcionarios` (ver
 * `types/funcionario.ts::FiltrosFuncionario` para el detalle exacto de
 * cada uno). Se sincronizan con la URL (`?nombre=...&page=2`) para poder
 * refrescar/compartir/usar atrás-adelante conservando la búsqueda.
 */
function leerFiltrosDesdeParams(params: URLSearchParams): FiltrosFuncionario {
  const filtros: FiltrosFuncionario = { solo_vigentes: params.get('solo_vigentes') !== 'false' }
  for (const campo of CAMPOS_TEXTO) {
    const valor = params.get(campo)
    if (valor) filtros[campo] = valor
  }
  const area = params.get('area')
  if (area === 'juridica' || area === 'financiera') filtros.area = area
  const page = Number(params.get('page'))
  filtros.page = Number.isInteger(page) && page > 0 ? page : 1
  const pageSize = Number(params.get('page_size'))
  filtros.page_size = (TAMANOS_PAGINA as readonly number[]).includes(pageSize) ? pageSize : PAGE_SIZE_DEFECTO
  return filtros
}

function filtrosAParams(filtros: FiltrosFuncionario): URLSearchParams {
  const params = new URLSearchParams()
  for (const campo of CAMPOS_TEXTO) {
    const valor = filtros[campo]
    if (valor) params.set(campo, valor)
  }
  if (filtros.area) params.set('area', filtros.area)
  if (filtros.solo_vigentes === false) params.set('solo_vigentes', 'false')
  if (filtros.page && filtros.page !== 1) params.set('page', String(filtros.page))
  if (filtros.page_size && filtros.page_size !== PAGE_SIZE_DEFECTO) {
    params.set('page_size', String(filtros.page_size))
  }
  return params
}

function hayFiltrosDeBusqueda(filtros: FiltrosFuncionario): boolean {
  return CAMPOS_TEXTO.some((c) => filtros[c]) || !!filtros.area || filtros.solo_vigentes === false
}

interface FuncionariosDeEntidadSectionProps {
  entidadId: number
}

export function FuncionariosDeEntidadSection({ entidadId }: FuncionariosDeEntidadSectionProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const filtrosAplicados = leerFiltrosDesdeParams(searchParams)

  // Borrador del formulario -- se inicializa desde la URL (para que un
  // enlace compartido/recargado muestre los mismos filtros ya aplicados)
  // y solo viaja al backend cuando el usuario presiona "Aplicar filtros".
  const [borrador, setBorrador] = useState<FiltrosFuncionario>(filtrosAplicados)

  const funcionarios = useFuncionariosDeEntidad(entidadId, filtrosAplicados)

  function actualizarParams(cambios: Partial<FiltrosFuncionario>, reiniciarPagina: boolean) {
    const siguiente: FiltrosFuncionario = {
      ...filtrosAplicados,
      ...cambios,
      page: reiniciarPagina ? 1 : (cambios.page ?? filtrosAplicados.page),
    }
    setSearchParams(filtrosAParams(siguiente))
  }

  function aplicarFiltros(e: FormEvent) {
    e.preventDefault()
    actualizarParams(borrador, true)
  }

  function limpiarFiltros() {
    const limpio: FiltrosFuncionario = { solo_vigentes: true, page: 1, page_size: filtrosAplicados.page_size }
    setBorrador(limpio)
    setSearchParams(filtrosAParams(limpio))
  }

  const hayFiltrosActivos = hayFiltrosDeBusqueda(filtrosAplicados)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-900">Funcionarios</h2>
        {funcionarios.data && funcionarios.data.items.length > 0 && (
          <ExportarFuncionariosButton entidadId={entidadId} />
        )}
      </div>
      {funcionarios.data && funcionarios.data.items.length > 0 && (
        <p className="-mt-3 text-xs text-slate-400">
          La exportación incluye todos los funcionarios vigentes de la entidad (no depende de los
          filtros de esta tabla).
        </p>
      )}

      <form onSubmit={aplicarFiltros} className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            label="Nombres"
            name="nombre"
            placeholder="Contiene…"
            value={borrador.nombre ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, nombre: e.target.value || undefined }))}
          />
          <Input
            label="Apellidos"
            name="apellido"
            placeholder="Contiene…"
            value={borrador.apellido ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, apellido: e.target.value || undefined }))}
          />
          <Input
            label="Cédula (exacta)"
            name="cedula"
            value={borrador.cedula ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, cedula: e.target.value || undefined }))}
          />
          <Input
            label="Cargo"
            name="cargo"
            placeholder="Contiene…"
            value={borrador.cargo ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, cargo: e.target.value || undefined }))}
          />
          <Input
            label="Dependencia"
            name="dependencia"
            placeholder="Contiene…"
            value={borrador.dependencia ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, dependencia: e.target.value || undefined }))}
          />
          <Input
            label="Correo"
            name="correo"
            placeholder="Contiene…"
            value={borrador.correo ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, correo: e.target.value || undefined }))}
          />
          <Input
            label="Teléfono (exacto)"
            name="telefono"
            value={borrador.telefono ?? ''}
            onChange={(e) => setBorrador((f) => ({ ...f, telefono: e.target.value || undefined }))}
          />
          <Select
            label="Área"
            name="area"
            value={borrador.area ?? ''}
            onChange={(e) =>
              setBorrador((f) => ({ ...f, area: (e.target.value || undefined) as AreaFuncionario | undefined }))
            }
          >
            <option value="">Todas las áreas</option>
            <option value="juridica">Jurídica</option>
            <option value="financiera">Financiera</option>
          </Select>
          <Select
            label="Vigencia"
            name="vigencia"
            value={borrador.solo_vigentes === false ? 'todos' : 'vigentes'}
            onChange={(e) => setBorrador((f) => ({ ...f, solo_vigentes: e.target.value !== 'todos' }))}
          >
            <option value="vigentes">Solo vigentes</option>
            <option value="todos">Todos (vigentes y no vigentes)</option>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Button type="submit" size="sm" icon={<Search className="size-4" aria-hidden="true" />}>
            Aplicar filtros
          </Button>
          <Button type="button" variant="ghost" size="sm" icon={<X className="size-4" aria-hidden="true" />} onClick={limpiarFiltros}>
            Limpiar filtros
          </Button>
          {funcionarios.isFetching && !funcionarios.isPending && (
            <span className="inline-flex items-center gap-1 text-xs text-slate-400">
              <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
              Actualizando…
            </span>
          )}
        </div>
      </form>

      {funcionarios.isPending && <Spinner label="Cargando funcionarios…" />}

      {funcionarios.isError && (
        <ErrorState
          error={funcionarios.error}
          title="No se pudieron cargar los funcionarios"
          onRetry={() => void funcionarios.refetch()}
        />
      )}

      {funcionarios.data && funcionarios.data.items.length === 0 && (
        // El botón "Limpiar filtros" ya está siempre visible en el
        // formulario de arriba -- no se repite aquí para evitar dos
        // controles idénticos en pantalla al mismo tiempo.
        <EmptyState
          icon={<Users2 className="size-10" aria-hidden="true" />}
          title={hayFiltrosActivos ? 'Sin resultados' : 'Sin funcionarios registrados'}
          description={
            hayFiltrosActivos
              ? 'No se encontraron funcionarios con estos filtros.'
              : "Esta entidad aún no tiene datos persistidos. Usa 'Consultar' para obtenerlos."
          }
        />
      )}

      {funcionarios.data && funcionarios.data.items.length > 0 && (
        <>
          <div className="hidden overflow-x-auto sm:block">
            <Table>
              <Thead>
                <Tr>
                  <Th>Nombre completo</Th>
                  <Th>Cédula</Th>
                  <Th>Cargo</Th>
                  <Th>Dependencia</Th>
                  <Th>Área</Th>
                  <Th>Correo</Th>
                  <Th>Teléfono</Th>
                  <Th>Estado</Th>
                  <Th>
                    <span className="sr-only">Acciones</span>
                  </Th>
                </Tr>
              </Thead>
              <Tbody>
                {funcionarios.data.items.map((f) => (
                  <Tr key={f.funcionario_id}>
                    <Td>
                      {f.persona_master_id !== null ? (
                        <Link to={`/funcionarios/${f.persona_master_id}`} className="font-medium text-slate-900 hover:underline">
                          {f.nombre_completo}
                        </Link>
                      ) : (
                        f.nombre_completo
                      )}
                    </Td>
                    <Td>
                      <div className="flex items-center gap-1">
                        {f.cedula ?? '—'}
                        <CopyButton value={f.cedula} label="Cédula" />
                      </div>
                    </Td>
                    <Td>{f.cargo}</Td>
                    <Td>{f.dependencia}</Td>
                    <Td className="capitalize">{f.area}</Td>
                    <Td>
                      <div className="flex items-center gap-1">
                        {f.correo ?? '—'}
                        <CopyButton value={f.correo} label="Correo" />
                      </div>
                    </Td>
                    <Td>
                      <div className="flex items-center gap-1">
                        {f.telefono ?? '—'}
                        <CopyButton value={f.telefono} label="Teléfono" />
                      </div>
                    </Td>
                    <Td>
                      <Badge tone={f.vigente ? 'success' : 'neutral'}>{f.vigente ? 'Vigente' : 'No vigente'}</Badge>
                    </Td>
                    <Td>
                      {f.persona_master_id !== null && (
                        <Link to={`/funcionarios/${f.persona_master_id}`} className="text-sm text-slate-500 hover:underline">
                          Ver perfil
                        </Link>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>

          <div className="flex flex-col gap-3 sm:hidden">
            {funcionarios.data.items.map((f) => (
              <Card key={f.funcionario_id}>
                <CardBody className="flex flex-col gap-1.5 text-sm">
                  <div className="flex items-start justify-between gap-2">
                    {f.persona_master_id !== null ? (
                      <Link to={`/funcionarios/${f.persona_master_id}`} className="font-medium text-slate-900 hover:underline">
                        {f.nombre_completo}
                      </Link>
                    ) : (
                      <span className="font-medium text-slate-900">{f.nombre_completo}</span>
                    )}
                    <Badge tone={f.vigente ? 'success' : 'neutral'}>{f.vigente ? 'Vigente' : 'No vigente'}</Badge>
                  </div>
                  <p className="text-slate-500">
                    {f.cargo} · {f.dependencia} · <span className="capitalize">{f.area}</span>
                  </p>
                  <div className="mt-1 flex items-center gap-1">
                    <span className="text-slate-500">Cédula: {f.cedula ?? '—'}</span>
                    <CopyButton value={f.cedula} label="Cédula" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">Correo: {f.correo ?? '—'}</span>
                    <CopyButton value={f.correo} label="Correo" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">Teléfono: {f.telefono ?? '—'}</span>
                    <CopyButton value={f.telefono} label="Teléfono" />
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
            <span>
              Página {funcionarios.data.page} de {funcionarios.data.pages || 1} · {funcionarios.data.total} funcionarios
            </span>
            <div className="flex items-center gap-3">
              <Select
                aria-label="Funcionarios por página"
                value={String(filtrosAplicados.page_size ?? PAGE_SIZE_DEFECTO)}
                onChange={(e) => actualizarParams({ page_size: Number(e.target.value) }, true)}
                className="h-8 w-20 text-sm"
              >
                {TAMANOS_PAGINA.map((tamano) => (
                  <option key={tamano} value={tamano}>
                    {tamano}
                  </option>
                ))}
              </Select>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={funcionarios.data.page <= 1}
                  onClick={() => actualizarParams({ page: funcionarios.data.page - 1 }, false)}
                >
                  Anterior
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={funcionarios.data.page >= funcionarios.data.pages}
                  onClick={() => actualizarParams({ page: funcionarios.data.page + 1 }, false)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
