"""Tests: Motor de Fusion -- seleccion de atributos ganadores (Submodulos
6.14/6.15)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.rules.motor_fusion_atributos import seleccionar_atributos_ganadores
from govdata.domain.value_objects.fuente_externa import FuenteExterna

_T1 = datetime(2026, 1, 1, tzinfo=UTC)
_T2 = datetime(2026, 2, 1, tzinfo=UTC)


def _atributo(campo: str, valor: str, score: float, obtenido_en: datetime, fuente=FuenteExterna.DPE) -> AtributoTrazable:
    return AtributoTrazable(
        persona_master_id=1, campo=campo, valor=valor, fuente=fuente, obtenido_en=obtenido_en, score=score
    )


class TestSeleccionarAtributosGanadores:
    def test_mayor_score_gana(self) -> None:
        atributos = [
            _atributo("correo", "viejo@x.com", score=50.0, obtenido_en=_T1),
            _atributo("correo", "nuevo@x.com", score=90.0, obtenido_en=_T1),
        ]
        ganadores = seleccionar_atributos_ganadores(atributos)
        assert ganadores["correo"].valor == "nuevo@x.com"

    def test_empate_de_score_gana_el_mas_reciente(self) -> None:
        atributos = [
            _atributo("titulo", "Abogado", score=80.0, obtenido_en=_T1),
            _atributo("titulo", "Doctor en Jurisprudencia", score=80.0, obtenido_en=_T2),
        ]
        ganadores = seleccionar_atributos_ganadores(atributos)
        assert ganadores["titulo"].valor == "Doctor en Jurisprudencia"

    def test_atributo_posterior_con_menor_score_no_reemplaza_al_ganador(self) -> None:
        atributos = [
            _atributo("correo", "bueno@x.com", score=90.0, obtenido_en=_T1),
            _atributo("correo", "peor@x.com", score=40.0, obtenido_en=_T2),
        ]
        ganadores = seleccionar_atributos_ganadores(atributos)
        assert ganadores["correo"].valor == "bueno@x.com"

    def test_campos_distintos_no_compiten_entre_si(self) -> None:
        atributos = [
            _atributo("correo", "a@x.com", score=90.0, obtenido_en=_T1),
            _atributo("telefono", "0991111111", score=90.0, obtenido_en=_T1),
        ]
        ganadores = seleccionar_atributos_ganadores(atributos)
        assert set(ganadores.keys()) == {"correo", "telefono"}

    def test_nunca_pierde_los_atributos_no_ganadores_de_la_lista_original(self) -> None:
        atributos = [
            _atributo("correo", "viejo@x.com", score=50.0, obtenido_en=_T1, fuente=FuenteExterna.DPE),
            _atributo("correo", "nuevo@x.com", score=90.0, obtenido_en=_T1, fuente=FuenteExterna.SENESCYT),
        ]
        seleccionar_atributos_ganadores(atributos)
        # la lista original nunca se muta ni se filtra -- solo se agrega un indice de ganadores
        assert len(atributos) == 2
        assert {a.fuente for a in atributos} == {FuenteExterna.DPE, FuenteExterna.SENESCYT}
