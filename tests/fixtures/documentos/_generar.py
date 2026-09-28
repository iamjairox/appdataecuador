"""Genera las fixtures binarias de este directorio. Ejecutar una sola vez
(o tras modificar el contenido esperado):

    python tests/fixtures/documentos/_generar.py

No se ejecuta como parte de la suite de tests -- los archivos generados
quedan versionados junto al codigo.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from openpyxl import Workbook

FIXTURES = Path(__file__).resolve().parent


def generar() -> None:
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    (FIXTURES / "directorio_valido.pdf").write_bytes(pdf)

    wb = Workbook()
    ws = wb.active
    ws.title = "Directorio"
    ws.append(["Nombres", "Apellidos", "Cargo", "Dependencia", "Correo", "Telefono"])
    ws.append(
        ["JUAN CARLOS", "PEREZ", "Director Juridico", "Procuraduria", "jperez@entidad.gob.ec", "0999999999"]
    )
    buffer = io.BytesIO()
    wb.save(buffer)
    (FIXTURES / "directorio_valido.xlsx").write_bytes(buffer.getvalue())

    (FIXTURES / "directorio_valido.xls").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 100)

    (FIXTURES / "directorio_valido.csv").write_bytes(
        b"nombres,apellidos,cargo,dependencia\nJUAN,PEREZ,Director Juridico,Procuraduria\n"
    )

    (FIXTURES / "pagina_error_disfrazada.pdf").write_bytes(
        b"<!DOCTYPE html>\n<html><head><title>404 Not Found</title></head>"
        b"<body><h1>404 Not Found</h1><p>El recurso solicitado no existe en este servidor.</p></body></html>"
    )

    (FIXTURES / "archivo_corrupto.bin").write_bytes(os.urandom(256))
    (FIXTURES / "respuesta_vacia.bin").write_bytes(b"")


if __name__ == "__main__":
    generar()
    print("Fixtures generadas en", FIXTURES)
