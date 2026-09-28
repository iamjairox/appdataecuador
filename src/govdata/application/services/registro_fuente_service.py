"""Servicio: RegistroFuenteService -- Submodulo 6.9 (Versionado por
Fuente) + Submodulo 6.15 (Trazabilidad).

Es el UNICO lugar que abre/cierra versiones de `RegistroFuente` (mismo
principio de `HistorialService`, Modulo 5, para `VersionFuncionario`):
"nunca sobrescribir" -- la version vigente anterior se cierra, se inserta
una nueva. Cada campo del `datos` recibido genera ademas un
`AtributoTrazable` (quien/cuando/fuente/score), sin excepcion.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from govdata.application.ports.atributo_trazable_repository_port import (
    AtributoTrazableRepositoryPort,
)
from govdata.application.ports.registro_fuente_repository_port import RegistroFuenteRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna

logger = get_logger(__name__)


def _hash_datos(datos: dict[str, Any]) -> str:
    canonico = json.dumps(datos, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def calcular_cambios(
    datos_anteriores: dict[str, Any], datos_nuevos: dict[str, Any]
) -> dict[str, tuple[str | None, str | None]]:
    """Diferencia campo a campo entre dos snapshots -- insumo directo de
    `generador_alertas_perfil`/`generador_eventos_perfil` (Submodulos
    6.12/6.13)."""
    cambios: dict[str, tuple[str | None, str | None]] = {}
    for campo, valor_nuevo in datos_nuevos.items():
        valor_anterior = datos_anteriores.get(campo)
        texto_anterior = None if valor_anterior is None else str(valor_anterior)
        texto_nuevo = None if valor_nuevo is None else str(valor_nuevo)
        if texto_anterior != texto_nuevo:
            cambios[campo] = (texto_anterior, texto_nuevo)
    return cambios


class RegistroFuenteService:
    def __init__(
        self,
        registro_fuente_repository: RegistroFuenteRepositoryPort,
        atributo_trazable_repository: AtributoTrazableRepositoryPort,
    ) -> None:
        self._registro_fuente_repository = registro_fuente_repository
        self._atributo_trazable_repository = atributo_trazable_repository

    def registrar_respuesta(
        self,
        persona_master_id: int,
        fuente: FuenteExterna,
        datos: dict[str, Any],
        consultado_en: datetime,
        score_confianza: float = 100.0,
    ) -> tuple[RegistroFuente, dict[str, tuple[str | None, str | None]]]:
        anterior = self._registro_fuente_repository.buscar_vigente(persona_master_id, fuente)
        datos_anteriores = anterior.datos if anterior is not None else {}
        cambios = calcular_cambios(datos_anteriores, datos)

        siguiente_version = 1
        if anterior is not None:
            anterior.cerrar()
            self._registro_fuente_repository.guardar(anterior)
            siguiente_version = anterior.version + 1

        nuevo_registro = RegistroFuente(
            persona_master_id=persona_master_id,
            fuente=fuente,
            version=siguiente_version,
            datos=datos,
            consultado_en=consultado_en,
            hash_contenido=_hash_datos(datos),
        )
        guardado = self._registro_fuente_repository.guardar(nuevo_registro)

        atributos = [
            AtributoTrazable(
                persona_master_id=persona_master_id,
                campo=campo,
                valor=str(valor),
                fuente=fuente,
                obtenido_en=consultado_en,
                score=score_confianza,
                registro_fuente_id=guardado.id,
            )
            for campo, valor in datos.items()
            if valor is not None
        ]
        if atributos:
            self._atributo_trazable_repository.guardar_lote(atributos)

        logger.info(
            "registro_fuente_versionado",
            persona_master_id=persona_master_id,
            fuente=fuente.value,
            version=siguiente_version,
            campos_cambiados=len(cambios),
        )
        return guardado, cambios
