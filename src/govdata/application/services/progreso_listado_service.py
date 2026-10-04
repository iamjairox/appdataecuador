"""Estado en memoria para mostrar progreso real de extracciones institucionales."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import Lock


@dataclass(slots=True)
class ProgresoListado:
    estado: str = "inactivo"
    total_filas: int | None = None
    filas_procesadas: int = 0
    funcionarios_extraidos: int = 0
    mensaje: str | None = None

    def a_dict(self) -> dict[str, int | str | None]:
        return asdict(self)


class ProgresoListadoService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._por_entidad: dict[int, ProgresoListado] = {}

    def iniciar(self, entidad_id: int) -> None:
        with self._lock:
            self._por_entidad[entidad_id] = ProgresoListado(
                estado="preparando", mensaje="Preparando el documento institucional…"
            )

    def establecer_total(self, entidad_id: int, total_filas: int) -> None:
        with self._lock:
            progreso = self._por_entidad.setdefault(entidad_id, ProgresoListado())
            progreso.estado = "extrayendo"
            progreso.total_filas = total_filas
            progreso.mensaje = "Extrayendo y guardando funcionarios…"

    def actualizar(self, entidad_id: int, filas_procesadas: int, funcionarios_extraidos: int) -> None:
        with self._lock:
            progreso = self._por_entidad.setdefault(entidad_id, ProgresoListado(estado="extrayendo"))
            progreso.estado = "extrayendo"
            progreso.filas_procesadas = filas_procesadas
            progreso.funcionarios_extraidos = funcionarios_extraidos

    def completar(self, entidad_id: int, funcionarios_extraidos: int) -> None:
        with self._lock:
            progreso = self._por_entidad.setdefault(entidad_id, ProgresoListado())
            progreso.estado = "completado"
            progreso.filas_procesadas = progreso.total_filas or progreso.filas_procesadas
            progreso.funcionarios_extraidos = funcionarios_extraidos
            progreso.mensaje = "Listado institucional actualizado."

    def fallar(self, entidad_id: int, mensaje: str) -> None:
        with self._lock:
            progreso = self._por_entidad.setdefault(entidad_id, ProgresoListado())
            progreso.estado = "error"
            progreso.mensaje = mensaje

    def obtener(self, entidad_id: int) -> dict[str, int | str | None]:
        with self._lock:
            progreso = self._por_entidad.get(entidad_id, ProgresoListado())
            return progreso.a_dict()


progreso_listados = ProgresoListadoService()
