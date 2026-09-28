"""Servidor HTTP local (modo simulacion) para los tests de integracion de
`RequestsHttpFetcherAdapter` / `DescargarDocumentoUseCase`.

Sirve las fixtures binarias de `tests/fixtures/documentos/` bajo distintas
rutas que simulan: 200 OK, 404, 500 (con recuperacion tras N intentos),
timeout (respuesta deliberadamente lenta), pagina de error disfrazada de
PDF, y contenido corrupto -- sin depender de ningun servidor externo.
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_DIR_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "documentos"


def _cargar(nombre_archivo: str) -> bytes:
    return (_DIR_FIXTURES / nombre_archivo).read_bytes()


class DescargaFixtureServer:
    """Servidor HTTP en un hilo de fondo, en un puerto libre del sistema."""

    def __init__(self) -> None:
        self.intentos_fallidos_restantes = 0
        self.segundos_de_retraso = 0.0
        self._servidor = ThreadingHTTPServer(("127.0.0.1", 0), self._crear_handler())
        self._hilo = threading.Thread(target=self._servidor.serve_forever, daemon=True)

    @property
    def url_origen(self) -> str:
        host, port = self._servidor.server_address[:2]
        return f"http://{host}:{port}"

    def iniciar(self) -> None:
        self._hilo.start()

    def detener(self) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()

    def _crear_handler(self) -> type[BaseHTTPRequestHandler]:
        servidor_externo = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_GET(self) -> None:
                ruta = self.path

                if ruta == "/archivo/valido.pdf":
                    self._responder(200, _cargar("directorio_valido.pdf"), "application/pdf")
                elif ruta == "/archivo/valido.xlsx":
                    self._responder(
                        200,
                        _cargar("directorio_valido.xlsx"),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                elif ruta == "/archivo/valido.csv":
                    self._responder(200, _cargar("directorio_valido.csv"), "text/csv")
                elif ruta == "/archivo/no-encontrado":
                    self.send_response(404)
                    self.end_headers()
                elif ruta == "/archivo/error-servidor":
                    self.send_response(500)
                    self.end_headers()
                elif ruta == "/archivo/pagina-error-disfrazada":
                    self._responder(200, _cargar("pagina_error_disfrazada.pdf"), "application/pdf")
                elif ruta == "/archivo/corrupto":
                    self._responder(200, _cargar("archivo_corrupto.bin"), "application/octet-stream")
                elif ruta == "/archivo/vacio":
                    self._responder(200, _cargar("respuesta_vacia.bin"), "application/pdf")
                elif ruta == "/archivo/lento":
                    time.sleep(servidor_externo.segundos_de_retraso)
                    self._responder(200, _cargar("directorio_valido.pdf"), "application/pdf")
                elif ruta == "/archivo/flaky":
                    if servidor_externo.intentos_fallidos_restantes > 0:
                        servidor_externo.intentos_fallidos_restantes -= 1
                        self.send_response(503)
                        self.end_headers()
                        return
                    self._responder(200, _cargar("directorio_valido.pdf"), "application/pdf")
                else:
                    self.send_response(404)
                    self.end_headers()

            def _responder(self, status: int, cuerpo: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("ETag", '"etag-de-prueba"')
                self.send_header("Last-Modified", "Tue, 04 Aug 2026 10:00:00 GMT")
                self.end_headers()
                self.wfile.write(cuerpo)

        return Handler
