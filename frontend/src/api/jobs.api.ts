import { apiClient } from './client'
import type { Job } from '../types'

/** `GET /api/v1/jobs/{job_id}`. */
export function obtenerJob(jobId: string) {
  return apiClient.get<Job>(`/api/v1/jobs/${jobId}`).then((r) => r.data)
}
