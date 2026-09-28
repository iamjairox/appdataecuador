import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface HealthRespuesta {
  status: string
  service: string
  version: string
  timestamp: string
}

/** `GET /health` -- estado de vida del proceso backend (no toca BD). Se usa para el indicador del Header. */
export function useApiHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get<HealthRespuesta>('/health').then((r) => r.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
  })
}
