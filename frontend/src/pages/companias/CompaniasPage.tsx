import { Fragment, useEffect, useRef, useState } from 'react'
import { Building2, Copy, Download, Eye, FileText, Search, Scale } from 'lucide-react'
import { Alert, Button, Card, CardBody, CardHeader, Input, PageHeader, Spinner, Table, Tbody, Td, Th, Thead, Tr } from '../../components/ui'
import { apiClient } from '../../api/client'

type Compania={ruc:string;nombre:string;situacion_legal:string|null;provincia:string|null;ciudad:string|null;direccion:string|null;telefono:string|null;representante:string|null;cargo_representante:string|null;ciiu:string|null}
type Ficha={empresa:string;ruc:string;actividad:string|null;contacto:string|null;ubicacion:string|null;representante:string|null;cedula:string|null;correo:string|null;celular:string|null;telefono_domicilio:string|null;telefono_oficina:string|null;direccion_domicilio:string|null;direccion_oficina:string|null;estado:string|null}
type Progreso={estado:string;total_filas:number|null;filas_procesadas:number;empresas_guardadas:number;mensaje:string|null}
type Vista='completo'|'juridicas'|'consultados'
const valor=(dato:string|null|undefined)=>dato||'No disponible'
const texto=(f:Ficha)=>`EMPRESA: ${f.empresa}\nRUC: ${f.ruc}\nACTIVIDAD: ${valor(f.actividad)}\nCONTACTO: ${valor(f.contacto)}\nUBICACIÓN: ${valor(f.ubicacion)}\nREPRESENTANTE: ${valor(f.representante)}\nCÉDULA: ${valor(f.cedula)}\nCORREO: ${valor(f.correo)}\nCELULAR: ${valor(f.celular)}\nTELÉFONO DOMICILIO: ${valor(f.telefono_domicilio)}\nTELÉFONO OFICINA: ${valor(f.telefono_oficina)}\nDIRECCIÓN DOMICILIO: ${valor(f.direccion_domicilio)}\nDIRECCIÓN OFICINA: ${valor(f.direccion_oficina)}`
function descargar(nombre:string,contenido:string,tipo:string){const enlace=document.createElement('a');enlace.href=URL.createObjectURL(new Blob([contenido],{type:tipo}));enlace.download=nombre;enlace.click();URL.revokeObjectURL(enlace.href)}
function Paginador({pagina,total,cargando,onCambiar}:{pagina:number;total:number;cargando:boolean;onCambiar:(pagina:number)=>void}){const paginas=Math.max(1,Math.ceil(total/50));return <div className="my-3 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600"><span>Página {pagina.toLocaleString()} de {paginas.toLocaleString()} · {total.toLocaleString()} compañías</span><div className="flex gap-2"><Button size="sm" variant="secondary" disabled={cargando||pagina<=1} onClick={()=>onCambiar(pagina-1)}>Anterior</Button><Button size="sm" variant="secondary" disabled={cargando||pagina>=paginas} onClick={()=>onCambiar(pagina+1)}>Siguiente</Button></div></div>}

