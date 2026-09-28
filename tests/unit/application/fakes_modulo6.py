"""Dobles de prueba (fakes) de los puertos nuevos del Modulo 6."""

from __future__ import annotations

import uuid
from datetime import datetime

from govdata.application.dto.resultado_consulta_fuente_dto import ResultadoConsultaFuenteDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.alerta_perfil_repository_port import AlertaPerfilRepositoryPort
from govdata.application.ports.atributo_trazable_repository_port import (
    AtributoTrazableRepositoryPort,
)
from govdata.application.ports.caso_revision_identidad_repository_port import (
    CasoRevisionIdentidadRepositoryPort,
)
from govdata.application.ports.consulta_fuente_log_repository_port import (
    ConsultaFuenteLogRepositoryPort,
)
from govdata.application.ports.evento_perfil_repository_port import EventoPerfilRepositoryPort
from govdata.application.ports.fuentes_externas_ports import ExternalSourcePort
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.ports.registro_fuente_repository_port import RegistroFuenteRepositoryPort
from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class FakePersonaMasterRepository(PersonaMasterRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[PersonaMaster] = []

    def guardar(self, persona_master: PersonaMaster) -> PersonaMaster:
        if persona_master.id is None:
            persona_master.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(persona_master)
        return persona_master

    def buscar_por_id(self, persona_master_id: int) -> PersonaMaster | None:
        return next((p for p in self.guardadas if p.id == persona_master_id), None)

    def buscar_por_persona_id(self, persona_id: int) -> PersonaMaster | None:
        return next((p for p in self.guardadas if p.persona_id == persona_id), None)

    def buscar_por_fingerprint_principal(self, fingerprint: str) -> PersonaMaster | None:
        return next(
            (
                p
                for p in self.guardadas
                if p.fingerprint_principal == fingerprint and p.estado != EstadoPersonaMaster.FUSIONADA
            ),
            None,
        )

    def buscar_candidatas_por_fingerprint_fonetico(self, fingerprint_fonetico: str) -> list[PersonaMaster]:
        return [
            p
            for p in self.guardadas
            if p.fingerprint_fonetico == fingerprint_fonetico and p.estado != EstadoPersonaMaster.FUSIONADA
        ]

    def buscar_candidatas_por_correo(self, correo: str) -> list[PersonaMaster]:
        correo_norm = correo.strip().lower()
        return [
            p
            for p in self.guardadas
            if p.correo_principal is not None
            and str(p.correo_principal) == correo_norm
            and p.estado != EstadoPersonaMaster.FUSIONADA
        ]

    def listar_activas(self, limite: int, offset: int = 0) -> list[PersonaMaster]:
        activas = [p for p in self.guardadas if p.estado != EstadoPersonaMaster.FUSIONADA]
        return activas[offset : offset + limite]

    def contar_activas(self) -> int:
        return len([p for p in self.guardadas if p.estado != EstadoPersonaMaster.FUSIONADA])


class FakeRegistroFuenteRepository(RegistroFuenteRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[RegistroFuente] = []

    def guardar(self, registro: RegistroFuente) -> RegistroFuente:
        if registro.id is None:
            registro.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardados.append(registro)
        return registro

    def buscar_vigente(self, persona_master_id: int, fuente: FuenteExterna) -> RegistroFuente | None:
        return next(
            (
                r
                for r in self.guardados
                if r.persona_master_id == persona_master_id and r.fuente == fuente and r.vigente
            ),
            None,
        )

    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroFuente]:
        return [r for r in self.guardados if r.persona_master_id == persona_master_id]

    def listar_historial(self, persona_master_id: int, fuente: FuenteExterna) -> list[RegistroFuente]:
        return sorted(
            (r for r in self.guardados if r.persona_master_id == persona_master_id and r.fuente == fuente),
            key=lambda r: r.version,
        )


class FakeAtributoTrazableRepository(AtributoTrazableRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[AtributoTrazable] = []

    def guardar_lote(self, atributos: list[AtributoTrazable]) -> list[AtributoTrazable]:
        for atributo in atributos:
            if atributo.id is None:
                atributo.id = self._siguiente_id
                self._siguiente_id += 1
                self.guardados.append(atributo)
        return atributos

    def listar_por_persona_master(self, persona_master_id: int) -> list[AtributoTrazable]:
        return [a for a in self.guardados if a.persona_master_id == persona_master_id]


class FakeCasoRevisionIdentidadRepository(CasoRevisionIdentidadRepositoryPort):
    def __init__(self) -> None:
        self.guardados: list[CasoRevisionIdentidad] = []

    def guardar(self, caso: CasoRevisionIdentidad) -> CasoRevisionIdentidad:
        if caso not in self.guardados:
            self.guardados.append(caso)
        return caso

    def buscar_por_id(self, caso_id: uuid.UUID) -> CasoRevisionIdentidad | None:
        return next((c for c in self.guardados if c.uuid == caso_id), None)

    def listar_pendientes(self, limite: int = 100) -> list[CasoRevisionIdentidad]:
        from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad

        return [c for c in self.guardados if c.estado == EstadoRevisionIdentidad.PENDIENTE_REVISION][:limite]

    def buscar_pendiente_entre(
        self, persona_master_id_a: int, persona_master_id_b: int
    ) -> CasoRevisionIdentidad | None:
        from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad

        pares = {frozenset({persona_master_id_a, persona_master_id_b})}
        return next(
            (
                c
                for c in self.guardados
                if c.estado == EstadoRevisionIdentidad.PENDIENTE_REVISION
                and frozenset({c.persona_master_id_a, c.persona_master_id_b}) in pares
            ),
            None,
        )


class FakeConsultaFuenteLogRepository(ConsultaFuenteLogRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[ConsultaFuenteLog] = []

    def guardar(self, log: ConsultaFuenteLog) -> ConsultaFuenteLog:
        if log.id is None:
            log.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardados.append(log)
        return log

    def listar_por_persona_master(self, persona_master_id: int) -> list[ConsultaFuenteLog]:
        return [log for log in self.guardados if log.persona_master_id == persona_master_id]

    def ultima_consulta(self, persona_master_id: int, fuente: FuenteExterna) -> ConsultaFuenteLog | None:
        candidatas = [
            log
            for log in self.guardados
            if log.persona_master_id == persona_master_id and log.fuente == fuente
        ]
        return max(candidatas, key=lambda log: log.iniciado_en) if candidatas else None


class FakeEventoPerfilRepository(EventoPerfilRepositoryPort):
    def __init__(self) -> None:
        self.guardados: list[EventoPerfil] = []

    def guardar(self, evento: EventoPerfil) -> EventoPerfil:
        if evento not in self.guardados:
            self.guardados.append(evento)
        return evento

    def guardar_lote(self, eventos: list[EventoPerfil]) -> list[EventoPerfil]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> EventoPerfil | None:
        return next((e for e in self.guardados if e.id == evento_id), None)

    def listar_pendientes(self, limite: int = 100) -> list[EventoPerfil]:
        from govdata.domain.value_objects.estado_evento_perfil import EstadoEventoPerfil

        return [e for e in self.guardados if e.estado == EstadoEventoPerfil.PENDIENTE][:limite]

    def listar_por_persona_master(self, persona_master_id: int) -> list[EventoPerfil]:
        return [e for e in self.guardados if e.persona_master_id == persona_master_id]


class FakeAlertaPerfilRepository(AlertaPerfilRepositoryPort):
    def __init__(self) -> None:
        self.guardadas: list[AlertaPerfil] = []

    def guardar(self, alerta: AlertaPerfil) -> AlertaPerfil:
        if alerta not in self.guardadas:
            self.guardadas.append(alerta)
        return alerta

    def guardar_lote(self, alertas: list[AlertaPerfil]) -> list[AlertaPerfil]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> AlertaPerfil | None:
        return next((a for a in self.guardadas if a.id == alerta_id), None)

    def listar_por_persona_master(self, persona_master_id: int) -> list[AlertaPerfil]:
        return [a for a in self.guardadas if a.persona_master_id == persona_master_id]


class FakeExternalSourcePort(ExternalSourcePort):
    """Doble de prueba de una fuente externa (Submodulo 6.6) -- el
    proximo modulo (SENESCYT) reemplazara esto por un adaptador real."""

    def __init__(
        self,
        fuente: FuenteExterna,
        datos_por_llamada: list[dict] | None = None,
        error: Exception | None = None,
        ahora_provider=lambda: datetime.now(),  # noqa: DTZ005 -- override en tests con UTC real
    ) -> None:
        self._fuente = fuente
        self._datos_por_llamada = datos_por_llamada or []
        self._error = error
        self._ahora_provider = ahora_provider
        self.llamadas = 0

    @property
    def fuente(self) -> FuenteExterna:
        return self._fuente

    def consultar(self, senales: SenalesIdentidadDTO) -> ResultadoConsultaFuenteDTO:
        indice = self.llamadas
        self.llamadas += 1
        if self._error is not None:
            raise self._error
        if indice >= len(self._datos_por_llamada):
            return ResultadoConsultaFuenteDTO(
                fuente=self._fuente, encontrado=False, consultado_en=self._ahora_provider(), datos={}
            )
        return ResultadoConsultaFuenteDTO(
            fuente=self._fuente,
            encontrado=True,
            consultado_en=self._ahora_provider(),
            datos=self._datos_por_llamada[indice],
        )
