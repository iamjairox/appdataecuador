"""Tests: Comparador Foro -- Submodulo 8.5."""

from __future__ import annotations

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.comparador_foro import comparar_registros
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo


def _registro(**kwargs) -> RegistroForoDTO:
    base = {"nombre_completo": "Juan Perez", "registro": "R1", "provincia": "Pichincha", "estado": "Vigente"}
    base.update(kwargs)
    return RegistroForoDTO(**base)


class TestSinCambios:
    def test_registros_identicos_no_generan_diferencia_de_cambio(self) -> None:
        r = _registro()
        diffs = comparar_registros([r], [r])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.SIN_CAMBIOS
        assert not diffs[0].es_cambio


class TestNuevoYEliminado:
    def test_registro_nuevo(self) -> None:
        diffs = comparar_registros([], [_registro()])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.DATO_NUEVO
        assert diffs[0].datos_anteriores is None

    def test_registro_eliminado(self) -> None:
        diffs = comparar_registros([_registro()], [])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.DATO_ELIMINADO
        assert diffs[0].datos_actuales is None


class TestCambiosDedicados:
    def test_cambio_estado(self) -> None:
        diffs = comparar_registros([_registro(estado="Vigente")], [_registro(estado="Suspendido")])
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_ESTADO

    def test_cambio_provincia(self) -> None:
        diffs = comparar_registros([_registro(provincia="Pichincha")], [_registro(provincia="Guayas")])
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_PROVINCIA

    def test_cambio_registro_via_respaldo(self) -> None:
        anterior = _registro(registro=None)
        actual = _registro(registro="R99")
        diffs = comparar_registros([anterior], [actual])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_REGISTRO
        assert diffs[0].clave_registro_anterior is not None


class TestCambioDatoCatchAll:
    def test_cambio_de_nombre_sin_categoria_dedicada_cae_en_cambio_dato(self) -> None:
        diffs = comparar_registros(
            [_registro(nombre_completo="Juan Perez")], [_registro(nombre_completo="Juan A. Perez")]
        )
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_DATO

    def test_multiples_campos_cambiados_cae_en_cambio_dato(self) -> None:
        anterior = _registro(provincia="Pichincha", estado="Vigente")
        actual = _registro(provincia="Guayas", estado="Suspendido")
        diffs = comparar_registros([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_DATO
        assert len(diffs[0].campos_modificados) == 2


class TestInsensibleAFormato:
    def test_diferencia_solo_de_mayusculas_no_genera_cambio(self) -> None:
        anterior = _registro(estado="vigente", provincia="pichincha")
        actual = _registro(estado="VIGENTE", provincia="PICHINCHA")
        diffs = comparar_registros([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambioForo.SIN_CAMBIOS


class TestEmparejamientoDeRespaldo:
    """Cuando el `registro` broto (o cambio), el respaldo
    (nombre_completo+provincia+cedula) debe emparejar el registro
    ANTERIOR con el ACTUAL -- nunca debe verse como eliminado+nuevo."""

    def test_broto_numero_de_registro_preserva_continuidad(self) -> None:
        anterior = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha", cedula="0999999999", registro=None)
        actual = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha", cedula="0999999999", registro="R-001")
        diffs = comparar_registros([anterior], [actual])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.CAMBIO_REGISTRO
        assert diffs[0].clave_registro_anterior != diffs[0].clave_registro

    def test_sin_coincidencia_de_respaldo_es_eliminado_mas_nuevo(self) -> None:
        anterior = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha", registro=None)
        actual = RegistroForoDTO(nombre_completo="Ana Gomez", provincia="Guayas", registro="R-002")
        diffs = comparar_registros([anterior], [actual])
        tipos = {d.tipo_cambio for d in diffs}
        assert tipos == {TipoCambioForo.DATO_ELIMINADO, TipoCambioForo.DATO_NUEVO}
