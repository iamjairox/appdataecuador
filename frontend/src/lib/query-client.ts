import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '../types/error'

/**
 * El backend YA es la fuente de verdad de cache (Módulos 4/5/7/8/9) --
 * este QueryClient solo evita refetches redundantes en el cliente, nunca
 * intenta ser un segundo sistema de cache paralelo.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        // Errores de negocio (404/401/422/...) no se reintentan solos;
        // solo problemas de red/servidor ameritan un reintento.
        if (error instanceof ApiError && error.status !== null && error.status < 500) {
          return false
        }
        return failureCount < 2
      },
    },
    mutations: {
      retry: false,
    },
  },
})
