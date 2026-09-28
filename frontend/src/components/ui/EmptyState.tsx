import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-300 px-6 py-14 text-center">
      <div className="text-slate-400">{icon ?? <Inbox className="size-10" aria-hidden="true" />}</div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-slate-700">{title}</p>
        {description && <p className="text-sm text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}
