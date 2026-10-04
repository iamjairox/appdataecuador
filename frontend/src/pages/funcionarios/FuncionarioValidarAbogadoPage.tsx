import { useParams } from 'react-router-dom'
import { Scale, BadgeCheck, Info, Mail, Phone, MapPin, Briefcase, Building2, ShieldCheck } from 'lucide-react'
import { useValidarAbogado } from '../../hooks/useFuncionario'
import { Badge, Button, Card, CardBody, EmptyState, PageHeader } from '../../components/ui'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'
import { CampoItem, SeccionItem, ETIQUETAS_ESTADO, ETIQUETAS_VALIDACION } from '../../components/ValidarAbogadoComponents'

/** Página de validación de abogado (POST /validar-abogado). La cédula NUNCA llega a esta pantalla (privacidad). */
export function FuncionarioValidarAbogadoPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined
  const validacion = useValidarAbogado()
  const data = validacion.data

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
          {data && (
            <>
              <Badge tone={ETIQUETAS_ESTADO[data.estado]?.tone || 'neutral'}>
                {ETIQUETAS_ESTADO[data.estado]?.label ?? data.estado}
              </Badge>
              <Badge tone={ETIQUETAS_ESTADO[data.estado_identificacion]?.tone || 'neutral'}>
                {ETIQUETAS_ESTADO[data.estado_identificacion]?.label ?? data.estado_identificacion}
              </Badge>
            </>
          )}
          {validacion.isError && <p className="text-sm text-red-700">No se pudo completar la validación.</p>}
        </CardBody>
      </Card>

      {data ? (
        <div className="space-y-6 mt-6">
          {/* Identificación */}
          <SeccionItem titulo="Resultado de la Identificación" icon={<ShieldCheck className="size-5" />}>
            <CampoItem label="Estado" valor={ETIQUETAS_VALIDACION[data.estado_identificacion]?.label ?? data.estado_identificacion} icon={ETIQUETAS_VALIDACION[data.estado_identificacion]?.icon} />
            <CampoItem label="Confianza" valor={`${(data.confianza || 0).toFixed(1)}%`} icon={<Info className="size-4" />} />
            <CampoItem label="Detalle" valor={data.detalle} icon={<Info className="size-4" />} />
            <CampoItem label="Fuente" valor={data.fuente} icon={<Building2 className="size-4" />} />
            <CampoItem label="Fecha de consulta" valor={data.fecha_consulta ? new Date(data.fecha_consulta).toLocaleString() : undefined} icon={<MapPin className="size-4" />} />
          </SeccionItem>

          {/* Datos del Directorio de Transparencia */}
          <SeccionItem titulo="Datos del Directorio de Transparencia" icon={<Building2 className="size-5" />}>
            <CampoItem label="Institución" valor={data.institucion} icon={<Building2 className="size-4" />} />
            <CampoItem label="Tipo de institución" valor={data.tipo_institucion} icon={<Building2 className="size-4" />} />
            <CampoItem label="Provincia" valor={data.provincia} icon={<MapPin className="size-4" />} />
            <CampoItem label="Mes de Transparencia" valor={data.mes_transparencia} icon={<MapPin className="size-4" />} />
            <CampoItem label="Nombre completo" valor={data.nombre_completo} icon={<BadgeCheck className="size-4" />} />
            <CampoItem label="Cargo" valor={data.cargo} icon={<Briefcase className="size-4" />} />
            <CampoItem label="Dependencia" valor={data.dependencia} icon={<Briefcase className="size-4" />} />
            <CampoItem label="Área normalizada" valor={data.area_normalizada} icon={<BadgeCheck className="size-4" />} />
            <CampoItem label="Ciudad" valor={data.ciudad} icon={<MapPin className="size-4" />} />
            <CampoItem label="Correo institucional" valor={data.correo_institucional} icon={<Mail className="size-4" />} />
            <CampoItem label="Teléfono institucional" valor={data.telefono_institucional} icon={<Phone className="size-4" />} />
          </SeccionItem>

          {/* Información Profesional - Foro de Abogados */}
          {(data.registro_foro || data.estado_foro || data.provincia_foro || data.correo_personal || data.celular_personal) && (
            <SeccionItem titulo="Información Profesional (Foro de Abogados)" icon={<ShieldCheck className="size-5" />}>
              <CampoItem label="Número de Registro" valor={data.registro_foro} icon={<BadgeCheck className="size-4" />} />
              <CampoItem label="Estado" valor={data.estado_foro} icon={<Info className="size-4" />} />
              <CampoItem label="Provincia" valor={data.provincia_foro} icon={<MapPin className="size-4" />} />
              <CampoItem label="Correo personal" valor={data.correo_personal} icon={<Mail className="size-4" />} />
              <CampoItem label="Celular personal" valor={data.celular_personal} icon={<Phone className="size-4" />} />
              <CampoItem label="Fuente" valor={data.fuente} icon={<Building2 className="size-4" />} />
            </SeccionItem>
          )}

          {/* Metadatos */}
          <SeccionItem titulo="Metadatos de la Validación" icon={<Info className="size-5" />}>
            <CampoItem label="Confianza" valor={`${(data.confianza || 0).toFixed(1)}%`} icon={<Info className="size-4" />} />
            <CampoItem label="Detalle" valor={data.detalle} icon={<Info className="size-4" />} />
          </SeccionItem>
        </div>
      ) : (
        <EmptyState icon={<Scale className="size-10" aria-hidden="true" />} title="Aún no se ha ejecutado una validación." />
      )}
    </>
  )
}
