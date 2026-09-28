"""Tests: Normalizador del Foro -- Submodulo 8.3."""

from __future__ import annotations

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.normalizador_foro import (
    interpretar_estado_foro,
    normalizar_etiqueta_campo,
    normalizar_registro_foro,
)
from govdata.domain.rules.reglas_foro import (
    CatalogoCamposForo,
    ReglasCacheForo,
    ReglasCircuitoForo,
    RuleEngineForo,
)
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo

_CATALOGO = CatalogoCamposForo(
    campo_por_etiqueta={"NO REGISTRO": "registro", "PROVINCIA": "provincia", "ESTADO": "estado"}
)
_REGLAS = RuleEngineForo(campos=_CATALOGO, cache=ReglasCacheForo(), circuito=ReglasCircuitoForo())


class TestNormalizarEtiquetaCampo:
    def test_no_punto_registro_resuelve_a_registro(self) -> None:
        assert normalizar_etiqueta_campo("No. Registro", _CATALOGO) == "registro"

    def test_con_dos_puntos_al_final(self) -> None:
        assert normalizar_etiqueta_campo("Provincia:", _CATALOGO) == "provincia"

    def test_etiqueta_desconocida_retorna_none(self) -> None:
        assert normalizar_etiqueta_campo("Direccion", _CATALOGO) is None


class TestInterpretarEstadoForo:
    def test_vigente(self) -> None:
        assert interpretar_estado_foro("VIGENTE") == EstadoRegistroForo.VIGENTE

    def test_activo_es_vigente(self) -> None:
        assert interpretar_estado_foro("Activo") == EstadoRegistroForo.VIGENTE

    def test_suspendido(self) -> None:
        assert interpretar_estado_foro("Suspendido") == EstadoRegistroForo.SUSPENDIDO

    def test_none_es_desconocido(self) -> None:
        assert interpretar_estado_foro(None) == EstadoRegistroForo.DESCONOCIDO

    def test_texto_no_reconocido_es_desconocido(self) -> None:
        assert interpretar_estado_foro("En Tramite") == EstadoRegistroForo.DESCONOCIDO


class TestNormalizarRegistroForo:
    def test_normaliza_texto_libre_pero_no_identificadores(self) -> None:
        dto = RegistroForoDTO(
            nombre_completo="juan perez", provincia="pichincha", estado="vigente",
            registro="R-001", cedula=" 0999999999 ",
        )
        normalizado = normalizar_registro_foro(dto, _REGLAS)
        assert normalizado.nombre_completo == "JUAN PEREZ"
        assert normalizado.provincia == "PICHINCHA"
        assert normalizado.estado == "VIGENTE"
        assert normalizado.registro == "R-001"  # nunca se normaliza (identificador oficial)
        assert normalizado.cedula == "0999999999"

    def test_campos_none_se_mantienen_none(self) -> None:
        dto = RegistroForoDTO()
        normalizado = normalizar_registro_foro(dto, _REGLAS)
        assert normalizado == RegistroForoDTO()
