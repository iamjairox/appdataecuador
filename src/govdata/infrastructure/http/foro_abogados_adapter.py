"""Adaptador: ForoAbogadosAdapter -- Submodulo 8.2.

"Debe ser extremadamente tolerante a cambios." Implementa `ForoAbogadosPort`
(8.1) via HTTP + el Parser HTML dedicado (8.4, `foro_html_parser.py`).
Detecta explicitamente, con logs completos en cada caso:

    - Cambio de HTML / cambio de nombres de campos: delegado al parser
      tolerante (8.4) + catalogo YAML (8.3) -- nunca hardcodeado aqui.
    - Mensajes de error / CAPTCHA: escaneo de palabras clave en el texto
      de la respuesta.
    - Timeout / errores HTTP / respuesta invalida: manejo explicito por
      cada rama de `requests`.
    - Pagina vacia: contenido demasiado corto tras remover espacios.

Reintentos inteligentes (Submodulo 8.9): reutiliza
`shared.retry.retry_policy.con_reintentos` (Modulo 1, NUNCA modificado)
con un `errores_reintentables` propio -- solo `ConsultaForoFallidaError`
(fallos TRANSITORIOS) se reintenta; `ConsultaForoPermanenteError`
(CAPTCHA, 4xx del cliente, forma irreconocible) NUNCA se reintenta, se
propaga de inmediato. El Circuit Breaker (`CircuitBreakerForo`) envuelve
la operacion completa (con sus reintentos incluidos) para proteger contra
rachas de fallos entre CONSULTAS sucesivas, no dentro de una sola.

Su propia `requests.Session`, independiente de `RequestsHttpFetcherAdapter`
(Modulo 3) y de `SenescytAdapter` (Modulo 7) -- ninguna se comparte ni se
reutiliza (Submodulo 8.1: "nunca reutilizar HttpFetcherPort")."""

from __future__ import annotations

import requests

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import (
    ConsultaForoFallidaError,
    ConsultaForoPermanenteError,
    ForoCircuitoAbiertoError,
)
from govdata.domain.rules.reglas_foro import CatalogoCamposForo, ReglasCircuitoForo
from govdata.infrastructure.http.circuit_breaker_foro import CircuitBreakerForo
from govdata.infrastructure.http.foro_html_parser import parsear_registro_foro
from govdata.shared.retry.retry_policy import con_reintentos

logger = get_logger(__name__)

_LONGITUD_MINIMA_PAGINA_VALIDA = 20
"""Umbral (caracteres, tras remover espacios) bajo el cual una respuesta
200 se considera "pagina vacia" -- Submodulo 8.2."""

_PALABRAS_CAPTCHA = ("captcha", "recaptcha", "g-recaptcha", "no soy un robot", "no eres un robot")
_PALABRAS_ERROR_TRANSITORIO = ("error interno", "servicio no disponible", "intente mas tarde", "intente nuevamente")
_PALABRAS_SIN_RESULTADOS = ("no se encontraron resultados", "sin resultados", "no existen registros", "no se encontro")


