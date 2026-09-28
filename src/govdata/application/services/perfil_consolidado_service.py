"""Servicio: PerfilConsolidadoService -- Submodulo 8.10, EL VERDADERO
OBJETIVO DEL SISTEMA.

Ensambla `PerfilConsolidadoDTO` a partir de lo que los pipelines de CADA
fuente ya calcularon -- Transparencia (Modulos 1-5, `Persona`/
`Funcionario`, REUTILIZADOS sin modificar), SENESCYT (Modulo 7,
`PerfilAcademicoService`, REUTILIZADO sin modificar) y Foro de Abogados
(Modulo 8, este mismo modulo). Este servicio no calcula nada nuevo -- solo
agrega, exactamente como `PerfilPersonaService` (Modulo 6) y
`PerfilAcademicoService` (Modulo 7) hicieron para sus propios contratos.

Es la pieza central de la mejora arquitectonica adoptada al cierre del
Modulo 8: el usuario nunca vuelve a pensar en "Transparencia" / "SENESCYT"
/ "Foro" por separado -- pide una PersonaMaster y recibe la ficha
consolidada. Agregar una fuente futura (Funcion Judicial, Contraloria,
SERCOP, ...) significa sumar UNA clave mas a este dict, nunca rediseñar
el pipeline de identidad/cache/comparacion/historial/alertas."""

from __future__ import annotations

from dataclasses import asdict

from govdata.application.dto.alerta_foro_dto import AlertaForoDTO
from govdata.application.dto.evento_foro_dto import EventoForoDTO
from govdata.application.dto.perfil_consolidado_dto import PerfilConsolidadoDTO
from govdata.application.dto.registro_foro_persistido_dto import RegistroForoPersistidoDTO
from govdata.application.ports.alerta_foro_repository_port import AlertaForoRepositoryPort
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.evento_foro_repository_port import EventoForoRepositoryPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.historial_foro_repository_port import HistorialForoRepositoryPort
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError


class PerfilConsolidadoService:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        entidad_repository: EntidadRepositoryPort,
        perfil_academico_service: PerfilAcademicoService,
        registro_foro_repository: RegistroForoRepositoryPort,
        historial_foro_repository: HistorialForoRepositoryPort,
        evento_foro_repository: EventoForoRepositoryPort,
        alerta_foro_repository: AlertaForoRepositoryPort,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._persona_repository = persona_repository
        self._funcionario_repository = funcionario_repository
        self._entidad_repository = entidad_repository
        self._perfil_academico_service = perfil_academico_service
        self._registro_foro_repository = registro_foro_repository
        self._historial_foro_repository = historial_foro_repository
        self._evento_foro_repository = evento_foro_repository
        self._alerta_foro_repository = alerta_foro_repository

    def construir_perfil(self, persona_master_id: int, entidad_id: int | None = None) -> PerfilConsolidadoDTO:
        persona_master = self._persona_master_repository.buscar_por_id(persona_master_id)
        if persona_master is None:
            raise PersonaMasterInvalidaError(f"PersonaMaster no encontrada: {persona_master_id}")

        persona = self._persona_repository.buscar_por_id(persona_master.persona_id)

        persona_dict = {
            "persona_master_id": persona_master.id,
            "persona_id": persona_master.persona_id,
            "nombre_completo": persona_master.nombre_completo.nombre_completo,
            "cedula": persona.cedula if persona else None,
            "correo_principal": str(persona_master.correo_principal) if persona_master.correo_principal else None,
            "telefono_principal": str(persona_master.telefono_principal) if persona_master.telefono_principal else None,
        }

        transparencia_dict = self._construir_transparencia(persona_master.persona_id, entidad_id)
        senescyt_dict = self._perfil_academico_service.construir_perfil(persona_master_id).to_dict()
        foro_dict = self.construir_foro(persona_master_id)

        return PerfilConsolidadoDTO(
            persona=persona_dict, transparencia=transparencia_dict, senescyt=senescyt_dict, foro=foro_dict,
        )

    def _construir_transparencia(self, persona_id: int, entidad_id: int | None) -> dict:
        """`FuncionarioRepositoryPort` (Modulo 4, congelado) no expone
        "listar TODOS los vinculos de una persona, sin conocer la
        entidad" -- solo `buscar_vigente(persona_id, entidad_id)`,
        `listar_por_entidad`, `listar_por_documento` y
        `buscar_con_filtros` (todos con alcance por entidad/documento).
        Cuando el llamador ya conoce la `entidad_id` (el caso normal: el
        flujo del Modulo 8 SIEMPRE arranca de una Entidad, Submodulo
        8.11) se usa `buscar_vigente` sin tocar el puerto congelado; sin
        `entidad_id` la seccion queda vacia -- nunca se inventa un
        vinculo que no se puede verificar."""
        if entidad_id is None:
            return {"cargos": []}

        funcionario = self._funcionario_repository.buscar_vigente(persona_id, entidad_id)
        if funcionario is None:
            return {"cargos": []}

        entidad = self._entidad_repository.buscar_por_id(funcionario.entidad_id)
        return {
            "cargos": [
                {
                    "entidad": entidad.nombre if entidad else None,
                    "cargo": str(funcionario.cargo),
                    "dependencia": funcionario.dependencia,
                    "area": funcionario.area_clasificada.value,
                    "vigente": funcionario.vigente,
                    "fecha_inicio": funcionario.fecha_inicio.isoformat() if funcionario.fecha_inicio else None,
                    "fecha_fin": funcionario.fecha_fin.isoformat() if funcionario.fecha_fin else None,
                }
            ]
        }

    def construir_foro(self, persona_master_id: int) -> dict:
        """Publico: reutilizado tambien por `ConsultarPersonaForoUseCase`
        (Submodulo 8.12) para armar la clave "foro" del contrato oficial
        (Submodulo 8.16) sin duplicar la logica de ensamblado."""
        registros = self._registro_foro_repository.listar_vigentes_por_persona_master(persona_master_id)
        historial = self._historial_foro_repository.listar_por_persona_master(persona_master_id)
        eventos = self._evento_foro_repository.listar_por_persona_master(persona_master_id)
        alertas = self._alerta_foro_repository.listar_por_persona_master(persona_master_id)

        return {
            "registros": [asdict(RegistroForoPersistidoDTO.desde_entidad(r)) for r in registros],
            "historial": [
                {
                    "clave_registro": h.clave_registro, "tipo_cambio": h.tipo_cambio.value,
                    "detectado_en": h.detectado_en.isoformat(), "campos_modificados": h.campos_modificados,
                    "descripcion": h.descripcion,
                }
                for h in historial
            ],
            "eventos": [asdict(EventoForoDTO.desde_entidad(e)) for e in eventos],
            "alertas": [asdict(AlertaForoDTO.desde_entidad(a)) for a in alertas],
            "estadisticas": {
                "cantidad_registros_vigentes": len(registros), "cantidad_cambios_historial": len(historial),
                "cantidad_alertas": len(alertas), "cantidad_eventos": len(eventos),
            },
        }
