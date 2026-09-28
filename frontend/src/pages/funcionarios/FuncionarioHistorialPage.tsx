import { useParams } from 'react-router-dom'
import { History } from 'lucide-react'
import { useFuncionarioHistorial } from '../../hooks/useFuncionario'
import {
  PageHeader,
  Spinner,
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'

/** `GET /funcionarios/{id}/historial` -- `VersionHistorialSchema[]` (Módulo 5, `HistorialService`), más antiguo primero, sin paginar. */
export function FuncionarioHistorialPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined

  const historial = useFuncionarioHistorial(id)

  return (
    <>
      <PageHeader title="Historial laboral" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {historial.isPending && <Spinner label="Cargando historial…" />}

      {historial.isError && (
        <ErrorState
          error={historial.error}
          title="No se pudo cargar el historial"
          onRetry={() => void historial.refetch()}
        />
      )}

      {historial.data && historial.data.length === 0 && (
        <EmptyState
          icon={<History className="size-10" aria-hidden="true" />}
          title="Sin historial"
          description="No hay versiones registradas para este funcionario."
        />
      )}

      {historial.data && historial.data.length > 0 && (
        <div className="overflow-x-auto">
          <Table>
            <Thead>
              <Tr>
                <Th>Versión</Th>
                <Th>Entidad</Th>
                <Th>Cargo</Th>
                <Th>Dependencia</Th>
                <Th>Área</Th>
                <Th>Correo</Th>
                <Th>Teléfono</Th>
                <Th>Desde</Th>
                <Th>Hasta</Th>
              </Tr>
            </Thead>
            <Tbody>
              {historial.data.map((v) => (
                <Tr key={`${v.entidad_id}-${v.numero_version}`}>
                  <Td>{v.numero_version}</Td>
                  <Td>{v.entidad_id}</Td>
                  <Td>{v.cargo}</Td>
                  <Td>{v.dependencia}</Td>
                  <Td className="capitalize">{v.area}</Td>
                  <Td>{v.correo ?? '—'}</Td>
                  <Td>{v.telefono ?? '—'}</Td>
                  <Td>{v.fecha_inicio}</Td>
                  <Td>{v.fecha_fin ?? '—'}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </div>
      )}
    </>
  )
}
