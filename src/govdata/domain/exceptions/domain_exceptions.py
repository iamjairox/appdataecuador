"""Jerarquia de excepciones del sistema GovData Intelligence Platform.

Todas las excepciones propias del sistema heredan de `GovDataError`. Esto
permite que capas superiores (orquestador, CLI, API) capturen un solo tipo
base cuando no les importa el detalle, o tipos especificos cuando si
necesitan decidir una politica distinta (reintentar, saltar, abortar).

Convencion de politica de reintento (aplicada por el orquestador en
modulos posteriores, documentada aqui porque es parte del contrato de
cada excepcion):

    - *Transitoria*  -> reintentable (fallas de red, timeouts)
    - *Permanente*   -> NO reintentable (dato invalido, formato no soportado)
"""

from __future__ import annotations


class GovDataError(Exception):
    """Excepcion base de todo el sistema."""


# --------------------------------------------------------------------------
# Errores de dominio (datos invalidos, reglas de negocio violadas)
# --------------------------------------------------------------------------


class ValorInvalidoError(GovDataError):
    """Un Value Object recibio un valor que no cumple sus invariantes."""


class EntidadInvalidaError(GovDataError):
    """Una Entidad publica no cumple los datos minimos requeridos."""


class PersonaInvalidaError(GovDataError):
    """Una Persona no cumple los datos minimos requeridos."""


class FuncionarioInvalidoError(GovDataError):
    """Un Funcionario (vinculo Persona-Entidad-Cargo) es invalido."""


# --------------------------------------------------------------------------
# Errores de flujo / infraestructura (capturados y clasificados por el
# orquestador en el modulo de Colas y Reintentos)
# --------------------------------------------------------------------------


class EntidadNoEncontradaError(GovDataError):
    """No se pudo localizar la entidad en el portal de origen. Transitorio."""


class PublicacionNoDisponibleError(GovDataError):
    """La entidad no tiene publicaciones de Transparencia Activa. Permanente."""


class DocumentoNoSoportadoError(GovDataError):
    """El documento descargado no es PDF/XLS/XLSX reconocible. Permanente."""


class DescargaFallidaError(GovDataError):
    """Fallo la descarga del documento (red, timeout, HTTP error 5xx/429). Transitorio."""


class RecursoNoDisponibleError(GovDataError):
    """El recurso remoto ya no existe (HTTP 404/410). Permanente."""


class ContenidoInvalidoError(GovDataError):
    """El contenido descargado no coincide con el tipo esperado (Content-Type,
    magic bytes o extension en conflicto), o es una pagina de error HTML
    disfrazada de documento. Permanente -- reintentar no lo arregla."""


class DocumentoYaEnProcesoError(GovDataError):
    """Otro worker ya reclamo este documento para descarga (colision de
    claim concurrente). Ni transitorio ni permanente: el llamador
    simplemente debe pasar al siguiente documento de la cola."""


class PresupuestoReintentosAgotadoError(GovDataError):
    """El documento ya acumulo el maximo de intentos de descarga
    configurado. Permanente hasta intervencion manual (o un `reintentar()`
    explicito que reinicie el conteo desde la perspectiva de negocio)."""


class ExtraccionFallidaError(GovDataError):
    """El parser no pudo extraer datos estructurados del documento."""


class ConfiguracionInvalidaError(GovDataError):
    """La configuracion cargada (settings/.env) es invalida o incompleta."""


class PersistenciaError(GovDataError):
    """Fallo al leer o escribir en el repositorio de persistencia."""


# --------------------------------------------------------------------------
# Modulo 5: Motor de Persistencia Inteligente, Historial, Deteccion de
# Cambios y Alertas
# --------------------------------------------------------------------------


class VersionFuncionarioInvalidaError(GovDataError):
    """Una VersionFuncionario (historial de cargo/dependencia) es invalida."""


class AlertaInvalidaError(GovDataError):
    """Una Alerta no cumple sus invariantes."""


class EventoInvalidoError(GovDataError):
    """Un Evento (cola de notificaciones, Submodulo 5.7) es invalido, o se
    intento una transicion de estado no permitida."""


