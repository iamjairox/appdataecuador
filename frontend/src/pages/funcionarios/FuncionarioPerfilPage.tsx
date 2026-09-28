import { useParams } from 'react-router-dom'
import { useFuncionarioPerfil } from '../../hooks/useFuncionario'
import { PageHeader, Spinner, Card, CardHeader, CardBody } from '../../components/ui'
import { ErrorState } from '../../components/ErrorState'
import { RecordPreview } from '../../components/RecordPreview'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'
import { CopyButton } from '../../components/CopyButton'
import { extraerTexto } from '../../lib/extraer-campo'

/**
 * `PerfilConsolidado` real: `persona`/`transparencia`/`senescyt`/`foro`
 * son objetos libres del backend (Submódulo 8.10) -- se muestran tal
 * cual con `RecordPreview`, sin aplanar ni inventar campos.
 */
export function FuncionarioPerfilPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined

  const perfil = useFuncionarioPerfil(id)

  const nombreCompleto = perfil.data ? extraerTexto(perfil.data.persona, 'nombre_completo') : null
  const cedula = perfil.data ? extraerTexto(perfil.data.persona, 'cedula') : null
  const correo = perfil.data ? extraerTexto(perfil.data.persona, 'correo_principal') : null
  const telefono = perfil.data ? extraerTexto(perfil.data.persona, 'telefono_principal') : null

  return (
    <>
      <PageHeader
        title={nombreCompleto ?? 'Perfil de funcionario'}
        description={id !== undefined ? `ID ${id}` : undefined}
      />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {perfil.isPending && <Spinner label="Cargando perfil…" />}
      {perfil.isError && <ErrorState error={perfil.error} title="No se pudo cargar el perfil" />}

      {perfil.data && (
        <>
          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold text-slate-900">Datos de contacto</h2>
            </CardHeader>
            <CardBody className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
              <div className="flex items-center gap-1">
                <span className="text-slate-500">Cédula:</span>
                <span className="font-medium text-slate-900">{cedula ?? '—'}</span>
                <CopyButton value={cedula} label="Cédula" />
              </div>
              <div className="flex items-center gap-1">
                <span className="text-slate-500">Correo:</span>
                <span className="font-medium text-slate-900">{correo ?? '—'}</span>
                <CopyButton value={correo} label="Correo" />
              </div>
              <div className="flex items-center gap-1">
                <span className="text-slate-500">Teléfono:</span>
                <span className="font-medium text-slate-900">{telefono ?? '—'}</span>
                <CopyButton value={telefono} label="Teléfono" />
              </div>
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <h2 className="text-sm font-semibold text-slate-900">Persona</h2>
              </CardHeader>
              <CardBody>
                <RecordPreview data={perfil.data.persona} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>
                <h2 className="text-sm font-semibold text-slate-900">Transparencia</h2>
              </CardHeader>
              <CardBody>
                <RecordPreview data={perfil.data.transparencia} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>
                <h2 className="text-sm font-semibold text-slate-900">SENESCYT</h2>
              </CardHeader>
              <CardBody>
                <RecordPreview data={perfil.data.senescyt} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>
                <h2 className="text-sm font-semibold text-slate-900">Foro de Abogados</h2>
              </CardHeader>
              <CardBody>
                <RecordPreview data={perfil.data.foro} />
              </CardBody>
            </Card>
            <p className="text-xs text-slate-400 lg:col-span-2">Generado: {perfil.data.generado_en}</p>
          </div>
        </>
      )}
    </>
  )
}
