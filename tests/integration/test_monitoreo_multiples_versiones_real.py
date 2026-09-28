"""Test de integracion end-to-end: `CompararDocumentosUseCase` con
persistencia REAL (SQLAlchemy/SQLite) a traves de VARIAS versiones
sucesivas del mismo documento -- exactamente los escenarios que el
cliente pidio explicitamente probar:

    - Multiples versiones del mismo documento (Junio -> Julio -> Agosto
      -> Septiembre).
    - Documento SIN cambios (Julio == Junio).
    - Cambios PARCIALES (Agosto: 1 cargo, 1 nuevo, 1 eliminado).
    - Cambios MASIVOS (Septiembre: >50% de turnover).

Cada "mes" reconstruye `funcionarios_anteriores` a partir de lo
REALMENTE persistido en el mes previo (via `funcionario_a_unificado`),
igual que hace `MonitoreoContinuoService` en produccion -- nunca se le
pasa al caso de uso una lista "de mentira".
"""

from __future__ import annotations

from datetime import date

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
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.rules.convertir_funcionario_unificado import funcionario_a_unificado
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
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

_JUNIO = [
    FuncionarioUnificadoDTO(nombre="Juan", apellido="Perez", cargo="Director Juridico", dependencia="Legal", correo="jp@x.com", telefono="0991111111", area="juridica", score=95.0, fingerprint="JUANPEREZ"),
    FuncionarioUnificadoDTO(nombre="Maria", apellido="Lopez", cargo="Procurador", dependencia="Procuraduria", correo="ml@x.com", telefono="0991111121", area="juridica", score=95.0, fingerprint="MARIALOPEZ"),
    FuncionarioUnificadoDTO(nombre="Pedro", apellido="Diaz", cargo="Director Financiero", dependencia="Finanzas", correo="pd@x.com", telefono="0991111131", area="financiera", score=95.0, fingerprint="PERODIAZ"),
]


def _entidad_y_use_case(sesion):
    entidad_modelo = EntidadModel(nombre="Entidad Timeline", url_transparencia="https://x/timeline", portal_origen="dpe")
    sesion.add(entidad_modelo)
    sesion.flush()
    entidad = Entidad(id=entidad_modelo.id, nombre=entidad_modelo.nombre, url_transparencia=entidad_modelo.url_transparencia, portal_origen="dpe")

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

    caso_uso = CompararDocumentosUseCase(persistencia, alerta_service, oportunidad_service, evento_service, auditoria_service, _RULE_ENGINE)
    return entidad, caso_uso, funcionario_repo, persona_repo, version_repo, alerta_repo


def _documento(sesion, publicacion_id: int, hash_char: str) -> DocumentoTransparencia:
    from govdata.infrastructure.persistence.postgresql.mappers import documento_mapper

    modelo = DocumentoModel(
        publicacion_id=publicacion_id, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
        url_documento=f"https://x/d{publicacion_id}.pdf", estado=EstadoDocumento.DESCARGADO,
        hash_sha256=hash_char * 64, tamano_bytes=10, ruta_almacenamiento="file:///x", version=1,
    )
    sesion.add(modelo)
    sesion.flush()
    return documento_mapper.a_dominio(modelo)


def _snapshot_actual(funcionario_repo, persona_repo, entidad_id: int) -> list[FuncionarioUnificadoDTO]:
    """Igual que `MonitoreoContinuoService._funcionarios_unificados_vigentes`:
    el snapshot "anterior" es lo VIGENTE para la entidad, nunca lo
    asociado a un `documento_id` exacto (que puede haber quedado
    desactualizado si el mes previo no tuvo cambios reales)."""
    funcionarios = funcionario_repo.listar_por_entidad(entidad_id, solo_vigentes=True)
    resultado = []
    for f in funcionarios:
        persona = persona_repo.buscar_por_id(f.persona_id)
        resultado.append(funcionario_a_unificado(f, persona))
    return resultado


