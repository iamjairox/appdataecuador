import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { PlayCircle, RefreshCw, Search } from 'lucide-react'
import { useEntidad, useConsultarEntidadMutation, useActualizarEntidadMutation } from '../../hooks/useEntidades'
import { PageHeader, Spinner, Select, Button, Card, CardBody } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { EntidadSubnav } from '../../components/EntidadSubnav'
import { ResultadoConsultaEntidad } from '../../components/ResultadoConsultaEntidad'
import type { PoliticaConsulta } from '../../types'

const POLITICAS: { value: PoliticaConsulta; label: string }[] = [
  { value: 'consulta_rapida', label: 'Consulta rápida (predeterminada)' },
  { value: 'actualizacion_completa', label: 'Actualización completa' },
  { value: 'solo_cambios', label: 'Solo cambios' },
  { value: 'masiva_nocturna', label: 'Masiva nocturna' },
]

type Accion = 'consultar' | 'actualizar'
type EstadoUI = 'intro' | 'confirmando'

/**
 * Flujo principal de "1-2 clics" (Módulo 9): explicar → confirmar →
 * ejecutar → esperar → resultado. Nunca se simula un stepper de
 * Transparencia/SENESCYT/Foro/Fusión -- el backend no reporta pasos en
 * vivo. Incluye dos operaciones REALES sobre la misma entidad:
 *
 * - "Consultar" -- `GET /entidades/{id}/consulta` (admite `politica`).
 * - "Actualizar" -- `POST /entidades/{id}/actualizar` (Submódulo 10.28:
 *   SIN body, fuerza `actualizacion_completa` internamente -- por eso NO
 *   se ofrece un selector de política para esta acción).
 *
 * Ambas devuelven exactamente `ConsultaEntidadResponseSchema`, por eso
 * comparten el mismo componente de resultado.
 */
export function EntidadConsultaPage() {
  const { entidadId } = useParams<{ entidadId: string }>()
  const id = entidadId ? Number(entidadId) : undefined

  const entidad = useEntidad(id)
  const [estadoUI, setEstadoUI] = useState<EstadoUI>('intro')
  const [accion, setAccion] = useState<Accion>('consultar')
  const [politica, setPolitica] = useState<PoliticaConsulta | ''>('')
  const mutacionConsultar = useConsultarEntidadMutation()
  const mutacionActualizar = useActualizarEntidadMutation()
  const mutacion = accion === 'actualizar' ? mutacionActualizar : mutacionConsultar

  function iniciar(accionElegida: Accion) {
    setAccion(accionElegida)
    setEstadoUI('confirmando')
  }

  function confirmar() {
    if (id === undefined || mutacion.isPending) return
    if (accion === 'actualizar') {
      mutacionActualizar.mutate(id)
    } else {
      mutacionConsultar.mutate({ entidadId: id, politica: politica || undefined })
    }
  }

  function reintentar() {
    mutacionConsultar.reset()
    mutacionActualizar.reset()
    setEstadoUI('intro')
  }

  return (
    <>
      <PageHeader title="Consultar entidad" description={entidad.data ? entidad.data.nombre : undefined} />

      {id !== undefined && <EntidadSubnav entidadId={id} />}

      {entidad.isPending && <Spinner label="Cargando entidad…" />}
      {entidad.isError && <ErrorState error={entidad.error} title="No se pudo cargar la entidad" />}

      {/* -- Resultado ya disponible (tiene prioridad sobre cualquier otro estado) -- */}
      {mutacion.isSuccess && (
        <>
          <ResultadoConsultaEntidad resultado={mutacion.data} />
          <div>
            <Button variant="secondary" onClick={reintentar} icon={<Search className="size-4" aria-hidden="true" />}>
              Nueva operación
            </Button>
          </div>
        </>
      )}

      {/* -- Procesando: SIN progreso falso, solo estado indeterminado -- */}
      {!mutacion.isSuccess && mutacion.isPending && (
        <Card>
          <CardBody className="flex flex-col items-center gap-3 py-10 text-center">
            <Spinner label={accion === 'actualizar' ? 'Procesando actualización…' : 'Procesando consulta…'} />
            <p className="max-w-md text-sm text-slate-500">
              GovData está recopilando y consolidando la información. Estamos consultando y
              consolidando información de las fuentes disponibles. Esto puede tardar unos momentos.
            </p>
          </CardBody>
        </Card>
      )}

      {/* -- La operación (petición) falló: error real del backend o de red -- */}
      {!mutacion.isSuccess && !mutacion.isPending && mutacion.isError && (
        <ErrorState
          error={mutacion.error}
          title={accion === 'actualizar' ? 'La actualización no se pudo completar' : 'La consulta no se pudo completar'}
          onRetry={reintentar}
        />
      )}

      {/* -- Aún no se ha ejecutado nada -- */}
      {!mutacionConsultar.isSuccess &&
        !mutacionActualizar.isSuccess &&
        !mutacion.isPending &&
        !mutacion.isError &&
        entidad.data && (
          <Card>
            <CardBody className="flex flex-col gap-4">
              {estadoUI === 'intro' && (
                <>
                  <p className="text-sm text-slate-600">
                    GovData consultará las fuentes disponibles para identificar y enriquecer los
                    funcionarios del área jurídica de esta entidad.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => iniciar('consultar')} icon={<PlayCircle className="size-4" aria-hidden="true" />}>
                      Ejecutar consulta
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => iniciar('actualizar')}
                      icon={<RefreshCw className="size-4" aria-hidden="true" />}
                    >
                      Actualizar (forzar)
                    </Button>
                  </div>
                  <details className="text-sm text-slate-500">
                    <summary className="cursor-pointer select-none">Opciones avanzadas</summary>
                    <div className="mt-3 max-w-xs">
                      <Select
                        label="Política de consulta"
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
                      <p className="mt-1 text-xs text-slate-400">
                        Solo aplica a "Ejecutar consulta". "Actualizar" fuerza siempre actualización
                        completa y no admite política personalizada.
                      </p>
                    </div>
                  </details>
                </>
              )}

              {estadoUI === 'confirmando' && accion === 'consultar' && (
                <>
                  <p className="font-medium text-slate-900">¿Consultar esta entidad?</p>
                  <p className="text-sm text-slate-600">
                    El proceso puede tardar unos momentos porque consulta y consolida información de
                    múltiples fuentes.
                  </p>
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => setEstadoUI('intro')}>
                      Cancelar
                    </Button>
                    <Button onClick={confirmar} icon={<PlayCircle className="size-4" aria-hidden="true" />}>
                      Consultar
                    </Button>
                  </div>
                </>
              )}

              {estadoUI === 'confirmando' && accion === 'actualizar' && (
                <>
                  <p className="font-medium text-slate-900">¿Forzar actualización completa de esta entidad?</p>
                  <p className="text-sm text-slate-600">
                    Esto ignora la caché vigente y vuelve a consultar Transparencia, SENESCYT y Foro
                    para esta entidad. Puede tardar más que una consulta normal.
                  </p>
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => setEstadoUI('intro')}>
                      Cancelar
                    </Button>
                    <Button onClick={confirmar} icon={<RefreshCw className="size-4" aria-hidden="true" />}>
                      Actualizar
                    </Button>
                  </div>
                </>
              )}
            </CardBody>
          </Card>
        )}
    </>
  )
}
