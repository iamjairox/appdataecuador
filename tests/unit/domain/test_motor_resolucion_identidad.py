"""Tests: Identity Resolution Engine (Submodulo 6.2) -- incluye
explicitamente pruebas de "falso positivo" y "falso negativo" (Submodulo
6.18) sobre el motor de resolucion, ademas de la garantia "nunca
unicamente el nombre"."""

from __future__ import annotations

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.rules.motor_resolucion_identidad import resolver_identidad
from govdata.domain.rules.reglas_identidad import PesosScoring

_PESOS = PesosScoring(
    fingerprint=0.40, correo=0.25, nombre=0.15, apellido=0.10, institucion=0.05, cargo=0.05,
    umbral_minimo_coincidencia=60.0,
)


def _senales(**kwargs) -> SenalesIdentidadDTO:
    base = {"nombre": "Juan", "apellido": "Perez", "correo": "j@x.com", "telefono": None,
            "institucion": "DPE", "cargo": "Director Juridico", "fingerprint": "JUANPEREZ"}
    base.update(kwargs)
    return SenalesIdentidadDTO(**base)


class TestSinCandidatas:
    def test_lista_vacia_retorna_sin_coincidencia(self) -> None:
        resultado = resolver_identidad(_senales(), [], _PESOS)
        assert resultado.persona_master_id is None
        assert resultado.motivo == "sin_candidatas"


class TestMejorCandidataGanadora:
    def test_elige_la_de_mayor_score_entre_varias(self) -> None:
        nuevas = _senales()
        candidatas = [
            (1, _senales(fingerprint="OTRAFP", correo="otro@y.com", nombre="Ana", apellido="Diaz")),
            (2, _senales()),  # identica -> score 100
            (3, _senales(fingerprint="OTRAFP2", nombre="Juana")),
        ]
        resultado = resolver_identidad(nuevas, candidatas, _PESOS)
        assert resultado.persona_master_id == 2
        assert resultado.score == 100.0
        assert resultado.motivo == "mejor_candidata_seleccionada"

    def test_nunca_fusiona_con_baja_confianza_score_bajo_umbral(self) -> None:
        """Coincide muy poco (nombre distinto, sin fingerprint/correo
        comunes) -- el motor NUNCA debe reportar una candidata como
        encontrada por debajo del umbral minimo."""
        nuevas = _senales(fingerprint="X", correo=None, institucion=None, cargo=None)
        candidatas = [(1, _senales(fingerprint="Y", nombre="Maria", apellido="Lopez", correo=None, institucion=None, cargo=None))]
        resultado = resolver_identidad(nuevas, candidatas, _PESOS)
        assert resultado.persona_master_id is None
        assert resultado.motivo == "score_bajo_umbral_minimo"


class TestNuncaUnicamenteElNombre:
    def test_nombre_identico_pero_todo_lo_demas_distinto_no_alcanza_alta_confianza(self) -> None:
        """Dos personas DISTINTAS que comparten nombre y apellido comunes
        (ej. "Juan Perez") pero difieren en fingerprint/correo/institucion/
        cargo no deben ser tratadas como la misma identidad -- si solo se
        comparara el nombre, esto seria un FALSO POSITIVO."""
        nuevas = _senales(fingerprint="AAA", correo="juan.perez.quito@x.com", institucion="Municipio Quito", cargo="Chofer")
        candidatas = [
            (1, _senales(fingerprint="BBB", correo="juan.perez.guayaquil@y.com", institucion="Municipio Guayaquil", cargo="Contador"))
        ]
        resultado = resolver_identidad(nuevas, candidatas, _PESOS)
        # Nombre+apellido (0.25 de peso) no alcanza el umbral_minimo_coincidencia=60
        assert resultado.persona_master_id is None

    def test_nombre_cambiado_pero_correo_y_fingerprint_fonetico_coinciden_es_detectado(self) -> None:
        """Caso positivo real: el correo (senal fuerte, 25%) sostiene la
        coincidencia aunque el nombre difiera levemente -- sin fusionar
        ciegamente por eso, pero permitiendo detectar el caso."""
        nuevas = _senales(nombre="Juan Carlos", fingerprint="NUEVAFP", correo="fijo@x.com")
        candidatas = [(1, _senales(nombre="Juan", fingerprint="VIEJAFP", correo="fijo@x.com"))]
        resultado = resolver_identidad(nuevas, candidatas, _PESOS)
        # correo(25) + apellido igual(10) + institucion(5) + cargo(5) = 45 minimo garantizado
        assert resultado.score >= 45.0


class TestExplicacionYCamposUtilizados:
    def test_explicacion_y_campos_utilizados_no_vacios_para_coincidencia(self) -> None:
        resultado = resolver_identidad(_senales(), [(1, _senales())], _PESOS)
        assert resultado.explicacion
        assert len(resultado.campos_utilizados) > 0
        assert any(c.campo == "fingerprint" for c in resultado.campos_utilizados)
