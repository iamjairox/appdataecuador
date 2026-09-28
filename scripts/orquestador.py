"""Entry point del Modulo 9: Orquestador Maestro del Sistema GovData.

Uso:
    python scripts/orquestador.py consultar-entidad "Procuraduria General del Estado"
    python scripts/orquestador.py consultar-entidad "Procuraduria" --politica actualizacion_completa
    python scripts/orquestador.py consultar-masivo
    python scripts/orquestador.py actualizar-entidad "Procuraduria General del Estado"
    python scripts/orquestador.py actualizar-masivo
    python scripts/orquestador.py reprocesar-job <uuid>
    python scripts/orquestador.py dashboard
    python scripts/orquestador.py estadisticas
    python scripts/orquestador.py reanudar

`reanudar` debe correrse UNA vez al arrancar el proceso (Submodulo 9.7) --
reencola cualquier trabajo que quedo EJECUTANDO por una caida previa del
servidor."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict

from govdata.config.container import Container


def _serializar(obj: object) -> object:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"No se puede serializar: {type(obj)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Orquestador Maestro del Sistema GovData -- Modulo 9")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_entidad = subparsers.add_parser("consultar-entidad", help="Submodulo 9.1 (consultar_entidad)")
    p_entidad.add_argument("nombre_entidad", type=str)
    p_entidad.add_argument("--politica", default=None)

    subparsers.add_parser("consultar-masivo", help="Submodulo 9.1 (consultar_masivo)")

    p_actualizar = subparsers.add_parser("actualizar-entidad", help="Submodulo 9.1 (actualizar_entidad)")
    p_actualizar.add_argument("nombre_entidad", type=str)

    subparsers.add_parser("actualizar-masivo", help="Submodulo 9.1 (actualizar_masivo)")

    p_reprocesar = subparsers.add_parser("reprocesar-job", help="Submodulo 9.7 (reprocesar_job)")
    p_reprocesar.add_argument("trabajo_id", type=str)

    subparsers.add_parser("dashboard", help="Submodulo 9.11 (Dashboard interno)")
    subparsers.add_parser("estadisticas", help="Submodulo 9.12 (Motor de Estadisticas)")
    subparsers.add_parser("reanudar", help="Submodulo 9.7 (Reanudacion automatica al arrancar)")

    args = parser.parse_args()
    container = Container()

    if args.comando == "reanudar":
        cantidad = container.reanudar_trabajos_interrumpidos()
        print(json.dumps({"trabajos_reanudados": cantidad}, ensure_ascii=False, indent=2))
        return 0

    with container.nueva_sesion() as sesion:
        if args.comando == "consultar-entidad":
            orquestador = container.crear_govdata_pipeline_orchestrator(sesion)
            resultado = orquestador.consultar_entidad(args.nombre_entidad, politica=args.politica)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "consultar-masivo":
            orquestador = container.crear_govdata_pipeline_orchestrator(sesion)
            resultados = orquestador.consultar_masivo()
            print(json.dumps([r.to_dict() for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "actualizar-entidad":
            orquestador = container.crear_govdata_pipeline_orchestrator(sesion)
            resultado = orquestador.actualizar_entidad(args.nombre_entidad)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "actualizar-masivo":
            orquestador = container.crear_govdata_pipeline_orchestrator(sesion)
            resultados = orquestador.actualizar_masivo()
            print(json.dumps([r.to_dict() for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "reprocesar-job":
            orquestador = container.crear_govdata_pipeline_orchestrator(sesion)
            resultado = orquestador.reprocesar_job(uuid.UUID(args.trabajo_id))
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "dashboard":
            servicio = Container.crear_dashboard_interno_service(sesion)
            print(json.dumps(asdict(servicio.construir()), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "estadisticas":
            servicio = Container.crear_motor_estadisticas_service(sesion)
            print(json.dumps(asdict(servicio.calcular()), default=_serializar, ensure_ascii=False, indent=2))
        else:
            print(f"Comando desconocido: {args.comando}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
