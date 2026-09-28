"""Mapper: PersonaModel <-> Persona (dominio)."""

from __future__ import annotations

from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel


def a_dominio(modelo: PersonaModel) -> Persona:
    return Persona(
        id=modelo.id,
        nombre_completo=NombreCompleto(nombres=modelo.nombres, apellidos=modelo.apellidos),
        cedula=modelo.cedula,
        correo=Correo.crear_opcional(modelo.correo),
        telefono=Telefono.crear_opcional(modelo.telefono),
        fingerprint=modelo.fingerprint,
        fingerprint_hash=modelo.fingerprint_hash,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(persona: Persona, modelo: PersonaModel | None = None) -> PersonaModel:
    modelo = modelo or PersonaModel()
    if persona.id is not None:
        modelo.id = persona.id
    modelo.nombres = persona.nombre_completo.nombres
    modelo.apellidos = persona.nombre_completo.apellidos
    modelo.cedula = persona.cedula
    modelo.correo = str(persona.correo) if persona.correo else None
    modelo.telefono = str(persona.telefono) if persona.telefono else None
    modelo.fingerprint = persona.fingerprint
    modelo.fingerprint_hash = persona.fingerprint_hash
    return modelo
