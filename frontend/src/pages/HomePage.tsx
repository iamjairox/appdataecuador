import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Building2, PlayCircle, Scale } from 'lucide-react'
import { useEntidades } from '../hooks/useEntidades'
import { PageHeader, Spinner, StatCard, Badge, LinkButton } from '../components/ui'
import { Card, CardBody } from '../components/ui/Card'
import { ErrorState } from '../components/ErrorState'

const ACCESOS = [
  {
    to: '/entidades',
    icon: Building2,
    titulo: 'Entidades',
    descripcion: 'Buscar una entidad pública y consultar sus funcionarios.',
  },
  {
    to: '/abogados-ecuador',
    icon: Scale,
    titulo: 'Abogados del Ecuador',
    descripcion: 'Buscar abogados, elegir una coincidencia y consultar su ficha individual.',
  },
  {
    to: '/companias',
    icon: Building2,
    titulo: 'Compañías',
    descripcion: 'Consultar empresas, representantes legales y su información persistida.',
  },
]

// Máximo real de `page_size` documentado en `ApiSettings.rate_limit_pagina_maxima`
// (Módulo 10, default 100) -- se pide en un solo request para poder
// mostrar "entidades con actualización más reciente" ordenando del lado
// del cliente, sin inventar un endpoint de estadísticas que no existe.
const TAMANO_MUESTRA = 100

/**
 * Panel operativo -- NO un dashboard decorativo. El backend (Módulo 10)
 * no expone estadísticas globales de funcionarios/alertas/cambios/jobs
 * (solo por entidad o por funcionario), así que esta página muestra
 * ÚNICAMENTE lo que puede obtenerse honestamente: el total real de
 * entidades (de la respuesta paginada) y, con esos mismos datos ya
 * traídos, las entidades cuya `ultima_actualizacion` es más reciente.
 */
export function HomePage() {
  const entidades = useEntidades({ page: 1, page_size: TAMANO_MUESTRA })

  const conActividadReciente = useMemo(() => {
    if (!entidades.data) return []
    return [...entidades.data.items]
      .filter((e) => e.ultima_actualizacion !== null)
      .sort((a, b) => (b.ultima_actualizacion as string).localeCompare(a.ultima_actualizacion as string))
      .slice(0, 6)
  }, [entidades.data])

  return (
    <>
      <PageHeader
        title="DataOK"
        description="Inteligencia y verificación de datos del sector público ecuatoriano."
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Entidades registradas"
          value={entidades.isPending ? <Spinner label="" className="text-slate-300" /> : (entidades.data?.total ?? '—')}
        />
      </div>

      {entidades.isError && <ErrorState error={entidades.error} title="No se pudieron cargar las entidades" />}

      {conActividadReciente.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Entidades con actualización más reciente</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {conActividadReciente.map((e) => (
              <Card key={e.id}>
                <CardBody className="flex flex-col gap-2">
                  <div className="flex items-start justify-between gap-2">
                    <Link to={`/entidades/${e.id}`} className="font-medium text-slate-900 hover:underline">
                      {e.nombre}
                    </Link>
                    <Badge tone={e.estado === 'activa' ? 'success' : 'neutral'}>{e.estado}</Badge>
                  </div>
                  <p className="text-xs text-slate-400">Actualizado: {e.ultima_actualizacion}</p>
                  <LinkButton
                    to={`/entidades/${e.id}/consulta`}
                    variant="secondary"
                    size="sm"
                    icon={<PlayCircle className="size-4" aria-hidden="true" />}
                  >
                    Consultar
                  </LinkButton>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {ACCESOS.map(({ to, icon: Icon, titulo, descripcion }) => (
          <Link key={to} to={to}>
            <Card className="h-full transition-shadow hover:shadow-md">
              <CardBody className="flex items-start gap-3">
                <Icon className="size-5 shrink-0 text-slate-500" aria-hidden="true" />
                <div>
                  <p className="font-medium text-slate-900">{titulo}</p>
                  <p className="mt-1 text-sm text-slate-500">{descripcion}</p>
                </div>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </>
  )
}
