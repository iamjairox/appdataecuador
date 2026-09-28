"""DTO: DiferenciaRegistroForoDTO -- salida del Comparador Foro
(Submodulo 8.5)."""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo


@dataclass(frozen=True, slots=True)
class CampoModificadoForoDTO:
    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None


@dataclass(frozen=True, slots=True)
class DiferenciaRegistroForoDTO:
    tipo_cambio: TipoCambioForo
    """La identidad VIGENTE de este registro de aqui en adelante."""
    clave_registro: str
    """Solo distinta de `None` cuando el Comparador Foro (8.5) emparejo
    este registro por la clave de RESPALDO (nombre_completo+provincia) en
    vez de la primaria (`registro`) -- tipicamente porque broto o cambio
    el numero de registro. Indica bajo que clave ANTERIOR debe buscarse
    la version vigente a cerrar, para no perder continuidad de historial
    (Submodulo 8.6/8.14)."""
    clave_registro_anterior: str | None = None
    """Datos ACTUALES (None cuando `tipo_cambio == DATO_ELIMINADO`, el
    registro ya no aparece en la respuesta del Foro)."""
    datos_actuales: RegistroForoDTO | None = None
    """Datos ANTERIORES (None cuando `tipo_cambio == DATO_NUEVO`, no
    habia version previa con la que comparar)."""
    datos_anteriores: RegistroForoDTO | None = None
    campos_modificados: tuple[CampoModificadoForoDTO, ...] = field(default_factory=tuple)

    @property
    def es_cambio(self) -> bool:
        return self.tipo_cambio != TipoCambioForo.SIN_CAMBIOS
