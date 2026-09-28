"""DTO: ResultadoUnificadoDTO -- Submodulo 4.10.

EL CONTRATO OFICIAL del Motor de Extraccion. TODOS los parsers, sin
importar el formato de origen (PDF/XLS/XLSX/CSV), convergen a esta misma
forma tras pasar por Normalizador -> Clasificador -> Identity Resolution.
Los modulos 5, 6, 7, la futura API, el Dashboard y n8n dependen de este
contrato exacto -- cambiar los NOMBRES de estos campos (no su contenido)
es un cambio incompatible y no debe hacerse sin versionar el contrato.

`FuncionarioUnificadoDTO` usa deliberadamente los nombres de campo
EXACTOS pedidos por el cliente (`nombre`/`apellido`, singular) aunque en
el resto del sistema de dominio se use `nombres`/`apellidos` (plural,
Value Objects) -- este DTO es la capa de PRESENTACION del contrato, no el
modelo de dominio interno.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class EntidadResumenDTO:
    id: int
    nombre: str
    portal_origen: str
    identificador_portal: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentoResumenDTO:
    id: int
    tipo_archivo: str
    mes_publicado: date
    hash_sha256: str
    version: int
    url: str


@dataclass(frozen=True, slots=True)
class FuncionarioUnificadoDTO:
    """Un funcionario clasificado, forma EXACTA del contrato oficial."""

    nombre: str
    apellido: str
    cargo: str
    dependencia: str
    correo: str | None
    telefono: str | None
    area: str
    score: float
    fingerprint: str


@dataclass(frozen=True, slots=True)
class ResultadoUnificadoDTO:
    """`{"entidad": {}, "documento": {}, "funcionarios": [...]}`."""

    entidad: EntidadResumenDTO
    documento: DocumentoResumenDTO | None
    funcionarios: list[FuncionarioUnificadoDTO] = field(default_factory=list)
    generado_en: datetime | None = None

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n)."""
        return asdict(self)
