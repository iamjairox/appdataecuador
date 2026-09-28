"""Tests: Motor de Comparacion (Submodulo 5.1) -- los 11 tipos de cambio
exigidos explicitamente, mas el emparejamiento primario por fingerprint y
el de respaldo por correo (nunca solo por nombre)."""

from __future__ import annotations

from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.domain.rules.motor_comparacion import calcular_estadisticas, comparar_funcionarios
from govdata.domain.value_objects.tipo_cambio import TipoCambio


def _f(
    fp: str,
    nombre: str = "Juan",
    apellido: str = "Perez",
    cargo: str = "Director Juridico",
    dependencia: str = "Legal",
    correo: str | None = "j@x.com",
    telefono: str | None = "0999",
    area: str = "juridica",
) -> FuncionarioUnificadoDTO:
    return FuncionarioUnificadoDTO(
        nombre=nombre, apellido=apellido, cargo=cargo, dependencia=dependencia,
        correo=correo, telefono=telefono, area=area, score=95.0, fingerprint=fp,
    )


class TestFuncionarioNuevoYEliminado:
    def test_funcionario_solo_en_actuales_es_nuevo(self) -> None:
        diffs = comparar_funcionarios([], [_f("A")])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO
        assert diffs[0].fingerprint == "A"

    def test_funcionario_solo_en_anteriores_es_eliminado(self) -> None:
        diffs = comparar_funcionarios([_f("A")], [])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO


class TestSinCambios:
    def test_funcionario_identico_en_ambos_lados(self) -> None:
        diffs = comparar_funcionarios([_f("A")], [_f("A")])
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambio.SIN_CAMBIOS
        assert diffs[0].campos_modificados == ()


class TestCambiosDeUnSoloCampo:
    def test_cambio_de_cargo(self) -> None:
        diffs = comparar_funcionarios([_f("A", cargo="Asesor Juridico")], [_f("A", cargo="Director Juridico")])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_CARGO
        assert diffs[0].campos_modificados[0].campo == "cargo"
        assert diffs[0].campos_modificados[0].valor_anterior == "Asesor Juridico"
        assert diffs[0].campos_modificados[0].valor_nuevo == "Director Juridico"

    def test_cambio_de_dependencia(self) -> None:
        diffs = comparar_funcionarios([_f("A", dependencia="Legal")], [_f("A", dependencia="Procuraduria")])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_DEPENDENCIA

    def test_cambio_de_correo(self) -> None:
        diffs = comparar_funcionarios([_f("A", correo="a@x.com")], [_f("A", correo="b@x.com")])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_CORREO

    def test_cambio_de_telefono(self) -> None:
        diffs = comparar_funcionarios([_f("A", telefono="0991")], [_f("A", telefono="0992")])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_TELEFONO

    def test_cambio_de_area(self) -> None:
        diffs = comparar_funcionarios([_f("A", area="juridica")], [_f("A", area="financiera")])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_AREA


class TestCambioDeNombreAndApellido:
    def test_cambio_de_nombre_detectado_via_correo(self) -> None:
        """El fingerprint SIEMPRE cambia si el nombre cambia (se deriva de
        el) -- solo se detecta como CAMBIO_NOMBRE (y no como
        eliminado+nuevo) porque el correo permite el emparejamiento de
        respaldo. Es la prueba de que la comparacion NUNCA usa solo el
        nombre como clave."""
        anteriores = [_f("FPVIEJO", nombre="Juan", correo="fijo@x.com")]
        actuales = [_f("FPNUEVO", nombre="Juan Carlos", correo="fijo@x.com")]
        diffs = comparar_funcionarios(anteriores, actuales)
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_NOMBRE

    def test_cambio_de_apellido_detectado_via_correo(self) -> None:
        anteriores = [_f("FPVIEJO", apellido="Perez", correo="fijo@x.com")]
        actuales = [_f("FPNUEVO", apellido="Perez Gomez", correo="fijo@x.com")]
        diffs = comparar_funcionarios(anteriores, actuales)
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_APELLIDO

    def test_sin_correo_en_comun_nombre_cambiado_es_eliminado_y_nuevo(self) -> None:
        """Sin una señal de respaldo (correo), un cambio de nombre real es
        indistinguible de una salida+un ingreso -- limitacion documentada,
        no un bug: nunca se asume identidad solo por similitud de nombre."""
        anteriores = [_f("FPVIEJO", nombre="Juan", correo=None)]
        actuales = [_f("FPNUEVO", nombre="Juan Carlos", correo=None)]
        diffs = comparar_funcionarios(anteriores, actuales)
        tipos = {d.tipo_cambio for d in diffs}
        assert tipos == {TipoCambio.FUNCIONARIO_ELIMINADO, TipoCambio.FUNCIONARIO_NUEVO}


