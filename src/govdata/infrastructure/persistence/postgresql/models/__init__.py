"""Registro central de modelos ORM.

Importar este paquete garantiza que todos los modelos queden registrados
en `Base.metadata` antes de llamar `Base.metadata.create_all(...)` o de
ejecutar Alembic autogenerate. Sin este import explicito, un modelo que
nadie mas importa directamente podria quedar fuera del metadata.
"""

from govdata.infrastructure.persistence.postgresql.models.alerta_academica_model import (
    AlertaAcademicaModel,
)
from govdata.infrastructure.persistence.postgresql.models.alerta_foro_model import AlertaForoModel
from govdata.infrastructure.persistence.postgresql.models.alerta_model import AlertaModel
from govdata.infrastructure.persistence.postgresql.models.alerta_perfil_model import (
    AlertaPerfilModel,
)
from govdata.infrastructure.persistence.postgresql.models.atributo_trazable_model import (
    AtributoTrazableModel,
)
from govdata.infrastructure.persistence.postgresql.models.auditoria_comparacion_model import (
    AuditoriaComparacionModel,
)
from govdata.infrastructure.persistence.postgresql.models.auditoria_etapa_model import (
    AuditoriaEtapaModel,
)
from govdata.infrastructure.persistence.postgresql.models.base import Base
from govdata.infrastructure.persistence.postgresql.models.caso_revision_identidad_model import (
    CasoRevisionIdentidadModel,
)
from govdata.infrastructure.persistence.postgresql.models.consulta_foro_model import (
    ConsultaForoModel,
)
from govdata.infrastructure.persistence.postgresql.models.consulta_fuente_log_model import (
    ConsultaFuenteLogModel,
)
from govdata.infrastructure.persistence.postgresql.models.consulta_senescyt_model import (
    ConsultaSenescytModel,
)
from govdata.infrastructure.persistence.postgresql.models.descarga_model import DescargaModel
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.ejecucion_model import EjecucionModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.evento_academico_model import (
    EventoAcademicoModel,
)
from govdata.infrastructure.persistence.postgresql.models.evento_foro_model import EventoForoModel
from govdata.infrastructure.persistence.postgresql.models.evento_model import EventoModel
from govdata.infrastructure.persistence.postgresql.models.evento_perfil_model import (
    EventoPerfilModel,
)
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.historial_academico_model import (
    HistorialAcademicoModel,
)
from govdata.infrastructure.persistence.postgresql.models.historial_cambios_model import (
    HistorialCambiosModel,
)
from govdata.infrastructure.persistence.postgresql.models.historial_foro_model import (
    HistorialForoModel,
)
from govdata.infrastructure.persistence.postgresql.models.job_model import JobModel
from govdata.infrastructure.persistence.postgresql.models.job_step_model import JobStepModel
from govdata.infrastructure.persistence.postgresql.models.manifest_model import ManifestModel
from govdata.infrastructure.persistence.postgresql.models.oportunidad_comercial_model import (
    OportunidadComercialModel,
)
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import (
    PersonaMasterModel,
)
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.models.publicacion_model import PublicacionModel
from govdata.infrastructure.persistence.postgresql.models.registro_foro_model import (
    RegistroForoModel,
)
from govdata.infrastructure.persistence.postgresql.models.registro_foro_version_model import (
    RegistroForoVersionModel,
)
from govdata.infrastructure.persistence.postgresql.models.registro_fuente_model import (
    RegistroFuenteModel,
)
from govdata.infrastructure.persistence.postgresql.models.titulo_academico_model import (
    TituloAcademicoModel,
)
from govdata.infrastructure.persistence.postgresql.models.titulo_version_academica_model import (
    TituloVersionAcademicaModel,
)
from govdata.infrastructure.persistence.postgresql.models.trabajo_orquestador_model import (
    TrabajoOrquestadorModel,
)
from govdata.infrastructure.persistence.postgresql.models.verificacion_model import (
    VerificacionModel,
)
from govdata.infrastructure.persistence.postgresql.models.version_funcionario_model import (
    VersionFuncionarioModel,
)

__all__ = [
    "AlertaAcademicaModel",
    "AlertaForoModel",
    "AlertaModel",
    "AlertaPerfilModel",
    "AtributoTrazableModel",
    "AuditoriaComparacionModel",
    "AuditoriaEtapaModel",
    "Base",
    "CasoRevisionIdentidadModel",
    "ConsultaForoModel",
    "ConsultaFuenteLogModel",
    "ConsultaSenescytModel",
    "DescargaModel",
    "DocumentoModel",
    "EjecucionModel",
    "EntidadModel",
    "EventoAcademicoModel",
    "EventoForoModel",
    "EventoModel",
    "EventoPerfilModel",
    "FuncionarioModel",
    "HistorialAcademicoModel",
    "HistorialCambiosModel",
    "HistorialForoModel",
    "JobModel",
    "JobStepModel",
    "ManifestModel",
    "OportunidadComercialModel",
    "PersonaMasterModel",
    "PersonaModel",
    "PublicacionModel",
    "RegistroForoModel",
    "RegistroForoVersionModel",
    "RegistroFuenteModel",
    "TituloAcademicoModel",
    "TituloVersionAcademicaModel",
    "TrabajoOrquestadorModel",
    "VerificacionModel",
    "VersionFuncionarioModel",
]
