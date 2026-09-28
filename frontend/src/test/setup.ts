import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  cleanup()
})
afterAll(() => server.close())

// jsdom no implementa el Clipboard API -- se mockea para probar `CopyButton`
// (Sección 22/31 de FASE 2) sin depender del portapapeles real del SO.
// Se exporta la referencia directa a la mock function (en vez de leerla desde
// `navigator.clipboard.writeText` en cada test) para evitar el problema de
// "unbound method" de un método extraído de su objeto.
export const clipboardWriteTextMock = vi.fn().mockResolvedValue(undefined)
Object.assign(navigator, { clipboard: { writeText: clipboardWriteTextMock } })

// jsdom no implementa `URL.createObjectURL`/`revokeObjectURL` y lanza
// "Not implemented: navigation" al hacer `.click()` en un `<a>` con
// `href` real -- se mockean para poder probar `descargarBlob` (FASE 3.1)
// sin depender de un navegador real.
export const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url')
export const revokeObjectURLMock = vi.fn()
Object.assign(URL, { createObjectURL: createObjectURLMock, revokeObjectURL: revokeObjectURLMock })

export const anchorClickMock = vi.fn()
HTMLAnchorElement.prototype.click = anchorClickMock