class TestCambioMultiple:
    def test_dos_o_mas_campos_cambiados_es_cambio_multiple(self) -> None:
        anterior = _f("A", cargo="Asesor Juridico", dependencia="Legal")
        actual = _f("A", cargo="Director Juridico", dependencia="Procuraduria")
        diffs = comparar_funcionarios([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambio.CAMBIO_MULTIPLE
        campos = {c.campo for c in diffs[0].campos_modificados}
        assert campos == {"cargo", "dependencia"}


class TestNoComparaScore:
    def test_diferencia_de_score_no_genera_cambio(self) -> None:
        anterior = FuncionarioUnificadoDTO(
            nombre="Juan", apellido="Perez", cargo="Director Juridico", dependencia="Legal",
            correo="j@x.com", telefono="0999", area="juridica", score=80.0, fingerprint="A",
        )
        actual = FuncionarioUnificadoDTO(
            nombre="Juan", apellido="Perez", cargo="Director Juridico", dependencia="Legal",
            correo="j@x.com", telefono="0999", area="juridica", score=99.0, fingerprint="A",
        )
        diffs = comparar_funcionarios([anterior], [actual])
        assert diffs[0].tipo_cambio == TipoCambio.SIN_CAMBIOS


class TestListaCompletaConVariosCambios:
    def test_lote_mixto_produce_todas_las_categorias(self) -> None:
        anteriores = [
            _f("SINCAMBIO", correo="sc@x.com"),
            _f("ELIMINADO", nombre="Maria", correo="me@x.com"),
            _f("CAMBIOCARGO", nombre="Pedro", cargo="Asesor Juridico", correo="pc@x.com"),
        ]
        actuales = [
            _f("SINCAMBIO", correo="sc@x.com"),
            _f("CAMBIOCARGO", nombre="Pedro", cargo="Director Juridico", correo="pc@x.com"),
            _f("NUEVO", nombre="Ana", correo="an@x.com"),
        ]
        diffs = comparar_funcionarios(anteriores, actuales)
        tipos = sorted(d.tipo_cambio.value for d in diffs)
        assert tipos == sorted(
            [
                TipoCambio.SIN_CAMBIOS.value,
                TipoCambio.FUNCIONARIO_ELIMINADO.value,
                TipoCambio.CAMBIO_CARGO.value,
                TipoCambio.FUNCIONARIO_NUEVO.value,
            ]
        )


class TestCalcularEstadisticas:
    def test_estadisticas_basicas(self) -> None:
        anteriores = [_f("A"), _f("B", nombre="Maria", correo="m@x.com")]
        actuales = [_f("A"), _f("C", nombre="Ana", correo="a@x.com")]
        diffs = comparar_funcionarios(anteriores, actuales)
        stats = calcular_estadisticas(diffs, len(anteriores), len(actuales))
        assert stats.total_funcionarios_anteriores == 2
        assert stats.total_funcionarios_actuales == 2
        assert stats.cantidad_nuevos == 1
        assert stats.cantidad_eliminados == 1
        assert stats.cantidad_sin_cambios == 1
        assert stats.cantidad_cambios == 0
        # Union de personas distintas involucradas = 3 (A sin cambios, B
        # eliminado, C nuevo); afectados = eliminado+nuevo = 2 -> 2/3.
        assert stats.porcentaje_cambios == 66.67

    def test_estadisticas_sin_diferencias_da_porcentaje_cero(self) -> None:
        stats = calcular_estadisticas([], 0, 0)
        assert stats.porcentaje_cambios == 0.0

    def test_cambios_por_campo_cuenta_ocurrencias_no_funcionarios(self) -> None:
        anterior = _f("A", cargo="Asesor Juridico", dependencia="Legal")
        actual = _f("A", cargo="Director Juridico", dependencia="Procuraduria")
        diffs = comparar_funcionarios([anterior], [actual])
        stats = calcular_estadisticas(diffs, 1, 1)
        assert stats.cambios_por_campo["cargo"] == 1
        assert stats.cambios_por_campo["dependencia"] == 1
        assert stats.cambios_por_campo["correo"] == 0

    def test_duracion_segundos_se_propaga(self) -> None:
        stats = calcular_estadisticas([], 0, 0, duracion_segundos=1.234)
        assert stats.duracion_segundos == 1.234
