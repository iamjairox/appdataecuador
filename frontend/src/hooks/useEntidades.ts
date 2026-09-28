import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  actualizarEntidad,
  actualizarMasivo,
  consultarEntidad,
  consultarMasivo,
  exportarFuncionarios,
  listarEntidades,
  obtenerAlertasEntidad,
  obtenerCambiosEntidad,
  obtenerEntidad,
  listarFuncionarios,
} from '../api/entidades.api'
import { descargarBlob } from '../lib/descargar-archivo'
import type {
  FiltrosCambio,
  FiltrosEntidad,
  FiltrosFuncionario,
  FormatoExportacion,
  PoliticaConsulta,
} from '../types'

/** Claves de query centralizadas -- evita strings mágicos repetidos y facilita invalidar. */
export const entidadesKeys = {
  todas: ['entidades'] as const,
  lista: (filtros: FiltrosEntidad) => [...entidadesKeys.todas, 'lista', filtros] as const,
  detalle: (id: number) => [...entidadesKeys.todas, 'detalle', id] as const,
  funcionarios: (id: number, filtros: FiltrosFuncionario) =>
    [...entidadesKeys.todas, id, 'funcionarios', filtros] as const,
  cambios: (id: number, filtros: FiltrosCambio) =>
    [...entidadesKeys.todas, id, 'cambios', filtros] as const,
  alertas: (id: number, page: number) => [...entidadesKeys.todas, id, 'alertas', page] as const,
}

/**
 * `placeholderData: keepPreviousData` (FASE 3.6, mismo criterio ya
 * aplicado en `useFuncionariosDeEntidad` desde FASE 3.2) -- esta lista SÍ
 * pagina en la UI (`EntidadesListPage`), así que sin esto cada cambio de
 * página vaciaba la tabla y mostraba un spinner de pantalla completa.
 */
export function useEntidades(filtros: FiltrosEntidad = {}) {
  return useQuery({
    queryKey: entidadesKeys.lista(filtros),
    queryFn: () => listarEntidades(filtros),
    placeholderData: keepPreviousData,
  })
}

export function useEntidad(entidadId: number | undefined) {
  return useQuery({
    queryKey: entidadesKeys.detalle(entidadId ?? -1),
    queryFn: () => obtenerEntidad(entidadId as number),
    enabled: entidadId !== undefined,
  })
}

/**
 * `placeholderData: keepPreviousData` -- al cambiar de página/filtros se
 * conserva la tabla anterior visible (con `isPlaceholderData: true`)
 * mientras llega la respuesta nueva, en vez de vaciar la tabla y mostrar
 * un spinner de pantalla completa en cada cambio (evita parpadeos).
 *
 * A diferencia de `useCambiosEntidad`/`useAlertasEntidad` (FASE 3.7), aquí
 * NO hace falta restringir el placeholder a la misma entidad: su único
 * consumidor (`FuncionariosDeEntidadSection`) vive dentro de
 * `EntidadDetallePage`, que retorna un `<Spinner>` mientras `useEntidad`
 * está pendiente -- eso desmonta esta sección en cada cambio de
 * `entidadId` "en frío" (sin caché previa), así que el observer nunca
 * conserva un `previousData` de OTRA entidad para filtrar.
 */
export function useFuncionariosDeEntidad(entidadId: number | undefined, filtros: FiltrosFuncionario = {}) {
  return useQuery({
    queryKey: entidadesKeys.funcionarios(entidadId ?? -1, filtros),
    queryFn: () => listarFuncionarios(entidadId as number, filtros),
    enabled: entidadId !== undefined,
    placeholderData: keepPreviousData,
  })
}

/**
 * `keepPreviousData` "a secas" (como en `useEntidades`) reutilizaría los
 * datos de OTRA entidad como placeholder si `entidadId` cambia mientras el
 * componente sigue montado (`EntidadCambiosPage` no desmonta al cambiar de
 * entidad, a diferencia de `EntidadDetallePage`/`FuncionariosDeEntidadSection`
 * -- ver auditoría FASE 3.7, Bloque React Query). Se restringe el
 * placeholder a "misma entidad, solo cambió la página/filtro": el índice
 * `[1]` del query key siempre es el `entidadId` (ver `entidadesKeys.cambios`).
 */
export function useCambiosEntidad(entidadId: number | undefined, filtros: FiltrosCambio = {}) {
  return useQuery({
    queryKey: entidadesKeys.cambios(entidadId ?? -1, filtros),
    queryFn: () => obtenerCambiosEntidad(entidadId as number, filtros),
    enabled: entidadId !== undefined,
    placeholderData: (data, query) => (query?.queryKey[1] === entidadId ? data : undefined),
  })
}

/** Mismo criterio que `useCambiosEntidad` -- placeholder restringido a la misma entidad (ver comentario arriba). */
export function useAlertasEntidad(entidadId: number | undefined, page = 1) {
  return useQuery({
    queryKey: entidadesKeys.alertas(entidadId ?? -1, page),
    queryFn: () => obtenerAlertasEntidad(entidadId as number, page),
    enabled: entidadId !== undefined,
    placeholderData: (data, query) => (query?.queryKey[1] === entidadId ? data : undefined),
  })
}

/**
 * `GET /entidades/{id}/consulta` es SÍNCRONO -- la mutación permanece
 * "pending" hasta que el backend termina de orquestar. No hay progreso
 * intermedio real que reportar (ver Regla crítica de progreso).
 */
export function useConsultarEntidadMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ entidadId, politica }: { entidadId: number; politica?: PoliticaConsulta }) =>
      consultarEntidad(entidadId, politica),
    onSuccess: (_datos, variables) => {
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.detalle(variables.entidadId) })
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
    },
  })
}

/**
 * `GET /entidades/{id}/funcionarios/exportar` -- descarga el archivo y
 * dispara el `download` del navegador. No hay progreso real que reportar
 * más allá de pendiente/éxito/error (el backend hace streaming sin
 * `Content-Length`, así que tampoco hay un porcentaje real que mostrar).
 */
export function useExportarFuncionariosMutation() {
  return useMutation({
    mutationFn: ({ entidadId, formato }: { entidadId: number; formato: FormatoExportacion }) =>
      exportarFuncionarios(entidadId, formato),
    onSuccess: ({ blob, nombreArchivo }) => {
      descargarBlob(blob, nombreArchivo)
    },
  })
}

export function useActualizarEntidadMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entidadId: number) => actualizarEntidad(entidadId),
    onSuccess: (_datos, entidadId) => {
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.detalle(entidadId) })
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
    },
  })
}

/**
 * `POST /entidades/consulta-masiva` -- SIN selección de entidades posible
 * (el backend siempre opera sobre TODAS las activas, ver
 * `api/entidades.api.ts::consultarMasivo`). Síncrona: puede tardar
 * bastante más que una consulta individual.
 */
export function useConsultarMasivoMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (politica?: PoliticaConsulta) => consultarMasivo(politica),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
    },
  })
}

/** `POST /entidades/actualizar-masivo` -- SIN parámetros (ni política, ni selección de entidades). */
export function useActualizarMasivoMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => actualizarMasivo(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: entidadesKeys.todas })
    },
  })
}
