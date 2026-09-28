"""Puertos: Fuentes Externas -- Submodulo 6.6.

"NO implementar aun SENESCYT... construir la infraestructura, crear
UNICAMENTE puertos." Este archivo declara el contrato comun
(`ExternalSourcePort`) y un puerto especifico por fuente futura -- todos
abstractos, CERO adaptadores. El siguiente modulo (SENESCYT) solo debe
crear una clase que implemente `SenescytPort` y reutilizar todo el
pipeline de Enriquecimiento (Submodulo 6.7) sin tocar nada de este.

Cada puerto especifico hereda de `ExternalSourcePort` en vez de
duplicar la firma -- Open/Closed: agregar una fuente nueva es agregar una
clase, nunca modificar el motor que las consume (`EnriquecimientoService`
solo conoce `ExternalSourcePort`, jamas un tipo concreto).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.resultado_consulta_fuente_dto import ResultadoConsultaFuenteDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class ExternalSourcePort(ABC):
    """Contrato comun de toda fuente externa consultable por el Motor de
    Enriquecimiento."""

    @property
    @abstractmethod
    def fuente(self) -> FuenteExterna: ...

    @abstractmethod
    def consultar(self, senales: SenalesIdentidadDTO) -> ResultadoConsultaFuenteDTO:
        """Consulta la fuente por las senales de identidad disponibles
        (nombre, apellido, cedula si la hubiera, correo...). Debe lanzar
        una subclase de `GovDataError` en fallas transitorias (red,
        timeout) para que el orquestador las audite y reintente segun su
        propia politica -- nunca silenciar el error internamente."""


class SenescytPort(ExternalSourcePort, ABC):
    """Titulos, profesiones y especializaciones registradas en SENESCYT.
    Pendiente de implementacion -- proximo modulo."""


class ForoAbogadosPort(ExternalSourcePort, ABC):
    """Matricula y estado de ejercicio profesional en el Foro de Abogados.
    Pendiente de implementacion."""


class FuncionJudicialPort(ExternalSourcePort, ABC):
    """Causas y roles en la Funcion Judicial. Pendiente de implementacion."""


class SriPort(ExternalSourcePort, ABC):
    """RUC y estado tributario en el SRI. Pendiente de implementacion."""


class ContraloriaPort(ExternalSourcePort, ABC):
    """Declaraciones e informes de la Contraloria General del Estado.
    Pendiente de implementacion."""


class RegistroMercantilPort(ExternalSourcePort, ABC):
    """Participacion societaria en el Registro Mercantil. Pendiente de
    implementacion."""
