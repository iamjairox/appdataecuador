import { NavLink } from 'react-router-dom'
import { cn } from '../lib/cn'

interface EntidadSubnavProps {
  entidadId: number
}

const PESTANAS = [
  { suffix: '', label: 'Detalle' },
  { suffix: '/alertas', label: 'Alertas' },
  { suffix: '/cambios', label: 'Cambios' },
  { suffix: '/consulta', label: 'Consultar' },
]

/** Subnavegación por pestañas para las vistas de una misma entidad (Módulo 10: detalle/alertas/cambios/consulta). */
export function EntidadSubnav({ entidadId }: EntidadSubnavProps) {
  const base = `/entidades/${entidadId}`
  return (
    <nav aria-label="Secciones de la entidad" className="flex flex-wrap gap-1 border-b border-slate-200">
      {PESTANAS.map(({ suffix, label }) => (
        <NavLink
          key={suffix}
          to={`${base}${suffix}`}
          end={suffix === ''}
          className={({ isActive }) =>
            cn(
              '-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700',
            )
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
