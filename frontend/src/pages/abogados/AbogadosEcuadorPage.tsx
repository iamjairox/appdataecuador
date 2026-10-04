import { Fragment, useEffect, useState } from 'react'
import { ClipboardCopy, FileSpreadsheet, FileText, Search } from 'lucide-react'
import { Alert, Button, Card, CardBody, CardHeader, Input, PageHeader } from '../../components/ui'
import { apiClient } from '../../api/client'

type Abogado = Record<string, string | null>
type EstadoDirectorio = { estado: string; mensaje: string | null; total_esperado: number | null; pagina_actual: number; registros_guardados: number }
type Vista = 'directorio' | 'consultados'

export function AbogadosEcuadorPage() {
  const [error, setError] = useState('')
  const [detalle, setDetalle] = useState<Abogado | null>(null)
  const [resultadosForo, setResultadosForo] = useState<Abogado[]>([])
  const [consultandoCodigo, setConsultandoCodigo] = useState<string | null>(null)
  const [consultados, setConsultados] = useState<Abogado[]>([])
  const [mensaje, setMensaje] = useState<string | null>(null)
  const [vista, setVista] = useState<Vista>('directorio')
  const [estadoDirectorio, setEstadoDirectorio] = useState<EstadoDirectorio | null>(null)
  const [profesionales, setProfesionales] = useState<Array<Record<string, string>>>([])
  const [filtroDirectorio, setFiltroDirectorio] = useState('')
  const [paginaDirectorio, setPaginaDirectorio] = useState(1)
  const [totalDirectorio, setTotalDirectorio] = useState(0)
  const [cargandoDirectorio, setCargandoDirectorio] = useState(false)
  const [actualizandoDirectorio, setActualizandoDirectorio] = useState(false)
  const mensajeDirectorio = estadoDirectorio?.mensaje?.includes('Server error')
    ? 'La carga se pausó porque la fuente externa no respondió. Puedes intentar nuevamente.'
    : estadoDirectorio?.mensaje

  async function cargarConsultados() {
    try { const { data } = await apiClient.get('/api/v1/abogados-ecuador/consultados'); setConsultados(data.items) } catch { /* El historial no bloquea la búsqueda. */ }
  }
  async function cargarEstadoDirectorio() {
    try { const { data } = await apiClient.get('/api/v1/abogados-ecuador/directorio/estado'); setEstadoDirectorio(data) } catch { /* La búsqueda individual sigue disponible. */ }
  }
  async function cargarDirectorio(pagina = paginaDirectorio, filtro = filtroDirectorio) {
    setCargandoDirectorio(true)
    try {
      const { data } = await apiClient.get('/api/v1/abogados-ecuador/directorio', { params: { q: filtro || undefined, page: pagina, page_size: 50 } })
      setProfesionales(data.items); setTotalDirectorio(data.total); setPaginaDirectorio(data.page)
    } catch { setError('Algo no salió bien. Intenta nuevamente.') }
    finally { setCargandoDirectorio(false) }
  }
  async function actualizarDirectorio() {
    setActualizandoDirectorio(true); setError('')
    try { const { data } = await apiClient.post('/api/v1/abogados-ecuador/directorio/actualizar'); setMensaje(data.mensaje); await cargarEstadoDirectorio() }
    catch { setError('Algo no salió bien. Intenta nuevamente.') }
    finally { setActualizandoDirectorio(false) }
  }
  async function cancelarCargaDirectorio() {
    try { const { data } = await apiClient.post('/api/v1/abogados-ecuador/directorio/cancelar'); setMensaje(data.mensaje); await cargarEstadoDirectorio() }
    catch { setError('Algo no salió bien. Intenta nuevamente.') }
  }
  useEffect(() => {
    void cargarConsultados()
    void cargarEstadoDirectorio()
  }, [])
  useEffect(() => {
    if (vista === 'directorio') void cargarDirectorio(1)
  }, [vista])
  useEffect(() => {
    if (estadoDirectorio?.estado !== 'en_proceso' && estadoDirectorio?.estado !== 'cancelando') return
    const id = window.setInterval(() => { void cargarEstadoDirectorio() }, 1500)
    return () => window.clearInterval(id)
  }, [estadoDirectorio?.estado])

  async function consultarDetalles(codigo: string) {
    setConsultandoCodigo(codigo); setError(''); setResultadosForo([])
    try {
      const { data } = await apiClient.post(`/api/v1/abogados-ecuador/${codigo}/consultar-detalles`)
      setDetalle(data)
      setResultadosForo(data.resultados ?? [])
      if (data.estado_consulta === 'completa') await cargarConsultados()
    } catch { setError('No fue posible completar la ficha del abogado. Intenta nuevamente en unos segundos.') }
    finally { setConsultandoCodigo(null) }
  }
  async function copiar(abogado: Abogado | null) {
    if (!abogado) return
    try { await navigator.clipboard.writeText(formatearAbogado(abogado)); setMensaje('Ficha copiada al portapapeles.') }
    catch { setMensaje('El navegador no permitió copiar. Usa Word o Excel.') }
  }
  function exportarExcel(abogado: Abogado | null) {
    if (!abogado) return
    const encabezado = ['ABOGADO(A)', 'CIUDAD', 'CÉDULA', 'CORREO', 'CELULAR', 'TELÉFONO DOMICILIO', 'TELÉFONO OFICINA', 'DIRECCIÓN DOMICILIO', 'DIRECCIÓN OFICINA']
    const fila = [nombreAbogado(abogado), dato(abogado.ciudad), dato(abogado.cedula), dato(abogado.correo), dato(abogado.celular), dato(abogado.telefono_domicilio), dato(abogado.telefono_oficina), dato(abogado.direccion_domicilio), dato(abogado.direccion_oficina)]
    descargarArchivo(new Blob([`\uFEFF${[encabezado, fila].map((r) => r.map(escaparCsv).join(';')).join('\r\n')}`], { type: 'text/csv;charset=utf-8' }), `abogado-${codigoAbogado(abogado)}.csv`)
  }
  function exportarWord(abogado: Abogado | null) {
    if (!abogado) return
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>Ficha de abogado</title></head><body style="font-family:Arial,sans-serif;font-size:11pt"><p>${formatearAbogado(abogado).split('\n').map(escaparHtml).join('<br>')}</p></body></html>`
    descargarArchivo(new Blob([html], { type: 'application/msword;charset=utf-8' }), `abogado-${codigoAbogado(abogado)}.doc`)
  }

  return <>
    <PageHeader title="Abogados del Ecuador" description="Consulta individual de profesionales; no modifica las entidades ni sus funcionarios." />
    <Alert tone="info">Cada ficha se consulta individualmente. Cuando queda completa, se guarda en “Abogados ya consultados” para reutilizarla sin repetir fuentes externas.</Alert>
    <Card><CardBody className="flex flex-wrap gap-3"><Button variant={vista === 'directorio' ? 'primary' : 'secondary'} onClick={() => setVista('directorio')}>1. Profesionales del Derecho</Button><Button variant={vista === 'consultados' ? 'primary' : 'secondary'} onClick={() => setVista('consultados')}>2. Abogados ya consultados</Button></CardBody></Card>
    {vista === 'directorio' && <Card><CardHeader><h2 className="text-base font-semibold text-slate-900">1. Profesionales del Derecho</h2><p className="mt-1 text-sm text-slate-500">Busca por nombre o apellido en el listado local y consulta el detalle únicamente del profesional elegido.</p></CardHeader><CardBody className="space-y-4"><div className="flex flex-wrap items-center gap-3"><span className="text-sm text-slate-600">{estadoDirectorio ? `${estadoDirectorio.registros_guardados.toLocaleString()} de ${(estadoDirectorio.total_esperado ?? 130107).toLocaleString()} profesionales guardados` : 'Cargando estado…'}</span><Button loading={actualizandoDirectorio} disabled={estadoDirectorio?.estado === 'en_proceso'} onClick={() => void actualizarDirectorio()}>Actualizar listado</Button>{estadoDirectorio?.estado === 'en_proceso' && <Button variant="secondary" onClick={() => void cancelarCargaDirectorio()}>Pausar carga</Button>}</div>{mensajeDirectorio && <p role="status" className="text-sm text-slate-600">{mensajeDirectorio} {estadoDirectorio?.estado === 'en_proceso' ? `Página ${estadoDirectorio.pagina_actual.toLocaleString()}.` : ''}</p>}<form className="flex flex-wrap gap-3" onSubmit={(e) => { e.preventDefault(); void cargarDirectorio(1) }}><div className="min-w-72 flex-1"><Input label="Buscar por nombres o apellidos" name="directorio" value={filtroDirectorio} onChange={(e) => setFiltroDirectorio(e.target.value)} /></div><div className="flex items-end"><Button type="submit" loading={cargandoDirectorio} icon={<Search className="size-4" />}>Buscar</Button></div></form>{profesionales.length > 0 && <><p className="text-sm text-slate-600">Página {paginaDirectorio.toLocaleString()} de {Math.max(1, Math.ceil(totalDirectorio / 50)).toLocaleString()} · {totalDirectorio.toLocaleString()} profesionales</p><div className="space-y-2">{profesionales.map((a) => <Fragment key={a.codigo}><div className="flex flex-wrap items-center justify-between gap-3 rounded border p-3"><div><p className="font-medium">{a.nombre_completo}</p><p className="text-sm text-slate-500">Matrícula: {a.matricula || 'No disponible'} · {a.estado || 'No disponible'}</p></div><Button variant="secondary" loading={consultandoCodigo === a.codigo} disabled={consultandoCodigo !== null || !a.codigo} onClick={() => void consultarDetalles(a.codigo ?? '')}>Consultar detalle</Button></div>{detalle && String(detalle.codigo) === String(a.codigo) && <Ficha abogado={detalle} onCopiar={() => void copiar(detalle)} onExcel={() => exportarExcel(detalle)} onWord={() => exportarWord(detalle)} />}</Fragment>)}</div><div className="flex justify-between gap-2"><Button variant="secondary" disabled={cargandoDirectorio || paginaDirectorio <= 1} onClick={() => void cargarDirectorio(paginaDirectorio - 1)}>Anterior</Button><Button variant="secondary" disabled={cargandoDirectorio || paginaDirectorio >= Math.ceil(totalDirectorio / 50)} onClick={() => void cargarDirectorio(paginaDirectorio + 1)}>Siguiente</Button></div></>}</CardBody></Card>}
    {error && <Alert tone="danger">{error}</Alert>}
    {mensaje && <Alert tone="success">{mensaje}</Alert>}
    {vista === 'directorio' && resultadosForo.length > 0 && <Card><CardHeader><h2 className="font-semibold">Resultados verificados de la consulta</h2><p className="text-sm text-slate-600">Se muestran por separado. No se guarda automáticamente una identidad mientras existan varias coincidencias o verificaciones pendientes.</p></CardHeader><CardBody className="space-y-3">{resultadosForo.map((ficha) => <Ficha key={`${ficha.cedula}-${ficha.matricula}`} abogado={ficha} onCopiar={() => void copiar(ficha)} onExcel={() => exportarExcel(ficha)} onWord={() => exportarWord(ficha)} />)}</CardBody></Card>}
    {detalle && vista === 'consultados' && <Ficha abogado={detalle} onCopiar={() => void copiar(detalle)} onExcel={() => exportarExcel(detalle)} onWord={() => exportarWord(detalle)} />}
    {vista === 'consultados' && <Card><CardHeader><h2 className="text-base font-semibold text-slate-900">2. Abogados ya consultados</h2><p className="mt-1 text-sm text-slate-500">Fichas completas guardadas localmente. Abrirlas no realiza una nueva consulta externa.</p></CardHeader><CardBody>{consultados.length === 0 ? <p className="text-sm text-slate-500">Todavía no hay fichas completas guardadas.</p> : <div className="space-y-2">{consultados.map((abogado) => <div key={codigoAbogado(abogado)} className="flex flex-wrap items-center justify-between gap-3 rounded border p-3"><div><p className="font-medium text-slate-900">{nombreAbogado(abogado)}</p><p className="text-sm text-slate-500">{dato(abogado.ciudad)} · Cédula: {dato(abogado.cedula)}</p></div><Button variant="secondary" onClick={() => setDetalle(abogado)}>Abrir ficha guardada</Button></div>)}</div>}</CardBody></Card>}
  </>
}

function Ficha({ abogado, onCopiar, onExcel, onWord }: { abogado: Abogado | null; onCopiar: () => void; onExcel: () => void; onWord: () => void }) {
  if (!abogado) return null
  return <Card><CardHeader><h2 className="text-base font-semibold">Ficha del abogado</h2></CardHeader><CardBody className="space-y-4"><div><p className="font-medium text-slate-900">{nombreAbogado(abogado)}</p><p className="text-sm text-slate-600">{dato(abogado.titulo)} · {dato(abogado.ciudad || abogado.provincia)}</p></div>{abogado.estado_consulta !== 'completa' && <Alert tone="warning">No fue posible completar los datos no públicos para esta coincidencia ({abogado.estado_consulta}). Se muestran los datos disponibles.</Alert>}<div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" onClick={onCopiar} icon={<ClipboardCopy className="size-4" />}>Copiar</Button><Button size="sm" variant="secondary" onClick={onExcel} icon={<FileSpreadsheet className="size-4" />}>Exportar Excel</Button><Button size="sm" variant="secondary" onClick={onWord} icon={<FileText className="size-4" />}>Exportar Word</Button></div><div className="grid gap-3 sm:grid-cols-2"><Campo etiqueta="Ciudad" valor={abogado.ciudad || abogado.canton || abogado.provincia} /><Campo etiqueta="Cédula" valor={abogado.cedula} /><Campo etiqueta="Correo" valor={abogado.correo} /><Campo etiqueta="Celular" valor={abogado.celular} /><Campo etiqueta="Teléfono domicilio" valor={abogado.telefono_domicilio} /><Campo etiqueta="Teléfono oficina" valor={abogado.telefono_oficina} /><Campo etiqueta="Dirección domicilio" valor={abogado.direccion_domicilio} /><Campo etiqueta="Dirección oficina" valor={abogado.direccion_oficina} /></div></CardBody></Card>
}
function Campo({ etiqueta, valor }: { etiqueta: string; valor: string | null | undefined }) { return <div><p className="text-xs font-medium uppercase text-slate-500">{etiqueta}</p><p className="text-sm text-slate-800">{dato(valor)}</p></div> }
function dato(valor: string | null | undefined) { return valor?.trim() || 'No disponible' }
function nombreAbogado(abogado: Abogado) { return abogado.nombre_completo || [abogado.nombres, abogado.apellidos].filter(Boolean).join(' ') || 'Abogado no identificado' }
function codigoAbogado(abogado: Abogado) { return abogado.codigo || 'ficha' }
function formatearAbogado(abogado: Abogado) { return `ABOGADO(A): ${nombreAbogado(abogado)}\nCIUDAD: ${dato(abogado.ciudad || abogado.canton || abogado.provincia)}\nCÉDULA: ${dato(abogado.cedula)}\nCORREO: ${dato(abogado.correo)}\nCELULAR: ${dato(abogado.celular)}\nTELÉFONO DOMICILIO: ${dato(abogado.telefono_domicilio)}\nTELÉFONO OFICINA: ${dato(abogado.telefono_oficina)}\nDIRECCIÓN DOMICILIO: ${dato(abogado.direccion_domicilio)}\nDIRECCIÓN OFICINA: ${dato(abogado.direccion_oficina)}` }
function escaparCsv(dato: string) { return `"${dato.replaceAll('"', '""')}"` }
function escaparHtml(dato: string) { return dato.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;') }
function descargarArchivo(contenido: Blob, nombre: string) { const enlace = document.createElement('a'); enlace.href = URL.createObjectURL(contenido); enlace.download = nombre; document.body.appendChild(enlace); enlace.click(); enlace.remove(); URL.revokeObjectURL(enlace.href) }
