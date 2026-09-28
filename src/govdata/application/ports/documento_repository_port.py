"""Puerto: DocumentoRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.documento import DocumentoTransparencia


class DocumentoRepositoryPort(ABC):
    """Persistencia de documentos fuente (descubiertos y/o descargados)."""

    @abstractmethod
    def guardar_o_actualizar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        """Inserta el documento o actualiza el existente para la misma
        publicacion (dentro del alcance actual, una publicacion tiene a lo
        sumo un documento de interes)."""

    @abstractmethod
    def buscar_por_hash(self, hash_sha256: str) -> DocumentoTransparencia | None:
        """Permite detectar si un archivo ya fue descargado/procesado antes."""

    @abstractmethod
    def buscar_por_publicacion(self, publicacion_id: int) -> DocumentoTransparencia | None:
        """Recupera el documento ya descubierto para una publicacion, si existe.

        Usado para deduplicar en la fase de descubrimiento (Modulo 2), donde
        aun no hay hash disponible para comparar.
        """

    @abstractmethod
    def buscar_por_id(self, documento_id: int) -> DocumentoTransparencia | None: ...

    @abstractmethod
    def reclamar_para_descarga(self, documento_id: int) -> bool:
        """Intenta reclamar atomicamente un documento (DESCUBIERTO|ERROR ->
        DESCARGANDO) para que ESTE worker lo descargue. Retorna True si el
        claim tuvo exito, False si otro worker ya lo reclamo primero (o ya
        no esta en un estado reclamable) -- este es el mecanismo que hace
        de `documentos` una cola segura para multiples workers concurrentes,
        sin necesitar un broker externo (Redis/RQ quedan como adaptador
        futuro detras del mismo puerto si la escala lo exige).
        """

    @abstractmethod
    def listar_pendientes(self, limite: int) -> list[DocumentoTransparencia]:
        """Lista hasta `limite` documentos en estado DESCUBIERTO o ERROR
        (candidatos a encolar para descarga), mas antiguos primero. Es la
        base de la cola: reiniciar el proceso simplemente vuelve a llamar
        esto -- nada se pierde si el proceso se interrumpe a mitad de camino
        (los que quedaron en DESCARGANDO se liberan por separado, ver
        `liberar_estancados`).
        """

    @abstractmethod
    def liberar_estancados(self, minutos_limite: int) -> int:
        """Devuelve a DESCUBIERTO cualquier documento que lleve mas de
        `minutos_limite` en DESCARGANDO (un worker se cayo a mitad de una
        descarga sin poder marcar exito/error). Retorna cuantos se liberaron.
        Es lo que hace que la cola sea REANUDABLE tras una interrupcion.
        """
