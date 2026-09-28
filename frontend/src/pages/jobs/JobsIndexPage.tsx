import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ListChecks } from 'lucide-react'
import { PageHeader, Input, Button, EmptyState, Alert } from '../../components/ui'

/**
 * El backend (Módulo 10) solo expone `GET /jobs/{job_id}` -- no hay
 * listado de trabajos. El `job_id` real se obtiene del resultado de una
 * consulta de entidad (`ConsultaEntidadResultado.job`).
 */
export function JobsIndexPage() {
  const [id, setId] = useState('')
  const navigate = useNavigate()

  function irAJob(e: FormEvent) {
    e.preventDefault()
    const jobId = id.trim()
    if (jobId) void navigate(`/jobs/${jobId}`)
  }

  return (
    <>
      <PageHeader title="Trabajos" description="Estado de un trabajo de orquestación." />

      <Alert tone="info">
        No existe un listado de trabajos en la API. El ID de un trabajo se obtiene al ejecutar una consulta
        desde una entidad.
      </Alert>

      <form onSubmit={irAJob} className="flex items-end gap-2">
        <Input
          label="ID de trabajo (job_id)"
          name="job_id"
          placeholder="UUID del trabajo"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
        <Button type="submit" icon={<ArrowRight className="size-4" aria-hidden="true" />}>
          Ver trabajo
        </Button>
      </form>

      <EmptyState
        icon={<ListChecks className="size-10" aria-hidden="true" />}
        title="Sin trabajo seleccionado"
        description="Ingresa un ID de trabajo para ver su estado y etapas."
      />
    </>
  )
}
