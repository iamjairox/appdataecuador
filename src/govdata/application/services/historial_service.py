"""Servicio: HistorialService -- Submodulos 5.2 (Historial de Personas),
5.3 (Historial de Cargo) y 5.4 (Historial de Dependencia).

"Nunca sobrescribir informacion. Toda modificacion genera una nueva
version" -- instruccion explicita del cliente. Este servicio es el UNICO
lugar que abre/cierra `VersionFuncionario`; `PersistenciaInteligenteService`
(5.11) le delega esa responsabilidad en vez de manipular el historial
directamente (evita que dos lugares distintos del codigo decidan cuando
"cerrar" una version).
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.ports.version_funcionario_repository_port import (
    VersionFuncionarioRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.version_funcionario import VersionFuncionario
from govdata.domain.value_objects.tipo_cambio import TipoCambio

logger = get_logger(__name__)


class HistorialService:
    def __init__(self, version_funcionario_repository: VersionFuncionarioRepositoryPort) -> None:
        self._version_repository = version_funcionario_repository

    # -- Escritura (delegada por Submodulo 5.11) -----------------------------

    def cerrar_version_vigente(self, persona_id: int, entidad_id: int, fecha_fin: date) -> VersionFuncionario | None:
        vigente = self._version_repository.buscar_vigente(persona_id, entidad_id)
        if vigente is None:
            return None
        vigente.cerrar(fecha_fin)
        return self._version_repository.guardar(vigente)

    def aplicar_diferencia(
        self,
        diferencia: DiferenciaFuncionarioDTO,
        entidad_id: int,
        persona_id: int,
        funcionario_id: int | None,
        documento_id: int,
        fecha: date,
    ) -> VersionFuncionario | None:
        """Traduce UNA diferencia ya clasificada en una transicion de
        historial: NUEVO abre v1, ELIMINADO cierra la vigente, cualquier
        CAMBIO_* cierra la vigente y abre la siguiente version, SIN_CAMBIOS
        no toca nada (nunca se reescribe una version sin motivo real)."""
        if diferencia.tipo_cambio == TipoCambio.SIN_CAMBIOS:
            return None

        if diferencia.tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO:
            return self.cerrar_version_vigente(persona_id, entidad_id, fecha)

        vigente = self._version_repository.buscar_vigente(persona_id, entidad_id)
        siguiente_numero = 1
        if vigente is not None:
            vigente.cerrar(fecha)
            self._version_repository.guardar(vigente)
            siguiente_numero = vigente.numero_version + 1

        nueva_version = VersionFuncionario(
            persona_id=persona_id,
            entidad_id=entidad_id,
            numero_version=siguiente_numero,
            cargo=diferencia.cargo,
            dependencia=diferencia.dependencia,
            area=diferencia.area,
            documento_id=documento_id,
            fecha_inicio=fecha,
            funcionario_id=funcionario_id,
            correo=diferencia.correo,
            telefono=diferencia.telefono,
        )
        guardada = self._version_repository.guardar(nueva_version)
        logger.info(
            "version_funcionario_abierta",
            persona_id=persona_id,
            entidad_id=entidad_id,
            numero_version=siguiente_numero,
            tipo_cambio=diferencia.tipo_cambio.value,
        )
        return guardada

    # -- Lectura (Submodulos 5.3/5.4) -----------------------------------------

    def quien_ocupa_cargo_ahora(self, entidad_id: int, cargo: str) -> VersionFuncionario | None:
        """"¿Quien es el Director Juridico actual?"."""
        return self._version_repository.buscar_vigente_por_entidad_y_cargo(entidad_id, cargo)

    def quien_ocupaba_cargo_en_fecha(self, entidad_id: int, cargo: str, en_fecha: date) -> VersionFuncionario | None:
        """"¿Quien era Director Juridico en junio?"."""
        return self._version_repository.buscar_vigente_en_fecha(entidad_id, cargo, en_fecha)

    def historial_del_cargo(self, entidad_id: int, cargo: str) -> list[VersionFuncionario]:
        """Toda la trayectoria de un cargo en una entidad -- base para
        "¿quien fue reemplazado?" (comparar version N con version N+1
        ordenadas por fecha_inicio)."""
        return sorted(
            self._version_repository.listar_por_entidad_y_cargo(entidad_id, cargo), key=lambda v: v.fecha_inicio
        )

    def cantidad_de_personas_en_cargo(self, entidad_id: int, cargo: str) -> int:
        """"¿Cuantos Directores Juridicos tuvo esta entidad?"."""
        return len({v.persona_id for v in self.historial_del_cargo(entidad_id, cargo)})

    def historial_de_persona(self, persona_id: int) -> list[VersionFuncionario]:
        """Toda la trayectoria de UNA persona (cualquier entidad/cargo),
        mas antigua primero."""
        return sorted(self._version_repository.listar_por_persona(persona_id), key=lambda v: v.fecha_inicio)

    def historial_de_dependencias(self, entidad_id: int) -> dict[int, list[VersionFuncionario]]:
        """Agrupa el historial COMPLETO de una entidad por persona,
        ordenado cronologicamente -- permite reconstruir la secuencia de
        dependencias de cada quien (Submodulo 5.4, ej. "Direccion Juridica
        -> Procuraduria -> Asesoria Juridica")."""
        agrupado: dict[int, list[VersionFuncionario]] = {}
        for version in sorted(self._version_repository.listar_por_entidad(entidad_id), key=lambda v: v.fecha_inicio):
            agrupado.setdefault(version.persona_id, []).append(version)
        return agrupado
