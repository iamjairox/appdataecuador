import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Building2, Loader2, PlayCircle, Search } from 'lucide-react'
import { useEntidades } from '../../hooks/useEntidades'
import {
  PageHeader,
  Input,
  Button,
  LinkButton,
  Spinner,
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
} from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import type { FiltrosEntidad } from '../../types'

/**
 * Filtros REALES de `GET /api/v1/entidades` (Módulo 10,
 * `routes/entidades.py::listar_entidades`): `nombre`, `tipo_institucion`,
 * `portal_origen`. `provincia`/`ciudad` se aceptan en el backend pero HOY
 * no filtran nada (Transparencia no captura esa información -- ver
 * `ListarEntidadesApiUseCase._coincide`), así que deliberadamente no se
 * exponen aquí para no simular un filtrado que no ocurre.
 */
const FILTROS_INICIALES: FiltrosEntidad = { page: 1, page_size: 20 }

export function EntidadesListPage() {
  const [nombre, setNombre] = useState('')
  const [tipoInstitucion, setTipoInstitucion] = useState('')
  const [portalOrigen, setPortalOrigen] = useState('')
  const [filtros, setFiltros] = useState<FiltrosEntidad>(FILTROS_INICIALES)
  const { data, isPending, isFetching, isError, error } = useEntidades(filtros)

  function buscar(e: FormEvent) {
    e.preventDefault()
    setFiltros({
      page: 1,
      page_size: 20,
      nombre: nombre.trim() || undefined,
      tipo_institucion: tipoInstitucion.trim() || undefined,
      portal_origen: portalOrigen.trim() || undefined,
    })
  }

  return (
    <>
      <PageHeader
        title="Entidades"
        description="Consulta y monitorea información de funcionarios de entidades públicas."
      />

      <form onSubmit={buscar} className="flex flex-wrap items-end gap-3">
        <Input
          label="Buscar entidad..."
          name="nombre"
          placeholder="Ej. Ministerio de..."
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className="min-w-56"
        />
        <Input
          label="Tipo de institución"
          name="tipo_institucion"
          placeholder="Ej. Ministerio"
          value={tipoInstitucion}
          onChange={(e) => setTipoInstitucion(e.target.value)}
        />
        <Input
          label="Portal de origen"
          name="portal_origen"
          placeholder="Ej. DPE"
          value={portalOrigen}
          onChange={(e) => setPortalOrigen(e.target.value)}
        />
        <Button type="submit" icon={<Search className="size-4" aria-hidden="true" />}>
          Buscar
        </Button>
        {isFetching && !isPending && (
          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
            Actualizando…
          </span>
        )}
      </form>

      {isPending && <Spinner label="Cargando entidades…" />}
      {isError && <ErrorState error={error} title="No se pudieron cargar las entidades" />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<Building2 className="size-10" aria-hidden="true" />}
          title="Sin resultados"
          description="No se encontraron entidades con ese criterio."
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <Table>
            <Thead>
              <Tr>
                <Th>Entidad</Th>
                <Th>Tipo</Th>
                <Th>Estado</Th>
                <Th>Última publicación</Th>
                <Th>Última actualización</Th>
                <Th>
                  <span className="sr-only">Acciones</span>
                </Th>
              </Tr>
            </Thead>
            <Tbody>
              {data.items.map((entidad) => (
                <Tr key={entidad.id}>
                  <Td>
                    <Link
                      to={`/entidades/${entidad.id}`}
                      className="font-medium text-slate-900 hover:underline"
                    >
                      {entidad.nombre}
                    </Link>
                  </Td>
                  <Td>{entidad.tipo ?? '—'}</Td>
                  <Td>
                    <Badge tone={entidad.estado === 'activa' ? 'success' : 'neutral'}>{entidad.estado}</Badge>
                  </Td>
                  <Td>{entidad.ultima_publicacion ?? '—'}</Td>
                  <Td>{entidad.ultima_actualizacion ?? '—'}</Td>
                  <Td>
                    <div className="flex items-center justify-end gap-1">
                      <LinkButton to={`/entidades/${entidad.id}`} variant="ghost" size="sm">
                        Ver detalle
                      </LinkButton>
                      <LinkButton
                        to={`/entidades/${entidad.id}/consulta`}
                        size="sm"
                        icon={<PlayCircle className="size-4" aria-hidden="true" />}
                      >
                        Consultar
                      </LinkButton>
                    </div>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              Página {data.page} de {data.pages} · {data.total} entidades
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page <= 1}
                onClick={() => setFiltros((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page >= data.pages}
                onClick={() => setFiltros((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </>
  )
}