export function CompaniasPage(){
 const [estado,setEstado]=useState<{total:number;periodo_fuente:string|null}|null>(null)
 const [progreso,setProgreso]=useState<Progreso|null>(null)
 const [items,setItems]=useState<Compania[]>([])
 const [pagina,setPagina]=useState(1)
 const [totalListado,setTotalListado]=useState(0)
 const [consultados,setConsultados]=useState<Ficha[]>([])
 const [q,setQ]=useState('')
 const [rucFiltro,setRucFiltro]=useState('')
 const [provincia,setProvincia]=useState('')
 const [representanteFiltro,setRepresentanteFiltro]=useState('')
 const [vista,setVista]=useState<Vista>('completo')
 const [cargando,setCargando]=useState(false)
 const [actualizando,setActualizando]=useState(false)
 const [error,setError]=useState('')
 const [ficha,setFicha]=useState<Ficha|null>(null)
 const [consultandoRuc,setConsultandoRuc]=useState<string|null>(null)
 const [aviso,setAviso]=useState('')
 const fichaRef=useRef<HTMLDivElement>(null)
 const esListado=vista!=='consultados'

 const estadoCarga=async()=>{const {data}=await apiClient.get('/api/v1/companias/estado');setEstado(data)}
 const progresoCarga=async()=>{const {data}=await apiClient.get('/api/v1/companias/progreso-carga');setProgreso(data)}
 const historial=async()=>{const {data}=await apiClient.get('/api/v1/companias/consultados');setConsultados(data.items)}
 const buscar=async(paginaSolicitada=pagina)=>{if(!esListado)return;setCargando(true);setError('');try{const {data}=await apiClient.get('/api/v1/companias',{params:{q:q||undefined,ruc:rucFiltro||undefined,provincia:provincia||undefined,representante:representanteFiltro||undefined,solo_juridicas:vista==='juridicas',page:paginaSolicitada,page_size:50}});setItems(data.items);setTotalListado(data.total);setPagina(data.page)}catch{setError('No fue posible leer el directorio local.')}finally{setCargando(false)}}
 useEffect(()=>{void estadoCarga();void progresoCarga();void historial()},[])
 useEffect(()=>{if(estado?.total&&esListado){setPagina(1);void buscar(1)}},[estado?.total,vista])
 const importando=actualizando||progreso?.estado==='procesando'||progreso?.estado==='descargando'
 useEffect(()=>{if(!importando)return;const id=window.setInterval(()=>{void progresoCarga();void estadoCarga()},1000);return()=>window.clearInterval(id)},[importando])
 const actualizar=async()=>{setActualizando(true);try{await apiClient.post('/api/v1/companias/actualizar-directorio',undefined,{timeout:1800000});await estadoCarga();if(esListado)await buscar()}catch(e:unknown){setError((e as {response?:{data?:{detail?:string}}})?.response?.data?.detail||'No se pudo actualizar el directorio.')}finally{void progresoCarga();setActualizando(false)}}
 const consultar=async(ruc:string)=>{if(consultandoRuc)return;setFicha(null);setError('');setAviso('Generando información de la empresa seleccionada…');setConsultandoRuc(ruc);try{const {data}=await apiClient.post(`/api/v1/companias/${ruc}/verificar-representante`,undefined,{timeout:300000});setFicha(data);setAviso('Información generada y guardada en Datos consultados.');await historial()}catch(e:unknown){setError((e as {response?:{data?:{detail?:string}}})?.response?.data?.detail||'No se pudo consultar la empresa seleccionada.')}finally{setConsultandoRuc(null)}}
 const acciones=(f:Ficha)=>{const contenido=texto(f);const copiar=async()=>{try{await navigator.clipboard.writeText(contenido);setAviso('Ficha copiada al portapapeles.')}catch{setAviso('No se pudo copiar la ficha.')}};const exportar=(extension:'csv'|'doc')=>{if(extension==='csv')descargar(`${f.ruc}.csv`,`Campo,Valor\n${contenido.split('\n').map(x=>x.replace(': ', ',')).join('\n')}`,'text/csv;charset=utf-8');else descargar(`${f.ruc}.doc`,`<html><body><pre>${contenido}</pre></body></html>`,'application/msword');setAviso(`Descarga de ${extension==='csv'?'Excel':'Word'} iniciada.`)};return <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" onClick={()=>void copiar()} icon={<Copy className="size-3.5"/>}>Copiar</Button><Button size="sm" variant="secondary" onClick={()=>exportar('csv')} icon={<Download className="size-3.5"/>}>Excel</Button><Button size="sm" variant="secondary" onClick={()=>exportar('doc')} icon={<FileText className="size-3.5"/>}>Word</Button></div>}
 const verFicha=(f:Ficha)=>{setFicha(f);window.setTimeout(()=>fichaRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),0)}
 const fichaDetalle=(f:Ficha)=><div className="rounded-md border border-slate-200 bg-slate-50 p-4"><h3 className="mb-3 font-semibold text-slate-900">Información de la empresa consultada</h3><pre className="mb-4 whitespace-pre-wrap font-sans text-sm leading-6">{texto(f)}</pre>{acciones(f)}</div>
 const tituloListado=vista==='completo'?'1. Listado completo de empresas':'2. Empresas jurídicas, legales y similares'

 return <>
  <PageHeader title="Compañías y representantes" description="Directorio de Supercias; SRI y datos del representante se consultan solo para la empresa seleccionada."/>
  <Card><CardHeader><h2 className="text-base font-semibold">Directorio de compañías de Supercias</h2></CardHeader><CardBody className="flex flex-wrap items-center gap-3"><span className="text-sm text-slate-600">{estado?`${estado.total.toLocaleString()} compañías guardadas · última carga: ${estado.periodo_fuente??'sin carga'}`:'Cargando estado…'}</span><Button loading={actualizando} disabled={importando} onClick={()=>void actualizar()} icon={<Download className="size-4"/>}>Actualizar directorio oficial</Button>{progreso?.estado==='procesando'&&<p className="w-full text-sm text-blue-700">Procesando: {progreso.filas_procesadas.toLocaleString()} de {progreso.total_filas?.toLocaleString()} · {progreso.empresas_guardadas.toLocaleString()} filas.</p>}{progreso?.estado==='completado'&&<p className="w-full text-sm text-emerald-700">{progreso.mensaje}</p>}</CardBody></Card>
  <Card><CardBody className="flex flex-wrap gap-3"><Button variant={vista==='completo'?'primary':'secondary'} onClick={()=>setVista('completo')} icon={<Building2 className="size-4"/>}>1. Listado completo de empresas</Button><Button variant={vista==='juridicas'?'primary':'secondary'} onClick={()=>setVista('juridicas')} icon={<Scale className="size-4"/>}>2. Jurídicas, legales y similares</Button><Button variant={vista==='consultados'?'primary':'secondary'} onClick={()=>setVista('consultados')} icon={<FileText className="size-4"/>}>3. Datos consultados</Button></CardBody></Card>
  {error&&<Alert tone="danger">{error}</Alert>}
  {aviso&&<Alert tone="success">{aviso}</Alert>}
  {esListado&&<Card><CardHeader><h2 className="text-base font-semibold">{tituloListado}</h2></CardHeader><CardBody className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5"><Input label="Nombre o razón social" name="q" value={q} onChange={e=>setQ(e.target.value)}/><Input label="RUC" name="ruc" inputMode="numeric" value={rucFiltro} onChange={e=>setRucFiltro(e.target.value)}/><Input label="Provincia" name="provincia" value={provincia} onChange={e=>setProvincia(e.target.value)}/><Input label="Representante legal" name="representante" value={representanteFiltro} onChange={e=>setRepresentanteFiltro(e.target.value)}/><div className="flex items-end"><Button className="w-full justify-center" onClick={()=>void buscar(1)} loading={cargando} icon={<Search className="size-4"/>}>Buscar</Button></div></CardBody></Card>}
  {cargando&&<Spinner label="Buscando compañías…"/>}
  {esListado&&items.length>0&&<Card><CardHeader><h2 className="text-base font-semibold">{tituloListado}</h2></CardHeader><CardBody><Paginador pagina={pagina} total={totalListado} cargando={cargando} onCambiar={(nuevaPagina)=>void buscar(nuevaPagina)}/><Table className="min-w-0 table-fixed"><colgroup><col/><col className="w-32 sm:w-44"/><col className="w-28 sm:w-32"/><col className="w-36 sm:w-44"/></colgroup><Thead><Tr><Th>Empresa</Th><Th className="px-2 sm:px-4">Representante legal</Th><Th className="px-2 sm:px-4">RUC</Th><Th className="px-2 sm:px-4">Acción</Th></Tr></Thead><Tbody>{items.map(x=><Fragment key={x.ruc}><Tr><Td className="break-words"><span className="font-medium">{x.nombre}</span><br/><span className="text-xs text-slate-500">{x.provincia??'Provincia no informada'} · CIIU {x.ciiu??'—'}</span></Td><Td className="break-words px-2 text-xs sm:px-4 sm:text-sm">{x.representante??'No informado'}</Td><Td className="whitespace-nowrap px-2 text-xs sm:px-4 sm:text-sm">{x.ruc}</Td><Td className="px-2 sm:px-4"><Button className="w-full whitespace-normal justify-center text-center leading-4" size="sm" variant="secondary" disabled={consultandoRuc!==null} loading={consultandoRuc===x.ruc} onClick={()=>void consultar(x.ruc)} icon={<Scale className="size-3.5"/>}>{consultandoRuc===x.ruc?'Generando información…':'Solicitar información'}</Button></Td></Tr>{ficha?.ruc===x.ruc&&<Tr><Td colSpan={4}>{fichaDetalle(ficha)}</Td></Tr>}</Fragment>)}</Tbody></Table><Paginador pagina={pagina} total={totalListado} cargando={cargando} onCambiar={(nuevaPagina)=>void buscar(nuevaPagina)}/></CardBody></Card>}
  {vista==='consultados'&&ficha&&<div ref={fichaRef}><Card><CardHeader><h2 className="text-base font-semibold">Ficha de empresa consultada</h2></CardHeader><CardBody>{fichaDetalle(ficha)}</CardBody></Card></div>}
  {vista==='consultados'&&<Card><CardHeader><h2 className="text-base font-semibold">3. Datos consultados</h2></CardHeader><CardBody>{consultados.length===0?<p className="text-sm text-slate-600">Aún no hay empresas consultadas individualmente.</p>:<Table><Thead><Tr><Th>Empresa</Th><Th>RUC</Th><Th>Representante</Th><Th>Actividad</Th><Th>Acciones</Th></Tr></Thead><Tbody>{consultados.map(f=><Tr key={f.ruc}><Td>{f.empresa}</Td><Td>{f.ruc}</Td><Td>{valor(f.representante)}<br/><span className="text-xs">{valor(f.cedula)}</span></Td><Td className="max-w-md text-xs">{valor(f.actividad)}</Td><Td><div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" onClick={()=>verFicha(f)} icon={<Eye className="size-3.5"/>}>Ver</Button>{acciones(f)}</div></Td></Tr>)}</Tbody></Table>}</CardBody></Card>}
 </>
}
