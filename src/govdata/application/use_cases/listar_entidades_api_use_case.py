"""Caso de uso: ListarEntidadesApiUseCase -- Modulo 10 (API REST).

NUEVO (propio del Modulo 10): compone `EntidadRepositoryPort` +
`PublicacionRepositoryPort` (ambos Modulo 2, congelados) para armar el
listado que pide `GET /api/v1/entidades`. No reimplementa descubrimiento
ni persistencia -- solo LEE lo que Modulo 2 ya calculo.

Paginacion EN MEMORIA (a diferencia de `FuncionarioConsultaPaginadaPort`):
el universo de Entidades es pequeno (decenas/cientos de instituciones
publicas, nunca miles de funcionarios), asi que no amerita un puerto SQL
paginado nuevo -- `EntidadRepositoryPort.listar_activas` ya es barato de
cargar completo."""

from __future__ import annotations

from govdata.application.dto.entidad_listado_dto import EntidadListadoDTO
from govdata.application.dto.filtros_entidad_listado_dto import FiltrosEntidadListadoDTO
from govdata.application.dto.pagina_dto import PaginaDTO
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.domain.entities.entidad import Entidad


class ListarEntidadesApiUseCase:
    def __init__(
        self, entidad_repository: EntidadRepositoryPort, publicacion_repository: PublicacionRepositoryPort,
    ) -> None:
        self._entidad_repository = entidad_repository
        self._publicacion_repository = publicacion_repository

    def _a_dto(self, entidad: Entidad) -> EntidadListadoDTO:
        assert entidad.id is not None
        publicacion = self._publicacion_repository.buscar_ultima_por_entidad(entidad.id)
        return EntidadListadoDTO(
            id=entidad.id,
            nombre=entidad.nombre,
            tipo=entidad.metadata_extra.get("tipo_institucion"),
            provincia=None,
            ciudad=None,
            portal_origen=entidad.portal_origen,
            estado="activa" if entidad.activo else "inactiva",
            ultima_publicacion=publicacion.mes_publicado if publicacion else None,
            ultima_actualizacion=entidad.actualizado_en,
        )

    def _coincide(self, entidad: Entidad, filtros: FiltrosEntidadListadoDTO) -> bool:
        if filtros.nombre and filtros.nombre.lower() not in entidad.nombre.lower():
            return False
        if filtros.portal_origen and entidad.portal_origen != filtros.portal_origen:
            return False
        # provincia/ciudad: aceptados, sin efecto (ver docstring del modulo).
        return not (
            filtros.tipo_institucion and entidad.metadata_extra.get("tipo_institucion") != filtros.tipo_institucion
        )

    def ejecutar(
        self, filtros: FiltrosEntidadListadoDTO, page: int, page_size: int,
    ) -> PaginaDTO[EntidadListadoDTO]:
        todas = [e for e in self._entidad_repository.listar_activas() if self._coincide(e, filtros)]
        total = len(todas)
        inicio = (page - 1) * page_size
        pagina = todas[inicio : inicio + page_size]
        return PaginaDTO(items=[self._a_dto(e) for e in pagina], page=page, page_size=page_size, total=total)

    def obtener_por_id(self, entidad_id: int) -> EntidadListadoDTO | None:
        entidad = self._entidad_repository.buscar_por_id(entidad_id)
        if entidad is None:
            return None
        return self._a_dto(entidad)
