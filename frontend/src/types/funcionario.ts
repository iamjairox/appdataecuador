/**
 * `FuncionarioResponseSchema` real (Módulo 10) -- listado desde
 * `GET /entidades/{id}/funcionarios`, SOLO información ya persistida
 * (Módulos 1/4). Deliberadamente NO tiene `celular`, `registro_foro`,
 * `estado_foro` ni `titulos` -- esos solo existen en el resultado de
 * consulta consolidada (`FuncionarioConsolidado`) o en el perfil
 * (`PerfilConsolidado`). Nunca agregar esos campos aquí.
 */
export interface Funcionario {
  funcionario_id: number
  persona_id: number
  persona_master_id: number | null
  nombre_completo: string
  nombres: string
  apellidos: string
  cedula: string | null
  correo: string | null
  telefono: string | null
  /** Columna "Extensión telefónica" del numeral 2 DPE. */
  extension_telefonica?: string | null
  cargo: string
  dependencia: string
  area: string
  vigente: boolean
  fecha_inicio: string | null
  fecha_fin: string | null
}

/**
 * `GET /entidades/{id}/funcionarios/exportar` -- únicos formatos reales
 * (`Query(default="csv", pattern="^(csv|json)$")`, Módulo 10). Exporta
 * SIEMPRE `solo_vigentes=True` (el backend construye
 * `FiltrosFuncionarioListadoDTO()` sin parámetros) -- ignora cualquier
 * filtro aplicado en la tabla del frontend.
 */
export type FormatoExportacion = 'csv' | 'json'

/**
 * `AreaRelevante` real (Módulo 4/10, dominio). `general` identifica los
 * contactos institucionales sin clasificación jurídica o financiera.
 */
export type AreaFuncionario = 'juridica' | 'financiera' | 'general'

/**
 * Filtros REALES de `GET /entidades/{id}/funcionarios`
 * (`routes/entidades.py::listar_funcionarios_de_entidad`, confirmados
 * leyendo `SqlAlchemyFuncionarioConsultaPaginadaRepository._condiciones`):
 *
 * - `nombre`/`apellido`/`cargo`/`dependencia`/`correo`: `ILIKE %valor%`
 *   (substring, sin distinguir mayúsculas) sobre columnas DISTINTAS --
 *   `nombre` solo compara contra `nombres`, nunca contra apellidos.
 * - `cedula`/`telefono`: coincidencia EXACTA.
 * - `area`: coincidencia EXACTA por área.
 * - `solo_vigentes`: `true` (default) filtra `fecha_fin IS NULL`; `false`
 *   quita ese filtro (devuelve vigentes Y no vigentes) -- el backend NO
 *   tiene un modo "solo no vigentes", no inventar esa tercera opción.
 * - No existe ordenamiento configurable (siempre `ORDER BY id ASC`).
 */
export interface FiltrosFuncionario {
  nombre?: string
  apellido?: string
  cedula?: string
  cargo?: string
  dependencia?: string
  area?: AreaFuncionario
  correo?: string
  telefono?: string
  solo_vigentes?: boolean
  page?: number
  page_size?: number
}

/**
 * Fila del arreglo `funcionarios` dentro de `ConsultaEntidadResponseSchema`
 * (forma de `FuncionarioConsolidadoDTO`, Módulo 9/10) -- objeto libre en
 * el backend (`dict[str, Any]`); estos SON los campos que realmente
 * produce ese contrato (Submódulo 8.11), a diferencia del listado plano.
 */
export interface FuncionarioConsolidado {
  nombre_completo: string
  cedula: string | null
  correo: string | null
  telefono: string | null
  /** Columna "Extensión telefónica" del numeral 2 DPE. */
  extension_telefonica?: string | null
  celular: string | null
  correo_personal: string | null
  cargo: string | null
  dependencia: string | null
  registro_foro: string | null
  estado_foro: string | null
  provincia_foro: string | null
  fecha_consulta: string | null
  estado_consulta_externa?: string | null
}

/** Funcionario cuyo Foro ya fue consultado y quedó persistido. */
export interface FuncionarioConsultado extends Funcionario {
  registro_foro: string | null
  estado_foro: string | null
  provincia_foro: string | null
  correo_personal: string | null
  celular_personal: string | null
  fecha_consulta: string | null
  estado_consulta_externa?: string | null
}
