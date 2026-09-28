"""Adaptador: SenescytAdapter -- Submodulo 7.2.

"No asumir aun como responde SENESCYT. Toda la logica debe quedar
desacoplada. El adaptador debe transformar cualquier respuesta al DTO
interno." No existe documentacion publica oficial y estable de la API de
consulta de SENESCYT en el momento de este modulo -- este adaptador:

  1. Llama a un endpoint HTTP configurable (base_url inyectable, NUNCA
     hardcodeado) via `requests`, mismo patron aislado que
     `HttpVerificadorCambiosAdapter` (Modulo 6): su propia `Session`,
     nunca comparte estado con `RequestsHttpFetcherAdapter` (Modulo 3).
  2. Parsea la respuesta de forma DEFENSIVA: intenta varios nombres de
     clave razonables por campo (`_ALIAS_CAMPOS`) en vez de asumir un
     unico formato -- si SENESCYT (o un proxy/cache intermedio) cambia
     nombres de campo, el adaptador se adapta sin tocar ninguna otra capa.
  3. Nunca deja pasar un item que no tenga al menos titulo+nivel+institucion
     (los 3 campos obligatorios de `PersonaAcademicaDTO`) -- lo descarta
     con un warning en vez de fallar toda la consulta por un item malformado.

Implementa DOS puertos: `SenescytPort` (7.1, las 4 formas de consulta) y,
opcionalmente, `ExternalSourcePort` (Modulo 6) para poder conectarse al
pipeline generico de Enriquecimiento si algun consumidor futuro lo
prefiere -- el pipeline especifico de Modulo 7
(`EnriquecimientoAcademicoService`) usa `SenescytPort` directamente.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import requests

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.dto.resultado_consulta_fuente_dto import ResultadoConsultaFuenteDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.fuentes_externas_ports import ExternalSourcePort
from govdata.application.ports.senescyt_port import SenescytPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import ConsultaSenescytFallidaError
from govdata.domain.value_objects.fuente_externa import FuenteExterna

logger = get_logger(__name__)

_ALIAS_CAMPOS: dict[str, tuple[str, ...]] = {
    "titulo": ("titulo", "nombre_titulo", "tituloObtenido", "titulo_obtenido"),
    "nivel": ("nivel", "nivel_formacion", "nivelTitulo", "nivel_titulo"),
    "institucion": ("institucion", "universidad", "ies", "nombre_ies"),
    "fecha_registro": ("fecha_registro", "fechaRegistro", "fecha_registro_senescyt"),
    "pais": ("pais", "pais_ies"),
    "estado": ("estado", "estado_registro", "estadoTitulo"),
    "modalidad": ("modalidad", "modalidad_estudio"),
    "numero_registro": ("numero_registro", "numeroRegistro", "registro", "codigo_registro"),
    "area_conocimiento": ("area_conocimiento", "areaConocimiento", "area"),
    "tipo_titulo": ("tipo_titulo", "tipoTitulo", "tipo"),
    "fecha_graduacion": ("fecha_graduacion", "fechaGraduacion"),
    "observaciones": ("observaciones", "observacion"),
}
_CAMPOS_FECHA = frozenset({"fecha_registro", "fecha_graduacion"})
_CAMPOS_OBLIGATORIOS = ("titulo", "nivel", "institucion")


def _extraer(item: dict[str, Any], campo: str) -> Any:
    for alias in _ALIAS_CAMPOS[campo]:
        if alias in item and item[alias] not in (None, ""):
            return item[alias]
    return None


def _parsear_fecha(valor: Any) -> date | None:
    if valor is None or isinstance(valor, date):
        return valor if isinstance(valor, date) else None
    if isinstance(valor, str):
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                # Solo se usa la parte de fecha (.date()) -- la zona
                # horaria es irrelevante para un campo de solo fecha.
                return datetime.strptime(valor, formato).date()  # noqa: DTZ007
            except ValueError:
                continue
    return None


def _item_a_dto(item: dict[str, Any]) -> PersonaAcademicaDTO | None:
    valores = {campo: _extraer(item, campo) for campo in _ALIAS_CAMPOS}
    if not all(valores[campo] for campo in _CAMPOS_OBLIGATORIOS):
        logger.warning("senescyt_item_descartado_campos_obligatorios_faltantes", item_claves=list(item.keys()))
        return None

    for campo in _CAMPOS_FECHA:
        valores[campo] = _parsear_fecha(valores[campo])

    return PersonaAcademicaDTO(
        titulo=str(valores["titulo"]), nivel=str(valores["nivel"]), institucion=str(valores["institucion"]),
        fecha_registro=valores["fecha_registro"], pais=valores["pais"], estado=valores["estado"],
        modalidad=valores["modalidad"], numero_registro=str(valores["numero_registro"]) if valores["numero_registro"] else None,
        area_conocimiento=valores["area_conocimiento"], tipo_titulo=valores["tipo_titulo"],
        fecha_graduacion=valores["fecha_graduacion"], observaciones=valores["observaciones"],
    )


def _respuesta_a_titulos(datos: Any) -> list[PersonaAcademicaDTO]:
    """Acepta tanto `{"titulos": [...]}` como una lista cruda `[...]` en
    la raiz -- otro punto de tolerancia a formato desconocido."""
    if isinstance(datos, dict):
        items = datos.get("titulos", datos.get("resultados", datos.get("data", [])))
    elif isinstance(datos, list):
        items = datos
    else:
        raise ConsultaSenescytFallidaError(f"Respuesta de SENESCYT con forma no reconocida: {type(datos)}")

    if not isinstance(items, list):
        raise ConsultaSenescytFallidaError("Respuesta de SENESCYT sin una lista de titulos reconocible")

    dtos = [_item_a_dto(item) for item in items if isinstance(item, dict)]
    return [dto for dto in dtos if dto is not None]


class SenescytAdapter(SenescytPort, ExternalSourcePort):
    def __init__(
        self,
        base_url: str,
        timeout_segundos: float = 15.0,
        user_agent: str = "GovDataIntelligencePlatform/1.0",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_segundos = timeout_segundos
        self._sesion = requests.Session()
        self._sesion.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    @property
    def fuente(self) -> FuenteExterna:
        return FuenteExterna.SENESCYT

    def consultar_por_cedula(self, cedula: str) -> list[PersonaAcademicaDTO]:
        return self._ejecutar_consulta({"cedula": cedula})

    def consultar_por_nombres(self, nombres: str, apellidos: str) -> list[PersonaAcademicaDTO]:
        return self._ejecutar_consulta({"nombres": nombres, "apellidos": apellidos})

    def consultar_por_identidad(self, senales: SenalesIdentidadDTO) -> list[PersonaAcademicaDTO]:
        return self._ejecutar_consulta({"nombres": senales.nombre, "apellidos": senales.apellido})

    def consultar_por_persona_master(self, persona_master: PersonaMaster) -> list[PersonaAcademicaDTO]:
        return self._ejecutar_consulta(
            {
                "nombres": persona_master.nombre_completo.nombres,
                "apellidos": persona_master.nombre_completo.apellidos,
            }
        )

    def consultar(self, senales: SenalesIdentidadDTO) -> ResultadoConsultaFuenteDTO:
        """Cumple `ExternalSourcePort` (Modulo 6) -- delega en
        `consultar_por_identidad` y envuelve el resultado en el DTO
        generico, para uso opcional del pipeline generico de Modulo 6."""
        titulos = self.consultar_por_identidad(senales)
        ahora = datetime.now(UTC)
        return ResultadoConsultaFuenteDTO(
            fuente=FuenteExterna.SENESCYT, encontrado=bool(titulos), consultado_en=ahora,
            datos={"titulos": [t.titulo for t in titulos]} if titulos else {},
        )

    def _ejecutar_consulta(self, parametros: dict[str, str]) -> list[PersonaAcademicaDTO]:
        try:
            respuesta = self._sesion.get(
                f"{self._base_url}/consulta", params=parametros, timeout=self._timeout_segundos
            )
        except requests.RequestException as exc:
            raise ConsultaSenescytFallidaError(f"Error de red consultando SENESCYT: {exc}") from exc

        if respuesta.status_code >= 500:
            raise ConsultaSenescytFallidaError(f"SENESCYT respondio {respuesta.status_code} (transitorio)")
        if respuesta.status_code == 404:
            return []
        if respuesta.status_code >= 400:
            raise ConsultaSenescytFallidaError(f"SENESCYT respondio {respuesta.status_code}")

        try:
            datos = respuesta.json()
        except ValueError as exc:
            raise ConsultaSenescytFallidaError("Respuesta de SENESCYT no es JSON valido") from exc

        return _respuesta_a_titulos(datos)

    def cerrar(self) -> None:
        self._sesion.close()
