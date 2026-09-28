/**
 * Forma real y literal de `PaginaSchema` (Módulo 10, backend):
 * `{ items, page, page_size, total, pages }`.
 *
 * Confirmado en el OpenAPI en vivo para: /entidades,
 * /entidades/{id}/funcionarios, /entidades/{id}/cambios,
 * /entidades/{id}/alertas.
 *
 * NO se usa para /funcionarios/{id}/historial, /alertas ni /timeline:
 * esos endpoints devuelven un arreglo u objeto directo, sin paginar.
 */
export interface Pagina<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  pages: number
}
