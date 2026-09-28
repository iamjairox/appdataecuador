import { NavLink } from 'react-router-dom'
import { cn } from '../lib/cn'

interface FuncionarioSubnavProps {
  personaMasterId: number
}

const PESTANAS = [
  { suffix: '', label: 'Perfil' },
  { suffix: '/historial', label: 'Historial' },
  { suffix: '/academico', label: 'Académico' },
  { suffix: '/foro', label: 'Foro de Abogados' },
  { suffix: '/alertas', label: 'Alertas' },
  { suffix: '/timeline', label: 'Línea de tiempo' },
]

/** Subnavegación por pestañas para las 6 vistas de un mismo funcionario (Módulo 10: perfil/historial/academico/foro/alertas/timeline). */
export function FuncionarioSubnav({ personaMasterId }: FuncionarioSubnavProps) {
  const base = `/funcionarios/${personaMasterId}`
  return (
    <nav aria-label="Secciones del funcionario" className="flex flex-wrap gap-1 border-b border-slate-200">
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
