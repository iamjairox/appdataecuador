"""Caso de uso: ObtenerCambiosEntidadUseCase -- Modulo 10 (API REST).

Compone `HistorialService.historial_de_dependencias` (Modulo 5,
congelado, REUTILIZADO) -- ver `CambioEntidadDTO` para la justificacion
de por que `tipo_cambio`/`criticidad` no se rellenan."""

from __future__ import annotations

from datetime import date

from govdata.application.dto.cambio_entidad_dto import CambioEntidadDTO
from govdata.application.dto.pagina_dto import PaginaDTO
from govdata.application.services.historial_service import HistorialService


class ObtenerCambiosEntidadUseCase:
    def __init__(self, historial_service: HistorialService) -> None:
        self._historial_service = historial_service

    def ejecutar(
        self, entidad_id: int, page: int, page_size: int, desde: date | None = None, hasta: date | None = None,
    ) -> PaginaDTO[CambioEntidadDTO]:
        por_persona = self._historial_service.historial_de_dependencias(entidad_id)
        cambios = [
            CambioEntidadDTO(
                persona_id=persona_id, numero_version=v.numero_version, cargo=v.cargo, dependencia=v.dependencia,
                fecha_inicio=v.fecha_inicio, fecha_fin=v.fecha_fin, tipo_cambio=None, criticidad=None,
            )
            for persona_id, versiones in por_persona.items()
            for v in versiones
            if (desde is None or v.fecha_inicio >= desde) and (hasta is None or v.fecha_inicio <= hasta)
        ]
        cambios.sort(key=lambda c: c.fecha_inicio, reverse=True)

        total = len(cambios)
        inicio = (page - 1) * page_size
        pagina = cambios[inicio : inicio + page_size]
        return PaginaDTO(items=pagina, page=page, page_size=page_size, total=total)
