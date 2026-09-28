import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Users } from 'lucide-react'
import { PageHeader, Input, Button, EmptyState, Alert } from '../../components/ui'

/**
 * El backend (Módulo 10) no expone un listado global de funcionarios --
 * solo `GET /entidades/{id}/funcionarios` (por entidad) y
 * `GET /funcionarios/{persona_master_id}` (por ID). Esta página no
 * inventa un endpoint que no existe: ofrece ir directo a un perfil por
 * ID y redirige a la búsqueda por entidad como vía real de descubrimiento.
 */
export function FuncionariosIndexPage() {
  const [id, setId] = useState('')
  const navigate = useNavigate()

  function irAPerfil(e: FormEvent) {
    e.preventDefault()
    const idNum = Number(id)
    if (Number.isInteger(idNum) && idNum > 0) {
      void navigate(`/funcionarios/${idNum}`)
    }
  }

  return (
    <>
      <PageHeader title="Funcionarios" description="Consulta el perfil consolidado de un funcionario." />

      <Alert tone="info">
        No existe un listado global de funcionarios en la API. Para descubrir funcionarios, entra primero a
        una entidad en <span className="font-medium">Entidades</span>.
      </Alert>

      <form onSubmit={irAPerfil} className="flex items-end gap-2">
        <Input
          label="ID de persona (persona_master_id)"
          name="persona_master_id"
          inputMode="numeric"
          placeholder="Ej. 123"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
        <Button type="submit" icon={<ArrowRight className="size-4" aria-hidden="true" />}>
          Abrir perfil
        </Button>
      </form>

      <EmptyState
        icon={<Users className="size-10" aria-hidden="true" />}
        title="Busca por entidad"
        description="Cada entidad lista sus funcionarios vigentes y sus IDs de perfil."
      />
    </>
  )
}
