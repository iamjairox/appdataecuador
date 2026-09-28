/** Estilos compartidos por `Button` (real `<button>`) y `LinkButton` (real `<a>` vía react-router `Link`) -- nunca se anida un `<button>` dentro de un `<a>` (HTML inválido / accesibilidad rota). */
export type Variante = 'primary' | 'secondary' | 'ghost' | 'danger'
export type Tamano = 'sm' | 'md'

export const BASE_BOTON =
  'inline-flex items-center justify-center rounded-md font-medium transition-colors ' +
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ' +
  'disabled:cursor-not-allowed disabled:opacity-50'

export const VARIANTES_BOTON: Record<Variante, string> = {
  primary: 'bg-slate-900 text-white hover:bg-slate-800 focus-visible:outline-slate-900',
  secondary:
    'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus-visible:outline-slate-400',
  ghost: 'text-slate-600 hover:bg-slate-100 focus-visible:outline-slate-400',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600',
}

export const TAMANOS_BOTON: Record<Tamano, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
}
