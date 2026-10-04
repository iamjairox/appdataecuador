import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../layouts/AppLayout'
import { HomePage } from '../pages/HomePage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { EntidadesListPage } from '../pages/entidades/EntidadesListPage'
import { EntidadDetallePage } from '../pages/entidades/EntidadDetallePage'
import { EntidadConsultaPage } from '../pages/entidades/EntidadConsultaPage'
import { EntidadAlertasPage } from '../pages/entidades/EntidadAlertasPage'
import { EntidadCambiosPage } from '../pages/entidades/EntidadCambiosPage'
import { OperacionesMasivasPage } from '../pages/entidades/OperacionesMasivasPage'
import { FuncionariosIndexPage } from '../pages/funcionarios/FuncionariosIndexPage'
import { FuncionarioPerfilPage } from '../pages/funcionarios/FuncionarioPerfilPage'
import { FuncionarioHistorialPage } from '../pages/funcionarios/FuncionarioHistorialPage'
import { FuncionarioAcademicoPage } from '../pages/funcionarios/FuncionarioAcademicoPage'
import { FuncionarioForoPage } from '../pages/funcionarios/FuncionarioForoPage'
import { FuncionarioValidarAbogadoPage } from '../pages/funcionarios/FuncionarioValidarAbogadoPage'
import { FuncionarioAlertasPage } from '../pages/funcionarios/FuncionarioAlertasPage'
import { FuncionarioTimelinePage } from '../pages/funcionarios/FuncionarioTimelinePage'
import { AlertasIndexPage } from '../pages/AlertasIndexPage'
import { JobsIndexPage } from '../pages/jobs/JobsIndexPage'
import { JobDetallePage } from '../pages/jobs/JobDetallePage'
import { AbogadosEcuadorPage } from '../pages/abogados/AbogadosEcuadorPage'
import { CompaniasPage } from '../pages/companias/CompaniasPage'
import { AuditoresEcuadorPage } from '../pages/auditores/AuditoresEcuadorPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'entidades', element: <EntidadesListPage /> },
      { path: 'abogados-ecuador', element: <AbogadosEcuadorPage /> },
      { path: 'auditores-ecuador', element: <AuditoresEcuadorPage /> },
      { path: 'companias', element: <CompaniasPage /> },
      { path: 'entidades/:entidadId', element: <EntidadDetallePage /> },
      { path: 'entidades/:entidadId/consulta', element: <EntidadConsultaPage /> },
      { path: 'entidades/:entidadId/alertas', element: <EntidadAlertasPage /> },
      { path: 'entidades/:entidadId/cambios', element: <EntidadCambiosPage /> },
      { path: 'operaciones', element: <OperacionesMasivasPage /> },
      { path: 'funcionarios', element: <FuncionariosIndexPage /> },
      { path: 'funcionarios/:personaMasterId', element: <FuncionarioPerfilPage /> },
      { path: 'funcionarios/:personaMasterId/historial', element: <FuncionarioHistorialPage /> },
      { path: 'funcionarios/:personaMasterId/academico', element: <FuncionarioAcademicoPage /> },
      { path: 'funcionarios/:personaMasterId/foro', element: <FuncionarioForoPage /> },
      { path: 'funcionarios/:personaMasterId/validar-abogado', element: <FuncionarioValidarAbogadoPage /> },
      { path: 'funcionarios/:personaMasterId/alertas', element: <FuncionarioAlertasPage /> },
      { path: 'funcionarios/:personaMasterId/timeline', element: <FuncionarioTimelinePage /> },
      { path: 'alertas', element: <AlertasIndexPage /> },
      { path: 'jobs', element: <JobsIndexPage /> },
      { path: 'jobs/:jobId', element: <JobDetallePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
