"""Dobles de prueba (fakes) de los puertos nuevos del Modulo 5."""

from __future__ import annotations

import uuid
from datetime import date

from govdata.application.ports.alerta_repository_port import AlertaRepositoryPort
from govdata.application.ports.auditoria_comparacion_repository_port import (
    AuditoriaComparacionRepositoryPort,
)
from govdata.application.ports.evento_repository_port import EventoRepositoryPort
from govdata.application.ports.oportunidad_comercial_repository_port import (
    OportunidadComercialRepositoryPort,
)
from govdata.application.ports.verificacion_remota_port import VerificacionRemotaPort
from govdata.application.ports.verificacion_repository_port import VerificacionRepositoryPort
from govdata.application.ports.version_funcionario_repository_port import (
    VersionFuncionarioRepositoryPort,
)
from govdata.domain.entities.alerta import Alerta
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.domain.entities.evento import Evento
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial
from govdata.domain.entities.verificacion import Verificacion
from govdata.domain.entities.version_funcionario import VersionFuncionario


class FakeVersionFuncionarioRepository(VersionFuncionarioRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[VersionFuncionario] = []

    def guardar(self, version: VersionFuncionario) -> VersionFuncionario:
        if version.id is None:
            version.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(version)
        return version

    def buscar_vigente(self, persona_id: int, entidad_id: int) -> VersionFuncionario | None:
        return next(
            (
                v
                for v in self.guardadas
                if v.persona_id == persona_id and v.entidad_id == entidad_id and v.vigente
            ),
            None,
        )

    def listar_por_persona(self, persona_id: int) -> list[VersionFuncionario]:
        return [v for v in self.guardadas if v.persona_id == persona_id]

    def listar_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> list[VersionFuncionario]:
        return [v for v in self.guardadas if v.entidad_id == entidad_id and v.cargo == cargo]

    def buscar_vigente_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> VersionFuncionario | None:
        return next(
            (v for v in self.guardadas if v.entidad_id == entidad_id and v.cargo == cargo and v.vigente), None
        )

    def buscar_vigente_en_fecha(self, entidad_id: int, cargo: str, en_fecha: date) -> VersionFuncionario | None:
        for v in self.guardadas:
            if v.entidad_id != entidad_id or v.cargo != cargo:
                continue
            if v.fecha_inicio <= en_fecha and (v.fecha_fin is None or en_fecha <= v.fecha_fin):
                return v
        return None

    def listar_por_entidad(self, entidad_id: int) -> list[VersionFuncionario]:
        return [v for v in self.guardadas if v.entidad_id == entidad_id]


class FakeAlertaRepository(AlertaRepositoryPort):
    def __init__(self) -> None:
        self.guardadas: list[Alerta] = []

    def guardar(self, alerta: Alerta) -> Alerta:
        self.guardadas.append(alerta)
        return alerta

    def guardar_lote(self, alertas: list[Alerta]) -> list[Alerta]:
        return [self.guardar(a) for a in alertas]

    def buscar_por_id(self, alerta_id: uuid.UUID) -> Alerta | None:
        return next((a for a in self.guardadas if a.id == alerta_id), None)

    def listar_por_entidad(self, entidad_id: int) -> list[Alerta]:
        return [a for a in self.guardadas if a.entidad_id == entidad_id]

    def listar_por_documento(self, documento_id: int) -> list[Alerta]:
        return [a for a in self.guardadas if a.documento_id == documento_id]


class FakeEventoRepository(EventoRepositoryPort):
    def __init__(self) -> None:
        self.guardados: list[Evento] = []

    def guardar(self, evento: Evento) -> Evento:
        if evento not in self.guardados:
            self.guardados.append(evento)
        return evento

    def guardar_lote(self, eventos: list[Evento]) -> list[Evento]:
        return [self.guardar(e) for e in eventos]

    def buscar_por_id(self, evento_id: uuid.UUID) -> Evento | None:
        return next((e for e in self.guardados if e.id == evento_id), None)

    def listar_pendientes(self, limite: int) -> list[Evento]:
        from govdata.domain.entities.evento import EstadoEvento

        return [e for e in self.guardados if e.estado == EstadoEvento.PENDIENTE][:limite]


class FakeVerificacionRepository(VerificacionRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[Verificacion] = []

    def registrar(self, verificacion: Verificacion) -> Verificacion:
        if verificacion.id is None:
            verificacion.id = self._siguiente_id
            self._siguiente_id += 1
        self.guardadas.append(verificacion)
        return verificacion

    def listar_por_entidad(self, entidad_id: int) -> list[Verificacion]:
        return [v for v in self.guardadas if v.entidad_id == entidad_id]

    def buscar_ultima_por_entidad(self, entidad_id: int) -> Verificacion | None:
        candidatas = self.listar_por_entidad(entidad_id)
        return max(candidatas, key=lambda v: v.verificado_en) if candidatas else None


class FakeAuditoriaComparacionRepository(AuditoriaComparacionRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[AuditoriaComparacion] = []

    def registrar(self, auditoria: AuditoriaComparacion) -> AuditoriaComparacion:
        if auditoria.id is None:
            auditoria.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(auditoria)
        return auditoria

    def listar_por_documento(self, documento_id: int) -> list[AuditoriaComparacion]:
        return [a for a in self.guardadas if a.documento_id == documento_id]


class FakeOportunidadComercialRepository(OportunidadComercialRepositoryPort):
    def __init__(self) -> None:
        self.guardadas: list[OportunidadComercial] = []

    def guardar(self, oportunidad: OportunidadComercial) -> OportunidadComercial:
        self.guardadas.append(oportunidad)
        return oportunidad

    def guardar_lote(self, oportunidades: list[OportunidadComercial]) -> list[OportunidadComercial]:
        return [self.guardar(o) for o in oportunidades]

    def listar_por_entidad(self, entidad_id: int) -> list[OportunidadComercial]:
        return [o for o in self.guardadas if o.entidad_id == entidad_id]


class FakeVerificacionRemota(VerificacionRemotaPort):
    def __init__(self, hay_cambios: bool = True) -> None:
        self._hay_cambios = hay_cambios
        self.llamadas = 0

    def hay_cambios(self, url: str, etag_conocido: str | None, last_modified_conocido: str | None) -> bool:
        self.llamadas += 1
        return self._hay_cambios
