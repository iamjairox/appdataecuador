import { Card, CardBody, CardHeader } from './ui'
import { BadgeCheck, AlertCircle, AlertTriangle } from 'lucide-react'

interface CampoItemProps {
  label: string
  valor?: string | null
  icon?: React.ReactNode
}

export const CampoItem = ({ label, valor, icon }: CampoItemProps) => {
  if (!valor) return null
  return (
    <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center p-3 bg-slate-50 rounded-lg">
      <dt className="flex items-center gap-2 text-slate-500 font-medium text-sm w-full sm:w-48 shrink-0">
        {icon && <span className="text-slate-400">{icon}</span>}
        {label}
      </dt>
      <dd className="font-medium text-slate-900 text-sm break-all">{valor}</dd>
    </div>
  )
}

interface SeccionItemProps {
  titulo: string
  icon?: React.ReactNode
  children: React.ReactNode
}

export const SeccionItem = ({ titulo, icon, children }: SeccionItemProps) => {
  return (
    <Card className="border border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 pb-2 border-b border-slate-200">
          {icon && <span className="text-slate-500">{icon}</span>}
          {titulo}
        </div>
      </CardHeader>
      <CardBody className="pt-2">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {children}
        </div>
      </CardBody>
    </Card>
  )
}

export const ETIQUETAS_ESTADO: Record<string, { label: string; tone: 'success' | 'warning' | 'danger' | 'neutral' }> = {
  match_exact: { label: 'Coincidencia exacta', tone: 'success' },
  match_high_confidence: { label: 'Coincidencia alta', tone: 'success' },
  ambiguous: { label: 'Resultado ambiguo', tone: 'warning' },
  no_match: { label: 'Sin coincidencia', tone: 'danger' },
  no_cedula_found: { label: 'Sin cédula encontrada', tone: 'danger' },
  source_unavailable: { label: 'Fuente no disponible', tone: 'warning' },
  foro_unavailable: { label: 'Foro no disponible', tone: 'warning' },
}

export const ETIQUETAS_VALIDACION: Record<string, { label: string; icon: React.ReactNode }> = {
  match_exact: { label: 'Identificación confirmada', icon: <BadgeCheck className="size-4" /> },
  match_high_confidence: { label: 'Identificación confirmada (alta confianza)', icon: <BadgeCheck className="size-4" /> },
  ambiguous: { label: 'Resultado ambiguo - Revisar manualmente', icon: <AlertTriangle className="size-4" /> },
  no_match: { label: 'No se encontró coincidencia', icon: <AlertCircle className="size-4" /> },
  no_cedula_found: { label: 'No se encontró cédula', icon: <AlertCircle className="size-4" /> },
  source_unavailable: { label: 'Fuente no disponible', icon: <AlertTriangle className="size-4" /> },
  foro_unavailable: { label: 'Foro de Abogados no disponible', icon: <AlertTriangle className="size-4" /> },
}