class VerificacionInvalidaError(GovDataError):
    """Un registro de Verificacion (Submodulos 5.10/5.15) es invalido."""


class AuditoriaComparacionInvalidaError(GovDataError):
    """Un registro de AuditoriaComparacion (Submodulo 5.9) es invalido."""


class OportunidadComercialInvalidaError(GovDataError):
    """Una OportunidadComercial (Submodulo 5.17) es invalida."""


class ComparacionFallidaError(GovDataError):
    """El Motor de Comparacion (Submodulo 5.1) no pudo completar la
    comparacion entre dos versiones de un documento."""


# --------------------------------------------------------------------------
# Modulo 6: Motor de Identidad, Enriquecimiento de Personas y Fuentes
# Externas
# --------------------------------------------------------------------------


class PersonaMasterInvalidaError(GovDataError):
    """Una PersonaMaster (Submodulo 6.1) no cumple sus invariantes."""


class RegistroFuenteInvalidoError(GovDataError):
    """Un RegistroFuente (respuesta versionada de una fuente externa,
    Submodulo 6.9) es invalido."""


class AtributoTrazableInvalidoError(GovDataError):
    """Un AtributoTrazable (Submodulo 6.15, trazabilidad de dato) es
    invalido."""


class CasoRevisionIdentidadInvalidoError(GovDataError):
    """Un CasoRevisionIdentidad (Submodulo 6.21) es invalido, o se intento
    una transicion de estado no permitida."""


class ConsultaFuenteLogInvalidoError(GovDataError):
    """Un ConsultaFuenteLog (historial de consultas, Submodulo 6.10) es
    invalido."""


class EventoPerfilInvalidoError(GovDataError):
    """Un EventoPerfil (Submodulo 6.12) es invalido, o se intento una
    transicion de estado no permitida."""


class AlertaPerfilInvalidaError(GovDataError):
    """Una AlertaPerfil (Submodulo 6.13) no cumple sus invariantes."""


class ResolucionIdentidadFallidaError(GovDataError):
    """El Motor de Resolucion de Identidad (Submodulo 6.2) no pudo
    completar la resolucion (ej. senales insuficientes)."""


class EnriquecimientoFallidoError(GovDataError):
    """El pipeline de Enriquecimiento (Submodulo 6.7) no pudo completarse
    para una Persona."""


# --------------------------------------------------------------------------
# Modulo 7: Adaptador SENESCYT + Enriquecimiento Academico
# --------------------------------------------------------------------------


class TituloAcademicoInvalidoError(GovDataError):
    """Un TituloAcademico (Submodulo 7.6) no cumple sus invariantes."""


class TituloVersionAcademicaInvalidaError(GovDataError):
    """Una TituloVersionAcademica (historial, Submodulo 7.6/7.14) es invalida."""


class HistorialAcademicoInvalidoError(GovDataError):
    """Un HistorialAcademico (registro de cambio, Submodulo 7.14) es invalido."""


class ConsultaSenescytInvalidaError(GovDataError):
    """Un registro de ConsultaSenescyt (auditoria, Submodulo 7.15) es invalido."""


class EventoAcademicoInvalidoError(GovDataError):
    """Un EventoAcademico (Submodulo 7.9) es invalido, o se intento una
    transicion de estado no permitida."""


class AlertaAcademicaInvalidaError(GovDataError):
    """Una AlertaAcademica (Submodulo 7.8) no cumple sus invariantes."""


class ConsultaSenescytFallidaError(GovDataError):
    """El adaptador SENESCYT (Submodulo 7.2) no pudo completar la consulta.
    Transitorio por defecto (red, timeout, respuesta inesperada) -- el
    llamador decide su propia politica de reintento."""


class EnriquecimientoAcademicoFallidoError(GovDataError):
    """El pipeline de Enriquecimiento Academico (Modulo 7) no pudo
    completarse para una PersonaMaster."""


# --------------------------------------------------------------------------
# Modulo 8: Motor de Consulta al Foro de Abogados, Fusion de Datos y
# Perfil Consolidado del Funcionario
# --------------------------------------------------------------------------


