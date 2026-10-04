import type {
  AlertaEntidad,
  AlertaFuncionario,
  CambioEntidad,
  ConsultaEntidadResultado,
  Entidad,
  EtapaJob,
  Funcionario,
  Job,
  Pagina,
  PerfilAcademico,
  PerfilConsolidado,
  PuntoTimeline,
  Timeline,
  VersionHistorial,
} from '../types'

/**
 * Fixtures que respetan EXACTAMENTE los contratos reales del backend
 * (Módulo 10, confirmados en el código fuente -- ver informes de FASE 0/1/2).
 * Nunca se inventa un campo que el backend no envía; estos objetos son la
 * base de los tests con MSW (Sección 31 del prompt de FASE 2).
 */

export function crearEntidad(overrides: Partial<Entidad> = {}): Entidad {
  return {
    id: 1,
    nombre: 'Ministerio de Ejemplo',
    tipo: 'Ministerio',
    provincia: null,
    ciudad: null,
    portal_origen: 'DPE',
    estado: 'activa',
    ultima_publicacion: '2026-06-01',
    ultima_actualizacion: '2026-06-02T10:00:00Z',
    ...overrides,
  }
}

export function crearPaginaEntidades(overrides: Partial<Pagina<Entidad>> = {}): Pagina<Entidad> {
  return {
    items: [crearEntidad()],
    page: 1,
    page_size: 20,
    total: 1,
    pages: 1,
    ...overrides,
  }
}

export function crearFuncionarioListado(overrides: Partial<Funcionario> = {}): Funcionario {
  return {
    funcionario_id: 10,
    persona_id: 20,
    persona_master_id: 30,
    nombre_completo: 'Ana Pérez',
    nombres: 'Ana',
    apellidos: 'Pérez',
    cedula: '1712345678',
    correo: 'ana.perez@ejemplo.gob.ec',
    telefono: '022345678',
    cargo: 'Abogada',
    dependencia: 'Asesoría Jurídica',
    area: 'juridica',
    vigente: true,
    fecha_inicio: '2024-01-01',
    fecha_fin: null,
    ...overrides,
  }
}

export function crearPaginaFuncionarios(overrides: Partial<Pagina<Funcionario>> = {}): Pagina<Funcionario> {
  return {
    items: [crearFuncionarioListado()],
    page: 1,
    page_size: 20,
    total: 1,
    pages: 1,
    ...overrides,
  }
}

export function crearResultadoConsulta(overrides: Partial<ConsultaEntidadResultado> = {}): ConsultaEntidadResultado {
  return {
    job: { id: 'job-123', tipo: 'consulta_entidad', estado: 'completado' },
    entidad: { id: 1, nombre: 'Ministerio de Ejemplo' },
    estadisticas: {
      funcionarios_encontrados: 1,
      funcionarios_juridicos: 1,
      consultas_senescyt: 1,
      consultas_foro: 1,
      cambios_detectados: 0,
      alertas: 0,
      errores: 0,
      cache_hit: 0,
      cache_miss: 1,
    },
    funcionarios: [
      {
        nombre_completo: 'Ana Pérez',
        cedula: '1712345678',
        correo: 'ana.perez@ejemplo.gob.ec',
        telefono: '022345678',
        celular: '0991234567',
        correo_personal: 'ana.perez@personal.ec',
        cargo: 'Abogada',
        dependencia: 'Asesoría Jurídica',
        registro_foro: 'REG-001',
        estado_foro: 'activo',
        provincia_foro: 'Pichincha',
        fecha_consulta: '2026-06-02T10:00:00Z',
      },
    ],
    alertas: [],
    errores: [],
    duracion_total: '3.2s',
    generado_en: '2026-06-02T10:00:03Z',
    ...overrides,
  }
}

export function crearPerfilConsolidado(overrides: Partial<PerfilConsolidado> = {}): PerfilConsolidado {
  return {
    persona: {
      persona_master_id: 30,
      persona_id: 20,
      nombre_completo: 'Ana Pérez',
      cedula: '1712345678',
      correo_principal: 'ana.perez@ejemplo.gob.ec',
      telefono_principal: '022345678',
    },
    transparencia: { cargos: [] },
    senescyt: {},
    foro: { registros: [], historial: [], eventos: [], alertas: [], estadisticas: {} },
    generado_en: '2026-06-02T10:00:03Z',
    ...overrides,
  }
}

/**
 * `prioridad`/`estado` reales: `NivelCriticidad` ("critico"|"alto"|"medio"|"bajo")
 * y `EstadoAlerta` ("pendiente"|"enviada"|"descartada") -- confirmados en
 * `domain/value_objects/nivel_criticidad.py` y `domain/entities/alerta.py`.
 */
export function crearAlertaEntidad(overrides: Partial<AlertaEntidad> = {}): AlertaEntidad {
  return {
    id: 'alerta-1',
    entidad_id: 1,
    tipo: 'cambio_cargo',
    prioridad: 'medio',
    descripcion: 'Cambio detectado en el cargo.',
    detectado_en: '2026-06-01T00:00:00Z',
    estado: 'pendiente',
    persona_id: null,
    documento_id: null,
    ...overrides,
  }
}

