"""Entry point del Modulo 6: Motor de Identidad, Enriquecimiento de
Personas y Fuentes Externas.

Uso:
    python scripts/identidad.py resolver 42
    python scripts/identidad.py resolver 42 --cargo "Director Juridico"
    python scripts/identidad.py perfil 7
    python scripts/identidad.py pendientes
    python scripts/identidad.py revisar <caso_uuid> aprobar --por "ana.revisora"
    python scripts/identidad.py revisar <caso_uuid> rechazar --por "ana.revisora"

Ninguna fuente externa real esta implementada todavia (Submodulo 6.6,
6.20) -- `resolver` solo ejecuta 6.1/6.2/6.21 (alta/fusion/revision de la
PersonaMaster); el enriquecimiento (6.7) queda listo para que el proximo
modulo (SENESCYT) le pase sus propios `ExternalSourcePort`.
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


def _persona_master_a_dict(pm: object) -> dict:
    return {
        "id": pm.id,  # type: ignore[attr-defined]
        "uuid": str(pm.uuid),  # type: ignore[attr-defined]
        "persona_id": pm.persona_id,  # type: ignore[attr-defined]
        "nombre_completo": str(pm.nombre_completo),  # type: ignore[attr-defined]
        "estado": pm.estado.value,  # type: ignore[attr-defined]
        "nivel_confianza": pm.nivel_confianza,  # type: ignore[attr-defined]
        "cantidad_fuentes": pm.cantidad_fuentes,  # type: ignore[attr-defined]
        "fusionada_en_id": pm.fusionada_en_id,  # type: ignore[attr-defined]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Motor de Identidad -- Modulo 6")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_resolver = subparsers.add_parser("resolver", help="Resuelve/crea la PersonaMaster de una Persona (6.1/6.2/6.21)")
    p_resolver.add_argument("persona_id", type=int)
    p_resolver.add_argument("--cargo", default=None)
    p_resolver.add_argument("--institucion", default=None)

    p_perfil = subparsers.add_parser("perfil", help="Contrato oficial PerfilPersonaDTO (6.4/6.16)")
    p_perfil.add_argument("persona_master_id", type=int)

    subparsers.add_parser("pendientes", help="Casos de revision manual pendientes (6.21)")

    p_revisar = subparsers.add_parser("revisar", help="Resuelve manualmente un caso de revision (6.21)")
    p_revisar.add_argument("caso_id")
    p_revisar.add_argument("decision", choices=["aprobar", "rechazar"])
    p_revisar.add_argument("--por", required=True, help="Identificador de quien revisa")

    args = parser.parse_args()
    container = Container()

    with container.nueva_sesion() as sesion:
        if args.comando == "resolver":
            persona = SqlAlchemyPersonaRepository(sesion).buscar_por_id(args.persona_id)
            if persona is None:
                print(f"Persona no encontrada: {args.persona_id}", file=sys.stderr)
                return 1
            caso_uso = container.crear_resolver_persona_master_use_case(sesion)
            persona_master = caso_uso.ejecutar(persona, cargo=args.cargo, institucion=args.institucion)
            print(json.dumps(_persona_master_a_dict(persona_master), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "perfil":
            servicio = container.crear_perfil_persona_service(sesion)
            perfil = servicio.construir_perfil(args.persona_master_id)
            print(json.dumps(perfil.to_dict(), default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "pendientes":
            from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
                SqlAlchemyCasoRevisionIdentidadRepository,
            )

            casos = SqlAlchemyCasoRevisionIdentidadRepository(sesion).listar_pendientes()
            print(json.dumps([asdict(c) for c in casos], default=_serializar, ensure_ascii=False, indent=2))

        elif args.comando == "revisar":
            from govdata.application.ports.caso_revision_identidad_repository_port import (
                CasoRevisionIdentidadRepositoryPort,
            )
            from govdata.application.ports.evento_perfil_repository_port import (
                EventoPerfilRepositoryPort,
            )
            from govdata.application.services.fusion_service import FusionService
            from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
                SqlAlchemyCasoRevisionIdentidadRepository,
            )
            from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
                SqlAlchemyEventoPerfilRepository,
            )
            from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
                SqlAlchemyPersonaMasterRepository,
            )

            caso_revision_repo: CasoRevisionIdentidadRepositoryPort = SqlAlchemyCasoRevisionIdentidadRepository(
                sesion
            )
            evento_perfil_repo: EventoPerfilRepositoryPort = SqlAlchemyEventoPerfilRepository(sesion)
            fusion_service = FusionService(
                persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
                caso_revision_repository=caso_revision_repo,
                evento_perfil_repository=evento_perfil_repo,
                umbrales=container.rule_engine_identidad.fusion,
            )
            caso = fusion_service.revisar_caso(
                uuid.UUID(args.caso_id), aprobar=args.decision == "aprobar", revisor=args.por,
                cuando=datetime.now(UTC),
            )
            print(json.dumps(asdict(caso), default=_serializar, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
