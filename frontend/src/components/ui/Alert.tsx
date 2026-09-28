import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import { cn } from '../../lib/cn'

type Tono = 'info' | 'success' | 'warning' | 'danger'

interface AlertProps {
  tone?: Tono
  title?: string
  children: ReactNode
  className?: string
}

const estilos: Record<Tono, { wrapper: string; icon: ReactNode }> = {
  info: {
    wrapper: 'bg-blue-50 text-blue-800 border-blue-200',
    icon: <Info className="size-5 text-blue-500" aria-hidden="true" />,
  },
  success: {
    wrapper: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    icon: <CheckCircle2 className="size-5 text-emerald-500" aria-hidden="true" />,
  },
  warning: {
    wrapper: 'bg-amber-50 text-amber-800 border-amber-200',
    icon: <AlertTriangle className="size-5 text-amber-500" aria-hidden="true" />,
  },
  danger: {
    wrapper: 'bg-red-50 text-red-800 border-red-200',
    icon: <XCircle className="size-5 text-red-500" aria-hidden="true" />,
  },
}

export function Alert({ tone = 'info', title, children, className }: AlertProps) {
  const estilo = estilos[tone]
  return (
    <div
      role={tone === 'danger' ? 'alert' : 'status'}
      className={cn('flex gap-3 rounded-md border p-4 text-sm', estilo.wrapper, className)}
    >
      {estilo.icon}
      <div className="flex flex-col gap-0.5">
        {title && <p className="font-medium">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  )
}
