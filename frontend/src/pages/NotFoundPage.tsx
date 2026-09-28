import { Compass } from 'lucide-react'
import { EmptyState, LinkButton } from '../components/ui'

export function NotFoundPage() {
  return (
    <EmptyState
      icon={<Compass className="size-10" aria-hidden="true" />}
      title="Página no encontrada"
      description="La ruta que buscas no existe en esta aplicación."
      action={
        <LinkButton to="/" variant="secondary">
          Volver al inicio
        </LinkButton>
      }
    />
  )
}
