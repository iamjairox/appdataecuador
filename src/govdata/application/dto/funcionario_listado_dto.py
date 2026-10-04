"""DTO: FuncionarioListadoDTO -- Modulo 10 (API REST), UNA fila del
listado paginado `GET /entidades/{id}/funcionarios`.

Deliberadamente PLANO y basado SOLO en informacion YA PERSISTIDA
(`Persona` + `Funcionario`, Modulos 1/4, congelados) -- este endpoint
nunca dispara descubrimiento/SENESCYT/Foro. Para el perfil FUSIONADO
(academico + Foro) el cliente sigue con `GET /funcionarios/{persona_master_id}`
(`PerfilConsolidadoService`, Modulo 8)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class FuncionarioListadoDTO:
    funcionario_id: int
    persona_id: int
    persona_master_id: int | None
    nombre_completo: str
    nombres: str
    apellidos: str
    cedula: str | None
    correo: str | None
    telefono: str | None
    cargo: str
    dependencia: str
    area: str
    vigente: bool
    fecha_inicio: str | None
    fecha_fin: str | None
    extension_telefonica: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
