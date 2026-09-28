import { useState } from 'react'
import { CheckCircle2, Download } from 'lucide-react'
import { useExportarFuncionariosMutation } from '../hooks/useEntidades'
import { Button, Select } from './ui'
import { ApiError } from '../types/error'
import { mensajeAmigable } from '../lib/error-messages'
import type { FormatoExportacion } from '../types'

interface ExportarFuncionariosButtonProps {
  entidadId: number
}

const FORMATOS: { value: FormatoExportacion; label: string }[] = [
  { value: 'csv', label: 'CSV' },
  { value: 'json', label: 'JSON' },
]

/**
 * `GET /entidades/{id}/funcionarios/exportar` -- exporta SIEMPRE todos
 * los funcionarios vigentes de la entidad (el backend ignora cualquier
 * filtro de la tabla, ver Submódulo 10.34). Estados reales: preparando/
 * descargando (una sola petición, sin progreso intermedio real),
 * completado, error -- nunca un porcentaje inventado.
 */
export function ExportarFuncionariosButton({ entidadId }: ExportarFuncionariosButtonProps) {
  const [formato, setFormato] = useState<FormatoExportacion>('csv')
  const mutacion = useExportarFuncionariosMutation()

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Select
        aria-label="Formato de exportación"
        value={formato}
        onChange={(e) => setFormato(e.target.value as FormatoExportacion)}
        disabled={mutacion.isPending}
        className="h-9 w-24"
      >
        {FORMATOS.map((f) => (
          <option key={f.value} value={f.value}>
            {f.label}
          </option>
        ))}
      </Select>
      <Button
        variant="secondary"
        size="sm"
        loading={mutacion.isPending}
        disabled={mutacion.isPending}
        icon={<Download className="size-4" aria-hidden="true" />}
        onClick={() => mutacion.mutate({ entidadId, formato })}
      >
        {mutacion.isPending ? 'Descargando…' : 'Exportar'}
      </Button>

      {!mutacion.isPending && mutacion.isSuccess && (
        <span className="inline-flex items-center gap-1 text-sm text-emerald-700">
          <CheckCircle2 className="size-4" aria-hidden="true" />
          Descarga completada
        </span>
      )}

      {!mutacion.isPending && mutacion.isError && (
        <span role="alert" className="text-sm text-red-700">
          {mutacion.error instanceof ApiError
            ? mensajeAmigable(mutacion.error)
            : 'No se pudo generar la exportación.'}
        </span>
      )}
    </div>
  )
}
