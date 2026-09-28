"""Servicio: PerfilAcademicoService -- Submodulo 7.16 (Contrato Oficial).

Ensambla `PerfilAcademicoDTO` a partir de lo que los demas servicios ya
calcularon: la `PersonaMaster` (Modulo 6, REUTILIZADA sin reimplementar),
los titulos vigentes, la bitacora de cambios, los eventos y las alertas.
Este servicio no calcula nada nuevo -- solo agrega.
"""

from __future__ import annotations

from dataclasses import asdict

from govdata.application.dto.alerta_academica_dto import AlertaAcademicaDTO
from govdata.application.dto.evento_academico_dto import EventoAcademicoDTO
from govdata.application.dto.perfil_academico_dto import PerfilAcademicoDTO
from govdata.application.dto.titulo_academico_dto import TituloAcademicoDTO
from govdata.application.ports.alerta_academica_repository_port import (
    AlertaAcademicaRepositoryPort,
)
from govdata.application.ports.evento_academico_repository_port import (
    EventoAcademicoRepositoryPort,
)
from govdata.application.ports.historial_academico_repository_port import (
    HistorialAcademicoRepositoryPort,
)
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.ports.titulo_academico_repository_port import (
    TituloAcademicoRepositoryPort,
)
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError


class PerfilAcademicoService:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        titulo_repository: TituloAcademicoRepositoryPort,
        historial_repository: HistorialAcademicoRepositoryPort,
        evento_repository: EventoAcademicoRepositoryPort,
        alerta_repository: AlertaAcademicaRepositoryPort,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._titulo_repository = titulo_repository
        self._historial_repository = historial_repository
        self._evento_repository = evento_repository
        self._alerta_repository = alerta_repository

    def construir_perfil(self, persona_master_id: int) -> PerfilAcademicoDTO:
        persona_master = self._persona_master_repository.buscar_por_id(persona_master_id)
        if persona_master is None:
            raise PersonaMasterInvalidaError(f"PersonaMaster no encontrada: {persona_master_id}")

        titulos = self._titulo_repository.listar_vigentes_por_persona_master(persona_master_id)
        historial = self._historial_repository.listar_por_persona_master(persona_master_id)
        eventos = self._evento_repository.listar_por_persona_master(persona_master_id)
        alertas = self._alerta_repository.listar_por_persona_master(persona_master_id)

        persona_master_dict = {
            "persona_master_id": persona_master.id,
            "persona_id": persona_master.persona_id,
            "nombre_completo": persona_master.nombre_completo.nombre_completo,
            "estado": persona_master.estado.value,
        }
        identidad_dict = {
            "uuid": str(persona_master.uuid),
            "fingerprint_principal": persona_master.fingerprint_principal,
            "nivel_confianza": persona_master.nivel_confianza,
        }
        estadisticas = {
            "cantidad_titulos_vigentes": len(titulos),
            "cantidad_cambios_historial": len(historial),
            "cantidad_alertas": len(alertas),
            "cantidad_eventos": len(eventos),
        }

        return PerfilAcademicoDTO(
            persona_master=persona_master_dict,
            identidad=identidad_dict,
            titulos=[asdict(TituloAcademicoDTO.desde_entidad(t)) for t in titulos],
            historial=[
                {
                    "clave_titulo": h.clave_titulo,
                    "tipo_cambio": h.tipo_cambio.value,
                    "detectado_en": h.detectado_en.isoformat(),
                    "campos_modificados": h.campos_modificados,
                    "descripcion": h.descripcion,
                }
                for h in historial
            ],
            alertas=[asdict(AlertaAcademicaDTO.desde_entidad(a)) for a in alertas],
            eventos=[asdict(EventoAcademicoDTO.desde_entidad(e)) for e in eventos],
            estadisticas=estadisticas,
        )
