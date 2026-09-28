"""Entry point del Modulo 3: descarga de documentos.

Toma los documentos en estado DESCUBIERTO/ERROR (la cola, persistida en
BD -- ver `DocumentoRepositoryPort`), los descarga con concurrencia
configurable, valida su contenido real (Content-Type -> Magic Bytes ->
Extension), calcula SHA-256, deduplica globalmente, almacena (local o
MinIO segun `STORAGE_BACKEND`) y deja auditoria completa en `Descarga` y
`Manifest`. Nunca parsea el contenido.

Uso:
    python scripts/descargar_documentos.py
"""

from __future__ import annotations

import sys

from govdata.config.container import Container


def main() -> int:
    container = Container()
    logger = container.logger

    documentos = container.listar_documentos_pendientes()
    if not documentos:
        logger.info("sin_documentos_pendientes")
        return 0

    orquestador = container.crear_pipeline_descarga()
    resumen = orquestador.ejecutar(documentos)

    logger.info(
        "resumen_final_descarga",
        total_documentos=resumen.total_documentos,
        descargados=resumen.descargados,
        omitidos=resumen.omitidos,
        errores=resumen.errores,
        bytes_totales=resumen.bytes_totales,
        duracion_segundos=round(resumen.duracion_segundos, 2),
        velocidad_promedio_bytes_por_segundo=round(resumen.velocidad_promedio_bytes_por_segundo, 2),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
