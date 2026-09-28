import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, id, className, ...props },
  ref,
) {
  const inputId = id ?? props.name
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error && inputId ? `${inputId}-error` : undefined}
        className={cn(
          'h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900 placeholder:text-slate-400',
          'focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500',
          error && 'border-red-400 focus:border-red-500 focus:ring-red-500',
          className,
        )}
        {...props}
      />
      {error && (
        <p id={inputId ? `${inputId}-error` : undefined} className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
})
