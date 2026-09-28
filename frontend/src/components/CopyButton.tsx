import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { cn } from '../lib/cn'

interface CopyButtonProps {
  value: string | null | undefined
  label: string
  className?: string
}

/**
 * Botón discreto para copiar un dato operativo (cédula, correo,
 * teléfono, celular -- Sección 22 de FASE 2). No hace nada más que
 * copiar el valor real ya mostrado en pantalla; si no hay valor, no se
 * renderiza (nunca copia un "—" inventado).
 */
export function CopyButton({ value, label, className }: CopyButtonProps) {
  const [copiado, setCopiado] = useState(false)

  if (!value) return null

  async function copiar() {
    try {
      await navigator.clipboard.writeText(value as string)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 1500)
    } catch {
      // Sin permisos de portapapeles u otro entorno restringido: no hay
      // nada útil que mostrar al usuario más allá de no dar feedback falso.
    }
  }

  return (
    <button
      type="button"
      onClick={() => void copiar()}
      aria-label={copiado ? `${label} copiado` : `Copiar ${label.toLowerCase()}`}
      className={cn(
        'inline-flex items-center gap-1 rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-slate-400',
        className,
      )}
    >
      {copiado ? (
        <Check className="size-3.5 text-emerald-600" aria-hidden="true" />
      ) : (
        <Copy className="size-3.5" aria-hidden="true" />
      )}
      <span className="text-xs">{copiado ? 'Copiado' : ''}</span>
    </button>
  )
}
