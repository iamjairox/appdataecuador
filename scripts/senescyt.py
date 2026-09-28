"""Entry point del Modulo 7: Adaptador SENESCYT + Enriquecimiento Academico.

Uso:
    python scripts/senescyt.py enriquecer 42
    python scripts/senescyt.py enriquecer 42 --cargo "Director Juridico"
    python scripts/senescyt.py masivo
    python scripts/senescyt.py perfil 7
    python scripts/senescyt.py metricas
    python scripts/senescyt.py candidatos

`enriquecer`/`masivo` requieren una `Persona` (Modulo 1-5) ya resuelta a
`PersonaMaster` (Modulo 6, se resuelve automaticamente si falta). Ninguna
llamada real a SENESCYT se puede verificar en este entorno (no hay
credenciales/documentacion oficial estable) -- ver Submodulo 7.2.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict
from datetime import UTC, datetime

from govdata.config.container import Container
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)


def _serializar(obj: object) -> object:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"No se puede serializar: {type(obj)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Adaptador SENESCYT + Enriquecimiento Academico -- Modulo 7")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_enriquecer = subparsers.add_parser("enriquecer", help="Enriquecimiento academico bajo demanda (7.11)")
    p_enriquecer.add_argument("persona_id", type=int)
    p_enriquecer.add_argument("--cargo", default=None)
    p_enriquecer.add_argument("--institucion", default=None)

    subparsers.add_parser("masivo", help="Enriquecimiento academico masivo (7.12)")

    p_perfil = subparsers.add_parser("perfil", help="Contrato oficial PerfilAcademicoDTO (7.16)")
    p_perfil.add_argument("persona_master_id", type=int)

    subparsers.add_parser("metricas", help="Metricas academicas agregadas (7.18)")
    subparsers.add_parser("candidatos", help="Candidatos a re-enriquecer (7.20, Programador)")

    args = parser.parse_args()
    container = Container()

    with container.nueva_sesion() as sesion:
        if args.comando == "enriquecer":
            persona = SqlAlchemyPersonaRepository(sesion).buscar_por_id(args.persona_id)
            if persona is None:
                print(f"Persona no encontrada: {args.persona_id}", file=sys.stderr)
                return 1
            caso_uso = container.crear_enriquecer_persona_academica_use_case(sesion)
            resultado = caso_uso.ejecutar(persona, cargo=args.cargo, institucion=args.institucion)
            print(json.dumps(asdict(resultado), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "masivo":
            caso_uso = container.crear_enriquecer_masivo_academico_use_case(sesion)
            resultados = caso_uso.ejecutar()
            print(json.dumps([asdict(r) for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "perfil":
            servicio = container.crear_perfil_academico_service(sesion)
            perfil = servicio.construir_perfil(args.persona_master_id)
            print(json.dumps(perfil.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "metricas":
            servicio = container.crear_metricas_academicas_service(sesion)
            print(json.dumps(asdict(servicio.calcular()), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "candidatos":
            servicio = container.crear_programador_enriquecimiento_service(sesion)
            candidatos = servicio.candidatos_a_enriquecer(datetime.now(UTC))
            print(
                json.dumps(
                    [{"persona_master_id": c.id, "nombre": str(c.nombre_completo)} for c in candidatos],
                    default=_serializar, ensure_ascii=False, indent=2,
                )
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
