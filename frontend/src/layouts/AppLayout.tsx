import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

export function AppLayout() {
  const [sidebarAbierto, setSidebarAbierto] = useState(false)

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      <Sidebar abierto={sidebarAbierto} onCerrar={() => setSidebarAbierto(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header onAbrirMenu={() => setSidebarAbierto(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto flex max-w-6xl flex-col gap-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
