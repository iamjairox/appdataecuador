import { useParams } from 'react-router-dom'
import { useEntidad } from '../../hooks/useEntidades'
import { PageHeader, Spinner } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { EntidadSubnav } from '../../components/EntidadSubnav'
import { ConsultaManualFuncionarios } from './ConsultaManualFuncionarios'

/**
 * Flujo seguro de consulta institucional.
 *
 * Esta pantalla no usa el pipeline heredado que enriquecía a todos los
 * funcionarios automáticamente. Primero persiste el directorio de
 * Transparencia; después el usuario elige qué profesionales consultar de
 * forma individual y secuencial contra fuentes externas.
 */
export function EntidadConsultaPage() {
  const { entidadId } = useParams<{ entidadId: string }>()
  const id = entidadId ? Number(entidadId) : undefined
  const entidad = useEntidad(id)

  return (
    <>
      <PageHeader
        title="Consulta controlada de entidad"
        description={entidad.data?.nombre ?? 'Primero obtiene el listado institucional; las consultas externas son individuales.'}
      />
      {id !== undefined && <EntidadSubnav entidadId={id} />}

      {entidad.isPending && <Spinner label="Cargando entidad…" />}
      {entidad.isError && <ErrorState error={entidad.error} title="No se pudo cargar la entidad" />}
      {id !== undefined && entidad.data && <ConsultaManualFuncionarios entidadId={id} />}
    </>
  )
}
