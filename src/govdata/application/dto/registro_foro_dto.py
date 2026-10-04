"""DTO: RegistroForoDTO -- el unico DTO de datos crudos/normalizados del
Foro de Abogados (mismo rol que `PersonaAcademicaDTO`, Modulo 7).

`ForoAbogadosAdapter` (Submodulo 8.2) transforma CUALQUIER forma de
respuesta HTML a este DTO antes de que llegue a cualquier otra capa; el
normalizador (8.3), el comparador (8.5), el motor de alertas (8.7) y
el de eventos (8.7) solo conocen esta forma -- nunca el HTML crudo
del Foro.

Todos los campos son opcionales a proposito (Submodulo 8.4: "extraer
UNICAMENTE los datos disponibles del Foro. Nunca inventar informacion.")
-- el parser HTML nunca debe forzar un valor que no encontro."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegistroForoDTO:
    nombre_completo: str | None = None
    registro: str | None = None
    """"No. Registro" -- la matricula/numero de registro del abogado en
    el Foro."""
    provincia: str | None = None
    estado: str | None = None
    cedula: str | None = None
    celular: str | None = None
    correo: str | None = None
    telefono_domicilio: str | None = None
    direccion_domicilio: str | None = None
    telefono_oficina: str | None = None
    direccion_oficina: str | None = None
