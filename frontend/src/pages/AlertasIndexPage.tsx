import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { PageHeader, Alert, EmptyState } from '../components/ui'

/**
 * El backend (Módulo 10) no expone un listado global de alertas -- solo
 * `GET /entidades/{id}/alertas` (paginado) y `GET /funcionarios/{id}/alertas`
 * (arreglo directo). No se inventa un endpoint agregado.
 */
export function AlertasIndexPage() {
  return (
    <>
      <PageHeader title="Alertas" description="Alertas detectadas por el sistema." />

      <Alert tone="info">
        No existe un listado global de alertas en la API. Las alertas se consultan por{' '}
        <Link to="/entidades" className="font-medium underline">
          entidad
        </Link>{' '}
        o desde el perfil de un funcionario.
      </Alert>

      <EmptyState
        icon={<AlertTriangle className="size-10" aria-hidden="true" />}
        title="Sin vista agregada"
        description="Abre una entidad o un funcionario para ver sus alertas."
      />
    </>
  )
}
