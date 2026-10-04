import { useState, type FormEvent } from 'react'
import { LockKeyhole } from 'lucide-react'
import { apiClient } from '../api/client'
import { Alert, Button, Card, CardBody, CardHeader, Input } from '../components/ui'

interface LoginPageProps {
  configurado: boolean
  onIngreso: () => void
}

export function LoginPage({ configurado, onIngreso }: LoginPageProps) {
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function ingresar(event: FormEvent) {
    event.preventDefault()
    setCargando(true)
    setError(null)
    try {
      await apiClient.post('/api/v1/auth/ingresar', { usuario, clave })
      onIngreso()
    } catch {
      setError('Usuario o clave incorrectos. Verifica los datos e inténtalo nuevamente.')
    } finally {
      setCargando(false)
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-5">
    <Card className="w-full max-w-md">
      <CardHeader><div className="flex items-center gap-2"><LockKeyhole className="size-5 text-slate-700" /><h1 className="text-xl font-semibold text-slate-900">Acceso a DataOK</h1></div><p className="mt-2 text-sm text-slate-500">Ingresa con las credenciales autorizadas para continuar.</p></CardHeader>
      <CardBody>
        {!configurado ? <Alert tone="warning" title="Acceso pendiente de configuración">El administrador aún debe configurar la cuenta segura en el servidor.</Alert> : <form className="space-y-4" onSubmit={(event) => void ingresar(event)}><Input label="Usuario" name="usuario" autoComplete="username" value={usuario} onChange={(event) => setUsuario(event.target.value)} required /><Input label="Clave" name="clave" type="password" autoComplete="current-password" value={clave} onChange={(event) => setClave(event.target.value)} required />{error && <Alert tone="danger">{error}</Alert>}<Button type="submit" className="w-full" loading={cargando} disabled={!usuario || !clave}>Ingresar</Button></form>}
      </CardBody>
    </Card>
  </main>
}
