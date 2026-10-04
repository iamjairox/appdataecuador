import { useEffect, useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { apiClient } from './api/client'
import { LoginPage } from './pages/LoginPage'
import { queryClient } from './lib/query-client'
import { router } from './routes'

export function App() {
  const [errorAcceso, setErrorAcceso] = useState(false)
  const [estadoAcceso, setEstadoAcceso] = useState<{ requerido: boolean; autenticado: boolean; configurado?: boolean } | null>(null)

  async function comprobarAcceso() {
    setErrorAcceso(false)
    try {
      const { data } = await apiClient.get('/api/v1/auth/estado')
      setEstadoAcceso(data)
    } catch {
      setErrorAcceso(true)
    }
  }

  useEffect(() => {
    void comprobarAcceso()
    const alCerrarSesion = () => setEstadoAcceso({ requerido: true, autenticado: false, configurado: true })
    window.addEventListener('dataok:sesion-cerrada', alCerrarSesion)
    return () => window.removeEventListener('dataok:sesion-cerrada', alCerrarSesion)
  }, [])

  if (errorAcceso) return <main className="grid min-h-screen place-items-center text-sm text-slate-600"><div className="space-y-4 text-center"><p>No fue posible conectar con el servidor. Puede estar iniciándose.</p><button type="button" className="rounded-md bg-slate-900 px-4 py-2 text-white" onClick={() => void comprobarAcceso()}>Intentar nuevamente</button></div></main>
  if (!estadoAcceso) return <main className="grid min-h-screen place-items-center text-sm text-slate-600">Iniciando DataOK…</main>
  if (estadoAcceso.requerido && !estadoAcceso.autenticado) return <LoginPage configurado={estadoAcceso.configurado !== false} onIngreso={() => void comprobarAcceso()} />

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
