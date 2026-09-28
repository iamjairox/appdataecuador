import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'
import { BASE_BOTON, TAMANOS_BOTON, VARIANTES_BOTON, type Tamano, type Variante } from './button-styles'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variante
  size?: Tamano
  loading?: boolean
  icon?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(BASE_BOTON, VARIANTES_BOTON[variant], TAMANOS_BOTON[size], className)}
      {...props}
    >
      {loading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : icon}
      {children}
    </button>
  )
}
