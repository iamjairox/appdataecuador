/**
 * Renderiza un `Record<string, unknown>` genérico como pares clave/valor.
 *
 * Varios contratos reales del backend (Módulo 10) son objetos libres
 * (`dict[str, Any]`): `persona`/`transparencia`/`senescyt`/`foro` del
 * perfil consolidado, `job`/`entidad`/`estadisticas` de una consulta,
 * etc. Este componente NO asume ninguna forma fija -- solo itera lo que
 * el backend realmente envió, para no inventar campos que no existen.
 */
export function RecordPreview({ data }: { data: Record<string, unknown> }) {
  const entradas = Object.entries(data)

  if (entradas.length === 0) {
    return <p className="text-sm text-slate-400">Sin datos.</p>
  }

  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
      {entradas.map(([clave, valor]) => (
        <div key={clave} className="flex flex-col gap-0.5">
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">{clave}</dt>
          <dd className="text-sm text-slate-800 break-words">{formatearValor(valor)}</dd>
        </div>
      ))}
    </dl>
  )
}

function formatearValor(valor: unknown): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  if (typeof valor === 'string' || typeof valor === 'number' || typeof valor === 'boolean') {
    return String(valor)
  }
  return JSON.stringify(valor)
}
