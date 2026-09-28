"""Dobles de prueba (fakes) de los puertos nuevos del Modulo 7."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.alerta_academica_repository_port import (
    AlertaAcademicaRepositoryPort,
)
from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.application.ports.evento_academico_repository_port import (
    EventoAcademicoRepositoryPort,
)
from govdata.application.ports.historial_academico_repository_port import (
    HistorialAcademicoRepositoryPort,
)
from govdata.application.ports.senescyt_port import SenescytPort
from govdata.application.ports.titulo_academico_repository_port import (
    TituloAcademicoRepositoryPort,
)
from govdata.application.ports.titulo_version_repository_port import TituloVersionRepositoryPort
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.entities.titulo_version_academica import (
    EstadoVersionAcademica,
    TituloVersionAcademica,
)
from govdata.domain.value_objects.estado_alerta_academica import EstadoAlertaAcademica
from govdata.domain.value_objects.estado_evento_academico import EstadoEventoAcademico


class FakeTituloAcademicoRepository(TituloAcademicoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[TituloAcademico] = []

    def guardar(self, titulo: TituloAcademico) -> TituloAcademico:
        if titulo.id is None:
            titulo.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardados.append(titulo)
        return titulo

    def buscar_vigente_por_clave(self, persona_master_id: int, clave_titulo: str) -> TituloAcademico | None:
        return next(
            (
                t
                for t in self.guardados
                if t.persona_master_id == persona_master_id and t.clave_titulo == clave_titulo and t.vigente
            ),
            None,
        )

    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[TituloAcademico]:
        return [t for t in self.guardados if t.persona_master_id == persona_master_id and t.vigente]


class FakeTituloVersionRepository(TituloVersionRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[TituloVersionAcademica] = []

    def guardar(self, version: TituloVersionAcademica) -> TituloVersionAcademica:
        if version.id is None:
            version.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(version)
        return version

    def buscar_vigente(self, persona_master_id: int, clave_titulo: str) -> TituloVersionAcademica | None:
        return next(
            (
                v
                for v in self.guardadas
                if v.persona_master_id == persona_master_id
                and v.clave_titulo == clave_titulo
                and v.estado_version == EstadoVersionAcademica.VIGENTE
            ),
            None,
        )

    def listar_historial(self, persona_master_id: int, clave_titulo: str) -> list[TituloVersionAcademica]:
        return sorted(
            (
                v
                for v in self.guardadas
                if v.persona_master_id == persona_master_id and v.clave_titulo == clave_titulo
            ),
            key=lambda v: v.numero_version,
        )

    def listar_por_persona_master(self, persona_master_id: int) -> list[TituloVersionAcademica]:
        return [v for v in self.guardadas if v.persona_master_id == persona_master_id]


class FakeHistorialAcademicoRepository(HistorialAcademicoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[HistorialAcademico] = []

    def guardar_lote(self, registros: list[HistorialAcademico]) -> list[HistorialAcademico]:
        for registro in registros:
            if registro.id is None:
                registro.id = self._siguiente_id
                self._siguiente_id += 1
                self.guardados.append(registro)
        return registros

    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialAcademico]:
        return [h for h in self.guardados if h.persona_master_id == persona_master_id]

    def listar_todo(self) -> list[HistorialAcademico]:
        return list(self.guardados)


class FakeConsultaSenescytRepository(ConsultaSenescytRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[ConsultaSenescyt] = []

    def guardar(self, consulta: ConsultaSenescyt) -> ConsultaSenescyt:
        if consulta.id is None:
            consulta.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(consulta)
        return consulta

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaSenescyt]:
        return [c for c in self.guardadas if c.persona_master_id == persona_master_id]

    def ultima_consulta(self, persona_master_id: int) -> ConsultaSenescyt | None:
        candidatas = self.listar_por_persona_master(persona_master_id)
        return max(candidatas, key=lambda c: c.iniciado_en) if candidatas else None

    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaSenescyt]:
        if desde is None:
            return list(self.guardadas)
        return [c for c in self.guardadas if c.iniciado_en >= desde]


class FakeEventoAcademicoRepository(EventoAcademicoRepositoryPort):
    def __init__(self) -> None:
        self.guardados: list[EventoAcademico] = []

    def guardar(self, evento: EventoAcademico) -> EventoAcademico:
        if evento not in self.guardados:
            self.guardados.append(evento)
        return evento

    def guardar_lote(self, eventos: list[EventoAcademico]) -> list[EventoAcademico]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoAcademico | None:
        return next((e for e in self.guardados if e.id == evento_id), None)

    def listar_pendientes(self, limite: int = 100) -> list[EventoAcademico]:
        return [e for e in self.guardados if e.estado == EstadoEventoAcademico.PENDIENTE][:limite]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoAcademico]:
        return [e for e in self.guardados if e.persona_master_id == persona_master_id]


class FakeAlertaAcademicaRepository(AlertaAcademicaRepositoryPort):
    def __init__(self) -> None:
        self.guardadas: list[AlertaAcademica] = []

    def guardar(self, alerta: AlertaAcademica) -> AlertaAcademica:
        if alerta not in self.guardadas:
            self.guardadas.append(alerta)
        return alerta

    def guardar_lote(self, alertas: list[AlertaAcademica]) -> list[AlertaAcademica]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaAcademica | None:
        return next((a for a in self.guardadas if a.id == alerta_id), None)

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaAcademica]:
        return [a for a in self.guardadas if a.persona_master_id == persona_master_id]

    def listar_pendientes(self, limite: int = 100) -> list[AlertaAcademica]:
        return [a for a in self.guardadas if a.estado == EstadoAlertaAcademica.PENDIENTE][:limite]


class FakeSenescytPort(SenescytPort):
    """Doble de prueba de SENESCYT -- el proximo adaptador real
    (`SenescytAdapter`) implementa el mismo contrato."""

    def __init__(
        self, resultados_por_llamada: list[list[PersonaAcademicaDTO]] | None = None, error: Exception | None = None
    ) -> None:
        self._resultados_por_llamada = resultados_por_llamada or []
        self._error = error
        self.llamadas = 0

    def _siguiente(self) -> list[PersonaAcademicaDTO]:
        indice = self.llamadas
        self.llamadas += 1
        if self._error is not None:
            raise self._error
        if indice >= len(self._resultados_por_llamada):
            return []
        return self._resultados_por_llamada[indice]

    def consultar_por_cedula(self, cedula: str) -> list[PersonaAcademicaDTO]:
        return self._siguiente()

    def consultar_por_nombres(self, nombres: str, apellidos: str) -> list[PersonaAcademicaDTO]:
        return self._siguiente()

    def consultar_por_identidad(self, senales: SenalesIdentidadDTO) -> list[PersonaAcademicaDTO]:
        return self._siguiente()

    def consultar_por_persona_master(self, persona_master: PersonaMaster) -> list[PersonaAcademicaDTO]:
        return self._siguiente()
