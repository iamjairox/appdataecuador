"""Servicio: PersistenciaInteligenteService -- Submodulo 5.11.

"Nunca insertar duplicados. Debe utilizar: Fingerprint, Documento,
Entidad, Correo, Cargo. Para decidir: Insertar, Actualizar, Ignorar,
Versionar" -- instruccion explicita del cliente. Aplica el resultado YA
CALCULADO por el Motor de Comparacion (5.1) sobre `Persona`/`Funcionario`
(Modulo 4) y delega la apertura/cierre de `VersionFuncionario` a
`HistorialService` (5.2) -- nunca duplica esa logica.

Regla de decision por `TipoCambio`:

    SIN_CAMBIOS          -> Ignorar (no se toca nada).
    FUNCIONARIO_NUEVO     -> Insertar Persona (si no existia por
                             fingerprint) + Insertar Funcionario vigente +
                             Versionar (abre v1).
    FUNCIONARIO_ELIMINADO -> Actualizar Funcionario (cierra fecha_fin) +
                             Versionar (cierra la vigente).
    CAMBIO_*              -> Actualizar Persona/Funcionario in-place +
                             Versionar (cierra vigente, abre siguiente).
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.resumen_persistencia_dto import ResumenPersistenciaDTO
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.historial_service import HistorialService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.rules.generador_fingerprint import generar_fingerprint
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono
from govdata.domain.value_objects.tipo_cambio import TipoCambio

logger = get_logger(__name__)


class PersistenciaInteligenteService:
    def __init__(
        self,
        persona_repository: PersonaRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        historial_service: HistorialService,
    ) -> None:
        self._persona_repository = persona_repository
        self._funcionario_repository = funcionario_repository
        self._historial_service = historial_service

    def aplicar(
        self, diferencias: list[DiferenciaFuncionarioDTO], entidad_id: int, documento_id: int, fecha: date
    ) -> ResumenPersistenciaDTO:
        insertados = actualizados = ignorados = versionados = 0
        persona_id_por_fingerprint: dict[str, int] = {}

        for diferencia in diferencias:
            if diferencia.tipo_cambio == TipoCambio.SIN_CAMBIOS:
                ignorados += 1
                continue

            if diferencia.tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO:
                self._aplicar_eliminado(diferencia, entidad_id, fecha, persona_id_por_fingerprint)
                versionados += 1
                continue

            persona, fue_insertada = self._buscar_o_crear_persona(diferencia)
            persona_id_por_fingerprint[diferencia.fingerprint] = persona.id  # type: ignore[assignment]
            insertados += int(fue_insertada)
            actualizados += int(not fue_insertada)

            funcionario = self._buscar_o_crear_funcionario(diferencia, persona.id, entidad_id, documento_id)  # type: ignore[arg-type]
            self._historial_service.aplicar_diferencia(
                diferencia, entidad_id, persona.id, funcionario.id, documento_id, fecha  # type: ignore[arg-type]
            )
            versionados += 1

        resumen = ResumenPersistenciaDTO(
            insertados=insertados,
            actualizados=actualizados,
            ignorados=ignorados,
            versionados=versionados,
            persona_id_por_fingerprint=persona_id_por_fingerprint,
        )
        logger.info(
            "persistencia_inteligente_aplicada",
            entidad_id=entidad_id,
            documento_id=documento_id,
            insertados=insertados,
            actualizados=actualizados,
            ignorados=ignorados,
            versionados=versionados,
        )
        return resumen

    def _aplicar_eliminado(
        self,
        diferencia: DiferenciaFuncionarioDTO,
        entidad_id: int,
        fecha: date,
        persona_id_por_fingerprint: dict[str, int],
    ) -> None:
        _, fingerprint_hash = generar_fingerprint(diferencia.nombre, diferencia.apellido)
        persona = self._persona_repository.buscar_por_fingerprint_hash(fingerprint_hash)
        if persona is None or persona.id is None:
            # No estaba persistida (dato inconsistente) -- nada que cerrar.
            return
        persona_id_por_fingerprint[diferencia.fingerprint] = persona.id

        funcionario = self._funcionario_repository.buscar_vigente(persona.id, entidad_id)
        if funcionario is not None:
            funcionario.fecha_fin = fecha
            self._funcionario_repository.guardar(funcionario)

        self._historial_service.cerrar_version_vigente(persona.id, entidad_id, fecha)

    def _buscar_o_crear_persona(self, diferencia: DiferenciaFuncionarioDTO) -> tuple[Persona, bool]:
        fingerprint, fingerprint_hash = generar_fingerprint(diferencia.nombre, diferencia.apellido)
        correo = Correo.crear_opcional(diferencia.correo)
        telefono = Telefono.crear_opcional(diferencia.telefono)

        persona = self._persona_repository.buscar_por_fingerprint_hash(fingerprint_hash)
        if persona is None:
            nueva = Persona(
                nombre_completo=NombreCompleto(nombres=diferencia.nombre, apellidos=diferencia.apellido),
                correo=correo,
                telefono=telefono,
                fingerprint=fingerprint,
                fingerprint_hash=fingerprint_hash,
            )
            return self._persona_repository.guardar(nueva), True

        persona.actualizar_datos_contacto(correo, telefono)
        return self._persona_repository.guardar(persona), False

    def _buscar_o_crear_funcionario(
        self, diferencia: DiferenciaFuncionarioDTO, persona_id: int, entidad_id: int, documento_id: int
    ) -> Funcionario:
        funcionario = self._funcionario_repository.buscar_vigente(persona_id, entidad_id)
        if funcionario is None:
            funcionario = Funcionario(
                persona_id=persona_id,
                entidad_id=entidad_id,
                cargo=Cargo(diferencia.cargo),
                dependencia=diferencia.dependencia,
                area_clasificada=AreaRelevante(diferencia.area),
                documento_id=documento_id,
            )
        else:
            funcionario.cargo = Cargo(diferencia.cargo)
            funcionario.dependencia = diferencia.dependencia
            funcionario.area_clasificada = AreaRelevante(diferencia.area)
            funcionario.documento_id = documento_id
        return self._funcionario_repository.guardar(funcionario)
