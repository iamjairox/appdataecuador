"""Dobles de prueba (fakes) de los puertos, para testear casos de uso sin
Playwright ni PostgreSQL reales.
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.descubrimiento_dto import NumeralPublicadoDTO
from govdata.application.dto.entidad_dto import EntidadDescubiertaDTO
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.portal_scraper_port import PortalScraperPort
from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import GovDataError


class FakePortalScraperPort(PortalScraperPort):
    """Doble en memoria: cada metodo retorna lo que el test precargue, o
    lanza la excepcion precargada (para simular fallas de red/portal)."""

    def __init__(
        self,
        entidades: list[EntidadDescubiertaDTO] | None = None,
        meses_por_anio: dict[int, list[int]] | None = None,
        numerales_por_mes: dict[tuple[int, int], list[NumeralPublicadoDTO]] | None = None,
        error_a_lanzar: GovDataError | None = None,
    ) -> None:
        self._entidades = entidades or []
        self._meses_por_anio = meses_por_anio or {}
        self._numerales_por_mes = numerales_por_mes or {}
        self._error_a_lanzar = error_a_lanzar
        self.llamadas_meses: list[tuple[str, int]] = []
        self.llamadas_publicaciones: list[tuple[str, int, int]] = []

    def listar_entidades(self) -> list[EntidadDescubiertaDTO]:
        if self._error_a_lanzar:
            raise self._error_a_lanzar
        return self._entidades

    def listar_meses_publicados(self, url_entidad: str, anio: int) -> list[int]:
        self.llamadas_meses.append((url_entidad, anio))
        if self._error_a_lanzar:
            raise self._error_a_lanzar
        return self._meses_por_anio.get(anio, [])

    def listar_publicaciones_mes(
        self, url_entidad: str, anio: int, mes: int
    ) -> list[NumeralPublicadoDTO]:
        self.llamadas_publicaciones.append((url_entidad, anio, mes))
        if self._error_a_lanzar:
            raise self._error_a_lanzar
        return self._numerales_por_mes.get((anio, mes), [])


class FakeEntidadRepository(EntidadRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[Entidad] = []

    def guardar_o_actualizar(self, entidad: Entidad) -> Entidad:
        for existente in self.guardadas:
            if existente.url_transparencia == entidad.url_transparencia:
                existente.nombre = entidad.nombre
                return existente
        entidad.id = self._siguiente_id
        self._siguiente_id += 1
        self.guardadas.append(entidad)
        return entidad

    def buscar_por_id(self, entidad_id: int) -> Entidad | None:
        return next((e for e in self.guardadas if e.id == entidad_id), None)

    def buscar_por_url(self, url_transparencia: str) -> Entidad | None:
        return next((e for e in self.guardadas if e.url_transparencia == url_transparencia), None)

    def listar_activas(self, portal_origen: str | None = None) -> list[Entidad]:
        return [e for e in self.guardadas if e.activo]

    def buscar_por_nombre(self, fragmento_nombre: str) -> Entidad | None:
        candidatas = [e for e in self.guardadas if fragmento_nombre.lower() in e.nombre.lower()]
        return min(candidatas, key=lambda e: len(e.nombre)) if candidatas else None


class FakePublicacionRepository(PublicacionRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[PublicacionMensual] = []

    def guardar_o_actualizar(self, publicacion: PublicacionMensual) -> PublicacionMensual:
        existente = self.buscar_por_entidad_y_mes(publicacion.entidad_id, publicacion.mes_publicado)
        if existente:
            return existente
        publicacion.id = self._siguiente_id
        self._siguiente_id += 1
        self.guardadas.append(publicacion)
        return publicacion

    def buscar_por_entidad_y_mes(
        self, entidad_id: int, mes_publicado: date
    ) -> PublicacionMensual | None:
        return next(
            (
                p
                for p in self.guardadas
                if p.entidad_id == entidad_id and p.mes_publicado == mes_publicado
            ),
            None,
        )

    def buscar_ultima_por_entidad(
        self, entidad_id: int, excluir_mes: date | None = None
    ) -> PublicacionMensual | None:
        candidatas = [
            p
            for p in self.guardadas
            if p.entidad_id == entidad_id and (excluir_mes is None or p.mes_publicado != excluir_mes)
        ]
        return max(candidatas, key=lambda p: p.mes_publicado) if candidatas else None


class FakeDocumentoRepository(DocumentoRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[DocumentoTransparencia] = []

    def guardar_o_actualizar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        existente = self.buscar_por_publicacion(documento.publicacion_id)
        if existente:
            return existente
        documento.id = self._siguiente_id
        self._siguiente_id += 1
        self.guardados.append(documento)
        return documento

    def buscar_por_hash(self, hash_sha256: str) -> DocumentoTransparencia | None:
        return next((d for d in self.guardados if d.hash_sha256 == hash_sha256), None)

    def buscar_por_publicacion(self, publicacion_id: int) -> DocumentoTransparencia | None:
        return next((d for d in self.guardados if d.publicacion_id == publicacion_id), None)

    def buscar_por_id(self, documento_id: int) -> DocumentoTransparencia | None:
        return next((d for d in self.guardados if d.id == documento_id), None)

    def reclamar_para_descarga(self, documento_id: int) -> bool:
        documento = self.buscar_por_id(documento_id)
        if documento is None or documento.estado not in (
            EstadoDocumento.DESCUBIERTO,
            EstadoDocumento.ERROR,
        ):
            return False
        documento.estado = EstadoDocumento.DESCARGANDO
        return True

    def listar_pendientes(self, limite: int) -> list[DocumentoTransparencia]:
        return [
            d
            for d in self.guardados
            if d.estado in (EstadoDocumento.DESCUBIERTO, EstadoDocumento.ERROR)
        ][:limite]

    def liberar_estancados(self, minutos_limite: int) -> int:
        return 0