class RegistroForoInvalidoError(GovDataError):
    """Un RegistroForo (Submodulo 8.1, puntero vigente) no cumple sus
    invariantes."""


class RegistroForoVersionInvalidaError(GovDataError):
    """Una RegistroForoVersion (historial, Submodulo 8.6/8.14) es invalida."""


class HistorialForoInvalidoError(GovDataError):
    """Un HistorialForo (registro de cambio, Submodulo 8.6) es invalido."""


class ConsultaForoInvalidaError(GovDataError):
    """Un registro de ConsultaForo (auditoria, Submodulo 8.17) es invalido."""


class EventoForoInvalidoError(GovDataError):
    """Un EventoForo (Submodulo 8.7) es invalido, o se intento una
    transicion de estado no permitida."""


class AlertaForoInvalidaError(GovDataError):
    """Una AlertaForo (Submodulo 8.7) no cumple sus invariantes."""


class ConsultaForoFallidaError(GovDataError):
    """El adaptador del Foro de Abogados (Submodulo 8.2) no pudo completar
    la consulta por un motivo TRANSITORIO (red, timeout, HTTP 5xx, pagina
    momentaneamente vacia/error de servidor). Reintentable (Submodulo
    8.9) -- ver `ConsultaForoPermanenteError` para el caso NO
    reintentable."""


class ConsultaForoPermanenteError(GovDataError):
    """El adaptador del Foro de Abogados (Submodulo 8.2/8.9) detecto un
    fallo PERMANENTE: CAPTCHA, HTTP 4xx del cliente (distinto de 404, que
    se interpreta como "sin resultados"), o una respuesta con forma tan
    irreconocible que reintentar no la arreglaria. NUNCA se reintenta."""


class ForoCircuitoAbiertoError(GovDataError):
    """El Circuit Breaker del adaptador del Foro (Submodulo 8.9) esta
    ABIERTO -- se rechazan consultas sin siquiera intentar la red, hasta
    que expire el periodo de enfriamiento. Transitorio (el llamador puede
    reintentar mas tarde, nunca es un error de datos)."""


class EnriquecimientoForoFallidoError(GovDataError):
    """El pipeline de consulta al Foro de Abogados (Modulo 8) no pudo
    completarse para una PersonaMaster."""


class PerfilConsolidadoInvalidoError(GovDataError):
    """El Perfil Consolidado (Submodulo 8.10/8.11) no pudo construirse --
    falta algun insumo obligatorio (persona, funcionario o identidad)."""


# --------------------------------------------------------------------------
# Modulo 9: Orquestador Maestro del Sistema GovData
# --------------------------------------------------------------------------


class TrabajoOrquestadorInvalidoError(GovDataError):
    """Un TrabajoOrquestador (Submodulo 9.6, cola persistente) no cumple
    sus invariantes, o se intento una transicion de estado no permitida."""


class BloqueoOptimistaFallidoError(GovDataError):
    """El bloqueo optimista de un TrabajoOrquestador (Submodulo 9.8) fallo:
    otro worker ya tomo/modifico el trabajo entre la lectura y la
    escritura. Transitorio -- el llamador debe pasar al siguiente
    candidato de la cola, nunca reintentar el MISMO trabajo a ciegas."""


class AuditoriaEtapaInvalidaError(GovDataError):
    """Un registro de AuditoriaEtapa (Submodulos 9.10/9.15) es invalido."""


class PoliticaEjecucionInvalidaError(GovDataError):
    """Una PoliticaEjecucion (Motor de Politicas, mejora sugerida por el
    cliente al cierre del Modulo 8) no existe en el catalogo configurado,
    o su definicion YAML es invalida."""


class PlanEjecucionInvalidoError(GovDataError):
    """Un PlanEjecucion (Submodulo 9.3) no pudo construirse."""


class OrquestacionFallidaError(GovDataError):
    """El `GovDataPipelineOrchestrator` (Submodulo 9.1) no pudo completar
    la orquestacion de una entidad."""
