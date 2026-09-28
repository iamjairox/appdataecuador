import { useQuery } from '@tanstack/react-query'
import { obtenerJob } from '../api/jobs.api'

export const jobKeys = {
  todos: ['jobs'] as const,
  detalle: (id: string) => [...jobKeys.todos, id] as const,
}

export function useJob(jobId: string | undefined) {
  return useQuery({
    queryKey: jobKeys.detalle(jobId ?? ''),
    queryFn: () => obtenerJob(jobId as string),
    enabled: jobId !== undefined,
  })
}
