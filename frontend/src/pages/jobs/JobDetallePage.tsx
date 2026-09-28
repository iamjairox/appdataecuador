import { Link, useParams } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { useJob } from '../../hooks/useJob'
import { PageHeader, Spinner, EmptyState, Table, Thead, Tbody, Tr, Th, Td, Card, CardHeader, CardBody } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { JobStatusBadge } from '../../components/JobStatusBadge'
import { RecordPreview } from '../../components/RecordPreview'
import { CopyButton } from '../../components/CopyButton'
import type { EstadoJob } from '../../types'

/** Estados en los que el Planificador (Módulo 9) todavía puede seguir agregando etapas -- no son "en vivo", solo distinguen el mensaje del EmptyState de etapas. */
const ESTADOS_NO_TERMINALES: EstadoJob[] = ['pendiente', 'en_cola', 'ejecutando', 'pausado', 'reintentando']

/**
 * `GET /jobs/{job_id}` -- estado real de `TrabajoOrquestador` + etapas de
 * `AuditoriaEtapa` (Módulo 9). Las etapas son HISTÓRICAS/auditadas, nunca
 * un indicador de progreso en vivo -- no se rellenan artificialmente.
 */
export function JobDetallePage() {
  const { jobId } = useParams<{ jobId: string }>()
  const job = useJob(jobId)

  if (job.isPending) return <Spinner label="Cargando trabajo…" />
  if (job.isError) {
    return (
      <ErrorState error={job.error} title="No se pudo cargar el trabajo" onRetry={() => void job.refetch()} />
    )
  }

  const j = job.data

  return (
    <>
      <PageHeader
        title="Trabajo"
        description={
          <span className="inline-flex items-center gap-1 font-mono text-xs">
            {j.id}
            <CopyButton value={j.id} label="ID de trabajo" />
          </span>
        }
        actions={<JobStatusBadge estado={j.estado} />}
      />

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Tipo</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.tipo}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Entidad</dt>
          <dd className="mt-1 text-sm text-slate-800">
            {j.entidad_id !== null ? (
              <Link to={`/entidades/${j.entidad_id}`} className="inline-flex items-center gap-1 text-slate-900 hover:underline">
                #{j.entidad_id} <ExternalLink className="size-3.5" aria-hidden="true" />
              </Link>
            ) : (
              '—'
            )}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Prioridad</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.prioridad}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Política</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.politica}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Intentos</dt>
          <dd className="mt-1 text-sm text-slate-800">
            {j.intentos} / {j.max_intentos}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Creado</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.creado_en ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Iniciado</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.iniciado_en ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Finalizado</dt>
          <dd className="mt-1 text-sm text-slate-800">{j.finalizado_en ?? '—'}</dd>
        </div>
      </dl>

      {j.ultimo_error && (
        <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {j.ultimo_error}
        </p>
      )}

      {Object.keys(j.parametros).length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-slate-900">Parámetros</h2>
          </CardHeader>
          <CardBody>
            <RecordPreview data={j.parametros} />
          </CardBody>
        </Card>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Etapas</h2>
        {j.etapas.length === 0 ? (
          <EmptyState
            title={
              ESTADOS_NO_TERMINALES.includes(j.estado)
                ? 'El backend aún no ha registrado etapas finalizadas.'
                : 'Sin etapas registradas'
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <Thead>
                <Tr>
                  <Th>Paso</Th>
                  <Th>Estado</Th>
                  <Th>Iniciado</Th>
                  <Th>Finalizado</Th>
                  <Th>Duración (s)</Th>
                  <Th>Registros</Th>
                  <Th>Omisión / Error</Th>
                </Tr>
              </Thead>
              <Tbody>
                {j.etapas.map((etapa, i) => (
                  <Tr key={i}>
                    <Td>{etapa.tipo_paso}</Td>
                    <Td>{etapa.estado_paso}</Td>
                    <Td>{etapa.iniciado_en}</Td>
                    <Td>{etapa.finalizado_en ?? '—'}</Td>
                    <Td>{etapa.duracion_segundos ?? '—'}</Td>
                    <Td>{etapa.cantidad_registros}</Td>
                    <Td className={etapa.error ? 'text-red-700' : undefined}>
                      {etapa.error ?? etapa.razon_omision ?? '—'}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>
        )}
      </div>
    </>
  )
}
