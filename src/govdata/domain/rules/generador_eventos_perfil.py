"""Regla de dominio: generador de Eventos de Perfil -- Submodulo 6.12.

Mismo espiritu que `generador_alertas.py` (Modulo 5): produce `EventoPerfil`
en PENDIENTE a partir de hechos ya ocurridos en el pipeline de
enriquecimiento (Submodulo 6.7) -- nunca los envia a ningun lado, eso es
responsabilidad de un futuro consumidor (Submodulo 6.7's "Preparacion").
"""

from __future__ import annotations

from datetime import datetime

from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad


def generar_evento_persona_enriquecida(
    persona_master_id: int, fuente: FuenteExterna, cuando: datetime
) -> EventoPerfil:
    return EventoPerfil(
        tipo=TipoEventoIdentidad.PERSONA_ENRIQUECIDA,
        persona_master_id=persona_master_id,
        payload={"fuente": fuente.value},
        creado_en=cuando,
    )


def generar_evento_persona_fusionada(
    persona_master_ganadora_id: int, persona_master_absorbida_id: int, score: float, cuando: datetime
) -> EventoPerfil:
    return EventoPerfil(
        tipo=TipoEventoIdentidad.PERSONA_FUSIONADA,
        persona_master_id=persona_master_ganadora_id,
        payload={"persona_master_absorbida_id": persona_master_absorbida_id, "score": score},
        creado_en=cuando,
    )


def generar_evento_nueva_fuente(persona_master_id: int, fuente: FuenteExterna, cuando: datetime) -> EventoPerfil:
    return EventoPerfil(
        tipo=TipoEventoIdentidad.NUEVA_FUENTE,
        persona_master_id=persona_master_id,
        payload={"fuente": fuente.value},
        creado_en=cuando,
    )


def generar_evento_fuente_actualizada(
    persona_master_id: int, fuente: FuenteExterna, version: int, cuando: datetime
) -> EventoPerfil:
    return EventoPerfil(
        tipo=TipoEventoIdentidad.FUENTE_ACTUALIZADA,
        persona_master_id=persona_master_id,
        payload={"fuente": fuente.value, "version": version},
        creado_en=cuando,
    )


_CAMPO_A_TIPO_EVENTO: dict[str, TipoEventoIdentidad] = {
    "titulo": TipoEventoIdentidad.NUEVO_TITULO,
    "profesion": TipoEventoIdentidad.CAMBIO_DE_PROFESION,
}


def generar_eventos_por_cambios(
    cambios: dict[str, tuple[str | None, str | None]], persona_master_id: int, cuando: datetime
) -> list[EventoPerfil]:
    """Genera `NUEVO_TITULO`/`CAMBIO_DE_PROFESION` cuando corresponde,
    ademas de las alertas equivalentes (Submodulo 6.13) -- eventos y
    alertas conviven, con audiencias distintas (eventos: consumidor
    automatico futuro; alertas: revision humana)."""
    eventos = []
    for campo, (anterior, nuevo) in cambios.items():
        tipo = _CAMPO_A_TIPO_EVENTO.get(campo)
        if tipo is None or not nuevo or anterior == nuevo:
            continue
        eventos.append(
            EventoPerfil(
                tipo=tipo,
                persona_master_id=persona_master_id,
                payload={"campo": campo, "valor_anterior": anterior, "valor_nuevo": nuevo},
                creado_en=cuando,
            )
        )
    return eventos
