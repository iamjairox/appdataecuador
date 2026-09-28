"""Puerto: DocumentParserPort -- Submodulo 4.1 (Parser Engine).

Cada formato soportado (PDF con tabla, PDF de solo texto, XLS, XLSX, CSV)
tiene su propia implementacion de este puerto (patron Strategy). Nunca
retornan `DataFrame` ni ningun objeto especifico de `pandas`/`openpyxl`/
`camelot`/`xlrd` -- solo `ResultadoParseoDTO`, que a su vez solo contiene
tipos primitivos (`TablaExtraidaDTO`).

Un PDF escaneado (sin capa de texto) NO se trata como error: el parser
debe detectarlo y retornar `EstadoParseo.REQUIERE_OCR` -- ese documento
queda pendiente para el futuro Modulo de OCR, nunca se descarta en
silencio ni se fuerza su procesamiento.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.resultado_parseo_dto import ResultadoParseoDTO
from govdata.domain.entities.documento import TipoArchivo


class DocumentParserPort(ABC):
    """Extrae una tabla cruda de un documento de un formato especifico."""

    @abstractmethod
    def soporta(self, tipo_archivo: TipoArchivo) -> bool:
        """Indica si esta implementacion puede procesar ese tipo de archivo."""

    @abstractmethod
    def extraer(self, ruta_archivo: str) -> ResultadoParseoDTO:
        """Extrae la tabla cruda del documento en `ruta_archivo` (ruta local
        de filesystem -- el llamador es responsable de que el contenido ya
        este disponible localmente, sin importar el backend de storage).

        Nunca lanza excepciones de la libreria subyacente (pdfplumber,
        camelot, openpyxl, xlrd, csv): cualquier fallo de lectura se
        traduce a `ResultadoParseoDTO(estado=ERROR, mensaje=...)`.
        """