export function crearPaginaAlertas(overrides: Partial<Pagina<AlertaEntidad>> = {}): Pagina<AlertaEntidad> {
  return {
    items: [crearAlertaEntidad()],
    page: 1,
    page_size: 50,
    total: 1,
    pages: 1,
    ...overrides,
  }
}

export function crearAlertaFuncionario(overrides: Partial<AlertaFuncionario> = {}): AlertaFuncionario {
  return {
    id: 'alerta-func-1',
    fuente: 'foro',
    tipo: 'registro_nuevo',
    prioridad: 'alto',
    descripcion: 'Nuevo registro en el Foro de Abogados.',
    detectado_en: '2026-06-01T00:00:00Z',
    estado: 'pendiente',
    ...overrides,
  }
}

/** `tipo_cambio`/`criticidad` reales casi siempre `null` (no persistidos junto a la versión). */
export function crearCambioEntidad(overrides: Partial<CambioEntidad> = {}): CambioEntidad {
  return {
    persona_id: 20,
    numero_version: 2,
    cargo: 'Directora Jurídica',
    dependencia: 'Asesoría Jurídica',
    fecha_inicio: '2026-01-15',
    fecha_fin: null,
    tipo_cambio: null,
    criticidad: null,
    ...overrides,
  }
}

export function crearPaginaCambios(overrides: Partial<Pagina<CambioEntidad>> = {}): Pagina<CambioEntidad> {
  return {
    items: [crearCambioEntidad()],
    page: 1,
    page_size: 20,
    total: 1,
    pages: 1,
    ...overrides,
  }
}

export function crearVersionHistorial(overrides: Partial<VersionHistorial> = {}): VersionHistorial {
  return {
    entidad_id: 1,
    numero_version: 1,
    cargo: 'Abogada',
    dependencia: 'Asesoría Jurídica',
    area: 'juridica',
    fecha_inicio: '2024-01-01',
    fecha_fin: null,
    correo: 'ana.perez@ejemplo.gob.ec',
    telefono: '022345678',
    ...overrides,
  }
}

export function crearPuntoTimeline(overrides: Partial<PuntoTimeline> = {}): PuntoTimeline {
  return {
    fecha_inicio: '2024-01-01',
    fecha_fin: null,
    origen: 'transparencia',
    descripcion: 'Ingresó como Abogada en Asesoría Jurídica.',
    referencia_id: 1,
    ...overrides,
  }
}

export function crearTimeline(overrides: Partial<Timeline> = {}): Timeline {
  return {
    persona_master_id: 30,
    puntos: [crearPuntoTimeline()],
    ...overrides,
  }
}

/** `titulos[]` real -- confirmado contra `TituloAcademicoDTO`. */
export function crearPerfilAcademico(overrides: Partial<PerfilAcademico> = {}): PerfilAcademico {
  return {
    persona_master: { persona_master_id: 30, persona_id: 20, nombre_completo: 'Ana Pérez', estado: 'activa' },
    identidad: { uuid: 'uuid-1', fingerprint_principal: 'fp-1', nivel_confianza: 0.95 },
    titulos: [
      {
        titulo: 'Abogada de los Tribunales de la República',
        nivel: 'tercer_nivel',
        institucion: 'Universidad Central del Ecuador',
        estado: 'vigente',
        fecha_registro: '2015-03-01',
      },
    ],
    historial: [],
    alertas: [],
    eventos: [],
    estadisticas: { cantidad_titulos_vigentes: 1, cantidad_cambios_historial: 0, cantidad_alertas: 0, cantidad_eventos: 0 },
    generado_en: '2026-06-02T10:00:03Z',
    ...overrides,
  }
}

export function crearEtapaJob(overrides: Partial<EtapaJob> = {}): EtapaJob {
  return {
    tipo_paso: 'transparencia',
    estado_paso: 'completado',
    iniciado_en: '2026-06-02T10:00:00Z',
    finalizado_en: '2026-06-02T10:00:02Z',
    duracion_segundos: 2,
    razon_omision: null,
    cantidad_registros: 5,
    error: null,
    ...overrides,
  }
}

export function crearJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    tipo: 'consulta_entidad',
    estado: 'completado',
    prioridad: 'normal',
    politica: 'consulta_rapida',
    parametros: { entidad_id: 1 },
    intentos: 1,
    max_intentos: 3,
    entidad_id: 1,
    creado_en: '2026-06-02T09:59:00Z',
    actualizado_en: '2026-06-02T10:00:03Z',
    iniciado_en: '2026-06-02T10:00:00Z',
    finalizado_en: '2026-06-02T10:00:03Z',
    ultimo_error: null,
    etapas: [crearEtapaJob()],
    ...overrides,
  }
}

/** Cuerpo de error EXACTO de `exception_handlers.py` (Módulo 10). */
export function crearErrorBody(codigo: string, mensaje: string, requestId: string | null = 'req-abc-123') {
  return { error: { codigo, mensaje, detalle: null, request_id: requestId } }
}
