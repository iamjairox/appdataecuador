"""Entidad de dominio: RegistroForo -- Submodulo 8.1 (puntero vigente).

Analoga a `TituloAcademico` (Modulo 7): la fila "actual" de la matricula
de un abogado en el Foro de Abogados para una PersonaMaster, identificada
por `clave_registro` (Submodulo 8.5, `generar_clave_registro`). El
historial append-only completo vive en `RegistroForoVersion`; esta fila
SIEMPRE refleja el ultimo estado conocido.

Incluye los mismos metadatos de confiabilidad por fuente sugeridos por el
cliente en Modulo 7 (`fuente`, `fecha_consulta`, `nivel_confianza`,
`version_fuente`, `evidencia`) -- para que, cuando existan mas fuentes
sobre el mismo profesional (Funcion Judicial, Contraloria, ...), el
sistema pueda decidir cual prevalece sin perder trazabilidad."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import RegistroForoInvalidoError
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo


@dataclass(slots=True)
class RegistroForo:
    """Snapshot vigente de la matricula de un abogado en el Foro, para
    una PersonaMaster."""

    persona_master_id: int
    clave_registro: str
    id: int | None = None
    nombre_completo: str | None = None
    """Tal como lo reporta el Foro -- nunca se inventa, puede venir vacio
    si el HTML no lo expone (Submodulo 8.4: "extraer unicamente los datos
    disponibles")."""
    registro: str | None = None
    provincia: str | None = None
    estado: EstadoRegistroForo = EstadoRegistroForo.DESCONOCIDO
    cedula: str | None = None
    numero_version: int = 1
    vigente: bool = True
    fuente: str = "foro_abogados"
    fecha_consulta: datetime | None = None
    nivel_confianza: float = 100.0
    version_fuente: int = 1
    evidencia: str | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.nombre_completo and not self.registro and not self.cedula:
            raise RegistroForoInvalidoError(
                "RegistroForo requiere al menos uno de: nombre_completo, registro, cedula"
            )
        if not (0.0 <= self.nivel_confianza <= 100.0):
            raise RegistroForoInvalidoError(f"nivel_confianza fuera de rango [0, 100]: {self.nivel_confianza}")
        if self.numero_version < 1:
            raise RegistroForoInvalidoError(f"numero_version invalida: {self.numero_version}")

    def cerrar(self) -> None:
        """El registro fue eliminado de la respuesta del Foro (o dejo de
        aparecer para esa cedula) -- deja de ser vigente (nunca se borra,
        ver `RegistroForoVersion`)."""
        self.vigente = False
