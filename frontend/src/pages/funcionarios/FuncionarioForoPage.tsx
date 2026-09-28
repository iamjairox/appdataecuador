import { useParams } from 'react-router-dom'
import { Scale } from 'lucide-react'
import { useValidarAbogado } from '../../hooks/useFuncionario'
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, PageHeader } from '../../components/ui'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'

const ETIQUETAS: Record<string, string> = {
  match_exact: 'Coincidencia encontrada',
  match_high_confidence: 'Coincidencia encontrada',
  ambiguous: 'Resultado ambiguo',
  no_match: 'No encontrado',
  no_cedula_found: 'No encontrado',
  source_unavailable: 'Fuente no disponible',
}

/** La cédula y el detalle del Foro nunca llegan a esta pantalla. */
export function FuncionarioForoPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined
  const validacion = useValidarAbogado()
  const resultado = validacion.data?.resultado

  return (
    <>
      <PageHeader title="Validación de abogado" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      <Card>
        <CardBody className="flex flex-wrap items-center gap-3">
          <Button
            disabled={id === undefined || validacion.isPending}
            onClick={() => {
              if (id !== undefined && window.confirm('Se realizará una validación mediante fuentes públicas. ¿Continuar?')) {
                validacion.mutate(id)
              }
            }}
          >
            {validacion.isPending ? 'Consultando…' : 'Validar abogado'}
          </Button>
          {validacion.data && <Badge tone={validacion.data.estado === 'match_exact' ? 'success' : 'neutral'}>{ETIQUETAS[validacion.data.estado] ?? 'Error'}</Badge>}
          {validacion.isError && <p className="text-sm text-red-700">No se pudo completar la validación.</p>}
        </CardBody>
      </Card>

      {resultado ? (
        <Card>
          <CardHeader><h2 className="text-sm font-semibold text-slate-900">Datos del Directorio de Transparencia</h2></CardHeader>
          <CardBody>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              {Object.entries(resultado).map(([etiqueta, valor]) => (
                <div key={etiqueta}><dt className="text-slate-500">{etiqueta}</dt><dd className="font-medium text-slate-900">{valor ?? 'No disponible'}</dd></div>
              ))}
            </dl>
          </CardBody>
        </Card>
      ) : (
        <EmptyState icon={<Scale className="size-10" aria-hidden="true" />} title="Aún no se ha ejecutado una validación." />
      )}
    </>
  )
}
