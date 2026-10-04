import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, ClipboardCopy, Database, FileSpreadsheet, FileText, PlayCircle, Users } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, CardBody, CardHeader, EmptyState, Input, Spinner, Table, Tbody, Td, Th, Thead, Tr } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { entidadesKeys, useActualizarListadoInstitucionalMutation, useEstadoListadoInstitucional, useFuncionariosConsultados, useFuncionariosDeEntidad } from '../../hooks/useEntidades'
import { useValidarAbogado } from '../../hooks/useFuncionario'
import { comprobarPublicacionDpe, marcarFuncionarioComoProfesional, marcarFuncionariosComoProfesionales, obtenerEstadosConsultaExterna, obtenerProgresoListadoInstitucional, prepararFuncionarioParaConsulta, type ComprobacionPublicacionDpe, type ProgresoListadoInstitucional } from '../../api/entidades.api'
import type { FuncionarioConsultado } from '../../types'

interface Props {
  entidadId: number
}

/**
 * Separa explícitamente el directorio institucional (lectura local) de las
 * consultas externas: el usuario marca cada funcionario jurídico que quiere
 * enriquecer y las peticiones se ejecutan de una en una.
 */
export function ConsultaManualFuncionarios({ entidadId }: Props) {
  // El directorio ya extraído es local y debe volver a mostrarse al regresar
  // a la entidad; no hace falta lanzar otra descarga para verlo.
  const [vista, setVista] = useState<'listado' | 'juridicos' | 'consultados'>('listado')
  const [profesionalesGenerados, setProfesionalesGenerados] = useState(false)
  const [seleccionados, setSeleccionados] = useState<Set<number>>(new Set())
  const [procesando, setProcesando] = useState(false)
  const [errores, setErrores] = useState<string[]>([])
  const [preparandoFuncionarioId, setPreparandoFuncionarioId] = useState<number | null>(null)
  const [marcandoProfesionales, setMarcandoProfesionales] = useState(false)
  const [mensajeMarcado, setMensajeMarcado] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const validacion = useValidarAbogado()
  const actualizarListado = useActualizarListadoInstitucionalMutation()
  const estadoListado = useEstadoListadoInstitucional(entidadId)
  const [progresoListado, setProgresoListado] = useState<ProgresoListadoInstitucional | null>(null)
  const [comprobacionDpe, setComprobacionDpe] = useState<ComprobacionPublicacionDpe | null>(null)
  const [comprobandoDpe, setComprobandoDpe] = useState(false)

  useEffect(() => {
    if (!actualizarListado.isPending) return
    let activo = true
    const actualizar = () => void obtenerProgresoListadoInstitucional(entidadId)
      .then((progreso) => { if (activo) setProgresoListado(progreso) })
      .catch(() => undefined)
    actualizar()
    const intervalo = window.setInterval(actualizar, 1000)
    return () => { activo = false; window.clearInterval(intervalo) }
  }, [actualizarListado.isPending, entidadId])

  const hayListadoGuardado = (estadoListado.data?.funcionarios_persistidos ?? 0) > 0
  const abrirListado = () => {
    setVista('listado')
    if (!hayListadoGuardado && !estadoListado.isPending && !actualizarListado.isPending) {
      actualizarListado.mutate(entidadId)
    }
  }
  const actualizarListadoDesdeTransparencia = () => {
    if (!actualizarListado.isPending) actualizarListado.mutate(entidadId, { onSuccess: () => setVista('listado') })
  }
  const comprobarDpe = async () => {
    if (comprobandoDpe) return
    setComprobandoDpe(true)
    try { setComprobacionDpe(await comprobarPublicacionDpe(entidadId)) }
    catch { setComprobacionDpe({ estado: 'no_se_pudo_comprobar', periodo_local: null, periodo_dpe: null, mensaje: 'No fue posible comprobar la última publicación en DPE.' }) }
    finally { setComprobandoDpe(false) }
  }
  const marcarProfesionales = async (funcionarioIds: number[]) => {
    if (funcionarioIds.length === 0 || marcandoProfesionales) return
    setMarcandoProfesionales(true)
    setMensajeMarcado(null)
    try {
      if (funcionarioIds.length === 1) await marcarFuncionarioComoProfesional(entidadId, funcionarioIds[0]!)
      else await marcarFuncionariosComoProfesionales(entidadId, funcionarioIds)
      setProfesionalesGenerados(false)
      setMensajeMarcado(`${funcionarioIds.length} funcionario${funcionarioIds.length === 1 ? '' : 's'} agregado${funcionarioIds.length === 1 ? '' : 's'} a profesionales jurídicos y afines.`)
      await queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
    } catch {
      setMensajeMarcado('No se pudo agregar el funcionario seleccionado. Inténtalo nuevamente.')
    } finally {
      setMarcandoProfesionales(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold text-slate-900">Consulta controlada por funcionario</h2>
          <p className="mt-1 text-sm text-slate-500">Elige una opción. Las fuentes externas solo se consultan para los funcionarios que selecciones.</p>
        </CardHeader>
        <CardBody className="flex flex-wrap gap-2">
          <div className="flex flex-col gap-1">
            <Button variant={vista === 'listado' ? 'primary' : 'secondary'} loading={actualizarListado.isPending} disabled={estadoListado.isPending} onClick={abrirListado} icon={<Users className="size-4" />}>
              1. Abrir listado guardado
            </Button>
            {actualizarListado.isPending && <p className="max-w-md text-xs text-amber-700">{progresoListado?.estado === 'extrayendo' && progresoListado.total_filas !== null ? `En proceso: ${progresoListado.filas_procesadas.toLocaleString()} de ${progresoListado.total_filas.toLocaleString()} filas procesadas · ${progresoListado.funcionarios_extraidos.toLocaleString()} funcionarios extraídos.` : 'Solicitud recibida. El directorio está en proceso; no presiones el botón nuevamente.'}</p>}
          </div>
          <Button variant={vista === 'juridicos' ? 'primary' : 'secondary'} onClick={() => { setVista('juridicos'); setProfesionalesGenerados(false) }} icon={<PlayCircle className="size-4" />}>
            2. Ver profesionales jurídicos y afines
          </Button>
          <Button variant={vista === 'consultados' ? 'primary' : 'secondary'} onClick={() => setVista('consultados')} icon={<Database className="size-4" />}>
            3. Datos ya consultados
          </Button>
          {hayListadoGuardado && <Button size="sm" variant="secondary" loading={actualizarListado.isPending} onClick={actualizarListadoDesdeTransparencia}>
            Descargar y actualizar desde DPE
          </Button>}
          <Button size="sm" variant="secondary" loading={comprobandoDpe} onClick={() => void comprobarDpe()}>
            Comprobar última publicación en DPE
          </Button>
        </CardBody>
        <CardBody className="border-t border-slate-100 pt-3">
          {estadoListado.isPending && <p className="text-sm text-slate-500">Comprobando el listado institucional guardado…</p>}
          {estadoListado.data && <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-slate-600">
            <span><strong className="text-slate-800">{estadoListado.data.funcionarios_persistidos.toLocaleString()}</strong> funcionarios guardados</span>
            <span><strong className="text-slate-800">{estadoListado.data.profesionales_juridicos.toLocaleString()}</strong> profesionales jurídicos y afines</span>
            <span><strong className="text-slate-800">{estadoListado.data.funcionarios_consultados.toLocaleString()}</strong> con intentos de consulta registrados</span>
            <span>Período: <strong className="text-slate-800">{formatearPeriodo(estadoListado.data.periodo_publicacion)}</strong></span>
            <span>Última extracción: <strong className="text-slate-800">{formatearFecha(estadoListado.data.fecha_extraccion)}</strong></span>
            <span>Última verificación DPE: <strong className="text-slate-800">{formatearFecha(estadoListado.data.ultima_verificacion_dpe)}</strong></span>
            <span className={estadoListado.data.requiere_actualizacion ? 'text-amber-700' : 'text-emerald-700'}>{estadoListado.data.mensaje}</span>
          </div>}
          {comprobacionDpe && <p className={comprobacionDpe.estado === 'vigente' ? 'mt-2 text-sm text-emerald-700' : comprobacionDpe.estado === 'hay_publicacion_mas_reciente' ? 'mt-2 text-sm text-amber-700' : 'mt-2 text-sm text-red-700'}>{comprobacionDpe.mensaje}</p>}
        </CardBody>
      </Card>

      {mensajeMarcado && <p className={mensajeMarcado.startsWith('No se pudo') ? 'text-sm text-red-700' : 'text-sm text-emerald-700'}>{mensajeMarcado}</p>}
      {vista === 'listado' && <ListadoInstitucional entidadId={entidadId} marcando={marcandoProfesionales} onMarcar={marcarProfesionales} />}
      {vista === 'juridicos' && !profesionalesGenerados && <Card>
        <CardHeader>
          <h2 className="text-base font-semibold text-slate-900">2. Profesionales jurídicos, legales y afines</h2>
          <p className="mt-1 text-sm text-slate-500">Genera una clasificación local a partir del listado institucional guardado. No se consultará ninguna fuente externa.</p>
        </CardHeader>
        <CardBody className="flex flex-wrap items-center gap-3">
          <Button disabled={!hayListadoGuardado || estadoListado.isPending} onClick={() => setProfesionalesGenerados(true)} icon={<PlayCircle className="size-4" />}>
            Generar listado de profesionales jurídicos y afines
          </Button>
          {!estadoListado.isPending && !hayListadoGuardado && <p className="text-sm text-amber-700">Primero verifica y abre el listado institucional de funcionarios.</p>}
        </CardBody>
      </Card>}
      {vista === 'juridicos' && profesionalesGenerados && (
        <PanelSeleccion entidadId={entidadId} seleccionados={seleccionados} setSeleccionados={setSeleccionados}
          procesando={procesando} preparandoFuncionarioId={preparandoFuncionarioId} errores={errores}
          onPreparar={async (funcionarioId) => {
            setPreparandoFuncionarioId(funcionarioId)
            try {
              const preparado = await prepararFuncionarioParaConsulta(entidadId, funcionarioId)
              setSeleccionados(new Set(seleccionados).add(preparado.persona_master_id))
              await queryClient.invalidateQueries({ queryKey: entidadesKeys.funcionarios(entidadId, { page: 1, page_size: 100, solo_vigentes: true, area: 'juridica' }) })
            } catch {
              setErrores((actual) => [...actual, 'No se pudo preparar la identidad del funcionario seleccionado.'])
            } finally {
              setPreparandoFuncionarioId(null)
            }
          }}
          onConsultar={async () => {
            if (seleccionados.size === 0 || procesando) return
            setProcesando(true)
            setErrores([])
            const fallos: string[] = []
            for (const personaMasterId of seleccionados) {
              try {
                const resultado = await validacion.mutateAsync(personaMasterId)
                if (resultado.estado_consulta_externa === 'error') fallos.push(`La consulta del funcionario #${personaMasterId} no pudo completarse. Puedes reintentar.`)
              } catch {
                fallos.push(`No se pudo completar la consulta del funcionario #${personaMasterId}.`)
              }
            }
            setErrores(fallos)
            setProcesando(false)
            setSeleccionados(new Set())
            await queryClient.invalidateQueries({ queryKey: entidadesKeys.consultados(entidadId) })
            await queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
            setVista('consultados')
          }} />
      )}

      {vista === 'consultados' && <FuncionariosConsultados entidadId={entidadId} />}
    </div>
  )
}

function ListadoInstitucional({ entidadId, marcando, onMarcar }: Props & { marcando: boolean; onMarcar: (funcionarioIds: number[]) => Promise<void> }) {
  const [pagina, setPagina] = useState(1)
  const [seleccionados, setSeleccionados] = useState<Set<number>>(new Set())
  const [nombre, setNombre] = useState('')
  const [cargo, setCargo] = useState('')
  const [dependencia, setDependencia] = useState('')
  const [filtros, setFiltros] = useState({ nombre: '', cargo: '', dependencia: '' })
  const funcionarios = useFuncionariosDeEntidad(entidadId, { page: pagina, page_size: 100, solo_vigentes: true, nombre: filtros.nombre || undefined, cargo: filtros.cargo || undefined, dependencia: filtros.dependencia || undefined })
  const items = funcionarios.data?.items ?? []
  const alternar = (funcionarioId: number) => setSeleccionados((actuales) => {
    const siguientes = new Set(actuales)
    if (siguientes.has(funcionarioId)) siguientes.delete(funcionarioId)
    else siguientes.add(funcionarioId)
    return siguientes
  })
  return <Card>
    <CardHeader>
      <h2 className="text-base font-semibold text-slate-900">1. Listado institucional completo</h2>
      <p className="mt-1 text-sm text-slate-500">Todos los funcionarios vigentes disponibles desde Transparencia, sin filtrar por área y sin consultar fuentes externas.</p>
      <div className="mt-3"><Button size="sm" disabled={seleccionados.size === 0 || marcando} loading={marcando} onClick={() => void onMarcar([...seleccionados])} icon={<PlayCircle className="size-4" />}>Agregar seleccionados a profesionales jurídicos y afines ({seleccionados.size})</Button></div>
    </CardHeader>
    <CardBody>
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4"><Input label="Nombre" name="nombre_funcionario" value={nombre} onChange={(e) => setNombre(e.target.value)} /><Input label="Cargo" name="cargo_funcionario" value={cargo} onChange={(e) => setCargo(e.target.value)} /><Input label="Dependencia" name="dependencia_funcionario" value={dependencia} onChange={(e) => setDependencia(e.target.value)} /><div className="flex items-end"><Button className="w-full justify-center" size="sm" onClick={() => { setPagina(1); setFiltros({ nombre, cargo, dependencia }) }} icon={<PlayCircle className="size-4" />}>Buscar funcionarios</Button></div></div>
      {funcionarios.isPending && <Spinner label="Cargando listado institucional…" />}
      {funcionarios.isError && <ErrorState error={funcionarios.error} title="No se pudo cargar el listado" onRetry={() => void funcionarios.refetch()} />}
      {funcionarios.data?.items.length === 0 && <EmptyState icon={<Users className="size-9" />} title="Sin funcionarios registrados" description="La entidad todavía no tiene un directorio institucional persistido." />}
      {funcionarios.data && funcionarios.data.items.length > 0 && <Table>
        <Thead><Tr><Th>Seleccionar</Th><Th>Funcionario</Th><Th>Acción</Th><Th>Cédula</Th><Th>Cargo</Th><Th>Dependencia</Th><Th>Área</Th><Th>Correo institucional</Th><Th>Teléfono</Th><Th>Extensión</Th></Tr></Thead>
        <Tbody>{items.map((f) => <Tr key={f.funcionario_id}>
          <Td><input aria-label={`Seleccionar ${f.nombre_completo} para profesionales jurídicos`} type="checkbox" disabled={marcando} checked={seleccionados.has(f.funcionario_id)} onChange={() => alternar(f.funcionario_id)} /></Td>
          <Td>{f.nombre_completo}</Td><Td><Button size="sm" variant="secondary" disabled={marcando || f.area === 'juridica'} onClick={() => void onMarcar([f.funcionario_id])}>{f.area === 'juridica' ? 'Ya incluido' : 'Enviar a profesionales jurídicos'}</Button></Td><Td>{f.cedula ?? '—'}</Td><Td>{f.cargo}</Td><Td>{f.dependencia}</Td><Td>{f.area}</Td>
          <Td>{f.correo ?? '—'}</Td><Td>{f.telefono ?? '—'}</Td><Td>{f.extension_telefonica ?? '—'}</Td>
        </Tr>)}</Tbody>
      </Table>}
      {funcionarios.data && funcionarios.data.pages > 1 && <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-sm text-slate-500">Mostrando página {funcionarios.data.page} de {funcionarios.data.pages} · {funcionarios.data.total} funcionarios</span>
        <div className="flex gap-2">
          <Button variant="secondary" disabled={pagina <= 1} onClick={() => setPagina((actual) => actual - 1)}>Anterior</Button>
          <Button variant="secondary" disabled={pagina >= funcionarios.data.pages} onClick={() => setPagina((actual) => actual + 1)}>Siguiente</Button>
        </div>
      </div>}
    </CardBody>
  </Card>
}

function PanelSeleccion({ entidadId, seleccionados, setSeleccionados, procesando, preparandoFuncionarioId, errores, onPreparar, onConsultar }: {
  entidadId: number
  seleccionados: Set<number>
  setSeleccionados: (valor: Set<number>) => void
  procesando: boolean
  preparandoFuncionarioId: number | null
  errores: string[]
  onPreparar: (funcionarioId: number) => Promise<void>
  onConsultar: () => Promise<void>
}) {
  // El filtro se hace en el servidor: filtrar solo la primera página de 100
  // funcionarios dejaba fuera jurídicos de directorios institucionales grandes.
  const todos = useFuncionariosDeEntidad(entidadId, { page: 1, page_size: 100, solo_vigentes: true, area: 'juridica' })
  const estadosConsulta = useQuery({ queryKey: ['entidades', entidadId, 'estados-consulta'], queryFn: () => obtenerEstadosConsultaExterna(entidadId) })
  const juridicos = todos.data?.items ?? []

  function alternar(personaMasterId: number) {
    const siguiente = new Set(seleccionados)
    if (siguiente.has(personaMasterId)) siguiente.delete(personaMasterId)
    else siguiente.add(personaMasterId)
    setSeleccionados(siguiente)
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-base font-semibold text-slate-900">2. Profesionales jurídicos, legales y afines</h2>
        <p className="mt-1 text-sm text-slate-500">Clasificación local del listado ya guardado: procuraduría, asesoría jurídica, abogados, intendencias y cargos afines. Esta acción no consulta fuentes externas.</p>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        {todos.isPending && <Spinner label="Cargando listado institucional…" />}
        {todos.isError && <ErrorState error={todos.error} title="No se pudo cargar el listado" onRetry={() => void todos.refetch()} />}
        {todos.data && juridicos.length === 0 && <EmptyState icon={<Users className="size-9" />} title="No hay funcionarios jurídicos clasificados" description="El directorio de Transparencia no contiene cargos clasificados como jurídicos para esta entidad." />}
        {juridicos.length > 0 && (
          <>
            <Table>
              <Thead><Tr><Th>Seleccionar</Th><Th>Funcionario</Th><Th>Cargo</Th><Th>Dependencia</Th><Th>Estado</Th></Tr></Thead>
              <Tbody>
                {juridicos.map((f) => {
                  const disponible = f.persona_master_id !== null
                  return <Tr key={f.funcionario_id}>
                    <Td><input aria-label={`Seleccionar ${f.nombre_completo}`} type="checkbox" disabled={procesando || preparandoFuncionarioId === f.funcionario_id}
                      checked={disponible && seleccionados.has(f.persona_master_id as number)} onChange={() => {
                        if (disponible) alternar(f.persona_master_id as number)
                        else void onPreparar(f.funcionario_id)
                      }} /></Td>
                    <Td>{f.nombre_completo}</Td><Td>{f.cargo}</Td><Td>{f.dependencia}</Td>
                    <Td>{preparandoFuncionarioId === f.funcionario_id ? 'En proceso' : etiquetaEstadoConsulta(estadosConsulta.data?.items[String(f.funcionario_id)]?.estado, disponible)}</Td>
                  </Tr>
                })}
              </Tbody>
            </Table>
            <div className="flex flex-wrap items-center gap-3">
              <Button loading={procesando} disabled={seleccionados.size === 0} onClick={() => void onConsultar()} icon={<PlayCircle className="size-4" />}>
                Consultar datos externos ({seleccionados.size})
              </Button>
              <span className="text-xs text-slate-500">Las consultas se ejecutan secuencialmente, solo para los seleccionados.</span>
            </div>
          </>
        )}
        {errores.map((error) => <p key={error} className="text-sm text-red-700">{error}</p>)}
      </CardBody>
    </Card>
  )
}

function etiquetaEstadoConsulta(estado: string | undefined, disponible: boolean) {
  const etiquetas: Record<string, string> = { pendiente: 'Pendiente', en_proceso: 'En proceso', completada: 'Completada', sin_coincidencia: 'Completada — sin datos externos', error: 'Error · selecciona para reintentar' }
  return estado ? etiquetas[estado] ?? estado : disponible ? 'Pendiente' : 'Selecciona para preparar y consultar'
}

function formatearPeriodo(periodo: string | null) {
  if (!periodo) return 'sin período identificado'
  const fecha = new Date(`${periodo}T00:00:00`)
  return Number.isNaN(fecha.getTime()) ? periodo : new Intl.DateTimeFormat('es-EC', { month: 'long', year: 'numeric' }).format(fecha)
}

function formatearFecha(fecha: string | null) {
  if (!fecha) return 'sin registro'
  const valor = new Date(fecha)
  return Number.isNaN(valor.getTime()) ? fecha : new Intl.DateTimeFormat('es-EC', { dateStyle: 'medium', timeStyle: 'short' }).format(valor)
}

function FuncionariosConsultados({ entidadId }: Props) {
  const bloqueoActualizacion = useRef(false)
  const [actualizando, setActualizando] = useState(false)
  const [funcionarioActual, setFuncionarioActual] = useState<number | null>(null)
  const consultados = useFuncionariosConsultados(entidadId)
  const actualizarFicha = useValidarAbogado()
  const queryClient = useQueryClient()
  const [seleccionados, setSeleccionados] = useState<Set<number>>(new Set())
  const [mensajeExportacion, setMensajeExportacion] = useState<string | null>(null)
  const items = consultados.data?.items ?? []
  const todosSeleccionados = items.length > 0 && items.every((f) => seleccionados.has(f.funcionario_id))

  useEffect(() => {
    setSeleccionados((actuales) => new Set([...actuales].filter((id) => items.some((f) => f.funcionario_id === id))))
  }, [consultados.data])

  function alternar(funcionarioId: number) {
    setSeleccionados((actuales) => {
      const siguientes = new Set(actuales)
      if (siguientes.has(funcionarioId)) siguientes.delete(funcionarioId)
      else siguientes.add(funcionarioId)
      return siguientes
    })
  }

  function alternarTodos() {
    setSeleccionados(todosSeleccionados ? new Set() : new Set(items.map((f) => f.funcionario_id)))
  }

  function seleccionadosComoFuncionarios() {
    return items.filter((f) => seleccionados.has(f.funcionario_id))
  }

  async function copiar(funcionarios: FuncionarioConsultado[]) {
    try {
      await navigator.clipboard.writeText(funcionarios.map(formatearFuncionarioParaCopia).join('\n\n\n'))
      setMensajeExportacion(`${funcionarios.length} funcionario${funcionarios.length === 1 ? '' : 's'} copiado${funcionarios.length === 1 ? '' : 's'} al portapapeles.`)
    } catch {
      setMensajeExportacion('El navegador no permitió copiar. Usa la exportación a Word o Excel.')
    }
  }

  async function actualizarSolo(f: FuncionarioConsultado) {
    await actualizarGrupo([f])
  }

  async function actualizarGrupo(funcionarios: FuncionarioConsultado[]) {
    if (bloqueoActualizacion.current || funcionarios.length === 0) return
    bloqueoActualizacion.current = true
    setActualizando(true)
    let completadas = 0
    let sinDatos = 0
    let fallos = 0
    try {
      for (const [indice, f] of funcionarios.entries()) {
        setFuncionarioActual(f.funcionario_id)
        setMensajeExportacion(`En proceso, por favor espera. ${indice + 1} de ${funcionarios.length}: ${f.nombre_completo}.`)
        try {
          if (f.persona_master_id === null) { fallos++; continue }
          const resultado = await actualizarFicha.mutateAsync(f.persona_master_id)
          if (resultado.estado_consulta_externa === 'error') { fallos++; break }
          if (resultado.estado_consulta_externa === 'sin_coincidencia') sinDatos++
          else completadas++
        } catch { fallos++; break }
      }
      await queryClient.invalidateQueries({ queryKey: ['entidades', entidadId] })
      const pendientes = funcionarios.length - completadas - sinDatos - fallos
      setMensajeExportacion(`${fallos ? 'No se pudo completar el lote. Se detuvo para evitar reintentos repetidos. ' : 'Proceso terminado. '}${completadas} con resultados; ${sinDatos} completadas sin datos externos; ${fallos} con error; ${pendientes} sin procesar. Se conservaron los datos guardados.`)
    } finally {
      setFuncionarioActual(null)
      setActualizando(false)
      bloqueoActualizacion.current = false
    }
  }

  function exportarExcel(funcionarios: FuncionarioConsultado[]) {
    const encabezado = ['FUNCIONARIO', 'CÉDULA', 'PUESTO O CARGO', 'UNIDAD O DEPENDENCIA', 'TELÉFONO INSTITUCIONAL', 'EXTENSIÓN', 'CELULAR', 'CORREO INSTITUCIONAL', 'CORREO PERSONAL']
    const filas = funcionarios.map((f) => [f.nombre_completo, valor(f.cedula), valor(f.cargo), valor(f.dependencia), valor(f.telefono), valor(f.extension_telefonica), valor(f.celular_personal), valor(f.correo), valor(f.correo_personal)])
    const csv = [encabezado, ...filas].map((fila) => fila.map(escaparCsv).join(';')).join('\r\n')
    descargarArchivo(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }), 'funcionarios-consultados.csv')
  }

  function exportarWord(funcionarios: FuncionarioConsultado[]) {
    const contenido = funcionarios.map((f) => `<section style="margin-bottom:24px"><p><strong>FUNCIONARIO:</strong> ${escaparHtml(f.nombre_completo)}<br><strong>CÉDULA:</strong> ${escaparHtml(valor(f.cedula))}<br><strong>PUESTO O CARGO:</strong> ${escaparHtml(valor(f.cargo))}<br><strong>UNIDAD O DEPENDENCIA:</strong> ${escaparHtml(valor(f.dependencia))}<br><strong>TELÉFONO INSTITUCIONAL:</strong> ${escaparHtml(valor(f.telefono))}${f.extension_telefonica ? ` &nbsp;&nbsp; <strong>EXT.:</strong> ${escaparHtml(f.extension_telefonica)}` : ''}<br><strong>CELULAR:</strong> ${escaparHtml(valor(f.celular_personal))}<br><strong>CORREO INSTITUCIONAL:</strong> ${enlaceCorreo(f.correo)}<br><strong>CORREO PERSONAL:</strong> ${enlaceCorreo(f.correo_personal)}</p></section>`).join('<hr>')
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>Funcionarios consultados</title></head><body style="font-family:Arial,sans-serif;font-size:11pt">${contenido}</body></html>`
    descargarArchivo(new Blob([html], { type: 'application/msword;charset=utf-8' }), 'funcionarios-consultados.doc')
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-base font-semibold text-slate-900">3. Funcionarios con datos ya consultados</h2>
        <p className="mt-1 text-sm text-slate-500">Información persistida; abrir esta sección no realiza nuevas consultas externas.</p>
      </CardHeader>
      <CardBody>
        {consultados.isPending && <Spinner label="Cargando datos consultados…" />}
        {consultados.isError && <ErrorState error={consultados.error} title="No se pudieron cargar los datos consultados" onRetry={() => void consultados.refetch()} />}
        {consultados.data?.items.length === 0 && <EmptyState icon={<Database className="size-9" />} title="Aún no hay datos externos consultados" description="Selecciona uno o más funcionarios jurídicos para consultar solo los que necesites." />}
        {items.length > 0 && <>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Button size="sm" variant="secondary" disabled={actualizando || seleccionados.size === 0} onClick={() => void actualizarGrupo(seleccionadosComoFuncionarios())}>Actualizar seleccionados ({seleccionados.size})</Button>
            <Button size="sm" variant="secondary" disabled={actualizando} onClick={() => void actualizarGrupo(items)}>Actualizar todos los mostrados ({items.length})</Button>
            <Button size="sm" variant="secondary" onClick={() => void copiar(items)} icon={<ClipboardCopy className="size-4" />}>Copiar todos</Button>
            <Button size="sm" variant="secondary" disabled={seleccionados.size === 0} onClick={() => void copiar(seleccionadosComoFuncionarios())} icon={<ClipboardCopy className="size-4" />}>Copiar seleccionados ({seleccionados.size})</Button>
            <Button size="sm" variant="secondary" onClick={() => exportarExcel(items)} icon={<FileSpreadsheet className="size-4" />}>Excel todos</Button>
            <Button size="sm" variant="secondary" disabled={seleccionados.size === 0} onClick={() => exportarExcel(seleccionadosComoFuncionarios())} icon={<FileSpreadsheet className="size-4" />}>Excel seleccionados</Button>
            <Button size="sm" variant="secondary" onClick={() => exportarWord(items)} icon={<FileText className="size-4" />}>Word todos</Button>
            <Button size="sm" variant="secondary" disabled={seleccionados.size === 0} onClick={() => exportarWord(seleccionadosComoFuncionarios())} icon={<FileText className="size-4" />}>Word seleccionados</Button>
            {mensajeExportacion && <span className={`text-xs ${mensajeExportacion.startsWith('No se pudo') ? 'text-red-700' : 'text-emerald-700'}`}>{mensajeExportacion}</span>}
          </div>
          <Table>
          <Thead><Tr><Th><input aria-label="Seleccionar todos los funcionarios consultados" type="checkbox" checked={todosSeleccionados} onChange={alternarTodos} /></Th><Th>Funcionario</Th><Th>Cédula</Th><Th>Cargo</Th><Th>Dependencia</Th><Th>Correo institucional</Th><Th>Teléfono</Th><Th>Extensión</Th><Th>Correo personal</Th><Th>Celular</Th><Th>Registro Foro</Th><Th>Estado</Th><Th>Última consulta</Th><Th>Acciones</Th></Tr></Thead>
          <Tbody>{items.map((f) => <Tr key={f.funcionario_id}>
            <Td><input aria-label={`Seleccionar ${f.nombre_completo}`} type="checkbox" checked={seleccionados.has(f.funcionario_id)} onChange={() => alternar(f.funcionario_id)} /></Td>
            <Td><span className="inline-flex items-center gap-1">{!f.estado_consulta_externa?.startsWith('Error') && <CheckCircle2 className="size-4 text-emerald-600" />}{f.nombre_completo}</span></Td>
            <Td>{f.cedula ?? '—'}</Td><Td>{f.cargo}</Td><Td>{f.dependencia}</Td><Td>{f.correo ?? '—'}</Td><Td>{f.telefono ?? '—'}</Td><Td>{f.extension_telefonica ?? '—'}</Td><Td>{f.correo_personal ?? '—'}</Td><Td>{f.celular_personal ?? '—'}</Td>
            <Td>{f.registro_foro ?? '—'}</Td><Td>{funcionarioActual === f.funcionario_id ? 'En proceso, por favor espera' : f.estado_consulta_externa ?? f.estado_foro ?? '—'}</Td><Td>{formatearFecha(f.fecha_consulta)}</Td>
            <Td><div className="flex gap-1"><Button size="sm" variant="secondary" loading={funcionarioActual === f.funcionario_id} disabled={actualizando || f.persona_master_id === null} aria-label={`Actualizar ficha de ${f.nombre_completo}`} onClick={() => void actualizarSolo(f)}>Actualizar ficha</Button><Button size="sm" variant="secondary" aria-label={`Copiar ${f.nombre_completo}`} onClick={() => void copiar([f])} icon={<ClipboardCopy className="size-3.5" />} /><Button size="sm" variant="secondary" aria-label={`Exportar ${f.nombre_completo} a Excel`} onClick={() => exportarExcel([f])} icon={<FileSpreadsheet className="size-3.5" />} /><Button size="sm" variant="secondary" aria-label={`Exportar ${f.nombre_completo} a Word`} onClick={() => exportarWord([f])} icon={<FileText className="size-3.5" />} /></div></Td>
          </Tr>)}</Tbody>
        </Table>
        </>}
      </CardBody>
    </Card>
  )
}

function valor(dato: string | null | undefined) {
  return dato?.trim() || 'No registrado'
}

function formatearFuncionarioParaCopia(f: FuncionarioConsultado) {
  const extension = f.extension_telefonica ? `    EXT.: ${f.extension_telefonica}` : ''
  return `FUNCIONARIO: ${f.nombre_completo}\nCÉDULA: ${valor(f.cedula)}\nPUESTO O CARGO: ${valor(f.cargo)}\nUNIDAD O DEPENDENCIA: ${valor(f.dependencia)}\nTELÉFONO INSTITUCIONAL: ${valor(f.telefono)}${extension}\nCELULAR: ${valor(f.celular_personal)}\nCORREO INSTITUCIONAL: ${valor(f.correo)}\nCORREO PERSONAL: ${valor(f.correo_personal)}`
}

function escaparCsv(dato: string) {
  return `"${dato.replaceAll('"', '""')}"`
}

function escaparHtml(dato: string) {
  return dato.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;')
}

function enlaceCorreo(correo: string | null) {
  return correo ? `<a href="mailto:${escaparHtml(correo)}">${escaparHtml(correo)}</a>` : 'No registrado'
}

function descargarArchivo(contenido: Blob, nombre: string) {
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(contenido)
  enlace.download = nombre
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(enlace.href)
}
