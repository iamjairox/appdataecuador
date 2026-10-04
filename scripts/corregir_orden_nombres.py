"""Corrige nombres/apellidos invertidos de personas YA guardadas.

Por que existe: hasta ahora el orden de una columna combinada de nombre se
tomaba solo del encabezado. Algunas entidades publican "Apellidos y
Nombres" en el encabezado pero llenan los datos al reves (caso real:
GAD Municipal de Zapotillo, "Grecia Catarina Moncada Sanchez"), y las
personas quedaron con nombres="MONCADA SANCHEZ" / apellidos="GRECIA
CATARINA". Con esos nombres la busqueda posterior no encuentra a nadie.

El normalizador ya corrige esto para extracciones nuevas
(`segmentador_nombre.detectar_orden_por_contenido`), pero una nueva
consulta no arregla lo guardado: `MonitoreoContinuoService` no reprocesa
un documento sin cambios y, si lo hiciera, el nombre corregido tiene otro
fingerprint y se crearia una persona duplicada.

Que hace -- y que NO hace:
    - Lee los archivos YA descargados (tabla `descargas`). Nunca consulta
      fuentes externas.
    - Solo actua en archivos donde el orden real (votacion del contenido)
      contradice al encabezado.
    - Ubica a cada persona por el fingerprint con el que se guardo (orden
      del encabezado) y, si es funcionario de esa entidad, corrige
      nombres, apellidos y fingerprints en `personas` y en su
      `personas_master` (que conserva su propia copia del nombre).
    - Si el nombre corregido ya pertenece a OTRA persona, no fusiona ni
      pisa nada: lo informa como conflicto.
    - Idempotente: una segunda ejecucion no encuentra nada que corregir.

Uso:
    python scripts/corregir_orden_nombres.py            # simulacion
    python scripts/corregir_orden_nombres.py --aplicar  # guarda
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import text

from govdata.config.container import Container
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.rules.generador_fingerprint import generar_fingerprint
from govdata.domain.rules.generador_fingerprint_fonetico import generar_fingerprint_fonetico
from govdata.domain.rules.normalizador_universal import (
    UMBRAL_MATCH_ENCABEZADO_DEFECTO,
    _mapear_encabezados,
    orden_nombre_de_la_tabla,
)
from govdata.domain.rules.segmentador_nombre import (
    detectar_orden_por_encabezado,
    segmentar_nombre_completo,
)
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

_DOCUMENTOS_DESCARGADOS = text(
    """
    SELECT DISTINCT ON (d.id) d.id AS documento_id, p.entidad_id, d.tipo_archivo, x.hash_sha256
    FROM documentos d
    JOIN publicaciones p ON p.id = d.publicacion_id
    JOIN descargas x ON x.documento_id = d.id AND x.estado = 'exito' AND x.hash_sha256 IS NOT NULL
    ORDER BY d.id, x.finalizado_en DESC NULLS LAST
    """
)


def _ubicar_archivo(ruta_base: Path, hash_sha256: str) -> Path | None:
    candidatos = sorted((ruta_base / hash_sha256[:2]).glob(f"{hash_sha256}.*"))
    return candidatos[0] if candidatos else None


def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--aplicar", action="store_true", help="guardar los cambios (por defecto solo simula)")
    aplicar = argumentos.parse_args().aplicar

    container = Container()
    ruta_base = Path(container.settings.storage.ruta_local)
    reglas = container.rule_engine.normalizacion
    totales: Counter[str] = Counter()

    with container.session_factory() as sesion:
        personas = SqlAlchemyPersonaRepository(sesion)
        maestras = SqlAlchemyPersonaMasterRepository(sesion)
        funcionarios = SqlAlchemyFuncionarioRepository(sesion)

        for documento_id, entidad_id, tipo_archivo, hash_sha256 in sesion.execute(_DOCUMENTOS_DESCARGADOS):
            archivo = _ubicar_archivo(ruta_base, hash_sha256)
            if archivo is None:
                totales["documentos_sin_archivo"] += 1
                continue
            tabla = container.parser_factory.obtener_parser(TipoArchivo(tipo_archivo)).extraer(str(archivo)).tabla
            if tabla is None:
                totales["documentos_ilegibles"] += 1
                continue

            mapeo = _mapear_encabezados(tabla.encabezados, reglas.sinonimos_por_campo, UMBRAL_MATCH_ENCABEZADO_DEFECTO)
            columna = next((e for e, campo in mapeo.items() if campo == "nombre_completo"), None)
            if columna is None:
                continue
            valores = [(fila.get(columna) or "").strip() for fila in tabla.filas]
            orden_guardado = detectar_orden_por_encabezado(columna)
            orden_real = orden_nombre_de_la_tabla(columna, valores, reglas)
            totales["documentos_revisados"] += 1
            if orden_real == orden_guardado:
                continue
            totales["documentos_con_orden_invertido"] += 1
            print(f"documento {documento_id} (entidad {entidad_id}): encabezado={orden_guardado.value}, real={orden_real.value}")

            personas_de_la_entidad = {f.persona_id for f in funcionarios.listar_por_entidad(entidad_id, solo_vigentes=False)}
            for valor in valores:
                if not valor:
                    continue
                viejo = segmentar_nombre_completo(valor, orden_guardado)
                nuevo = segmentar_nombre_completo(valor, orden_real)
                _, hash_viejo = generar_fingerprint(viejo.nombres, viejo.apellidos)
                persona = personas.buscar_por_fingerprint_hash(hash_viejo)
                if persona is None or persona.id not in personas_de_la_entidad:
                    continue
                fingerprint_nuevo, hash_nuevo = generar_fingerprint(nuevo.nombres, nuevo.apellidos)
                if hash_nuevo == hash_viejo:
                    continue
                otra = personas.buscar_por_fingerprint_hash(hash_nuevo)
                if otra is not None and otra.id != persona.id:
                    print(f"  CONFLICTO: '{nuevo.nombres} {nuevo.apellidos}' ya existe como persona {otra.id}; no se toca")
                    totales["conflictos"] += 1
                    continue

                antes = f"{persona.nombre_completo.nombres} | {persona.nombre_completo.apellidos}"
                persona.nombre_completo = NombreCompleto(nombres=nuevo.nombres, apellidos=nuevo.apellidos)
                persona.fingerprint, persona.fingerprint_hash = fingerprint_nuevo, hash_nuevo
                personas.guardar(persona)
                totales["personas_corregidas"] += 1

                maestra = maestras.buscar_por_persona_id(persona.id) if persona.id is not None else None
                if maestra is not None:
                    maestra.nombre_completo = persona.nombre_completo
                    maestra.fingerprint_principal = fingerprint_nuevo
                    maestra.fingerprint_fonetico = generar_fingerprint_fonetico(nuevo.nombres, nuevo.apellidos)
                    maestras.guardar(maestra)
                    totales["personas_master_corregidas"] += 1
                despues = f"{persona.nombre_completo.nombres} | {persona.nombre_completo.apellidos}"
                print(f"  persona {persona.id}: [{antes}] -> [{despues}]")

        if aplicar:
            sesion.commit()
        else:
            sesion.rollback()

    print()
    print("APLICADO" if aplicar else "SIMULACION (nada se guardo; usar --aplicar para guardar)")
    for clave in (
        "documentos_revisados", "documentos_con_orden_invertido", "personas_corregidas",
        "personas_master_corregidas", "conflictos", "documentos_sin_archivo", "documentos_ilegibles",
    ):
        print(f"  {clave}: {totales[clave]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
