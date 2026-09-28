import { useMutation, useQuery } from '@tanstack/react-query'
import {
  obtenerAcademicoFuncionario,
  obtenerAlertasFuncionario,
  obtenerForoFuncionario,
  obtenerFuncionario,
  obtenerHistorialFuncionario,
  obtenerTimelineFuncionario,
  validarAbogado,
} from '../api/funcionarios.api'

export const funcionarioKeys = {
  todos: ['funcionarios'] as const,
  perfil: (id: number) => [...funcionarioKeys.todos, id, 'perfil'] as const,
  historial: (id: number) => [...funcionarioKeys.todos, id, 'historial'] as const,
  academico: (id: number) => [...funcionarioKeys.todos, id, 'academico'] as const,
  foro: (id: number) => [...funcionarioKeys.todos, id, 'foro'] as const,
  alertas: (id: number) => [...funcionarioKeys.todos, id, 'alertas'] as const,
  timeline: (id: number) => [...funcionarioKeys.todos, id, 'timeline'] as const,
}

export function useValidarAbogado() {
  return useMutation({
    mutationFn: (personaMasterId: number) => validarAbogado(personaMasterId),
  })
}

export function useFuncionarioPerfil(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.perfil(personaMasterId ?? -1),
    queryFn: () => obtenerFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}

export function useFuncionarioHistorial(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.historial(personaMasterId ?? -1),
    queryFn: () => obtenerHistorialFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}

export function useFuncionarioAcademico(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.academico(personaMasterId ?? -1),
    queryFn: () => obtenerAcademicoFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}

export function useFuncionarioForo(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.foro(personaMasterId ?? -1),
    queryFn: () => obtenerForoFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}

export function useFuncionarioAlertas(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.alertas(personaMasterId ?? -1),
    queryFn: () => obtenerAlertasFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}

export function useFuncionarioTimeline(personaMasterId: number | undefined) {
  return useQuery({
    queryKey: funcionarioKeys.timeline(personaMasterId ?? -1),
    queryFn: () => obtenerTimelineFuncionario(personaMasterId as number),
    enabled: personaMasterId !== undefined,
  })
}
