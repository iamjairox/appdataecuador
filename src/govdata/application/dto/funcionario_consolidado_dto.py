"""DTO: FuncionarioConsolidadoDTO -- UNA fila del contrato de resultado
final por Entidad (Submodulo 8.11). Forma EXACTA pedida por el cliente:

    {
      "nombre_completo": "",
      "cedula": "",
      "correo": "",
      "telefono": "",
      "celular": "",
      "cargo": "",
      "dependencia": "",
      "registro_foro": "",
      "estado_foro": "",
      "provincia_foro": "",
      "fecha_consulta": ""
    }

Deliberadamente PLANO (a diferencia de `PerfilConsolidadoDTO`, 8.10, que
agrupa por fuente): esta es la ficha "para mostrar" -- lo unico que el
cliente pidio ver por funcionario. `celular` y `telefono` pueden coincidir
si Transparencia solo publico un numero -- nunca se inventa el que falta."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FuncionarioConsolidadoDTO:
    nombre_completo: str
    cedula: str | None = None
    correo: str | None = None
    telefono: str | None = None
    celular: str | None = None
    cargo: str | None = None
    dependencia: str | None = None
    registro_foro: str | None = None
    estado_foro: str | None = None
    provincia_foro: str | None = None
    fecha_consulta: str | None = None
