"""Caso de uso: ObtenerAlertasFuncionarioUseCase -- Modulo 10 (API REST).

Agrega las 3 fuentes de alertas por `persona_master_id` (Modulos 6/7/8,
congelados), ordenadas por `detectado_en` descendente (mas reciente
primero). Ver `AlertaFuncionarioDTO` para la justificacion completa."""

from __future__ import annotations

from govdata.application.dto.alerta_funcionario_dto import AlertaFuncionarioDTO
from govdata.application.ports.alerta_academica_repository_port import AlertaAcademicaRepositoryPort
from govdata.application.ports.alerta_foro_repository_port import AlertaForoRepositoryPort
from govdata.application.ports.alerta_perfil_repository_port import AlertaPerfilRepositoryPort


class ObtenerAlertasFuncionarioUseCase:
    def __init__(
        self,
        alerta_perfil_repository: AlertaPerfilRepositoryPort,
        alerta_academica_repository: AlertaAcademicaRepositoryPort,
        alerta_foro_repository: AlertaForoRepositoryPort,
    ) -> None:
        self._alerta_perfil_repository = alerta_perfil_repository
        self._alerta_academica_repository = alerta_academica_repository
        self._alerta_foro_repository = alerta_foro_repository

    def ejecutar(self, persona_master_id: int) -> list[AlertaFuncionarioDTO]:
        alertas: list[AlertaFuncionarioDTO] = []
        for alerta in self._alerta_perfil_repository.listar_por_persona_master(persona_master_id):
            alertas.append(
                AlertaFuncionarioDTO(
                    id=str(alerta.id), fuente="identidad", tipo=alerta.tipo.value, prioridad=alerta.prioridad.value,
                    descripcion=alerta.descripcion, detectado_en=alerta.detectado_en, estado=alerta.estado.value,
                )
            )
        for alerta_a in self._alerta_academica_repository.listar_por_persona_master(persona_master_id):
            alertas.append(
                AlertaFuncionarioDTO(
                    id=str(alerta_a.id), fuente="academico", tipo=alerta_a.tipo.value,
                    prioridad=alerta_a.prioridad.value, descripcion=alerta_a.descripcion,
                    detectado_en=alerta_a.detectado_en, estado=alerta_a.estado.value,
                )
            )
        for alerta_f in self._alerta_foro_repository.listar_por_persona_master(persona_master_id):
            alertas.append(
                AlertaFuncionarioDTO(
                    id=str(alerta_f.id), fuente="foro", tipo=alerta_f.tipo.value, prioridad=alerta_f.prioridad.value,
                    descripcion=alerta_f.descripcion, detectado_en=alerta_f.detectado_en, estado=alerta_f.estado.value,
                )
            )
        return sorted(alertas, key=lambda a: a.detectado_en, reverse=True)
