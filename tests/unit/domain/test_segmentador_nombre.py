"""Tests: segmentacion de nombre completo segun el orden del encabezado."""

from __future__ import annotations

import pytest

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.domain.rules.normalizador_universal import normalizar_tabla
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion
from govdata.domain.rules.segmentador_nombre import (
    ConfianzaSegmentacion,
    OrdenNombre,
    detectar_orden_por_encabezado,
    segmentar_nombre_completo,
)


class TestDetectarOrden:
    @pytest.mark.parametrize(
        ("encabezado", "esperado"),
        [
            ("Apellidos y Nombres", OrdenNombre.APELLIDOS_PRIMERO),
            ("APELLIDOS Y NOMBRES ", OrdenNombre.APELLIDOS_PRIMERO),
            ("Nombres y Apellidos", OrdenNombre.NOMBRES_PRIMERO),
            ("Nombre y apellido del servidor", OrdenNombre.NOMBRES_PRIMERO),
            ("Servidor", OrdenNombre.DESCONOCIDO),
            ("Nombre Completo", OrdenNombre.DESCONOCIDO),
        ],
    )
    def test_orden_por_encabezado(self, encabezado: str, esperado: OrdenNombre) -> None:
        assert detectar_orden_por_encabezado(encabezado) == esperado


class TestSegmentar:
    def test_apellidos_primero_cuatro_palabras_confianza_alta(self) -> None:
        s = segmentar_nombre_completo("PEREZ GOMEZ JUAN CARLOS", OrdenNombre.APELLIDOS_PRIMERO)
        assert (s.nombres, s.apellidos) == ("JUAN CARLOS", "PEREZ GOMEZ")
        assert s.confianza == ConfianzaSegmentacion.ALTA

    def test_nombres_primero_cuatro_palabras(self) -> None:
        s = segmentar_nombre_completo("Juan Carlos Pérez Gómez", OrdenNombre.NOMBRES_PRIMERO)
        assert (s.nombres, s.apellidos) == ("Juan Carlos", "Pérez Gómez")
        assert s.confianza == ConfianzaSegmentacion.ALTA

    def test_apellidos_primero_tres_palabras_confianza_media(self) -> None:
        s = segmentar_nombre_completo("PEREZ GOMEZ ANA", OrdenNombre.APELLIDOS_PRIMERO)
        assert (s.nombres, s.apellidos) == ("ANA", "PEREZ GOMEZ")
        assert s.confianza == ConfianzaSegmentacion.MEDIA

    def test_apellido_compuesto_con_particulas(self) -> None:
        s = segmentar_nombre_completo("DE LA CRUZ MORA LUIS ALBERTO", OrdenNombre.APELLIDOS_PRIMERO)
        assert (s.nombres, s.apellidos) == ("LUIS ALBERTO", "DE LA CRUZ MORA")
        assert s.confianza == ConfianzaSegmentacion.MEDIA

    def test_orden_desconocido_no_inventa_certeza(self) -> None:
        s = segmentar_nombre_completo("Juan Carlos Perez Gomez", OrdenNombre.DESCONOCIDO)
        assert (s.nombres, s.apellidos) == ("Juan Carlos", "Perez Gomez")
        assert s.confianza == ConfianzaSegmentacion.BAJA

    def test_una_sola_palabra(self) -> None:
        s = segmentar_nombre_completo("MADONNA", OrdenNombre.APELLIDOS_PRIMERO)
        assert (s.nombres, s.apellidos) == ("MADONNA", "")
        assert s.confianza == ConfianzaSegmentacion.BAJA

    def test_seis_palabras_confianza_baja(self) -> None:
        s = segmentar_nombre_completo("PEREZ GOMEZ JUAN CARLOS ANDRES MIGUEL", OrdenNombre.APELLIDOS_PRIMERO)
        assert s.apellidos == "PEREZ GOMEZ"
        assert s.confianza == ConfianzaSegmentacion.BAJA


class TestNormalizarTablaConOrden:
    _REGLAS = ReglasNormalizacion(
        sinonimos_por_campo={
            "nombre_completo": ["Apellidos y Nombres", "Nombres y Apellidos"],
            "cargo": ["Puesto Institucional"],
        }
    )

    def test_plantilla_dpe_apellidos_y_nombres(self) -> None:
        tabla = TablaExtraidaDTO(
            encabezados=("Apellidos y Nombres", "Puesto Institucional"),
            filas=[{"Apellidos y Nombres": "PEREZ GOMEZ JUAN CARLOS", "Puesto Institucional": "ANALISTA JURIDICO"}],
        )
        fila = normalizar_tabla(tabla, self._REGLAS)[0]
        assert (fila.nombres, fila.apellidos) == ("JUAN CARLOS", "PEREZ GOMEZ")
        assert fila.nombre_completo_original == "PEREZ GOMEZ JUAN CARLOS"
        assert fila.orden_nombre == "apellidos_primero"
        assert fila.confianza_segmentacion == "alta"

    def test_mismo_nombre_en_ambos_ordenes_produce_la_misma_segmentacion(self) -> None:
        a = TablaExtraidaDTO(encabezados=("Apellidos y Nombres",), filas=[{"Apellidos y Nombres": "PEREZ GOMEZ JUAN CARLOS"}])
        b = TablaExtraidaDTO(encabezados=("Nombres y Apellidos",), filas=[{"Nombres y Apellidos": "JUAN CARLOS PEREZ GOMEZ"}])
        fa, fb = normalizar_tabla(a, self._REGLAS)[0], normalizar_tabla(b, self._REGLAS)[0]
        assert (fa.nombres, fa.apellidos) == (fb.nombres, fb.apellidos)

    def test_columnas_separadas_no_marcan_segmentacion(self) -> None:
        reglas = ReglasNormalizacion(sinonimos_por_campo={"nombres": ["Nombres"], "apellidos": ["Apellidos"]})
        tabla = TablaExtraidaDTO(encabezados=("Nombres", "Apellidos"), filas=[{"Nombres": "Ana", "Apellidos": "Lopez"}])
        fila = normalizar_tabla(tabla, reglas)[0]
        assert fila.nombre_completo_original is None
        assert fila.confianza_segmentacion is None
