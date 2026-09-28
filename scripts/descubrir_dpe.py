"""Entry point del Modulo 2: descubrimiento del portal DPE.

Ejecuta el pipeline completo de descubrimiento (no descarga archivos):

    1. Lista y persiste todas las entidades del portal.
    2. Para cada entidad (en paralelo, con concurrencia/rate-limit
       configurables), detecta su ultima publicacion mensual y el
       documento "Directorio y distributivo del personal", persistiendo
       la metadata encontrada.

Uso:
    python scripts/descubrir_dpe.py
"""

from __future__ import annotations

import sys

from govdata.config.container import Container


def main() -> int:
    container = Container()
    logger = container.logger

    entidades = container.descubrir_y_persistir_entidades()
    if not entidades:
        logger.warning("sin_entidades_descubiertas")
        return 0

    orquestador = container.crear_pipeline_descubrimiento()
    resumen = orquestador.ejecutar(entidades)

    logger.info(
        "resumen_final",
        total_entidades=resumen.total_entidades,
        publicaciones_encontradas=resumen.publicaciones_encontradas,
        documentos_encontrados=resumen.documentos_encontrados,
        errores=resumen.errores,
        duracion_segundos=round(resumen.duracion_segundos, 2),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
