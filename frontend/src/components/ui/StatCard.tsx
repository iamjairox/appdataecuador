import type { ReactNode } from 'react'
import { Card, CardBody } from './Card'
import { cn } from '../../lib/cn'

interface StatCardProps {
  label: string
  value: ReactNode
  icon?: ReactNode
  className?: string
}

/** Tarjeta de estadística genérica -- reutilizada por el resultado de consulta y por el panel principal. Nunca calcula el valor; solo lo presenta. */
export function StatCard({ label, value, icon, className }: StatCardProps) {
  return (
    <Card className={cn(className)}>
      <CardBody className="flex flex-col gap-1">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
          {icon}
          {label}
        </span>
        <span className="text-2xl font-semibold text-slate-900">{value ?? '—'}</span>
      </CardBody>
    </Card>
  )
}
