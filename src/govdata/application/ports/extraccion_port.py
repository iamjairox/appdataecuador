"""Puerto: ExtraccionPort.

Fachada sobre el Motor de Extraccion del Modulo 4 (`ExtraerDocumentoUseCase`)
para UN documento ya descargado -- resuelve la ruta local (que puede
implicar bajar de MinIO a un archivo temporal) antes de invocar el parser.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from govdata.application.dto.resultado_unificado_dto import ResultadoUnificadoDTO
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad


class ExtraccionPort(ABC):
    @abstractmethod
    def extraer(
        self, entidad: Entidad, documento: DocumentoTransparencia, mes_publicado: date
    ) -> ResultadoUnificadoDTO: ...
