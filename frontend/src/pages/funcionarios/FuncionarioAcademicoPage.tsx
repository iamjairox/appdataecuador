import { useParams } from 'react-router-dom'
import { GraduationCap } from 'lucide-react'
import { useFuncionarioAcademico } from '../../hooks/useFuncionario'
import { PageHeader, Spinner, EmptyState, Card, CardHeader, CardBody, Badge } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { RecordPreview } from '../../components/RecordPreview'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'
import { extraerTexto } from '../../lib/extraer-campo'

/**
 * `GET /funcionarios/{id}/academico` -- `PerfilAcademicoResponseSchema`
 * (Módulo 7, SENESCYT). `titulos[]` es un `dict[str, Any]` libre, pero
 * verificado contra `TituloAcademicoDTO`: se destacan `titulo`/
 * `institucion`/`nivel`/`estado`/`fecha_registro` (los campos que el
 * backend REALMENTE produce) y el resto se muestra sin aplanar.
 */
export function FuncionarioAcademicoPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined

  const academico = useFuncionarioAcademico(id)

  return (
    <>
      <PageHeader title="Perfil académico" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {academico.isPending && <Spinner label="Cargando perfil académico…" />}

      {academico.isError && (
        <ErrorState
          error={academico.error}
          title="No se pudo cargar el perfil académico"
          onRetry={() => void academico.refetch()}
        />
      )}

      {academico.data && (
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold text-slate-900">Identidad</h2>
            </CardHeader>
            <CardBody>
              <RecordPreview data={academico.data.identidad} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold text-slate-900">
                Títulos ({academico.data.titulos.length})
              </h2>
            </CardHeader>
            <CardBody className="flex flex-col gap-4">
              {academico.data.titulos.length === 0 ? (
                <EmptyState
                  icon={<GraduationCap className="size-10" aria-hidden="true" />}
                  title="Sin títulos registrados"
                  description="SENESCYT no tiene títulos vigentes para este funcionario."
                />
              ) : (
                academico.data.titulos.map((titulo, i) => {
                  const nombreTitulo = extraerTexto(titulo, 'titulo')
                  const institucion = extraerTexto(titulo, 'institucion')
                  const nivel = extraerTexto(titulo, 'nivel')
                  const estado = extraerTexto(titulo, 'estado')
                  const fechaRegistro = extraerTexto(titulo, 'fecha_registro')
                  return (
                    <div key={i} className="border-b border-slate-100 pb-4 last:border-0 last:pb-0">
                      {(nombreTitulo ?? institucion ?? nivel ?? estado) && (
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <p className="font-medium text-slate-900">{nombreTitulo ?? 'Título sin nombre registrado'}</p>
                          {nivel && <Badge tone="info">{nivel}</Badge>}
                          {estado && <Badge tone="neutral">{estado}</Badge>}
                        </div>
                      )}
                      {(institucion ?? fechaRegistro) && (
                        <p className="mb-2 text-sm text-slate-500">
                          {institucion ?? '—'}
                          {fechaRegistro ? ` · Registrado: ${fechaRegistro}` : ''}
                        </p>
                      )}
                      <RecordPreview data={titulo} />
                    </div>
                  )
                })
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold text-slate-900">Estadísticas</h2>
            </CardHeader>
            <CardBody>
              <RecordPreview data={academico.data.estadisticas} />
            </CardBody>
          </Card>

          <p className="text-xs text-slate-400">Generado: {academico.data.generado_en}</p>
        </div>
      )}
    </>
  )
}
