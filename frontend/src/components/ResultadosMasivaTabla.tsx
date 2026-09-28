import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { EmptyState, Table, Thead, Tbody, Tr, Th, Td, Badge } from './ui'
import { extraerNumero, extraerTexto } from '../lib/extraer-campo'
import type { ConsultaEntidadResultado } from '../types'

interface ResultadosMasivaTablaProps {
  resultados: ConsultaEntidadResultado[]
}

/**
 * Resume el arreglo `ConsultaEntidadResultado[]` que devuelven
 * `POST /entidades/consulta-masiva` y `POST /entidades/actualizar-masivo`
 * -- una fila por entidad, con los datos REALES de cada resultado
 * (`entidad`/`estadisticas`/`errores`/`job` son objetos libres, se leen
 * con los extractores seguros existentes, nunca se asume una forma fija).
 */
export function ResultadosMasivaTabla({ resultados }: ResultadosMasivaTablaProps) {
  if (resultados.length === 0) {
    return <EmptyState title="El backend no devolvió resultados para ninguna entidad." />
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <Thead>
          <Tr>
            <Th>Entidad</Th>
            <Th>Funcionarios jurídicos</Th>
            <Th>Cambios detectados</Th>
            <Th>Errores</Th>
            <Th>Duración</Th>
            <Th>Job</Th>
          </Tr>
        </Thead>
        <Tbody>
          {resultados.map((r, i) => {
            const nombreEntidad = extraerTexto(r.entidad, 'nombre')
            const idEntidad = extraerNumero(r.entidad, 'id')
            const jobId = extraerTexto(r.job, 'id')
            const funcionariosJuridicos = extraerNumero(r.estadisticas, 'funcionarios_juridicos')
            const cambiosDetectados = extraerNumero(r.estadisticas, 'cambios_detectados')
            return (
              <Tr key={i}>
                <Td>
                  {idEntidad !== null ? (
                    <Link to={`/entidades/${idEntidad}`} className="font-medium text-slate-900 hover:underline">
                      {nombreEntidad ?? `Entidad #${idEntidad}`}
                    </Link>
                  ) : (
                    (nombreEntidad ?? '—')
                  )}
                </Td>
                <Td>{funcionariosJuridicos ?? '—'}</Td>
                <Td>{cambiosDetectados ?? '—'}</Td>
                <Td>
                  {r.errores.length > 0 ? (
                    <Badge tone="warning">{r.errores.length}</Badge>
                  ) : (
                    <Badge tone="success">0</Badge>
                  )}
                </Td>
                <Td>{r.duracion_total}</Td>
                <Td>
                  {jobId ? (
                    <Link to={`/jobs/${jobId}`} className="inline-flex items-center gap-1 text-xs hover:underline">
                      Ver <ExternalLink className="size-3" aria-hidden="true" />
                    </Link>
                  ) : (
                    '—'
                  )}
                </Td>
              </Tr>
            )
          })}
        </Tbody>
      </Table>
    </div>
  )
}
