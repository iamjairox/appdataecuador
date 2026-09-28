"""Entidad de dominio: CasoRevisionIdentidad -- Submodulo 6.21 (Motor de
Confianza y Revision Manual).

"En sistemas de resolucion de identidad nunca es recomendable fusionar
automaticamente todas las coincidencias." Cuando el score de dos
identidades candidatas cae en la zona ambigua (85% <= score < 98%), el
sistema NO fusiona: crea uno de estos casos, en PENDIENTE_REVISION, con
la explicacion completa de coincidencias/diferencias, para que una
revision humana (futuro dashboard) decida. Toda decision -- automatica o
manual -- queda auditada aqui: quien/que la tomo, cuando, y con que
criterio.
"""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import CasoRevisionIdentidadInvalidoError
from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad

_TRANSICIONES_VALIDAS: dict[EstadoRevisionIdentidad, set[EstadoRevisionIdentidad]] = {
    EstadoRevisionIdentidad.PENDIENTE_REVISION: {
        EstadoRevisionIdentidad.APROBADO,
        EstadoRevisionIdentidad.RECHAZADO,
    },
    EstadoRevisionIdentidad.APROBADO: set(),
    EstadoRevisionIdentidad.RECHAZADO: set(),
}


@dataclass(slots=True)
class CasoRevisionIdentidad:
    """Caso de revision manual (o auditoria de fusion automatica) entre
    dos identidades candidatas."""

    persona_master_id_a: int
    score: float
    explicacion: str
    campos_utilizados: tuple[str, ...]
    creado_en: datetime
    uuid: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    """Identidad del caso (equivalente al `id: UUID` de `Alerta`/`Evento`,
    Modulo 5 -- se llama `uuid` aqui para no chocar con
    `persona_master_id_a`/`_b`, que ya usan `id` en su nombre)."""
    persona_master_id_b: int | None = None
    registro_fuente_id: int | None = None
    estado: EstadoRevisionIdentidad = EstadoRevisionIdentidad.PENDIENTE_REVISION
    resuelto_en: datetime | None = None
    resuelto_por: str | None = None
    criterio_resolucion: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id_a is None:
            raise CasoRevisionIdentidadInvalidoError("CasoRevisionIdentidad requiere persona_master_id_a")
        if not (0.0 <= self.score <= 100.0):
            raise CasoRevisionIdentidadInvalidoError(f"score fuera de rango [0, 100]: {self.score}")
        if self.persona_master_id_b is None and self.registro_fuente_id is None:
            raise CasoRevisionIdentidadInvalidoError(
                "CasoRevisionIdentidad requiere persona_master_id_b o registro_fuente_id "
                "(contra que se esta comparando)"
            )
        estado_resuelto = self.estado != EstadoRevisionIdentidad.PENDIENTE_REVISION
        if estado_resuelto and (self.resuelto_en is None or self.resuelto_por is None):
            raise CasoRevisionIdentidadInvalidoError(
                "Un caso resuelto requiere resuelto_en y resuelto_por"
            )
        if not estado_resuelto and (self.resuelto_en is not None or self.resuelto_por is not None):
            raise CasoRevisionIdentidadInvalidoError(
                "Un caso PENDIENTE_REVISION no puede tener resuelto_en/resuelto_por"
            )

    def _transicionar(
        self, nuevo_estado: EstadoRevisionIdentidad, por: str, cuando: datetime, criterio: str
    ) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise CasoRevisionIdentidadInvalidoError(
                f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value}"
            )
        self.estado = nuevo_estado
        self.resuelto_en = cuando
        self.resuelto_por = por
        self.criterio_resolucion = criterio

    def aprobar(self, por: str, cuando: datetime, criterio: str = "revision_manual") -> None:
        """Confirma que las dos candidatas son la misma persona -> dispara
        fusion (orquestada por `FusionService`, esta entidad solo registra
        la decision)."""
        self._transicionar(EstadoRevisionIdentidad.APROBADO, por, cuando, criterio)

    def rechazar(self, por: str, cuando: datetime, criterio: str = "revision_manual") -> None:
        """Confirma que son personas distintas -> se mantienen separadas
        permanentemente (el caso queda como historial de la decision)."""
        self._transicionar(EstadoRevisionIdentidad.RECHAZADO, por, cuando, criterio)
