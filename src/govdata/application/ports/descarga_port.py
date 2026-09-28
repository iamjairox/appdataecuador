"""Puerto: DescargaPort.

Fachada sobre el pipeline de descarga del Modulo 3 para UN documento ya
descubierto. Ver `descubrimiento_port.py` para el razonamiento completo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.documento import DocumentoTransparencia


class DescargaPort(ABC):
    @abstractmethod
    def descargar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia: ...
