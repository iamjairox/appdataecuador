"""Tests de integracion: modelos ORM, mappers y repositorio (Repository Pattern)."""

from __future__ import annotations

from datetime import date

from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.persistence.postgresql.mappers import entidad_mapper, persona_mapper
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.models.publicacion_model import PublicacionModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)


def test_crea_esquema_completo_sin_errores(sqlite_engine) -> None:
    """Las 7 tablas del Modulo 1 deben quedar registradas en el metadata."""
    tablas = set(sqlite_engine.dialect.get_table_names(sqlite_engine.connect()))
    esperadas = {
        "entidades",
        "personas",
        "funcionarios",
        "publicaciones",
        "documentos",
        "historial_cambios",
        "ejecuciones",
    }
    assert esperadas <= tablas


def test_mapper_entidad_ida_y_vuelta(sesion) -> None:
    entidad = Entidad(
        nombre="Defensoria del Pueblo",
        url_transparencia="https://transparencia.dpe.gob.ec/entidades/dpe",
        portal_origen="dpe",
    )
    modelo = entidad_mapper.a_modelo(entidad)
    sesion.add(modelo)
    sesion.commit()

    recuperado = sesion.get(EntidadModel, modelo.id)
    entidad_recuperada = entidad_mapper.a_dominio(recuperado)

    assert entidad_recuperada.id is not None
    assert entidad_recuperada.nombre == "Defensoria del Pueblo"


def test_mapper_persona_ida_y_vuelta(sesion) -> None:
    persona = Persona(
        nombre_completo=NombreCompleto("Juan Carlos", "Perez"),
        correo=Correo("juan.perez@dpe.gob.ec"),
    )
    modelo = persona_mapper.a_modelo(persona)
    sesion.add(modelo)
    sesion.commit()

    recuperado = sesion.get(PersonaModel, modelo.id)
    persona_recuperada = persona_mapper.a_dominio(recuperado)

    assert persona_recuperada.nombre_completo.nombre_completo == "JUAN CARLOS PEREZ"
    assert persona_recuperada.correo == Correo("juan.perez@dpe.gob.ec")


def test_repositorio_entidad_guarda_y_evita_duplicados_por_url(sesion) -> None:
    repo = SqlAlchemyEntidadRepository(sesion)

    entidad = Entidad(
        nombre="Defensoria del Pueblo",
        url_transparencia="https://transparencia.dpe.gob.ec/entidades/dpe",
        portal_origen="dpe",
    )
    repo.guardar_o_actualizar(entidad)
    sesion.commit()

    # Segunda corrida del scraper con el mismo url_transparencia: debe
    # actualizar el registro existente, no crear uno nuevo.
    entidad_actualizada = Entidad(
        nombre="Defensoria del Pueblo del Ecuador",
        url_transparencia="https://transparencia.dpe.gob.ec/entidades/dpe",
        portal_origen="dpe",
    )
    repo.guardar_o_actualizar(entidad_actualizada)
    sesion.commit()

    todas = repo.listar_activas()
    assert len(todas) == 1
    assert todas[0].nombre == "Defensoria del Pueblo del Ecuador"


def test_persona_funcionario_permite_misma_persona_en_dos_entidades(sesion) -> None:
    """Verifica el cambio arquitectonico central: una Persona (identidad
    unica) puede vincularse a mas de una Entidad via Funcionario, sin
    duplicar el registro de la persona.
    """
    persona = PersonaModel(nombres="JUAN CARLOS", apellidos="PEREZ")
    sesion.add(persona)
    sesion.flush()

    entidad_1 = EntidadModel(nombre="Entidad A", url_transparencia="https://a.gob.ec", portal_origen="dpe")
    entidad_2 = EntidadModel(nombre="Entidad B", url_transparencia="https://b.gob.ec", portal_origen="dpe")
    sesion.add_all([entidad_1, entidad_2])
    sesion.flush()

    sesion.add_all(
        [
            FuncionarioModel(
                persona_id=persona.id,
                entidad_id=entidad_1.id,
                cargo="Director Juridico",
                dependencia="Procuraduria",
                area_clasificada="juridica",
            ),
            FuncionarioModel(
                persona_id=persona.id,
                entidad_id=entidad_2.id,
                cargo="Asesor Juridico",
                dependencia="Procuraduria",
                area_clasificada="juridica",
            ),
        ]
    )
    sesion.commit()

    total_personas = sesion.query(PersonaModel).count()
    total_funcionarios = sesion.query(FuncionarioModel).filter_by(persona_id=persona.id).count()

    assert total_personas == 1
    assert total_funcionarios == 2


def test_documento_y_publicacion_encadenan_con_funcionario(sesion) -> None:
    entidad = EntidadModel(nombre="Entidad A", url_transparencia="https://a.gob.ec", portal_origen="dpe")
    sesion.add(entidad)
    sesion.flush()

    publicacion = PublicacionModel(
        entidad_id=entidad.id, mes_publicado=date(2026, 7, 1), url_item="https://a.gob.ec/julio"
    )
    sesion.add(publicacion)
    sesion.flush()

    # Estado "descubierto" (Modulo 2): solo se conoce la url del archivo,
    # todavia no se descargo -- ruta_almacenamiento y hash_sha256 son None.
    documento = DocumentoModel(
        publicacion_id=publicacion.id,
        tipo_archivo="pdf",
        nombre_original="directorio_julio.pdf",
        url_documento="https://a.gob.ec/media/publications/directorio_julio.pdf",
    )
    sesion.add(documento)
    sesion.commit()

    assert documento.id is not None
    assert documento.publicacion_id == publicacion.id
    assert documento.ruta_almacenamiento is None
    assert documento.hash_sha256 is None
