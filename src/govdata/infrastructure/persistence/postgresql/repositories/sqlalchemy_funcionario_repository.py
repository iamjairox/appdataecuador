"""Adaptador: SqlAlchemyFuncionarioRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.domain.entities.funcionario import Funcionario
from govdata.infrastructure.persistence.postgresql.mappers import funcionario_mapper
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel


class SqlAlchemyFuncionarioRepository(FuncionarioRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, funcionario: Funcionario) -> Funcionario:
        modelo_existente = self._session.get(FuncionarioModel, funcionario.id) if funcionario.id else None
        modelo = funcionario_mapper.a_modelo(funcionario, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return funcionario_mapper.a_dominio(modelo)

    def guardar_lote(self, funcionarios: list[Funcionario]) -> list[Funcionario]:
        return [self.guardar(f) for f in funcionarios]

    def buscar_vigente(self, persona_id: int, entidad_id: int) -> Funcionario | None:
        modelo = (
            self._session.execute(
                select(FuncionarioModel).where(
                    FuncionarioModel.persona_id == persona_id,
                    FuncionarioModel.entidad_id == entidad_id,
                    FuncionarioModel.fecha_fin.is_(None),
                )
            )
            .scalars()
            .first()
        )
        return funcionario_mapper.a_dominio(modelo) if modelo else None

    def listar_por_entidad(self, entidad_id: int, solo_vigentes: bool = True) -> list[Funcionario]:
        condiciones = [FuncionarioModel.entidad_id == entidad_id]
        if solo_vigentes:
            condiciones.append(FuncionarioModel.fecha_fin.is_(None))
        modelos = self._session.execute(select(FuncionarioModel).where(*condiciones)).scalars().all()
        return [funcionario_mapper.a_dominio(m) for m in modelos]

    def listar_por_documento(self, documento_id: int) -> list[Funcionario]:
        modelos = (
            self._session.execute(
                select(FuncionarioModel).where(FuncionarioModel.documento_id == documento_id)
            )
            .scalars()
            .all()
        )
        return [funcionario_mapper.a_dominio(m) for m in modelos]

    def buscar_con_filtros(self, filtros: FiltrosConsultaDTO) -> list[Funcionario]:
        consulta = select(FuncionarioModel).join(
            PersonaModel, FuncionarioModel.persona_id == PersonaModel.id
        )

        condiciones = []
        if filtros.area is not None:
            condiciones.append(FuncionarioModel.area_clasificada == filtros.area)
        if filtros.cargo_contiene:
            condiciones.append(FuncionarioModel.cargo.ilike(f"%{filtros.cargo_contiene}%"))
        if filtros.correo_disponible is True:
            condiciones.append(PersonaModel.correo.is_not(None))
        elif filtros.correo_disponible is False:
            condiciones.append(PersonaModel.correo.is_(None))
        if filtros.telefono_disponible is True:
            condiciones.append(PersonaModel.telefono.is_not(None))
        elif filtros.telefono_disponible is False:
            condiciones.append(PersonaModel.telefono.is_(None))
        if condiciones:
            consulta = consulta.where(*condiciones)

        modelos = self._session.execute(consulta).scalars().all()
        resultado = [funcionario_mapper.a_dominio(m) for m in modelos]

        # provincia/ciudad/tipo_institucion viven en `Entidad.metadata_extra`
        # (JSON), sin indice dedicado todavia -- se filtran en Python tras
        # la consulta SQL. Documentado como limite de escala conocido (ver
        # "mejoras futuras" del Modulo 4): con volumenes grandes conviene
        # promover estos campos a columnas propias indexadas.
        if filtros.tipo_institucion:
            entidad_ids_validos = self._entidad_ids_por_tipo_institucion(filtros.tipo_institucion)
            resultado = [f for f in resultado if f.entidad_id in entidad_ids_validos]

        return resultado

    def _entidad_ids_por_tipo_institucion(self, tipo_institucion: str) -> set[int]:
        modelos = self._session.execute(select(EntidadModel)).scalars().all()
        return {
            m.id
            for m in modelos
            if (m.metadata_extra or {}).get("tipo_institucion") == tipo_institucion
        }
