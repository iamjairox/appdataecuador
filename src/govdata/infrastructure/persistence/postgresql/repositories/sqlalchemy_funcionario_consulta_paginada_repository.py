"""Adaptador: SqlAlchemyFuncionarioConsultaPaginadaRepository -- Modulo 10.

Consulta de SOLO LECTURA, paginada a nivel SQL (`LIMIT`/`OFFSET` + `COUNT`),
sobre los mismos modelos ORM de Modulos 1/4/6 (`FuncionarioModel`,
`PersonaModel`, `PersonaMasterModel`) -- ningun modelo/mapper/repositorio
existente se modifica, ver docstring de `FuncionarioConsultaPaginadaPort`."""

from __future__ import annotations

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from govdata.application.dto.filtros_funcionario_listado_dto import FiltrosFuncionarioListadoDTO
from govdata.application.dto.funcionario_listado_dto import FuncionarioListadoDTO
from govdata.application.ports.funcionario_consulta_paginada_port import (
    FuncionarioConsultaPaginadaPort,
)
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import (
    PersonaMasterModel,
)
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel


class SqlAlchemyFuncionarioConsultaPaginadaRepository(FuncionarioConsultaPaginadaPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _condiciones(
        self, entidad_id: int, filtros: FiltrosFuncionarioListadoDTO,
    ) -> list[ColumnElement[bool]]:
        condiciones: list[ColumnElement[bool]] = [FuncionarioModel.entidad_id == entidad_id]
        if filtros.solo_vigentes:
            condiciones.append(FuncionarioModel.fecha_fin.is_(None))
        if filtros.nombre:
            condiciones.append(PersonaModel.nombres.ilike(f"%{filtros.nombre}%"))
        if filtros.apellido:
            condiciones.append(PersonaModel.apellidos.ilike(f"%{filtros.apellido}%"))
        if filtros.cedula:
            condiciones.append(PersonaModel.cedula == filtros.cedula)
        if filtros.cargo:
            condiciones.append(FuncionarioModel.cargo.ilike(f"%{filtros.cargo}%"))
        if filtros.dependencia:
            condiciones.append(FuncionarioModel.dependencia.ilike(f"%{filtros.dependencia}%"))
        if filtros.area:
            condiciones.append(FuncionarioModel.area_clasificada == filtros.area)
        if filtros.correo:
            condiciones.append(PersonaModel.correo.ilike(f"%{filtros.correo}%"))
        if filtros.telefono:
            condiciones.append(PersonaModel.telefono == filtros.telefono)
        return condiciones

    def buscar_paginado(
        self, entidad_id: int, filtros: FiltrosFuncionarioListadoDTO, page: int, page_size: int,
    ) -> tuple[list[FuncionarioListadoDTO], int]:
        condiciones = self._condiciones(entidad_id, filtros)

        consulta_total = (
            select(func.count(FuncionarioModel.id))
            .select_from(FuncionarioModel)
            .join(PersonaModel, PersonaModel.id == FuncionarioModel.persona_id)
            .where(*condiciones)
        )
        total = self._session.execute(consulta_total).scalar_one()

        consulta_items = (
            select(FuncionarioModel, PersonaModel, PersonaMasterModel.id)
            .select_from(FuncionarioModel)
            .join(PersonaModel, PersonaModel.id == FuncionarioModel.persona_id)
            .outerjoin(PersonaMasterModel, PersonaMasterModel.persona_id == PersonaModel.id)
            .where(*condiciones)
            .order_by(FuncionarioModel.id.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        filas = self._session.execute(consulta_items).all()

        items = [
            FuncionarioListadoDTO(
                funcionario_id=funcionario.id,
                persona_id=persona.id,
                persona_master_id=persona_master_id,
                nombre_completo=f"{persona.nombres} {persona.apellidos}".strip(),
                nombres=persona.nombres,
                apellidos=persona.apellidos,
                cedula=persona.cedula,
                correo=persona.correo,
                telefono=persona.telefono,
                cargo=funcionario.cargo,
                dependencia=funcionario.dependencia,
                area=funcionario.area_clasificada.value,
                vigente=funcionario.fecha_fin is None,
                fecha_inicio=funcionario.fecha_inicio.isoformat() if funcionario.fecha_inicio else None,
                fecha_fin=funcionario.fecha_fin.isoformat() if funcionario.fecha_fin else None,
            )
            for funcionario, persona, persona_master_id in filas
        ]
        return items, total
