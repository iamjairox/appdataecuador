"""Entry point del Modulo 8: Motor de Consulta al Foro de Abogados,
Fusion de Datos y Perfil Consolidado del Funcionario.

Uso:
    python scripts/foro.py consultar-persona 42
    python scripts/foro.py consultar-cedula 0999999999
    python scripts/foro.py masivo
    python scripts/foro.py entidad "Procuraduria General del Estado"
    python scripts/foro.py perfil-consolidado 7
    python scripts/foro.py metricas

Ninguna llamada real al Foro de Abogados se puede verificar en este
entorno (no hay credenciales/documentacion oficial estable) -- ver
Submodulo 8.2.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict

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
    parser = argparse.ArgumentParser(
        description="Motor de Consulta al Foro de Abogados + Perfil Consolidado -- Modulo 8"
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_persona = subparsers.add_parser("consultar-persona", help="Consulta individual por Persona (8.12)")
    p_persona.add_argument("persona_id", type=int)
    p_persona.add_argument("--entidad", default="")

    p_cedula = subparsers.add_parser("consultar-cedula", help="Consulta individual por cedula (8.12)")
    p_cedula.add_argument("cedula", type=str)
    p_cedula.add_argument("--entidad", default="")

    subparsers.add_parser("masivo", help="Consulta masiva al Foro (8.13)")

    p_entidad = subparsers.add_parser("entidad", help="EL FLUJO OBLIGATORIO completo por Entidad (8.11)")
    p_entidad.add_argument("nombre_entidad", type=str)

    p_perfil = subparsers.add_parser("perfil-consolidado", help="Contrato oficial PerfilConsolidadoDTO (8.10)")
    p_perfil.add_argument("persona_master_id", type=int)
    p_perfil.add_argument("--entidad-id", type=int, default=None)

    subparsers.add_parser("metricas", help="Metricas del Foro (8.15)")

    args = parser.parse_args()
    container = Container()

    with container.nueva_sesion() as sesion:
        if args.comando == "consultar-persona":
            persona = SqlAlchemyPersonaRepository(sesion).buscar_por_id(args.persona_id)
            if persona is None:
                print(f"Persona no encontrada: {args.persona_id}", file=sys.stderr)
                return 1
            caso_uso = container.crear_consultar_persona_foro_use_case(sesion)
            resultado = caso_uso.ejecutar(persona, entidad_nombre=args.entidad)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "consultar-cedula":
            caso_uso = container.crear_consultar_por_cedula_foro_use_case(sesion)
            resultado = caso_uso.ejecutar(args.cedula, entidad_nombre=args.entidad)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "masivo":
            caso_uso = container.crear_consultar_masivo_foro_use_case(sesion)
            resultados = caso_uso.ejecutar()
            print(json.dumps([asdict(r) for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "entidad":
            caso_uso = container.crear_consultar_entidad_use_case(sesion)
            resultado = caso_uso.ejecutar(args.nombre_entidad)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "perfil-consolidado":
            servicio = container.crear_perfil_consolidado_service(sesion)
            perfil = servicio.construir_perfil(args.persona_master_id, entidad_id=args.entidad_id)
            print(json.dumps(perfil.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "metricas":
            servicio = Container.crear_metricas_foro_service(sesion)
            metricas = servicio.calcular()
            print(json.dumps(asdict(metricas), default=_serializar, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
