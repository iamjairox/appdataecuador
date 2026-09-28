"""Tests: Normalizador Academico (Submodulo 7.4)."""

from __future__ import annotations

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.domain.rules.normalizador_academico import (
    interpretar_estado_registro,
    normalizar_nivel,
    normalizar_persona_academica,
    normalizar_titulo,
    normalizar_universidad,
)
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico

_REGLAS = cargar_rule_engine_academico()


class TestNormalizarTitulo:
    def test_abreviatura_conocida_resuelve_a_forma_canonica(self) -> None:
        assert normalizar_titulo("Ing. Sistemas", _REGLAS) == "INGENIERO EN SISTEMAS"

    def test_valor_sin_entrada_en_catalogo_solo_se_normaliza(self) -> None:
        assert normalizar_titulo("Arquitecto", _REGLAS) == "ARQUITECTO"


class TestNormalizarUniversidad:
    def test_universidad_sin_abreviatura_solo_mayusculas(self) -> None:
        assert normalizar_universidad("Universidad Central", _REGLAS) == "UNIVERSIDAD CENTRAL"

    def test_abreviatura_conocida(self) -> None:
        assert normalizar_universidad("PUCE", _REGLAS) == "PONTIFICIA UNIVERSIDAD CATOLICA DEL ECUADOR"


class TestNormalizarNivel:
    def test_lic_resuelve_a_licenciado(self) -> None:
        assert normalizar_titulo("Lic.", _REGLAS) == "LICENCIADO"

    def test_pregrado_resuelve_a_tercer_nivel(self) -> None:
        assert normalizar_nivel("Pregrado", _REGLAS) == "TERCER NIVEL"


class TestNormalizarPersonaAcademica:
    def test_normaliza_titulo_nivel_institucion(self) -> None:
        dto = PersonaAcademicaDTO(titulo="Ing. Sistemas", nivel="Pregrado", institucion="Universidad Central")
        resultado = normalizar_persona_academica(dto, _REGLAS)
        assert resultado.titulo == "INGENIERO EN SISTEMAS"
        assert resultado.nivel == "TERCER NIVEL"
        assert resultado.institucion == "UNIVERSIDAD CENTRAL"

    def test_numero_registro_nunca_se_normaliza(self) -> None:
        dto = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="AB-123-xyz")
        resultado = normalizar_persona_academica(dto, _REGLAS)
        assert resultado.numero_registro == "AB-123-xyz"

    def test_campos_opcionales_none_no_fallan(self) -> None:
        dto = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE")
        resultado = normalizar_persona_academica(dto, _REGLAS)
        assert resultado.estado is None
        assert resultado.modalidad is None


class TestInterpretarEstadoRegistro:
    def test_vigente(self) -> None:
        assert interpretar_estado_registro("VIGENTE") == EstadoRegistroAcademico.VIGENTE

    def test_suspendido(self) -> None:
        assert interpretar_estado_registro("Suspendido") == EstadoRegistroAcademico.SUSPENDIDO

    def test_anulado(self) -> None:
        assert interpretar_estado_registro("anulado") == EstadoRegistroAcademico.ANULADO

    def test_desconocido_para_texto_no_reconocido(self) -> None:
        assert interpretar_estado_registro("EN TRAMITE") == EstadoRegistroAcademico.DESCONOCIDO

    def test_desconocido_para_none(self) -> None:
        assert interpretar_estado_registro(None) == EstadoRegistroAcademico.DESCONOCIDO
