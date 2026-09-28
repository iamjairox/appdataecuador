# Fixtures binarias -- Modulo 3 (Descarga de Documentos)

Generadas programaticamente (ver `tests/integration/conftest.py` o el
script de generacion documentado abajo), no descargadas de ningun sitio
real. Sirven al `HttpFetcherFixtureServer` (servidor HTTP local) para
simular respuestas reales sin depender de Internet.

| Archivo | Firma (magic bytes) | Uso en tests |
|---|---|---|
| `directorio_valido.pdf` | `%PDF-1.4` | Descarga exitosa, tipo PDF |
| `directorio_valido.xlsx` | `PK\x03\x04` (ZIP) | Descarga exitosa, tipo XLSX (generado con `openpyxl`, XLSX real) |
| `directorio_valido.xls` | `\xd0\xcf\x11\xe0...` (OLE) | Descarga exitosa, tipo XLS (solo firma -- Modulo 3 no parsea) |
| `directorio_valido.csv` | texto plano | Descarga exitosa, tipo CSV (sin magic bytes propios) |
| `pagina_error_disfrazada.pdf` | `<!DOCTYPE html>` | El caso central del modulo: servidor devuelve `200 OK` + `Content-Type: application/pdf` pero el cuerpo es una pagina de error HTML -- debe rechazarse (`ContenidoInvalidoError`) |
| `archivo_corrupto.bin` | bytes aleatorios, sin firma reconocible | Ninguna senal (Content-Type/magic-bytes/extension) coincide -- debe rechazarse |
| `respuesta_vacia.bin` | 0 bytes | Respuesta HTTP 200 sin cuerpo |

Regenerar con:

```bash
python tests/fixtures/documentos/_generar.py
```

Servidas a los tests de integracion via `tests/integration/descarga_fixture_server.py`
(servidor HTTP local que simula 200/404/500/timeout/duplicados sobre estos archivos).
