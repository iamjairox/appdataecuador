"""Estado en memoria de la importación del directorio de Supercias."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import Lock


@dataclass(slots=True)
class ProgresoCompanias:
    estado: str = "inactivo"
    total_filas: int | None = None
    filas_procesadas: int = 0
    empresas_guardadas: int = 0
    bytes_descargados: int = 0
    bytes_totales: int | None = None
    mensaje: str | None = None

    def a_dict(self) -> dict[str, int | str | None]:
        return asdict(self)


class ProgresoCompaniasService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._progreso = ProgresoCompanias()

    def iniciar_descarga(self) -> None:
        with self._lock:
            self._progreso = ProgresoCompanias(
                estado="descargando", mensaje="Descargando el Excel oficial de Supercias…"
            )

    def descarga(self, descargados: int, totales: int | None) -> None:
        with self._lock:
            self._progreso.bytes_descargados = descargados
            self._progreso.bytes_totales = totales

    def iniciar_procesamiento(self, total_filas: int | None) -> None:
        with self._lock:
            self._progreso.estado = "procesando"
            self._progreso.total_filas = total_filas
            self._progreso.mensaje = "Leyendo y guardando empresas en el directorio local…"

    def actualizar(self, filas: int, empresas: int) -> None:
        with self._lock:
            self._progreso.estado = "procesando"
            self._progreso.filas_procesadas = filas
            self._progreso.empresas_guardadas = empresas

    def completar(self, empresas: int) -> None:
        with self._lock:
            self._progreso.estado = "completado"
            self._progreso.filas_procesadas = self._progreso.total_filas or self._progreso.filas_procesadas
            self._progreso.empresas_guardadas = empresas
            self._progreso.mensaje = "Directorio de compañías actualizado correctamente."

    def fallar(self, mensaje: str) -> None:
        with self._lock:
            self._progreso.estado = "error"
            self._progreso.mensaje = mensaje

    def obtener(self) -> dict[str, int | str | None]:
        with self._lock:
            return self._progreso.a_dict()


progreso_companias = ProgresoCompaniasService()
