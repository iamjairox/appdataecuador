"""Entidad de dominio: Persona.

Representa a un individuo, independiente de cualquier cargo o entidad
publica especifica. Es el resultado directo del cambio arquitectonico
solicitado: una misma persona puede aparecer en Transparencia, SENESCYT,
Funcion Judicial, SERCOP, Contraloria, SRI, etc., y NO debe duplicarse.

La vinculacion Persona <-> Entidad publica + cargo vive en `Funcionario`
(relacion N:M en el tiempo). La deduplicacion/matching entre fuentes con
nombres escritos distinto ("JUAN CARLOS PEREZ" vs "PEREZ JUAN CARLOS") es
responsabilidad del futuro Motor de Identity Resolution, no de esta clase.
Aqui solo se garantiza que una Persona bien formada es valida.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import PersonaInvalidaError
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono


@dataclass(slots=True)
class Persona:
    """Individuo identificable, potencialmente presente en multiples fuentes."""

    nombre_completo: NombreCompleto
    id: int | None = None
    cedula: str | None = None
    correo: Correo | None = None
    telefono: Telefono | None = None
    extension_telefonica: str | None = None
    fingerprint: str | None = None
    """Huella de identidad (Submodulo 4.4, `generador_fingerprint`). Aun
    NO se usa para comparar/fusionar personas -- solo se almacena, como
    base para la segunda etapa de Identity Resolution (modulo futuro)."""
    fingerprint_hash: str | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.cedula is not None:
            cedula_normalizada = self.cedula.strip()
            if cedula_normalizada and not cedula_normalizada.isdigit():
                raise PersonaInvalidaError(
                    f"Cedula invalida para '{self.nombre_completo}': '{self.cedula}'"
                )
            self.cedula = cedula_normalizada or None

    def actualizar_datos_contacto(
        self, correo: Correo | None = None, telefono: Telefono | None = None, extension_telefonica: str | None = None
    ) -> None:
        """Enriquece los datos de contacto sin perder los existentes.

        Una nueva fuente puede aportar un correo/telefono que la fuente
        original no tenia; nunca sobreescribe con None un dato ya conocido.
        """
        if correo is not None:
            self.correo = correo
        if telefono is not None:
            self.telefono = telefono
        if extension_telefonica:
            self.extension_telefonica = extension_telefonica.strip()
