import { useParams } from 'react-router-dom'
import { PlayCircle } from 'lucide-react'
import { useEntidad } from '../../hooks/useEntidades'
import { PageHeader, Spinner, Badge, LinkButton } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { EntidadSubnav } from '../../components/EntidadSubnav'
import { FuncionariosDeEntidadSection } from './FuncionariosDeEntidadSection'

export function EntidadDetallePage() {
  const { entidadId } = useParams<{ entidadId: string }>()
  const id = entidadId ? Number(entidadId) : undefined

  const entidad = useEntidad(id)

  if (entidad.isPending) return <Spinner label="Cargando entidad…" />
  if (entidad.isError) return <ErrorState error={entidad.error} title="No se pudo cargar la entidad" />

  const e = entidad.data

  return (
    <>
      <PageHeader
        title={e.nombre}
        description="Detalle de la entidad y sus funcionarios vigentes."
        actions={
          <LinkButton to={`/entidades/${id}/consulta`} icon={<PlayCircle className="size-4" aria-hidden="true" />}>
            Consultar entidad
          </LinkButton>
        }
      />

      {id !== undefined && <EntidadSubnav entidadId={id} />}

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Tipo</dt>
          <dd className="mt-1 text-sm text-slate-800">{e.tipo ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Estado</dt>
          <dd className="mt-1">
            <Badge tone={e.estado === 'activa' ? 'success' : 'neutral'}>{e.estado}</Badge>
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Portal de origen</dt>
          <dd className="mt-1 text-sm text-slate-800">{e.portal_origen}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Provincia</dt>
          <dd className="mt-1 text-sm text-slate-800">{e.provincia ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Ciudad</dt>
          <dd className="mt-1 text-sm text-slate-800">{e.ciudad ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Última publicación
          </dt>
          <dd className="mt-1 text-sm text-slate-800">{e.ultima_publicacion ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Última actualización
          </dt>
          <dd className="mt-1 text-sm text-slate-800">{e.ultima_actualizacion ?? '—'}</dd>
        </div>
      </dl>

      {id !== undefined && <FuncionariosDeEntidadSection entidadId={id} />}
    </>
  )
}
