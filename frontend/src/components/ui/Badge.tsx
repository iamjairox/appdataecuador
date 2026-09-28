import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

export type Tono = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tono
}

const tonos: Record<Tono, string> = {
  neutral: 'bg-slate-100 text-slate-700',
  success: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  danger: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
}

export function Badge({ tone = 'neutral', className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        tonos[tone],
        className,
      )}
      {...props}
    />
  )
}
