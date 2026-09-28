import { Link } from 'react-router-dom'
import { AlertTriangle, ExternalLink, Users2 } from 'lucide-react'
import {
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  Card,
  CardBody,
  StatCard,
} from './ui'
import { CopyButton } from './CopyButton'
import { extraerNumero, extraerTexto } from '../lib/extraer-campo'
import type { ConsultaEntidadResultado } from '../types'

interface ResultadoConsultaEntidadProps {
  resultado: ConsultaEntidadResultado
  /** Título de la entidad, cuando el resultado no lo trae con contexto suficiente (ej. dentro de una lista de resultados masivos). */
  tituloEntidad?: string
}

/**
 * Presenta un `ConsultaEntidadResultado` (Submódulo 9.14/8.11) tal cual lo
 * devuelve el backend -- reutilizado por `GET /entidades/{id}/consulta`,
 * `POST /entidades/{id}/actualizar` (misma forma exacta) y, fila por fila,
 * por los resultados de `POST /entidades/consulta-masiva` y
 * `POST /entidades/actualizar-masivo` (que devuelven un arreglo de esta
 * misma forma, uno por entidad).
 */
export function ResultadoConsultaEntidad({ resultado, tituloEntidad }: ResultadoConsultaEntidadProps) {
  const hayObservaciones = resultado.errores.length > 0
  const jobId = extraerTexto(resultado.job, 'id')

  return (
    <div className="flex flex-col gap-4">
      <Alert
        tone={hayObservaciones ? 'warning' : 'success'}
        title={hayObservaciones ? 'Consulta completada con observaciones' : 'Consulta completada'}
      >
        <p>
          {tituloEntidad && <span className="font-medium">{tituloEntidad} · </span>}
          {resultado.funcionarios.length} funcionario{resultado.funcionarios.length === 1 ? '' : 's'}{' '}
          encontrado{resultado.funcionarios.length === 1 ? '' : 's'} · Duración: {resultado.duracion_total}
        </p>
      </Alert>

      {hayObservaciones && (
        <Card>
          <CardBody>
            <p className="mb-2 text-sm font-medium text-slate-900">Observaciones</p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
              {resultado.errores.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Funcionarios jurídicos" value={extraerNumero(resultado.estadisticas, 'funcionarios_juridicos')} />
        <StatCard label="Consultas SENESCYT" value={extraerNumero(resultado.estadisticas, 'consultas_senescyt')} />
        <StatCard label="Consultas Foro" value={extraerNumero(resultado.estadisticas, 'consultas_foro')} />
        <StatCard label="Cambios detectados" value={extraerNumero(resultado.estadisticas, 'cambios_detectados')} />
        <StatCard label="Errores" value={extraerNumero(resultado.estadisticas, 'errores')} />
        <StatCard label="Duración" value={resultado.duracion_total} />
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Funcionarios jurídicos encontrados</h2>
          {jobId && (
            <Link
              to={`/jobs/${jobId}`}
              className="inline-flex items-center gap-1 text-xs text-slate-500 hover:underline"
            >
              Ver trabajo <ExternalLink className="size-3" aria-hidden="true" />
            </Link>
          )}
        </div>

        {resultado.funcionarios.length === 0 ? (
          <EmptyState
            icon={<Users2 className="size-10" aria-hidden="true" />}
            title="No se encontraron funcionarios jurídicos para esta consulta."
          />
        ) : (
          <>
            {/* Desktop: tabla completa */}
            <div className="hidden overflow-x-auto sm:block">
              <Table>
                <Thead>
                  <Tr>
                    <Th>Nombre completo</Th>
                    <Th>Cédula</Th>
                    <Th>Cargo</Th>
                    <Th>Dependencia</Th>
                    <Th>Correo</Th>
                    <Th>Teléfono</Th>
                    <Th>Celular</Th>
                    <Th>Registro Foro</Th>
                    <Th>Estado Foro</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {resultado.funcionarios.map((f, i) => (
                    <Tr key={i}>
                      <Td>{f.nombre_completo}</Td>
                      <Td>
                        <div className="flex items-center gap-1">
                          {f.cedula ?? '—'}
                          <CopyButton value={f.cedula} label="Cédula" />
                        </div>
                      </Td>
                      <Td>{f.cargo ?? '—'}</Td>
                      <Td>{f.dependencia ?? '—'}</Td>
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
                        <div className="flex items-center gap-1">
                          {f.celular ?? '—'}
                          <CopyButton value={f.celular} label="Celular" />
                        </div>
                      </Td>
                      <Td>{f.registro_foro ?? '—'}</Td>
                      <Td>{f.estado_foro ?? '—'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </div>

            {/* Mobile: tarjeta por funcionario */}
            <div className="flex flex-col gap-3 sm:hidden">
              {resultado.funcionarios.map((f, i) => (
                <Card key={i}>
                  <CardBody className="flex flex-col gap-1.5 text-sm">
                    <p className="font-medium text-slate-900">{f.nombre_completo}</p>
                    <p className="text-slate-500">
                      {f.cargo ?? '—'} · {f.dependencia ?? '—'}
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
                    <div className="flex items-center gap-1">
                      <span className="text-slate-500">Celular: {f.celular ?? '—'}</span>
                      <CopyButton value={f.celular} label="Celular" />
                    </div>
                    <p className="text-slate-500">
                      Foro: {f.registro_foro ?? '—'} ({f.estado_foro ?? '—'})
                    </p>
                  </CardBody>
                </Card>
              ))}
            </div>
            <p className="text-xs text-slate-400">
              Para ver el perfil consolidado completo de un funcionario (incluyendo historial y datos
              académicos), ábrelo desde la lista de «Funcionarios vigentes» en el detalle de la entidad.
            </p>
          </>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Alertas generadas</h2>
        {resultado.alertas.length === 0 ? (
          <EmptyState icon={<AlertTriangle className="size-10" aria-hidden="true" />} title="Sin alertas." />
        ) : (
          <ul className="flex flex-col gap-2">
            {resultado.alertas.map((a, i) => (
              <li key={i} className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                {extraerTexto(a, 'descripcion') ?? JSON.stringify(a)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
