"""Entidad de dominio: PersonaMaster -- Submodulo 6.1 (Master Person).

El registro maestro unico de una Persona a traves de TODAS las fuentes
(DPE, SENESCYT, Foro de Abogados, Funcion Judicial, SRI, Contraloria,
Registro Mercantil, ...). "Nunca existiran personas duplicadas: debe
existir un unico registro maestro" -- esta clase es ese registro.

Deliberadamente NO reemplaza ni modifica `Persona` (Modulo 1-5, congelada):
`PersonaMaster.persona_id` apunta a la `Persona` original (la identidad
minima ya validada por el pipeline de DPE) y la enriquece con lo que
Modulo 6 agrega -- huella fonetica, confianza, conteo de fuentes, estado
de resolucion de identidad. Cuando aparezcan mas fuentes en el futuro,
cada una seguira produciendo su propio `Persona`-like record de origen (o,
para fuentes sin tabla propia, solo un `RegistroFuente`); el vinculo
"estas N cosas son la misma persona" vive aqui, nunca en `Persona`.

Solo contiene informacion CONSOLIDADA (nunca duplicada): correo/telefono
"principal" son el mejor dato conocido en un momento dado, no una copia
de cada fuente -- el dato crudo, versionado y con procedencia, vive en
`RegistroFuente` + `AtributoTrazable`.
"""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import date, datetime

from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono


@dataclass(slots=True)
class PersonaMaster:
    """Registro maestro de identidad, unico por individuo real."""

    persona_id: int
    nombre_completo: NombreCompleto
    id: int | None = None
    uuid: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    fingerprint_principal: str | None = None
    fingerprint_fonetico: str | None = None
    sexo: str | None = None
    fecha_nacimiento: date | None = None
    correo_principal: Correo | None = None
    telefono_principal: Telefono | None = None
    estado: EstadoPersonaMaster = EstadoPersonaMaster.ACTIVA
    nivel_confianza: float = 100.0
    cantidad_fuentes: int = 1
    cantidad_cargos_historicos: int = 0
    fusionada_en_id: int | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.persona_id is None:
            raise PersonaMasterInvalidaError("PersonaMaster requiere persona_id")
        if not (0.0 <= self.nivel_confianza <= 100.0):
            raise PersonaMasterInvalidaError(
                f"nivel_confianza fuera de rango [0, 100]: {self.nivel_confianza}"
            )
        if self.cantidad_fuentes < 0:
            raise PersonaMasterInvalidaError("cantidad_fuentes no puede ser negativa")
        if self.cantidad_cargos_historicos < 0:
            raise PersonaMasterInvalidaError("cantidad_cargos_historicos no puede ser negativa")
        if self.estado == EstadoPersonaMaster.FUSIONADA and self.fusionada_en_id is None:
            raise PersonaMasterInvalidaError(
                "PersonaMaster FUSIONADA requiere fusionada_en_id (registro ganador)"
            )
        if self.estado != EstadoPersonaMaster.FUSIONADA and self.fusionada_en_id is not None:
            raise PersonaMasterInvalidaError(
                "fusionada_en_id solo aplica cuando estado es FUSIONADA"
            )

    @property
    def activa(self) -> bool:
        return self.estado != EstadoPersonaMaster.FUSIONADA

    def registrar_nueva_fuente(self) -> None:
        """Una fuente adicional (ej. SENESCYT ademas de DPE) confirmo o
        aporto datos a esta identidad -- Submodulo 6.1 ("cantidad de
        fuentes")."""
        self.cantidad_fuentes += 1

    def actualizar_cargos_historicos(self, cantidad: int) -> None:
        if cantidad < 0:
            raise PersonaMasterInvalidaError("cantidad de cargos historicos no puede ser negativa")
        self.cantidad_cargos_historicos = cantidad

    def enriquecer_contacto(self, correo: Correo | None = None, telefono: Telefono | None = None) -> None:
        """Nunca sobreescribe un dato conocido con None -- misma politica
        que `Persona.actualizar_datos_contacto` (Modulo 1)."""
        if correo is not None:
            self.correo_principal = correo
        if telefono is not None:
            self.telefono_principal = telefono

    def marcar_en_revision(self) -> None:
        if self.estado == EstadoPersonaMaster.FUSIONADA:
            raise PersonaMasterInvalidaError("No se puede poner en revision una PersonaMaster ya fusionada")
        self.estado = EstadoPersonaMaster.EN_REVISION

    def marcar_activa(self) -> None:
        if self.estado == EstadoPersonaMaster.FUSIONADA:
            raise PersonaMasterInvalidaError("No se puede reactivar una PersonaMaster ya fusionada")
        self.estado = EstadoPersonaMaster.ACTIVA

    def fusionar_en(self, persona_master_ganadora_id: int) -> None:
        """Marca esta PersonaMaster como absorbida por otra (Submodulo
        6.14/6.21). Nunca se borra -- solo queda inerte, con trazabilidad
        de a donde fue a parar."""
        if persona_master_ganadora_id == self.id:
            raise PersonaMasterInvalidaError("Una PersonaMaster no puede fusionarse consigo misma")
        self.estado = EstadoPersonaMaster.FUSIONADA
        self.fusionada_en_id = persona_master_ganadora_id
