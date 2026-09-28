"""Dobles de prueba (fakes) de los puertos nuevos del Modulo 8."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.alerta_foro_repository_port import AlertaForoRepositoryPort
from govdata.application.ports.consulta_foro_repository_port import ConsultaForoRepositoryPort
from govdata.application.ports.evento_foro_repository_port import EventoForoRepositoryPort
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.application.ports.historial_foro_repository_port import HistorialForoRepositoryPort
from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.application.ports.registro_foro_version_repository_port import (
    RegistroForoVersionRepositoryPort,
)
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.entities.historial_foro import HistorialForo
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.entities.registro_foro_version import EstadoVersionForo, RegistroForoVersion
from govdata.domain.value_objects.estado_alerta_foro import EstadoAlertaForo
from govdata.domain.value_objects.estado_evento_foro import EstadoEventoForo


class FakeRegistroForoRepository(RegistroForoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[RegistroForo] = []

    def guardar(self, registro: RegistroForo) -> RegistroForo:
        if registro.id is None:
            registro.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardados.append(registro)
        return registro

    def buscar_vigente_por_clave(self, persona_master_id: int, clave_registro: str) -> RegistroForo | None:
        return next(
            (
                r
                for r in self.guardados
                if r.persona_master_id == persona_master_id and r.clave_registro == clave_registro and r.vigente
            ),
            None,
        )

    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[RegistroForo]:
        return [r for r in self.guardados if r.persona_master_id == persona_master_id and r.vigente]


class FakeRegistroForoVersionRepository(RegistroForoVersionRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[RegistroForoVersion] = []

    def guardar(self, version: RegistroForoVersion) -> RegistroForoVersion:
        if version.id is None:
            version.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(version)
        return version

    def buscar_vigente(self, persona_master_id: int, clave_registro: str) -> RegistroForoVersion | None:
        return next(
            (
                v
                for v in self.guardadas
                if v.persona_master_id == persona_master_id
                and v.clave_registro == clave_registro
                and v.estado_version == EstadoVersionForo.VIGENTE
            ),
            None,
        )

    def listar_historial(self, persona_master_id: int, clave_registro: str) -> list[RegistroForoVersion]:
        return sorted(
            (
                v
                for v in self.guardadas
                if v.persona_master_id == persona_master_id and v.clave_registro == clave_registro
            ),
            key=lambda v: v.numero_version,
        )

    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroForoVersion]:
        return [v for v in self.guardadas if v.persona_master_id == persona_master_id]


class FakeHistorialForoRepository(HistorialForoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[HistorialForo] = []

    def guardar_lote(self, registros: list[HistorialForo]) -> list[HistorialForo]:
        for registro in registros:
            if registro.id is None:
                registro.id = self._siguiente_id
                self._siguiente_id += 1
                self.guardados.append(registro)
        return registros

    def listar_por_persona_master(self, persona_master_id: int) -> list[HistorialForo]:
        return [h for h in self.guardados if h.persona_master_id == persona_master_id]

    def listar_todo(self) -> list[HistorialForo]:
        return list(self.guardados)


class FakeConsultaForoRepository(ConsultaForoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[ConsultaForo] = []

    def guardar(self, consulta: ConsultaForo) -> ConsultaForo:
        if consulta.id is None:
            consulta.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(consulta)
        return consulta

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaForo]:
        return [c for c in self.guardadas if c.persona_master_id == persona_master_id]

    def ultima_consulta(self, persona_master_id: int) -> ConsultaForo | None:
        candidatas = self.listar_por_persona_master(persona_master_id)
        return max(candidatas, key=lambda c: c.iniciado_en) if candidatas else None

    def listar_todas(self, desde: datetime | None = None) -> list[ConsultaForo]:
        if desde is None:
            return list(self.guardadas)
        return [c for c in self.guardadas if c.iniciado_en >= desde]


class FakeEventoForoRepository(EventoForoRepositoryPort):
    def __init__(self) -> None:
        self.guardados: list[EventoForo] = []

    def guardar(self, evento: EventoForo) -> EventoForo:
        if evento not in self.guardados:
            self.guardados.append(evento)
        return evento

    def guardar_lote(self, eventos: list[EventoForo]) -> list[EventoForo]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoForo | None:
        return next((e for e in self.guardados if e.id == evento_id), None)

    def listar_pendientes(self, limite: int = 100) -> list[EventoForo]:
        return [e for e in self.guardados if e.estado == EstadoEventoForo.PENDIENTE][:limite]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoForo]:
        return [e for e in self.guardados if e.persona_master_id == persona_master_id]


class FakeAlertaForoRepository(AlertaForoRepositoryPort):
    def __init__(self) -> None:
        self.guardadas: list[AlertaForo] = []

    def guardar(self, alerta: AlertaForo) -> AlertaForo:
        if alerta not in self.guardadas:
            self.guardadas.append(alerta)
        return alerta

    def guardar_lote(self, alertas: list[AlertaForo]) -> list[AlertaForo]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaForo | None:
        return next((a for a in self.guardadas if a.id == alerta_id), None)

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaForo]:
        return [a for a in self.guardadas if a.persona_master_id == persona_master_id]

    def listar_pendientes(self, limite: int = 100) -> list[AlertaForo]:
        return [a for a in self.guardadas if a.estado == EstadoAlertaForo.PENDIENTE][:limite]


class FakeForoAbogadosPort(ForoAbogadosPort):
    """Doble de prueba del Foro de Abogados -- el adaptador real
    (`ForoAbogadosAdapter`) implementa el mismo contrato."""

    def __init__(
        self, resultados_por_llamada: list[list[RegistroForoDTO]] | None = None, error: Exception | None = None
    ) -> None:
        self._resultados_por_llamada = resultados_por_llamada or []
        self._error = error
        self.llamadas = 0

    def _siguiente(self) -> list[RegistroForoDTO]:
        indice = self.llamadas
        self.llamadas += 1
        if self._error is not None:
            raise self._error
        if indice >= len(self._resultados_por_llamada):
            return []
        return self._resultados_por_llamada[indice]

    def buscar_por_cedula(self, cedula: str) -> list[RegistroForoDTO]:
        return self._siguiente()

    def buscar_por_persona(self, persona: Persona) -> list[RegistroForoDTO]:
        return self._siguiente()

    def buscar_por_persona_master(self, persona_master: PersonaMaster) -> list[RegistroForoDTO]:
        return self._siguiente()
