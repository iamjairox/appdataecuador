"""Entry point del Modulo 5: Motor de Monitoreo Continuo.

Uso:
    python scripts/monitorear.py entidad "Procuraduria General del Estado"
    python scripts/monitorear.py masiva
    python scripts/monitorear.py masiva "Ministerio de Salud" "Contraloria"
    python scripts/monitorear.py historial-cargo "Procuraduria" "Director Juridico"
    python scripts/monitorear.py timeline "Procuraduria"

Imprime `ResultadoMonitoreoDTO` (con el contrato oficial 5.14 anidado en
`comparacion` cuando hubo cambios) como JSON en stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from govdata.application.dto.resultado_unificado_dto import EntidadResumenDTO
from govdata.config.container import Container


def _serializar(obj: object) -> object:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"No se puede serializar: {type(obj)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Motor de Monitoreo Continuo -- Modulo 5")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_entidad = subparsers.add_parser("entidad", help="Monitorea una entidad (Submodulo 5.15)")
    p_entidad.add_argument("nombre", help="Nombre (o fragmento) de la entidad")

    p_masiva = subparsers.add_parser("masiva", help="Monitorea varias/todas las entidades")
    p_masiva.add_argument("nombres", nargs="*", help="Lista de entidades (vacio = todas las activas)")

    p_historial = subparsers.add_parser("historial-cargo", help="Historial de un cargo (Submodulo 5.3)")
    p_historial.add_argument("nombre_entidad")
    p_historial.add_argument("cargo")

    p_timeline = subparsers.add_parser("timeline", help="Linea de tiempo de una entidad (Submodulo 5.13)")
    p_timeline.add_argument("nombre_entidad")

    args = parser.parse_args()
    container = Container()

    with container.nueva_sesion() as sesion:
        if args.comando == "entidad":
            entidad = container.buscar_entidad_por_nombre(sesion, args.nombre)
            if entidad is None:
                print(f"Entidad no encontrada: {args.nombre}", file=sys.stderr)
                return 1
            servicio = container.crear_monitoreo_service(sesion)
            resultado = servicio.monitorear(entidad)
            print(json.dumps(asdict(resultado), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "masiva":
            servicio = container.crear_monitoreo_service(sesion)
            entidades = None
            if args.nombres:
                entidades = [
                    e for nombre in args.nombres if (e := container.buscar_entidad_por_nombre(sesion, nombre))
                ]
            resultados = servicio.monitorear_masiva(entidades)
            print(json.dumps([asdict(r) for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "historial-cargo":
            entidad = container.buscar_entidad_por_nombre(sesion, args.nombre_entidad)
            if entidad is None or entidad.id is None:
                print(f"Entidad no encontrada: {args.nombre_entidad}", file=sys.stderr)
                return 1
            historial_service = container.crear_historial_service(sesion)
            versiones = historial_service.historial_del_cargo(entidad.id, args.cargo)
            print(json.dumps([asdict(v) for v in versiones], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "timeline":
            entidad = container.buscar_entidad_por_nombre(sesion, args.nombre_entidad)
            if entidad is None or entidad.id is None:
                print(f"Entidad no encontrada: {args.nombre_entidad}", file=sys.stderr)
                return 1
            timeline_service = container.crear_timeline_service(sesion)
            timeline = timeline_service.construir(
                EntidadResumenDTO(id=entidad.id, nombre=entidad.nombre, portal_origen=entidad.portal_origen)
            )
            print(json.dumps(asdict(timeline), default=_serializar, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
