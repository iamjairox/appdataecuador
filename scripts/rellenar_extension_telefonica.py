"""Relleno (backfill) de la extension y el telefono de personas ya
guardadas, desde documentos ya descargados.

Por que existe: dos columnas del numeral 2 DPE se perdian en la
extraccion. "Extension telefonica" no se leia (faltaba el sinonimo exacto
en `config/rules/sinonimos_campos.yaml`), y "Telefono institucional" se
descartaba entero cuando la celda traia varios numeros ("(07) 2647-117\\n
(07) 2647-118"). Las personas extraidas antes de esas correcciones
quedaron con esos datos vacios, y una nueva consulta NO lo corrige:
`MonitoreoContinuoService` nunca reprocesa un documento cuyo hash no
cambio (ni siquiera con la politica `actualizacion_completa`, que solo
invalida las caches de SENESCYT/Foro).

Que hace -- y que NO hace:
    - Lee los archivos YA descargados (tabla `descargas`, estado exito,
      almacenamiento local por hash). Nunca consulta fuentes externas.
    - Pasa cada archivo por el mismo parser + Normalizador Universal del
      pipeline y ubica a la persona por el mismo fingerprint.
    - Solo completa `extension_telefonica` y `telefono` de personas que YA
      existen, son funcionarios de esa entidad y tienen ese dato vacio; el
      telefono tambien en su `personas_master` si esta vacio (de ahi lo
      toma el resultado de consulta). Nunca sobreescribe un valor
      existente, nunca crea funcionarios ni toca otros campos. Se puede
      ejecutar varias veces (idempotente).

Uso:
    python scripts/rellenar_extension_telefonica.py            # simulacion
    python scripts/rellenar_extension_telefonica.py --aplicar  # guarda
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
from govdata.domain.rules.normalizador_universal import normalizar_tabla
from govdata.domain.value_objects.telefono import Telefono
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
                print(f"documento {documento_id} (entidad {entidad_id}): archivo no encontrado en {ruta_base}")
                totales["documentos_sin_archivo"] += 1
                continue

            resultado = container.parser_factory.obtener_parser(TipoArchivo(tipo_archivo)).extraer(str(archivo))
            if resultado.tabla is None:
                print(f"documento {documento_id} (entidad {entidad_id}): no se pudo leer ({resultado.mensaje})")
                totales["documentos_ilegibles"] += 1
                continue

            personas_de_la_entidad = {f.persona_id for f in funcionarios.listar_por_entidad(entidad_id, solo_vigentes=False)}
            for fila in normalizar_tabla(resultado.tabla, reglas):
                telefono = Telefono.crear_opcional(fila.telefono)
                if not fila.extension_telefonica and telefono is None:
                    continue
                _, fingerprint_hash = generar_fingerprint(fila.nombres, fila.apellidos)
                persona = personas.buscar_por_fingerprint_hash(fingerprint_hash)
                if persona is None or persona.id not in personas_de_la_entidad:
                    totales["filas_sin_persona_guardada"] += 1
                    continue

                completado = []
                if fila.extension_telefonica and not persona.extension_telefonica:
                    persona.actualizar_datos_contacto(extension_telefonica=fila.extension_telefonica)
                    completado.append(f"extension {persona.extension_telefonica}")
                    totales["extensiones_completadas"] += 1
                if telefono is not None and persona.telefono is None:
                    persona.actualizar_datos_contacto(telefono=telefono)
                    completado.append(f"telefono {telefono}")
                    totales["telefonos_completados"] += 1
                    maestra = maestras.buscar_por_persona_id(persona.id) if persona.id is not None else None
                    if maestra is not None and maestra.telefono_principal is None:
                        maestra.enriquecer_contacto(telefono=telefono)
                        maestras.guardar(maestra)
                if not completado:
                    totales["personas_ya_completas"] += 1
                    continue
                personas.guardar(persona)
                print(f"  entidad {entidad_id}: {fila.nombres} {fila.apellidos} -> {', '.join(completado)}")

            totales["documentos_procesados"] += 1

        if aplicar:
            sesion.commit()
        else:
            sesion.rollback()

    print()
    print("APLICADO" if aplicar else "SIMULACION (nada se guardo; usar --aplicar para guardar)")
    for clave in (
        "documentos_procesados", "extensiones_completadas", "telefonos_completados", "personas_ya_completas",
        "filas_sin_persona_guardada", "documentos_sin_archivo", "documentos_ilegibles",
    ):
        print(f"  {clave}: {totales[clave]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
