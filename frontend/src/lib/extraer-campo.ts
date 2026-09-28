/**
 * Extractores seguros para los `dict[str, Any]` libres que el backend
 * (Módulo 10) devuelve tal cual en varios contratos (`estadisticas`,
 * `persona`, `job`, alertas de consulta, ...). Nunca inventan un valor:
 * si la clave no existe o no coincide con el tipo esperado, devuelven
 * `null` para que la UI muestre "—" en lugar de un dato falso.
 */
export function extraerTexto(obj: Record<string, unknown>, clave: string): string | null {
  const valor = obj[clave]
  return typeof valor === 'string' ? valor : null
}

export function extraerNumero(obj: Record<string, unknown>, clave: string): number | null {
  const valor = obj[clave]
  return typeof valor === 'number' ? valor : null
}
