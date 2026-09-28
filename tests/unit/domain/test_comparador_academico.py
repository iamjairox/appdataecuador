"""Tests: Comparador Academico (Submodulo 7.7) -- las 9 categorias
explicitas de la especificacion."""

from __future__ import annotations

from datetime import date

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.comparador_academico import comparar_titulos
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico


def _dto(**kwargs) -> PersonaAcademicaDTO:
    base = {
        "titulo": "ABOGADO", "nivel": "TERCER NIVEL", "institucion": "UCE", "numero_registro": "REG-1",
        "estado": "VIGENTE", "modalidad": "PRESENCIAL",
    }
    base.update(kwargs)
    return PersonaAcademicaDTO(**base)


class TestTituloNuevoYEliminado:
    def test_solo_en_actuales_es_nuevo(self) -> None:
        diffs = comparar_titulos([], [_dto()])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioAcademico.TITULO_NUEVO
        assert diffs[0].datos_actuales is not None

    def test_solo_en_anteriores_es_eliminado(self) -> None:
        diffs = comparar_titulos([_dto()], [])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO
        assert diffs[0].datos_anteriores is not None


class TestSinCambios:
    def test_identico_en_ambos_lados(self) -> None:
        diffs = comparar_titulos([_dto()], [_dto()])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.SIN_CAMBIOS
        assert diffs[0].campos_modificados == ()

    def test_estado_reconstruido_desde_enum_minusculas_no_genera_falso_cambio(self) -> None:
        """Regresion: `TituloAcademico.estado` (VO, minusculas) vueltos a
        `PersonaAcademicaDTO` no deben compararse case-sensitive contra
        una respuesta fresca en MAYUSCULAS."""
        anterior = _dto(estado="vigente")
        actual = _dto(estado="VIGENTE")
        diffs = comparar_titulos([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.SIN_CAMBIOS


class TestCambiosDeUnSoloCampo:
    def test_cambio_de_universidad(self) -> None:
        diffs = comparar_titulos([_dto(institucion="UCE")], [_dto(institucion="PUCE")])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_UNIVERSIDAD

    def test_cambio_de_nivel(self) -> None:
        diffs = comparar_titulos([_dto(nivel="TERCER NIVEL")], [_dto(nivel="CUARTO NIVEL")])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_NIVEL

    def test_cambio_de_modalidad(self) -> None:
        diffs = comparar_titulos([_dto(modalidad="PRESENCIAL")], [_dto(modalidad="VIRTUAL")])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_MODALIDAD

    def test_cambio_de_registro(self) -> None:
        """Caso real: SENESCYT reporta el titulo primero SIN numero de
        registro (tramite en curso, se empareja por hash titulo+nivel+
        institucion) y luego CON numero de registro asignado -- mismo
        titulo, el campo numero_registro cambio."""
        anterior = _dto(numero_registro=None)
        actual = _dto(numero_registro="REG-NUEVO")
        diffs = comparar_titulos([anterior], [actual])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_REGISTRO

    def test_cambio_de_estado(self) -> None:
        diffs = comparar_titulos([_dto(estado="VIGENTE")], [_dto(estado="SUSPENDIDO")])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_ESTADO

    def test_cambio_de_fecha(self) -> None:
        diffs = comparar_titulos(
            [_dto(fecha_registro=date(2020, 1, 1))], [_dto(fecha_registro=date(2021, 1, 1))]
        )
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_FECHA


class TestCambioMultiple:
    def test_dos_campos_modificados(self) -> None:
        anterior = _dto(nivel="TERCER NIVEL", institucion="UCE")
        actual = _dto(nivel="CUARTO NIVEL", institucion="PUCE")
        diffs = comparar_titulos([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_MULTIPLE
        campos = {c.campo for c in diffs[0].campos_modificados}
        assert campos == {"nivel", "institucion"}

    def test_campo_secundario_unico_tambien_es_multiple(self) -> None:
        """`observaciones` no tiene categoria propia en la especificacion
        (solo 9 categorias explicitas) -- se agrupa en CAMBIO_MULTIPLE,
        nunca se pierde el dato (sigue en campos_modificados)."""
        diffs = comparar_titulos([_dto(observaciones="a")], [_dto(observaciones="b")])
        assert diffs[0].tipo_cambio == TipoCambioAcademico.CAMBIO_MULTIPLE
        assert diffs[0].campos_modificados[0].campo == "observaciones"


class TestEmparejamientoDeRespaldo:
    def test_clave_titulo_anterior_se_registra_cuando_broto_el_registro(self) -> None:
        anterior = _dto(numero_registro=None)
        actual = _dto(numero_registro="REG-NUEVO")
        diffs = comparar_titulos([anterior], [actual])
        assert len(diffs) == 1
        assert diffs[0].clave_titulo_anterior is not None
        assert diffs[0].clave_titulo_anterior != diffs[0].clave_titulo

    def test_sin_coincidencia_de_respaldo_es_eliminado_y_nuevo(self) -> None:
        """Titulos genuinamente distintos (ni clave primaria ni de
        respaldo coinciden) nunca se fusionan."""
        anterior = _dto(titulo="ABOGADO", institucion="UCE", nivel="TERCER NIVEL", numero_registro=None)
        actual = _dto(titulo="MEDICO", institucion="PUCE", nivel="CUARTO NIVEL", numero_registro=None)
        diffs = comparar_titulos([anterior], [actual])
        tipos = {d.tipo_cambio for d in diffs}
        assert tipos == {TipoCambioAcademico.TITULO_ELIMINADO, TipoCambioAcademico.TITULO_NUEVO}


class TestEmparejamientoPorNumeroRegistro:
    def test_mismo_numero_registro_diferente_texto_de_titulo_es_el_mismo_titulo(self) -> None:
        """El numero de registro es la clave fuerte -- una correccion de
        formato del nombre del titulo NO se trata como titulo nuevo+eliminado."""
        anterior = _dto(titulo="ABOGADO", numero_registro="REG-1")
        actual = _dto(titulo="ABOGADO DE LOS TRIBUNALES", numero_registro="REG-1")
        diffs = comparar_titulos([anterior], [actual])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio != TipoCambioAcademico.TITULO_NUEVO
        assert diffs[0].tipo_cambio != TipoCambioAcademico.TITULO_ELIMINADO


class TestListaCompletaConVariosCambios:
    def test_lote_mixto_produce_todas_las_categorias(self) -> None:
        anteriores = [
            _dto(numero_registro="SINCAMBIO"),
            _dto(numero_registro="ELIMINADO", titulo="INGENIERO"),
            _dto(numero_registro="CAMBIOESTADO", estado="VIGENTE"),
        ]
        actuales = [
            _dto(numero_registro="SINCAMBIO"),
            _dto(numero_registro="CAMBIOESTADO", estado="SUSPENDIDO"),
            _dto(numero_registro="NUEVO", titulo="MEDICO"),
        ]
        diffs = comparar_titulos(anteriores, actuales)
        tipos = sorted(d.tipo_cambio.value for d in diffs)
        assert tipos == sorted(
            [
                TipoCambioAcademico.SIN_CAMBIOS.value,
                TipoCambioAcademico.TITULO_ELIMINADO.value,
                TipoCambioAcademico.CAMBIO_ESTADO.value,
                TipoCambioAcademico.TITULO_NUEVO.value,
            ]
        )
