import { NavLink } from 'react-router-dom'
import { Building2, Home, LogOut, Scale, X } from 'lucide-react'
import { apiClient } from '../api/client'
import { cn } from '../lib/cn'

const ENLACES = [
  { to: '/', label: 'Inicio', icon: Home, end: true },
  { to: '/entidades', label: 'Entidades', icon: Building2 },
  { to: '/abogados-ecuador', label: 'Abogados del Ecuador', icon: Scale },
  { to: '/auditores-ecuador', label: 'Auditores Ecuador', icon: Scale },
  { to: '/companias', label: 'Compañías', icon: Building2 },
]

interface SidebarProps {
  /** Controla el panel deslizable en viewport móvil (`< md`). En `md:` y superiores el sidebar es siempre estático/visible, sin importar este valor. */
  abierto: boolean
  onCerrar: () => void
}

/**
 * FASE 3.6 -- BLOQUE 3: en viewport móvil el sidebar fijo de 224px dejaba
 * solo ~151px de ancho útil para el contenido (bug real confirmado con
 * `getBoundingClientRect` a 375px de ancho). Por debajo de `md` el sidebar
 * pasa a ser un panel deslizable fuera de pantalla (`-translate-x-full`)
 * que se abre con el botón de menú del `Header`, con un fondo semitransparente
 * para cerrarlo; en `md:` y superiores se comporta exactamente igual que antes
 * (estático, siempre visible, sin overlay).
 */
export function Sidebar({ abierto, onCerrar }: SidebarProps) {
  async function cerrarSesion() {
    try {
      await apiClient.post('/api/v1/auth/salir')
    } finally {
      window.dispatchEvent(new Event('dataok:sesion-cerrada'))
      onCerrar()
    }
  }

  return (
    <>
      {abierto && (
        <div className="fixed inset-0 z-30 bg-slate-900/40 md:hidden" onClick={onCerrar} aria-hidden="true" />
      )}
      <nav
        aria-label="Navegación principal"
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform duration-200 md:static md:z-auto md:translate-x-0',
          abierto ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4">
          <span className="text-base font-semibold tracking-tight text-slate-900">DataOK</span>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar menú de navegación"
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 md:hidden"
          >
            <X className="size-5" aria-hidden="true" />
          </button>
        </div>
        <ul className="flex flex-col gap-1 p-3">
          {ENLACES.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                onClick={onCerrar}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                  )
                }
              >
                <Icon className="size-4 shrink-0" aria-hidden="true" />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="mt-auto border-t border-slate-200 p-3">
          <button
            type="button"
            onClick={() => void cerrarSesion()}
            className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut className="size-4 shrink-0" aria-hidden="true" />
            Cerrar sesión
          </button>
        </div>
      </nav>
    </>
  )
}
