import { Circle, Menu } from 'lucide-react'
import { useApiHealth } from '../hooks/useApiHealth'
import { cn } from '../lib/cn'

interface HeaderProps {
  onAbrirMenu: () => void
}

export function Header({ onAbrirMenu }: HeaderProps) {
  const { data, isPending, isError } = useApiHealth()

  const estado = isPending ? 'verificando' : isError ? 'sin_conexion' : 'ok'
  const etiqueta =
    estado === 'ok' ? 'API conectada' : estado === 'sin_conexion' ? 'API sin conexión' : 'Verificando API…'
  const color =
    estado === 'ok' ? 'text-emerald-500' : estado === 'sin_conexion' ? 'text-red-500' : 'text-slate-400'

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:justify-end md:px-6">
      <button
        type="button"
        onClick={onAbrirMenu}
        aria-label="Abrir menú de navegación"
        className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 md:hidden"
      >
        <Menu className="size-5" aria-hidden="true" />
      </button>
      <div
        className="flex items-center gap-2 text-sm text-slate-500"
        title={data ? `${data.service} v${data.version}` : undefined}
      >
        <Circle className={cn('size-2.5 fill-current', color)} aria-hidden="true" />
        <span>{etiqueta}</span>
      </div>
    </header>
  )
}
