"""Test de concurrencia: `CompararDocumentosUseCase` corriendo en
paralelo para MULTIPLES entidades distintas, cada hilo con su propia
`Session` SQLAlchemy (nunca compartida entre hilos) contra el mismo
archivo SQLite -- mismo patron que `test_concurrencia_extraccion.py`
(Modulo 4): archivo real (no ":memory:") porque cada hilo necesita su
propia conexion DBAPI fisica."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from sqlalchemy.orm import sessionmaker

from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import EstadoDocumento, TipoArchivo
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_comparacion_repository import (
    SqlAlchemyAuditoriaComparacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_repository import (
    SqlAlchemyEventoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_oportunidad_comercial_repository import (
    SqlAlchemyOportunidadComercialRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_version_funcionario_repository import (
    SqlAlchemyVersionFuncionarioRepository,
)

_RULE_ENGINE = cargar_rule_engine()
_FUNCIONARIOS_POR_ENTIDAD = 20


def _funcionarios(prefijo: str) -> list[FuncionarioUnificadoDTO]:
    return [
        FuncionarioUnificadoDTO(
            nombre=f"Persona{prefijo}{i}", apellido=f"Apellido{prefijo}{i}", cargo="Director Juridico",
            dependencia="Legal", correo=f"{prefijo}{i}@x.com", telefono=f"099{i:07d}", area="juridica",
            score=95.0, fingerprint=f"FP{prefijo}{i}",
        )
        for i in range(_FUNCIONARIOS_POR_ENTIDAD)
    ]


def test_multiples_entidades_en_paralelo_cada_una_con_su_propia_sesion(sqlite_engine_multihilo) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    cantidad_hilos = 6

    def _tarea(indice: int) -> int:
        sesion = Factory()
        try:
            entidad_modelo = EntidadModel(
                nombre=f"Entidad Concurrente M5 {indice}", url_transparencia=f"https://x/concurrente5/{indice}",
                portal_origen="dpe",
            )
            sesion.add(entidad_modelo)
            sesion.flush()
            documento_modelo = DocumentoModel(
                publicacion_id=indice + 1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
                url_documento=f"https://x/concurrente5/{indice}", estado=EstadoDocumento.DESCARGADO,
                hash_sha256=f"{indice:064d}", tamano_bytes=10, ruta_almacenamiento="file:///x", version=1,
            )
            sesion.add(documento_modelo)
            sesion.flush()

            from govdata.infrastructure.persistence.postgresql.mappers import (
                documento_mapper,
                entidad_mapper,
            )

            entidad = entidad_mapper.a_dominio(entidad_modelo)
            documento = documento_mapper.a_dominio(documento_modelo)

            persona_repo = SqlAlchemyPersonaRepository(sesion)
            funcionario_repo = SqlAlchemyFuncionarioRepository(sesion)
            version_repo = SqlAlchemyVersionFuncionarioRepository(sesion)
            alerta_repo = SqlAlchemyAlertaRepository(sesion)
            evento_repo = SqlAlchemyEventoRepository(sesion)
            auditoria_repo = SqlAlchemyAuditoriaComparacionRepository(sesion)
            oportunidad_repo = SqlAlchemyOportunidadComercialRepository(sesion)

            historial = HistorialService(version_repo)
            persistencia = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial)
            alerta_service = AlertaService(alerta_repo, _RULE_ENGINE.criticidad)
            oportunidad_service = OportunidadComercialService(oportunidad_repo, _RULE_ENGINE.criticidad)
            evento_service = EventoService(evento_repo)
            auditoria_service = AuditoriaComparacionService(auditoria_repo)
            caso_uso = CompararDocumentosUseCase(
                persistencia, alerta_service, oportunidad_service, evento_service, auditoria_service, _RULE_ENGINE
            )

            actuales = _funcionarios(f"H{indice}")
            resultado = caso_uso.ejecutar(entidad, None, documento, [], actuales, mes_publicado_actual=date(2026, 6, 1))
            sesion.commit()
            assert len(resultado.nuevos) == _FUNCIONARIOS_POR_ENTIDAD
            return len(resultado.nuevos)
        finally:
            sesion.close()

    with ThreadPoolExecutor(max_workers=cantidad_hilos) as executor:
        futuros = [executor.submit(_tarea, i) for i in range(cantidad_hilos)]
        resultados = [f.result() for f in as_completed(futuros)]

    assert resultados == [_FUNCIONARIOS_POR_ENTIDAD] * cantidad_hilos

    # Verificacion final: cada hilo persistio sus propios funcionarios sin
    # perdida ni duplicacion por condicion de carrera entre sesiones.
    sesion_verificacion = Factory()
    try:
        total = sesion_verificacion.query(FuncionarioModel).count()
        assert total == cantidad_hilos * _FUNCIONARIOS_POR_ENTIDAD
    finally:
        sesion_verificacion.close()