def test_ciclo_completo_junio_julio_agosto_septiembre(sesion) -> None:
    entidad, caso_uso, funcionario_repo, persona_repo, version_repo, alerta_repo = _entidad_y_use_case(sesion)

    # -- JUNIO: primera version, todo "nuevo" --------------------------------
    doc_junio = _documento(sesion, publicacion_id=1, hash_char="a")
    resultado_junio = caso_uso.ejecutar(
        entidad, None, doc_junio, [], _JUNIO, mes_publicado_actual=date(2026, 6, 1)
    )
    sesion.flush()
    assert len(resultado_junio.nuevos) == 3
    assert len(version_repo.listar_por_entidad(entidad.id)) == 3

    # -- JULIO: SIN CAMBIOS -- se reconstruye desde lo persistido -----------
    anteriores_julio = _snapshot_actual(funcionario_repo, persona_repo, entidad.id)
    assert len(anteriores_julio) == 3
    doc_julio = _documento(sesion, publicacion_id=2, hash_char="b")
    resultado_julio = caso_uso.ejecutar(
        entidad, doc_junio, doc_julio, anteriores_julio, anteriores_julio,
        mes_publicado_actual=date(2026, 7, 1), mes_publicado_anterior=date(2026, 6, 1),
    )
    sesion.flush()
    assert len(resultado_julio.sin_cambios) == 3
    assert resultado_julio.nuevos == []
    assert resultado_julio.eliminados == []
    # Sin cambios reales -- NO se abren nuevas versiones (nunca sobrescribe sin motivo).
    assert len(version_repo.listar_por_entidad(entidad.id)) == 3

    # -- AGOSTO: CAMBIOS PARCIALES (1 cargo, 1 nuevo, 1 eliminado) -----------
    anteriores_agosto = _snapshot_actual(funcionario_repo, persona_repo, entidad.id)
    actuales_agosto = [
        FuncionarioUnificadoDTO(nombre="Juan", apellido="Perez", cargo="Procurador", dependencia="Procuraduria", correo="jp@x.com", telefono="0991111111", area="juridica", score=95.0, fingerprint="JUANPEREZ"),  # cambio de cargo
        # Maria Lopez (Procurador) -- eliminada
        FuncionarioUnificadoDTO(nombre="Pedro", apellido="Diaz", cargo="Director Financiero", dependencia="Finanzas", correo="pd@x.com", telefono="0991111131", area="financiera", score=95.0, fingerprint="PERODIAZ"),  # sin cambios
        FuncionarioUnificadoDTO(nombre="Ana", apellido="Ruiz", cargo="Abogado", dependencia="Legal", correo="ar@x.com", telefono="0991111141", area="juridica", score=95.0, fingerprint="ANARUIZ"),  # nuevo
    ]
    doc_agosto = _documento(sesion, publicacion_id=3, hash_char="c")
    resultado_agosto = caso_uso.ejecutar(
        entidad, doc_julio, doc_agosto, anteriores_agosto, actuales_agosto,
        mes_publicado_actual=date(2026, 8, 1), mes_publicado_anterior=date(2026, 7, 1),
    )
    sesion.flush()
    assert len(resultado_agosto.nuevos) == 1
    assert len(resultado_agosto.eliminados) == 1
    assert len(resultado_agosto.cambios) == 1
    assert len(resultado_agosto.sin_cambios) == 1
    # Juan Perez ahora tiene 2 versiones (v1 Director Juridico cerrada, v2 Procurador vigente).
    historial_juan = [v for v in version_repo.listar_por_persona(persona_repo.buscar_por_fingerprint_hash(_fingerprint_hash("Juan", "Perez")).id)]
    assert len(historial_juan) == 2
    assert sum(1 for v in historial_juan if v.vigente) == 1

    # -- SEPTIEMBRE: CAMBIO MASIVO (turnover completo) -----------------------
    anteriores_septiembre = _snapshot_actual(funcionario_repo, persona_repo, entidad.id)
    actuales_septiembre = [
        FuncionarioUnificadoDTO(nombre="Carlos", apellido="Nuevo1", cargo="Director Juridico", dependencia="Legal", correo="c1@x.com", telefono="0991111151", area="juridica", score=95.0, fingerprint="CARLOSNUEVO1"),
        FuncionarioUnificadoDTO(nombre="Diana", apellido="Nueva2", cargo="Director Financiero", dependencia="Finanzas", correo="c2@x.com", telefono="0991111161", area="financiera", score=95.0, fingerprint="DIANANUEVA2"),
        FuncionarioUnificadoDTO(nombre="Eva", apellido="Nueva3", cargo="Procurador", dependencia="Procuraduria", correo="c3@x.com", telefono="0991111171", area="juridica", score=95.0, fingerprint="EVANUEVA3"),
    ]
    doc_septiembre = _documento(sesion, publicacion_id=4, hash_char="d")
    resultado_septiembre = caso_uso.ejecutar(
        entidad, doc_agosto, doc_septiembre, anteriores_septiembre, actuales_septiembre,
        mes_publicado_actual=date(2026, 9, 1), mes_publicado_anterior=date(2026, 8, 1),
    )
    sesion.flush()
    assert len(resultado_septiembre.nuevos) == 3
    assert len(resultado_septiembre.eliminados) == 3
    assert resultado_septiembre.estadisticas.porcentaje_cambios == 100.0
    # Cambio masivo -> debe haber generado alertas CAMBIO_MASIVO/CAMBIO_SUPERIOR_30_PORCIENTO.
    from govdata.domain.entities.alerta import TipoAlerta

    tipos_alerta = {a.tipo for a in alerta_repo.listar_por_documento(doc_septiembre.id)}
    assert TipoAlerta.CAMBIO_SUPERIOR_30_PORCIENTO in tipos_alerta or TipoAlerta.CAMBIO_MASIVO in tipos_alerta


def _fingerprint_hash(nombres: str, apellidos: str) -> str:
    from govdata.domain.rules.generador_fingerprint import generar_fingerprint

    _, hash_ = generar_fingerprint(nombres, apellidos)
    return hash_
