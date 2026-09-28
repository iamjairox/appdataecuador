"""Entidad de dominio: TituloAcademico -- Submodulo 7.6 (puntero vigente).

Analoga a `Funcionario` (Modulo 4/5) o `RegistroFuente` vigente (Modulo
6): la fila "actual" de un titulo para una PersonaMaster, identificado por
`clave_titulo` (Submodulo 7.7, `generar_clave_titulo`). El historial
append-only completo vive en `TituloVersionAcademica`; esta fila SIEMPRE
refleja el ultimo estado conocido.

Incluye los metadatos de confiabilidad por fuente sugeridos por el
cliente (Submodulo 7.20, mejora 1): `fuente`, `fecha_consulta`,
`nivel_confianza`, `version_fuente`, `evidencia` -- para que, cuando
existan mas fuentes ademas de SENESCYT sobre el mismo dato academico, el
sistema pueda decidir cual prevalece sin perder trazabilidad.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.exceptions.domain_exceptions import TituloAcademicoInvalidoError
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico


@dataclass(slots=True)
class TituloAcademico:
    """Snapshot vigente de un titulo academico para una PersonaMaster."""

    persona_master_id: int
    clave_titulo: str
    titulo: str
    nivel: str
    institucion: str
    id: int | None = None
    fecha_registro: date | None = None
    pais: str | None = None
    estado: EstadoRegistroAcademico = EstadoRegistroAcademico.DESCONOCIDO
    modalidad: str | None = None
    numero_registro: str | None = None
    area_conocimiento: str | None = None
    tipo_titulo: str | None = None
    fecha_graduacion: date | None = None
    observaciones: str | None = None
    numero_version: int = 1
    vigente: bool = True
    fuente: str = "senescyt"
    fecha_consulta: datetime | None = None
    nivel_confianza: float = 100.0
    version_fuente: int = 1
    evidencia: str | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.titulo or not self.titulo.strip():
            raise TituloAcademicoInvalidoError("TituloAcademico requiere titulo no vacio")
        if not self.institucion or not self.institucion.strip():
            raise TituloAcademicoInvalidoError("TituloAcademico requiere institucion no vacia")
        if not self.nivel or not self.nivel.strip():
            raise TituloAcademicoInvalidoError("TituloAcademico requiere nivel no vacio")
        if not (0.0 <= self.nivel_confianza <= 100.0):
            raise TituloAcademicoInvalidoError(f"nivel_confianza fuera de rango [0, 100]: {self.nivel_confianza}")
        if self.numero_version < 1:
            raise TituloAcademicoInvalidoError(f"numero_version invalida: {self.numero_version}")

    def cerrar(self) -> None:
        """El titulo fue eliminado de la respuesta de SENESCYT -- deja de
        ser vigente (nunca se borra, ver `TituloVersionAcademica`)."""
        self.vigente = False