class ForoAbogadosAdapter(ForoAbogadosPort):
    def __init__(
        self,
        base_url: str,
        catalogo_campos: CatalogoCamposForo,
        reglas_circuito: ReglasCircuitoForo | None = None,
        timeout_segundos: float = 15.0,
        max_reintentos: int = 3,
        backoff_base_segundos: float = 2.0,
        user_agent: str = "GovDataIntelligencePlatform/1.0",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._catalogo_campos = catalogo_campos
        self._timeout_segundos = timeout_segundos
        self._sesion = requests.Session()
        self._sesion.headers.update({"User-Agent": user_agent, "Accept": "text/html"})
        self._circuito = CircuitBreakerForo(reglas_circuito or ReglasCircuitoForo())
        self._consultar_con_reintentos = con_reintentos(
            max_intentos=max_reintentos, espera_inicial_segundos=backoff_base_segundos,
            errores_reintentables=(ConsultaForoFallidaError,),
        )(self._consultar_raw)

    def buscar_por_cedula(self, cedula: str) -> list[RegistroForoDTO]:
        return self._ejecutar_consulta({"cedula": cedula})

    def buscar_por_persona(self, persona: Persona) -> list[RegistroForoDTO]:
        if persona.cedula:
            return self.buscar_por_cedula(persona.cedula)
        return self._ejecutar_consulta(
            {"nombres": persona.nombre_completo.nombres, "apellidos": persona.nombre_completo.apellidos}
        )

    def buscar_por_persona_master(self, persona_master: PersonaMaster) -> list[RegistroForoDTO]:
        # `PersonaMaster` (Modulo 6) no lleva cedula propia (solo
        # `Persona`, Modulo 1, la tiene) -- se cae a busqueda por nombre,
        # documentado explicitamente (nunca se inventa una cedula).
        return self._ejecutar_consulta(
            {"nombres": persona_master.nombre_completo.nombres, "apellidos": persona_master.nombre_completo.apellidos}
        )

    def cerrar(self) -> None:
        self._sesion.close()

    # -- Circuit Breaker + Reintentos ------------------------------------

    def _ejecutar_consulta(self, parametros: dict[str, str]) -> list[RegistroForoDTO]:
        if not self._circuito.permitir_intento():
            logger.warning("foro_circuito_rechaza_intento")
            raise ForoCircuitoAbiertoError("Circuit Breaker del Foro de Abogados ABIERTO -- consulta rechazada")

        try:
            resultado = self._consultar_con_reintentos(parametros)
        except (ConsultaForoFallidaError, ConsultaForoPermanenteError):
            self._circuito.registrar_fallo()
            raise
        else:
            self._circuito.registrar_exito()
            return resultado

    # -- Consulta HTTP + deteccion defensiva -----------------------------

    def _consultar_raw(self, parametros: dict[str, str]) -> list[RegistroForoDTO]:
        respuesta = self._solicitar(parametros)
        self._validar_status(respuesta)

        texto = respuesta.text or ""
        texto_normalizado = " ".join(texto.split())

        if len(texto_normalizado) < _LONGITUD_MINIMA_PAGINA_VALIDA:
            logger.warning("foro_pagina_vacia", longitud=len(texto_normalizado))
            raise ConsultaForoFallidaError("El Foro de Abogados respondio una pagina vacia")

        texto_minusculas = texto_normalizado.lower()
        if any(palabra in texto_minusculas for palabra in _PALABRAS_CAPTCHA):
            logger.error("foro_captcha_detectado")
            raise ConsultaForoPermanenteError("El Foro de Abogados exige resolver un CAPTCHA")

        if any(palabra in texto_minusculas for palabra in _PALABRAS_SIN_RESULTADOS):
            logger.info("foro_sin_resultados")
            return []

        if any(palabra in texto_minusculas for palabra in _PALABRAS_ERROR_TRANSITORIO):
            logger.warning("foro_mensaje_error_detectado")
            raise ConsultaForoFallidaError("El Foro de Abogados mostro un mensaje de error transitorio")

        try:
            registro = parsear_registro_foro(texto, self._catalogo_campos)
        except Exception as exc:
            logger.error("foro_respuesta_invalida", error=str(exc))
            raise ConsultaForoPermanenteError(f"Respuesta del Foro de Abogados no se pudo interpretar: {exc}") from exc

        if registro is None:
            logger.info("foro_sin_campos_reconocidos", parametros=parametros)
            return []

        logger.info("foro_consulta_exitosa")
        return [registro]

    def _solicitar(self, parametros: dict[str, str]) -> requests.Response:
        try:
            return self._sesion.get(f"{self._base_url}/consulta", params=parametros, timeout=self._timeout_segundos)
        except requests.Timeout as exc:
            logger.warning("foro_timeout")
            raise ConsultaForoFallidaError(f"Timeout consultando el Foro de Abogados: {exc}") from exc
        except requests.RequestException as exc:
            logger.warning("foro_error_red", error="error de red")
            raise ConsultaForoFallidaError(f"Error de red consultando el Foro de Abogados: {exc}") from exc

    @staticmethod
    def _validar_status(respuesta: requests.Response) -> None:
        if respuesta.status_code >= 500:
            raise ConsultaForoFallidaError(f"El Foro de Abogados respondio {respuesta.status_code} (transitorio)")
        if respuesta.status_code == 404:
            # 404 se interpreta como "sin resultados para esta busqueda",
            # nunca como error -- el llamador recibe lista vacia mas abajo
            # (se deja pasar hasta el chequeo de pagina vacia/parseo).
            return
        if respuesta.status_code >= 400:
            raise ConsultaForoPermanenteError(f"El Foro de Abogados respondio {respuesta.status_code} (permanente)")
