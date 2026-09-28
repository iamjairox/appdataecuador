import { forwardRef, type SelectHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, id, className, children, ...props },
  ref,
) {
  const selectId = id ?? props.name
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={selectId} className="text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <select
        ref={ref}
        id={selectId}
        className={cn(
          'h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900',
          'focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500',
          className,
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  )
})
