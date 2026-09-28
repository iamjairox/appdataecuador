"""DTO: DiferenciaTituloDTO -- salida del Comparador Academico
(Submodulo 7.7)."""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico


@dataclass(frozen=True, slots=True)
class CampoModificadoTituloDTO:
    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None


@dataclass(frozen=True, slots=True)
class DiferenciaTituloDTO:
    tipo_cambio: TipoCambioAcademico
    """La identidad VIGENTE de este titulo de aqui en adelante."""
    clave_titulo: str
    """Solo distinta de `None` cuando el Comparador Academico (7.7)
    emparejo este titulo por la clave de RESPALDO (titulo+institucion+
    nivel) en vez de la primaria (`numero_registro`) -- tipicamente
    porque broto o cambio el numero de registro. Indica bajo que clave
    ANTERIOR debe buscarse la version vigente a cerrar, para no perder
    continuidad de historial (Submodulo 7.14)."""
    clave_titulo_anterior: str | None = None
    """Datos ACTUALES (None cuando `tipo_cambio == TITULO_ELIMINADO`, el
    titulo ya no aparece en la respuesta de SENESCYT)."""
    datos_actuales: PersonaAcademicaDTO | None = None
    """Datos ANTERIORES (None cuando `tipo_cambio == TITULO_NUEVO`, no
    habia version previa con la que comparar)."""
    datos_anteriores: PersonaAcademicaDTO | None = None
    campos_modificados: tuple[CampoModificadoTituloDTO, ...] = field(default_factory=tuple)

    @property
    def es_cambio(self) -> bool:
        return self.tipo_cambio != TipoCambioAcademico.SIN_CAMBIOS
