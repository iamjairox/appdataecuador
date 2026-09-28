import { useMemo, useState } from 'react'
import { PlayCircle, RefreshCw, Search } from 'lucide-react'
import { useEntidades, useConsultarMasivoMutation, useActualizarMasivoMutation } from '../../hooks/useEntidades'
import { PageHeader, Alert, Spinner, StatCard, Select, Button, Card, CardHeader, CardBody } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { ResultadosMasivaTabla } from '../../components/ResultadosMasivaTabla'
import type { PoliticaConsulta } from '../../types'

const POLITICAS: { value: PoliticaConsulta; label: string }[] = [
  { value: 'consulta_rapida', label: 'Consulta rápida (predeterminada)' },
  { value: 'actualizacion_completa', label: 'Actualización completa' },
  { value: 'solo_cambios', label: 'Solo cambios' },
  { value: 'masiva_nocturna', label: 'Masiva nocturna' },
]

// `GET /entidades` con el `page_size` máximo real (100, ver
// `ApiSettings.rate_limit_pagina_maxima`) -- solo para poder mostrar
// honestamente cuántas entidades activas hay, no para "seleccionarlas"
// (el backend no lo permite, ver aviso en pantalla).
const TAMANO_MUESTRA = 100

type EstadoUI = 'intro' | 'confirmando'

/**
 * `/operaciones` -- "Operaciones masivas".
 *
 * HALLAZGO CLAVE de la auditoría de FASE 3.5 (leído directamente de
 * `routes/entidades.py` y `GovDataPipelineOrchestrator.consultar_masivo`/
 * `actualizar_masivo`): NINGUNO de los dos endpoints masivos acepta una
 * lista de `entidad_id` -- ambos operan SIEMPRE sobre
 * `EntidadRepositoryPort.listar_activas()` completo. Por eso esta
 * pantalla NO tiene checkboxes de selección de entidades: construir esa
 * UI sería simular una capacidad que el backend no tiene (Regla de No
 * Invención). En su lugar, se informa con cuántas entidades activas
 * reales se ejecutará la operación (mismo dato que ya usa el dashboard).
 */
export function OperacionesMasivasPage() {
  const entidades = useEntidades({ page: 1, page_size: TAMANO_MUESTRA })
  const cantidadActivas = useMemo(
    () => entidades.data?.items.filter((e) => e.estado === 'activa').length ?? null,
    [entidades.data],
  )
  // El backend pagina, así que si `total` supera lo que trajo esta
  // muestra, el conteo de activas visible podría ser parcial -- se avisa
  // en vez de mostrar un número que podría no ser el real.
  const muestraIncompleta = entidades.data ? entidades.data.total > entidades.data.items.length : false

  return (
    <>
      <PageHeader
        title="Operaciones masivas"
        description="Ejecuta consulta o actualización sobre todas las entidades activas registradas en GovData."
      />

      <Alert tone="info">
        El backend no permite seleccionar un subconjunto de entidades para estas operaciones: tanto{' '}
        <strong>consulta masiva</strong> como <strong>actualización masiva</strong> se ejecutan siempre sobre{' '}
        <strong>todas las entidades activas</strong>.
      </Alert>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Entidades activas"
          value={entidades.isPending ? <Spinner label="" className="text-slate-300" /> : (cantidadActivas ?? '—')}
        />
      </div>
      {muestraIncompleta && (
        <p className="text-xs text-slate-400">
          Mostrando el conteo sobre las primeras {entidades.data?.items.length} entidades de{' '}
          {entidades.data?.total} registradas.
        </p>
      )}
      {entidades.isError && <ErrorState error={entidades.error} title="No se pudo cargar el número de entidades" onRetry={() => void entidades.refetch()} />}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ConsultaMasivaCard cantidadActivas={cantidadActivas} />
        <ActualizacionMasivaCard cantidadActivas={cantidadActivas} />
      </div>
    </>
  )
}

interface OperacionCardProps {
  cantidadActivas: number | null
}

