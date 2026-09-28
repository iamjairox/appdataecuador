"""DTO: ResumenPersistenciaDTO -- Submodulo 5.11 (Persistencia Inteligente).

Resultado de aplicar una lista de `DiferenciaFuncionarioDTO` sobre
`Persona`/`Funcionario`/`VersionFuncionario`: cuantos registros se
insertaron, actualizaron, ignoraron o versionaron, y el mapeo
fingerprint -> persona_id resuelto durante el proceso (para que capas
posteriores del mismo caso de uso -- alertas, oportunidades -- no
necesiten volver a resolver la Persona por su cuenta)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResumenPersistenciaDTO:
    insertados: int = 0
    actualizados: int = 0
    ignorados: int = 0
    versionados: int = 0
    persona_id_por_fingerprint: dict[str, int] = field(default_factory=dict)
