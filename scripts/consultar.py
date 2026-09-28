"""Entry point del Modulo 4: consultas bajo demanda / masivas / filtradas.

Uso:
    python scripts/consultar.py entidad "Procuraduria General del Estado"
    python scripts/consultar.py masiva
    python scripts/consultar.py masiva "Ministerio de Salud" "Contraloria"
    python scripts/consultar.py filtros --area juridica --correo-disponible

Imprime el contrato oficial (`ResultadoUnificadoDTO.to_dict()`) como JSON
en stdout -- pensado para consumirse desde n8n, un script, o inspeccion
manual.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.config.container import Container
from govdata.domain.value_objects.area_relevante import AreaRelevante


def _serializar(obj: object) -> object:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"No se puede serializar: {type(obj)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Motor de Extraccion Inteligente -- consultas")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_entidad = subparsers.add_parser("entidad", help="Consulta individual (Submodulo 4.5)")
    p_entidad.add_argument("nombre", help="Nombre (o fragmento) de la entidad")

    p_masiva = subparsers.add_parser("masiva", help="Consulta masiva (Submodulo 4.6)")
    p_masiva.add_argument("nombres", nargs="*", help="Lista de entidades (vacio = todas)")

    p_filtros = subparsers.add_parser("filtros", help="Consulta por filtros (Submodulo 4.7)")
    p_filtros.add_argument("--area", choices=[a.value for a in AreaRelevante])
    p_filtros.add_argument("--cargo-contiene")
    p_filtros.add_argument("--tipo-institucion")
    p_filtros.add_argument("--correo-disponible", action="store_true", default=None)
    p_filtros.add_argument("--telefono-disponible", action="store_true", default=None)

    args = parser.parse_args()
    container = Container()

    with container.nueva_sesion() as sesion:
        servicio = container.crear_consulta_service(sesion)

        if args.comando == "entidad":
            entidad = container.buscar_entidad_por_nombre(sesion, args.nombre)
            if entidad is None:
                print(f"Entidad no encontrada: {args.nombre}", file=sys.stderr)
                return 1
            resultado = servicio.consultar_entidad(entidad)
            print(json.dumps(resultado.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "masiva":
            entidades = None
            if args.nombres:
                entidades = [
                    e for nombre in args.nombres if (e := container.buscar_entidad_por_nombre(sesion, nombre))
                ]
            resultados = servicio.consultar_masiva(entidades)
            print(json.dumps([r.to_dict() for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "filtros":
            filtros = FiltrosConsultaDTO(
                area=AreaRelevante(args.area) if args.area else None,
                cargo_contiene=args.cargo_contiene,
                tipo_institucion=args.tipo_institucion,
                correo_disponible=args.correo_disponible,
                telefono_disponible=args.telefono_disponible,
            )
            resultados = servicio.consultar_con_filtros(filtros)
            print(json.dumps([asdict(r) for r in resultados], default=_serializar, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
