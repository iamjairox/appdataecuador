import type { ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import { cn } from '../../lib/cn'
import { BASE_BOTON, TAMANOS_BOTON, VARIANTES_BOTON, type Tamano, type Variante } from './button-styles'

interface LinkButtonProps extends LinkProps {
  variant?: Variante
  size?: Tamano
  icon?: ReactNode
}

/**
 * Mismo lenguaje visual que `Button` pero renderiza un `<a>` real (react-router
 * `Link`) -- para navegación, nunca para acciones. Evita anidar un `<button>`
 * dentro de un `<a>` (HTML inválido / rompe la accesibilidad de teclado y
 * lectores de pantalla) que ocurría al envolver `<Button>` con `<Link>`.
 */
export function LinkButton({ variant = 'primary', size = 'md', icon, className, children, ...props }: LinkButtonProps) {
  return (
    <Link className={cn(BASE_BOTON, VARIANTES_BOTON[variant], TAMANOS_BOTON[size], className)} {...props}>
      {icon}
      {children}
    </Link>
  )
}
