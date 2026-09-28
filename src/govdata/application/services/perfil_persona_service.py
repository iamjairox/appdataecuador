"""Servicio: PerfilPersonaService -- Submodulo 6.4 (Perfiles de Persona)
+ Submodulo 6.16 (Contrato Unificado).

Ensambla el contrato oficial `PerfilPersonaDTO` a partir de TODO lo que ya
existe: la `PersonaMaster` (6.1), sus `RegistroFuente` (6.9), el
historial institucional YA EXISTENTE (`HistorialService`, Modulo 5,
reutilizado sin reimplementar), sus `EventoPerfil`/`AlertaPerfil`
(6.12/6.13) y su timeline (6.5). Este servicio no calcula nada nuevo --
solo agrega lo que los demas servicios ya calcularon.
"""

from __future__ import annotations

from dataclasses import asdict

from govdata.application.dto.alerta_perfil_dto import AlertaPerfilDTO
from govdata.application.dto.evento_perfil_dto import EventoPerfilDTO
from govdata.application.dto.perfil_persona_dto import PerfilPersonaDTO
from govdata.application.dto.registro_fuente_dto import RegistroFuenteDTO
from govdata.application.ports.alerta_perfil_repository_port import AlertaPerfilRepositoryPort
from govdata.application.ports.evento_perfil_repository_port import EventoPerfilRepositoryPort
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.ports.registro_fuente_repository_port import RegistroFuenteRepositoryPort
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.timeline_persona_service import TimelinePersonaService
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError


class PerfilPersonaService:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        registro_fuente_repository: RegistroFuenteRepositoryPort,
        historial_service: HistorialService,
        evento_perfil_repository: EventoPerfilRepositoryPort,
        alerta_perfil_repository: AlertaPerfilRepositoryPort,
        timeline_service: TimelinePersonaService,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._registro_fuente_repository = registro_fuente_repository
        self._historial_service = historial_service
        self._evento_perfil_repository = evento_perfil_repository
        self._alerta_perfil_repository = alerta_perfil_repository
        self._timeline_service = timeline_service

    def construir_perfil(self, persona_master_id: int) -> PerfilPersonaDTO:
        persona_master = self._persona_master_repository.buscar_por_id(persona_master_id)
        if persona_master is None:
            raise PersonaMasterInvalidaError(f"PersonaMaster no encontrada: {persona_master_id}")

        registros = self._registro_fuente_repository.listar_por_persona_master(persona_master_id)
        vigentes = [r for r in registros if r.vigente]
        historial_versiones = self._historial_service.historial_de_persona(persona_master.persona_id)
        eventos = self._evento_perfil_repository.listar_por_persona_master(persona_master_id)
        alertas = self._alerta_perfil_repository.listar_por_persona_master(persona_master_id)
        timeline = self._timeline_service.construir(persona_master)

        persona_dict = {
            "persona_id": persona_master.persona_id,
            "nombres": persona_master.nombre_completo.nombres,
            "apellidos": persona_master.nombre_completo.apellidos,
            "nombre_completo": persona_master.nombre_completo.nombre_completo,
            "sexo": persona_master.sexo,
            "fecha_nacimiento": persona_master.fecha_nacimiento.isoformat()
            if persona_master.fecha_nacimiento
            else None,
            "correo_principal": str(persona_master.correo_principal)
            if persona_master.correo_principal
            else None,
            "telefono_principal": str(persona_master.telefono_principal)
            if persona_master.telefono_principal
            else None,
        }
        identidad_dict = {
            "persona_master_id": persona_master.id,
            "uuid": str(persona_master.uuid),
            "fingerprint_principal": persona_master.fingerprint_principal,
            "fingerprint_fonetico": persona_master.fingerprint_fonetico,
            "estado": persona_master.estado.value,
            "nivel_confianza": persona_master.nivel_confianza,
            "fusionada_en_id": persona_master.fusionada_en_id,
        }
        perfil_dict = {
            "cargo_actual": historial_versiones[-1].cargo if historial_versiones else None,
            "dependencia_actual": historial_versiones[-1].dependencia if historial_versiones else None,
            "titulos": sorted({str(r.datos["titulo"]) for r in vigentes if r.datos.get("titulo")}),
            "profesiones": sorted({str(r.datos["profesion"]) for r in vigentes if r.datos.get("profesion")}),
            "especializaciones": sorted(
                {str(r.datos["especializacion"]) for r in vigentes if r.datos.get("especializacion")}
            ),
            "fuentes_consultadas": sorted({r.fuente.value for r in registros}),
            "ultima_actualizacion": persona_master.actualizado_en.isoformat()
            if persona_master.actualizado_en
            else None,
        }
        estadisticas_dict = {
            "cantidad_fuentes": persona_master.cantidad_fuentes,
            "cantidad_cargos_historicos": persona_master.cantidad_cargos_historicos,
            "cantidad_alertas": len(alertas),
            "cantidad_eventos": len(eventos),
            "nivel_confianza": persona_master.nivel_confianza,
        }

        return PerfilPersonaDTO(
            persona=persona_dict,
            identidad=identidad_dict,
            perfil=perfil_dict,
            fuentes=[asdict(RegistroFuenteDTO.desde_entidad(r)) for r in registros],
            historial=[
                {
                    "cargo": v.cargo,
                    "dependencia": v.dependencia,
                    "area": v.area,
                    "fecha_inicio": v.fecha_inicio.isoformat(),
                    "fecha_fin": v.fecha_fin.isoformat() if v.fecha_fin else None,
                    "numero_version": v.numero_version,
                }
                for v in historial_versiones
            ],
            eventos=[asdict(EventoPerfilDTO.desde_entidad(e)) for e in eventos],
            alertas=[asdict(AlertaPerfilDTO.desde_entidad(a)) for a in alertas],
            timeline=[
                {
                    "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
                    "fecha_fin": p.fecha_fin.isoformat() if p.fecha_fin else None,
                    "origen": p.origen,
                    "descripcion": p.descripcion,
                    "referencia_id": p.referencia_id,
                }
                for p in timeline.puntos
            ],
            estadisticas=estadisticas_dict,
        )
