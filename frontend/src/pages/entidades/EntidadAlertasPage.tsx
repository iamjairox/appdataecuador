import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { useAlertasEntidad, useEntidad } from '../../hooks/useEntidades'
import { PageHeader, Spinner, EmptyState, Table, Thead, Tbody, Tr, Th, Td, Badge, Button } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { EntidadSubnav } from '../../components/EntidadSubnav'
import { tonoPorEstadoAlerta, tonoPorPrioridad } from '../../lib/criticidad'

/** `GET /entidades/{id}/alertas` -- `Alerta` (Módulo 5, ya clasificada y persistida), paginada, sin filtros propios. */
export function EntidadAlertasPage() {
  const { entidadId } = useParams<{ entidadId: string }>()
  const id = entidadId ? Number(entidadId) : undefined
  const [page, setPage] = useState(1)

  const entidad = useEntidad(id)
  const alertas = useAlertasEntidad(id, page)

  return (
    <>
      <PageHeader title="Alertas de la entidad" description={entidad.data?.nombre} />
      {id !== undefined && <EntidadSubnav entidadId={id} />}

      {alertas.isFetching && !alertas.isPending && (
        <span className="inline-flex items-center gap-1 text-xs text-slate-400">
          <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
          Actualizando…
        </span>
      )}

      {alertas.isPending && <Spinner label="Cargando alertas…" />}

      {alertas.isError && (
        <ErrorState
          error={alertas.error}
          title="No se pudieron cargar las alertas"
          onRetry={() => void alertas.refetch()}
        />
      )}

      {alertas.data && alertas.data.items.length === 0 && (
        <EmptyState
          icon={<AlertTriangle className="size-10" aria-hidden="true" />}
          title="Sin alertas"
          description="No hay alertas registradas para esta entidad."
        />
      )}

      {alertas.data && alertas.data.items.length > 0 && (
        <>
          <Table>
            <Thead>
              <Tr>
                <Th>Prioridad</Th>
                <Th>Tipo</Th>
                <Th>Descripción</Th>
                <Th>Funcionario</Th>
                <Th>Detectado</Th>
                <Th>Estado</Th>
              </Tr>
            </Thead>
            <Tbody>
              {alertas.data.items.map((a) => (
                <Tr key={a.id}>
                  <Td>
                    <Badge tone={tonoPorPrioridad(a.prioridad)}>{a.prioridad}</Badge>
                  </Td>
                  <Td>{a.tipo}</Td>
                  <Td>{a.descripcion}</Td>
                  <Td>
                    {a.persona_id !== null ? (
                      <span className="text-slate-500">Persona #{a.persona_id}</span>
                    ) : (
                      '—'
                    )}
                  </Td>
                  <Td>{a.detectado_en}</Td>
                  <Td>
                    <Badge tone={tonoPorEstadoAlerta(a.estado)}>{a.estado}</Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              Página {alertas.data.page} de {alertas.data.pages || 1} · {alertas.data.total} alertas
            </span>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm" disabled={alertas.data.page <= 1} onClick={() => setPage((p) => p - 1)}>
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={alertas.data.page >= alertas.data.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}

      <p className="text-xs text-slate-400">
        Esta alerta identifica a la persona por su ID interno -- para ver su ficha completa, ábrela desde{' '}
        <Link to={id !== undefined ? `/entidades/${id}` : '/entidades'} className="underline">
          Funcionarios vigentes
        </Link>{' '}
        (el listado de alertas de la entidad no incluye el enlace directo al perfil).
      </p>
    </>
  )
}
