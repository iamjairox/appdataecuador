import { useParams } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { useFuncionarioAlertas } from '../../hooks/useFuncionario'
import { PageHeader, Spinner, EmptyState, Table, Thead, Tbody, Tr, Th, Td, Badge } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'
import { tonoPorEstadoAlerta, tonoPorPrioridad } from '../../lib/criticidad'

/** `GET /funcionarios/{id}/alertas` -- agregado de alertas de Módulos 6/7/8, arreglo directo sin paginar. */
export function FuncionarioAlertasPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined

  const alertas = useFuncionarioAlertas(id)

  return (
    <>
      <PageHeader title="Alertas del funcionario" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {alertas.isPending && <Spinner label="Cargando alertas…" />}
      {alertas.isError && (
        <ErrorState
          error={alertas.error}
          title="No se pudieron cargar las alertas"
          onRetry={() => void alertas.refetch()}
        />
      )}

      {alertas.data && alertas.data.length === 0 && (
        <EmptyState
          icon={<AlertTriangle className="size-10" aria-hidden="true" />}
          title="Sin alertas"
          description="No hay alertas registradas para este funcionario."
        />
      )}

      {alertas.data && alertas.data.length > 0 && (
        <Table>
          <Thead>
            <Tr>
              <Th>Fuente</Th>
              <Th>Tipo</Th>
              <Th>Prioridad</Th>
              <Th>Descripción</Th>
              <Th>Detectado</Th>
              <Th>Estado</Th>
            </Tr>
          </Thead>
          <Tbody>
            {alertas.data.map((a) => (
              <Tr key={a.id}>
                <Td>{a.fuente}</Td>
                <Td>{a.tipo}</Td>
                <Td>
                  <Badge tone={tonoPorPrioridad(a.prioridad)}>{a.prioridad}</Badge>
                </Td>
                <Td>{a.descripcion}</Td>
                <Td>{a.detectado_en}</Td>
                <Td>
                  <Badge tone={tonoPorEstadoAlerta(a.estado)}>{a.estado}</Badge>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </>
  )
}
