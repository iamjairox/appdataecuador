/**
 * Dispara la descarga de un `Blob` ya recibido del backend (nunca vuelve
 * a pedirlo). Usa un `<a download>` temporal -- necesario porque una
 * navegación directa (`<a href="...">` a la URL de la API) no puede
 * llevar `X-API-Key` (ver Sección 22, FASE 1). Libera el Object URL
 * después de disparar la descarga para no dejar memory leaks.
 */
export function descargarBlob(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  document.body.appendChild(enlace)
  enlace.click()
  document.body.removeChild(enlace)
  // Pequeño margen antes de revocar: algunos navegadores inician la
  // descarga de forma asíncrona tras el `click()`.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
