"""Servidor HTTP local (modo simulacion) que sirve las fixtures del
portal DPE para los tests de integracion de `DpeScraperAdapter`.

Se descarto mockear via `BrowserContext.route()` porque se verifico
empiricamente que Playwright NO enruta las peticiones hechas con
`context.request` (APIRequestContext) por los handlers de `route()` --
solo intercepta trafico de paginas. Un servidor HTTP real local es en
realidad una prueba MEJOR: ejercita la pila HTTP completa (status codes,
headers, parseo JSON) exactamente como en produccion, solo que contra
`localhost` en vez del portal real.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_DIR_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "dpe"


def _cargar(nombre_archivo: str) -> bytes:
    return (_DIR_FIXTURES / nombre_archivo).read_bytes()


class DpeFixtureServer:
    """Servidor HTTP en un hilo de fondo, en un puerto libre del sistema."""

    def __init__(self) -> None:
        self.intentos_fallidos_restantes = 0  # simula N fallos 500 antes de exito (retry)
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
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)

                if parsed.path == "/simular-fallos-luego-exito":
                    if servidor_externo.intentos_fallidos_restantes > 0:
                        servidor_externo.intentos_fallidos_restantes -= 1
                        self.send_response(503)
                        self.end_headers()
                        return
                    self._responder_json(_cargar("months_2026_publicado.json"))
                    return

                if parsed.path == "/backend/v1/admin/public/establishment/list":
                    self._responder_json(_cargar("establishment_list_sample.json"))
                    return

                if parsed.path == "/backend/v1/transparency/transparency/months":
                    anio = query.get("year", [""])[0]
                    establishment_id = query.get("establishment_id", [""])[0]
                    if establishment_id == "9999":
                        self.send_response(404)
                        self.end_headers()
                        return
                    archivo = "months_2026_publicado.json" if anio == "2026" else "months_vacio.json"
                    self._responder_json(_cargar(archivo))
                    return

                if parsed.path == "/backend/v1/transparency/transparency/active/public":
                    establishment_id = query.get("establishment_id", [""])[0]
                    mes = query.get("month", [""])[0]
                    if establishment_id == "1920" and mes == "6":
                        self._responder_json(_cargar("active_public_junio_2026.json"))
                    elif establishment_id == "1358":
                        self._responder_json(_cargar("active_public_sin_item_directorio.json"))
                    elif establishment_id == "7777":
                        self._responder_json(_cargar("active_public_variante_pdf_sintetica.json"))
                    elif establishment_id == "6666":
                        self._responder_texto_no_json()
                    else:
                        self._responder_json(b"[]")
                    return

                self.send_response(404)
                self.end_headers()

            def _responder_json(self, cuerpo: bytes) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(cuerpo)

            def _responder_texto_no_json(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html>esto no es JSON</html>")

        return Handler
