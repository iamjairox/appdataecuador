/**
 * Extrae `filename` de un header `Content-Disposition` real
 * (`attachment; filename=funcionarios_entidad_1.csv`, Módulo 10,
 * `routes/entidades.py::exportar_funcionarios`). Soporta tanto la forma
 * sin comillas que envía el backend hoy como `filename="..."` por si
 * cambiara. Devuelve `null` si el header no vino o no trae `filename`
 * -- el llamador decide el fallback, nunca se inventa aquí.
 */
export function extraerNombreArchivo(contentDisposition: string | undefined | null): string | null {
  if (!contentDisposition) return null
  const coincidencia = /filename\*?=(?:UTF-8''|")?([^";]+)"?/i.exec(contentDisposition)
  return coincidencia?.[1] ? decodeURIComponent(coincidencia[1]) : null
}
