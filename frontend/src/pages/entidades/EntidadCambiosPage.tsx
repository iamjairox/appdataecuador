import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { History, Loader2 } from 'lucide-react'
import { useCambiosEntidad, useEntidad } from '../../hooks/useEntidades'
import { PageHeader, Spinner, EmptyState, Table, Thead, Tbody, Tr, Th, Td, Button, Input } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { EntidadSubnav } from '../../components/EntidadSubnav'
import type { FiltrosCambio } from '../../types'

/**
 * `GET /entidades/{id}/cambios` -- historial de versiones de cargo
 * (`VersionFuncionario`, Módulo 5). `tipo_cambio`/`criticidad` casi
 * siempre llegan `null` porque esa clasificación no se persiste junto a
 * la versión (confirmado en el propio backend) -- se muestran tal cual,
 * nunca se inventa un valor cuando faltan.
 */
export function EntidadCambiosPage() {
  const { entidadId } = useParams<{ entidadId: string }>()
  const id = entidadId ? Number(entidadId) : undefined

  const entidad = useEntidad(id)
  const [filtros, setFiltros] = useState<FiltrosCambio>({ page: 1, page_size: 20 })
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const cambios = useCambiosEntidad(id, filtros)

  function aplicarFiltros(e: FormEvent) {
    e.preventDefault()
    setFiltros({ page: 1, page_size: 20, desde: desde || undefined, hasta: hasta || undefined })
  }

  function limpiarFiltros() {
    setDesde('')
    setHasta('')
    setFiltros({ page: 1, page_size: 20 })
  }

  return (
    <>
      <PageHeader title="Cambios detectados" description={entidad.data?.nombre} />
      {id !== undefined && <EntidadSubnav entidadId={id} />}

      <form onSubmit={aplicarFiltros} className="flex flex-wrap items-end gap-3">
        <Input
          label="Desde"
          type="date"
          name="desde"
          value={desde}
          onChange={(e) => setDesde(e.target.value)}
        />
        <Input label="Hasta" type="date" name="hasta" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        <Button type="submit" size="sm">
          Aplicar
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={limpiarFiltros}>
          Limpiar
        </Button>
        {cambios.isFetching && !cambios.isPending && (
          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
            Actualizando…
          </span>
        )}
      </form>

      {cambios.isPending && <Spinner label="Cargando cambios…" />}

      {cambios.isError && (
        <ErrorState
          error={cambios.error}
          title="No se pudieron cargar los cambios"
          onRetry={() => void cambios.refetch()}
        />
      )}

      {cambios.data && cambios.data.items.length === 0 && (
        <EmptyState
          icon={<History className="size-10" aria-hidden="true" />}
          title="Sin cambios"
          description="No hay cambios registrados en el rango seleccionado."
        />
      )}

      {cambios.data && cambios.data.items.length > 0 && (
        <>
          <Table>
            <Thead>
              <Tr>
                <Th>Persona</Th>
                <Th>Versión</Th>
                <Th>Cargo</Th>
                <Th>Dependencia</Th>
                <Th>Desde</Th>
                <Th>Hasta</Th>
                <Th>Tipo de cambio</Th>
                <Th>Criticidad</Th>
              </Tr>
            </Thead>
            <Tbody>
              {cambios.data.items.map((c) => (
                <Tr key={`${c.persona_id}-${c.numero_version}`}>
                  <Td>Persona #{c.persona_id}</Td>
                  <Td>{c.numero_version}</Td>
                  <Td>{c.cargo}</Td>
                  <Td>{c.dependencia}</Td>
                  <Td>{c.fecha_inicio}</Td>
                  <Td>{c.fecha_fin ?? '—'}</Td>
                  <Td>{c.tipo_cambio ?? '—'}</Td>
                  <Td>{c.criticidad ?? '—'}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              Página {cambios.data.page} de {cambios.data.pages || 1} · {cambios.data.total} cambios
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={cambios.data.page <= 1}
                onClick={() => setFiltros((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={cambios.data.page >= cambios.data.pages}
                onClick={() => setFiltros((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </>
  )
}