function ConsultaMasivaCard({ cantidadActivas }: OperacionCardProps) {
  const [estadoUI, setEstadoUI] = useState<EstadoUI>('intro')
  const [politica, setPolitica] = useState<PoliticaConsulta | ''>('')
  const mutacion = useConsultarMasivoMutation()

  function ejecutar() {
    if (mutacion.isPending) return
    mutacion.mutate(politica || undefined)
  }

  function reiniciar() {
    mutacion.reset()
    setEstadoUI('intro')
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold text-slate-900">Consulta masiva</h2>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        {!mutacion.isSuccess && !mutacion.isPending && !mutacion.isError && (
          <>
            <p className="text-sm text-slate-600">
              Ejecuta el pipeline de consulta (Transparencia → SENESCYT → Foro) sobre todas las entidades
              activas{cantidadActivas !== null ? ` (${cantidadActivas})` : ''}.
            </p>
            {estadoUI === 'intro' && (
              <>
                <Select
                  label="Política"
                  name="politica"
                  value={politica}
                  onChange={(e) => setPolitica(e.target.value as PoliticaConsulta | '')}
                >
                  <option value="">Predeterminada del backend (consulta_rapida)</option>
                  {POLITICAS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </Select>
                <div>
                  <Button onClick={() => setEstadoUI('confirmando')} icon={<PlayCircle className="size-4" aria-hidden="true" />}>
                    Ejecutar consulta masiva
                  </Button>
                </div>
              </>
            )}
            {estadoUI === 'confirmando' && (
              <>
                <p className="font-medium text-slate-900">
                  ¿Deseas ejecutar consulta masiva sobre{' '}
                  {cantidadActivas !== null ? `las ${cantidadActivas} entidades activas` : 'todas las entidades activas'}?
                </p>
                <p className="text-sm text-slate-600">
                  Puede tardar varios minutos: el backend consulta cada entidad de forma síncrona, una por una.
                </p>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setEstadoUI('intro')}>
                    Cancelar
                  </Button>
                  <Button onClick={ejecutar} icon={<PlayCircle className="size-4" aria-hidden="true" />}>
                    Confirmar
                  </Button>
                </div>
              </>
            )}
          </>
        )}

        {mutacion.isPending && (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <Spinner label="Ejecutando consulta masiva…" />
            <p className="max-w-sm text-sm text-slate-500">
              GovData está consultando y consolidando información de todas las entidades activas. Esto puede
              tardar varios minutos.
            </p>
          </div>
        )}

        {mutacion.isError && (
          <ErrorState error={mutacion.error} title="La consulta masiva no se pudo completar" onRetry={reiniciar} />
        )}

        {mutacion.isSuccess && (
          <>
            <p className="text-sm text-slate-600">
              {mutacion.data.length} entidad{mutacion.data.length === 1 ? '' : 'es'} procesada
              {mutacion.data.length === 1 ? '' : 's'}.
            </p>
            <ResultadosMasivaTabla resultados={mutacion.data} />
            <div>
              <Button variant="secondary" size="sm" onClick={reiniciar} icon={<Search className="size-4" aria-hidden="true" />}>
                Nueva consulta masiva
              </Button>
            </div>
          </>
        )}
      </CardBody>
    </Card>
  )
}

function ActualizacionMasivaCard({ cantidadActivas }: OperacionCardProps) {
  const [estadoUI, setEstadoUI] = useState<EstadoUI>('intro')
  const mutacion = useActualizarMasivoMutation()

  function ejecutar() {
    if (mutacion.isPending) return
    mutacion.mutate()
  }

  function reiniciar() {
    mutacion.reset()
    setEstadoUI('intro')
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold text-slate-900">Actualización masiva</h2>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        {!mutacion.isSuccess && !mutacion.isPending && !mutacion.isError && (
          <>
            <p className="text-sm text-slate-600">
              Fuerza la política "masiva nocturna" (ignora la caché) sobre todas las entidades activas
              {cantidadActivas !== null ? ` (${cantidadActivas})` : ''}. No admite elegir política -- el
              backend siempre fuerza `masiva_nocturna`.
            </p>
            {estadoUI === 'intro' && (
              <div>
                <Button
                  variant="secondary"
                  onClick={() => setEstadoUI('confirmando')}
                  icon={<RefreshCw className="size-4" aria-hidden="true" />}
                >
                  Ejecutar actualización masiva
                </Button>
              </div>
            )}
            {estadoUI === 'confirmando' && (
              <>
                <p className="font-medium text-slate-900">
                  ¿Deseas forzar la actualización de{' '}
                  {cantidadActivas !== null ? `las ${cantidadActivas} entidades activas` : 'todas las entidades activas'}?
                </p>
                <p className="text-sm text-slate-600">
                  Ignora la caché vigente de cada entidad -- puede tardar significativamente más que una
                  consulta masiva normal.
                </p>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setEstadoUI('intro')}>
                    Cancelar
                  </Button>
                  <Button onClick={ejecutar} icon={<RefreshCw className="size-4" aria-hidden="true" />}>
                    Confirmar
                  </Button>
                </div>
              </>
            )}
          </>
        )}

        {mutacion.isPending && (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <Spinner label="Ejecutando actualización masiva…" />
            <p className="max-w-sm text-sm text-slate-500">
              GovData está actualizando todas las entidades activas ignorando la caché. Esto puede tardar
              varios minutos.
            </p>
          </div>
        )}

        {mutacion.isError && (
          <ErrorState error={mutacion.error} title="La actualización masiva no se pudo completar" onRetry={reiniciar} />
        )}

        {mutacion.isSuccess && (
          <>
            <p className="text-sm text-slate-600">
              {mutacion.data.length} entidad{mutacion.data.length === 1 ? '' : 'es'} procesada
              {mutacion.data.length === 1 ? '' : 's'}.
            </p>
            <ResultadosMasivaTabla resultados={mutacion.data} />
            <div>
              <Button variant="secondary" size="sm" onClick={reiniciar} icon={<Search className="size-4" aria-hidden="true" />}>
                Nueva actualización masiva
              </Button>
            </div>
          </>
        )}
      </CardBody>
    </Card>
  )
}
