import { useParams } from 'react-router-dom'
import { Route } from 'lucide-react'
import { useFuncionarioTimeline } from '../../hooks/useFuncionario'
import { PageHeader, Spinner, EmptyState, Badge } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'

/**
 * `GET /funcionarios/{id}/timeline` -- forma real de `TimelinePersonaDTO`
 * (Submódulo 6.5): cada punto trae `origen` como ÚNICA clasificación que
 * el backend realmente entrega -- se usa tal cual (badge), nunca se
 * inventa un tipo de evento adicional.
 */
export function FuncionarioTimelinePage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined

  const timeline = useFuncionarioTimeline(id)

  return (
    <>
      <PageHeader title="Línea de tiempo" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {timeline.isPending && <Spinner label="Cargando línea de tiempo…" />}

      {timeline.isError && (
        <ErrorState
          error={timeline.error}
          title="No se pudo cargar la línea de tiempo"
          onRetry={() => void timeline.refetch()}
        />
      )}

      {timeline.data && timeline.data.puntos.length === 0 && (
        <EmptyState
          icon={<Route className="size-10" aria-hidden="true" />}
          title="Sin eventos"
          description="No hay puntos registrados en la línea de tiempo."
        />
      )}

      {timeline.data && timeline.data.puntos.length > 0 && (
        <ol className="flex flex-col gap-4 border-l-2 border-slate-200 pl-4">
          {timeline.data.puntos.map((p, i) => (
            <li key={i} className="relative">
              <span className="absolute -left-[21px] top-1 size-2.5 rounded-full bg-slate-400" />
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="neutral">{p.origen}</Badge>
                <p className="text-sm font-medium text-slate-900">{p.descripcion}</p>
              </div>
              <p className="mt-0.5 text-xs text-slate-500">
                {p.fecha_inicio ?? '—'}
                {p.fecha_fin ? ` – ${p.fecha_fin}` : ''}
              </p>
            </li>
          ))}
        </ol>
      )}
    </>
  )
}
