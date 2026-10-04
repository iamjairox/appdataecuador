import { useParams } from 'react-router-dom'
import { Scale, Mail, Phone, Building2, User, ShieldCheck, AlertTriangle } from 'lucide-react'
import { useFuncionarioForo } from '../../hooks/useFuncionario'
import { Card, CardBody, CardHeader, EmptyState, PageHeader } from '../../components/ui'
import { FuncionarioSubnav } from '../../components/FuncionarioSubnav'

/** Muestra la información del Foro de Abogados ya persistida (GET /foro). */
export function FuncionarioForoPage() {
  const { personaMasterId } = useParams<{ personaMasterId: string }>()
  const id = personaMasterId ? Number(personaMasterId) : undefined
  const foro = useFuncionarioForo(id)

  return (
    <>
      <PageHeader title="Foro de Abogados" description={id !== undefined ? `ID ${id}` : undefined} />
      {id !== undefined && <FuncionarioSubnav personaMasterId={id} />}

      {foro.isPending && <div className="flex justify-center py-8"><Scale className="size-8 animate-spin text-slate-400" /></div>}
      {foro.isError && <div className="text-center py-8 text-red-700">No se pudo cargar la información del Foro.</div>}

      {foro.data ? (
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-slate-900">Información del Foro de Abogados</h2>
          </CardHeader>
          <CardBody>
            {foro.data.registros && foro.data.registros.length > 0 ? (
              <div className="space-y-4">
                {foro.data.registros.map((registro, idx) => (
                  <Card key={idx} className="border-slate-200">
                    <CardBody>
                      <div className="space-y-4">
                        {/* Nombre completo */}
                        {registro.nombre_completo && (
                          <div className="flex items-start gap-2">
                            <User className="size-4 text-slate-400 mt-0.5 shrink-0" />
                            <div>
                              <dt className="text-xs text-slate-500">Nombre completo</dt>
                              <dd className="font-medium text-slate-900">{registro.nombre_completo}</dd>
                            </div>
                          </div>
                        )}

                        {/* Número de registro */}
                        {registro.registro && (
                          <div className="flex items-start gap-2">
                            <ShieldCheck className="size-4 text-slate-400 mt-0.5 shrink-0" />
                            <div>
                              <dt className="text-xs text-slate-500">Número de registro</dt>
                              <dd className="font-medium text-slate-900">{registro.registro}</dd>
                            </div>
                          </div>
                        )}

                        {/* Estado */}
                        {registro.estado && (
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="size-4 text-slate-400 mt-0.5 shrink-0" />
                            <div>
                              <dt className="text-xs text-slate-500">Estado</dt>
                              <dd className="font-medium text-slate-900">{registro.estado}</dd>
                            </div>
                          </div>
                        )}

                        {/* Provincia */}
                        {registro.provincia && (
                          <div className="flex items-start gap-2">
                            <Building2 className="size-4 text-slate-400 mt-0.5 shrink-0" />
                            <div>
                              <dt className="text-xs text-slate-500">Provincia</dt>
                              <dd className="font-medium text-slate-900">{registro.provincia}</dd>
                            </div>
                          </div>
                        )}

                        {/* Contacto */}
                        <div className="flex flex-wrap gap-4 pt-2 border-t border-slate-100">
                          {registro.correo && (
                            <div className="flex items-center gap-1.5 text-sm text-slate-600">
                              <Mail className="size-3.5 text-slate-400" />
                              {registro.correo}
                            </div>
                          )}
                          {registro.celular && (
                            <div className="flex items-center gap-1.5 text-sm text-slate-600">
                              <Phone className="size-3.5 text-slate-400" />
                              {registro.celular}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Scale className="size-10" aria-hidden="true" />}
                title="Sin registros en el Foro de Abogados"
                description="No se encontraron registros profesionales para este funcionario."
              />
            )}
          </CardBody>
        </Card>
      ) : (
        <EmptyState icon={<Scale className="size-10" aria-hidden="true" />} title="Cargando información del Foro…" />
      )}
    </>
  )
}
