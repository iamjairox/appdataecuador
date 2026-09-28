"""Entidad de dominio: ConsultaForo -- Submodulo 8.17 (Auditoria):
"Registrar: Inicio. Fin. Tiempo. Respuesta. Codigo HTTP. Cache. Version.
Usuario. Job."

Mas rica que `ConsultaSenescyt` (Modulo 7): agrega los campos de
deteccion propios de un scraper HTML tolerante (Submodulo 8.2) --
`codigo_http`, `captcha_detectado`, `pagina_vacia` -- y los campos de
auditoria explicitos que 8.17 pide por nombre y que Modulo 7 no
necesitaba (`usuario`, `job_id`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import ConsultaForoInvalidaError


@dataclass(slots=True)
class ConsultaForo:
    """Un intento (exitoso o fallido) de consulta al Foro de Abogados
    para una PersonaMaster."""

    persona_master_id: int
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    exito: bool | None = None
    duracion_segundos: float | None = None
    error: str | None = None
    reintentos: int = 0
    cache_utilizado: bool = False
    version_resultante: int | None = None
    respuesta_cruda: dict[str, Any] | None = None
    """Evidencia: referencia estructurada de lo que el Foro devolvio (nunca
    el HTML crudo completo -- ver `ForoAbogadosAdapter`), para poder
    auditar de donde salio un dato."""
    codigo_http: int | None = None
    captcha_detectado: bool = False
    pagina_vacia: bool = False
    usuario: str = "sistema"
    job_id: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise ConsultaForoInvalidaError("ConsultaForo requiere persona_master_id")
        if self.reintentos < 0:
            raise ConsultaForoInvalidaError("reintentos no puede ser negativo")
        if self.finalizado_en is not None and self.finalizado_en < self.iniciado_en:
            raise ConsultaForoInvalidaError("finalizado_en no puede ser anterior a iniciado_en")

    def finalizar(
        self,
        exito: bool,
        cuando: datetime,
        duracion_segundos: float,
        error: str | None = None,
        version_resultante: int | None = None,
        respuesta_cruda: dict[str, Any] | None = None,
        cache_utilizado: bool = False,
        codigo_http: int | None = None,
        captcha_detectado: bool = False,
        pagina_vacia: bool = False,
    ) -> None:
        if cuando < self.iniciado_en:
            raise ConsultaForoInvalidaError("No se puede finalizar antes de iniciado_en")
        self.exito = exito
        self.finalizado_en = cuando
        self.duracion_segundos = duracion_segundos
        self.error = error
        self.version_resultante = version_resultante
        self.respuesta_cruda = respuesta_cruda
        self.cache_utilizado = cache_utilizado
        self.codigo_http = codigo_http
        self.captcha_detectado = captcha_detectado
        self.pagina_vacia = pagina_vacia

    def registrar_reintento(self) -> None:
        self.reintentos += 1
