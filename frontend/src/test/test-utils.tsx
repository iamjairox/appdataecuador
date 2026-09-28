import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router-dom'

/** QueryClient aislado por test -- sin reintentos ni cache compartida entre tests. */
export function crearQueryClientDePrueba(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })
}

/**
 * Monta un árbol de rutas real (react-router-dom `createMemoryRouter`) con
 * su propio `QueryClient` -- usado por los tests de páginas para poder
 * ejercitar navegación real (Sección 26 de FASE 2) sin levantar toda la
 * aplicación (Sidebar/Header no son necesarios para estos tests).
 */
export function renderConRouter(routes: RouteObject[], initialEntries: string[] = ['/']) {
  const queryClient = crearQueryClientDePrueba()
  const router = createMemoryRouter(routes, { initialEntries })
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { ...utils, queryClient, router }
}
