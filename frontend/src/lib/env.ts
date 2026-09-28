/**
 * Punto único de lectura de variables de entorno (Regla 9-adjacent:
 * nunca se lee `import.meta.env` fuera de este archivo). `VITE_API_KEY`
 * es opcional -- el backend la exige solo si `API_KEY` está configurada
 * en el servidor (Módulo 10, `verificar_api_key`); nunca se imprime ni
 * se expone en la UI.
 */

const apiUrl = import.meta.env.VITE_API_URL
if (!apiUrl) {
  throw new Error(
    'VITE_API_URL no está configurada. Copia .env.example a .env y define la URL del backend.',
  )
}

export const env = {
  apiUrl,
  apiKey: import.meta.env.VITE_API_KEY || undefined,
} as const
