import { afterEach, describe, expect, it, vi } from 'vitest'
import { createObjectURLMock, revokeObjectURLMock, anchorClickMock } from '../../test/setup'
import { descargarBlob } from '../descargar-archivo'

describe('descargarBlob', () => {
  afterEach(() => {
    createObjectURLMock.mockClear()
    revokeObjectURLMock.mockClear()
    anchorClickMock.mockClear()
  })

  it('crea un Object URL, dispara la descarga con el nombre de archivo correcto y no deja el <a> en el DOM', () => {
    const blob = new Blob(['a,b\n1,2'], { type: 'text/csv' })
    // `appendChild` real (sin mockear la implementación) -- solo se
    // observa qué nodo se agregó, para que el posterior `removeChild`
    // dentro de `descargarBlob` siga funcionando normalmente.
    const appendSpy = vi.spyOn(document.body, 'appendChild')

    descargarBlob(blob, 'funcionarios_entidad_1.csv')

    const anchorCapturado = appendSpy.mock.calls[0]?.[0] as HTMLAnchorElement
    expect(createObjectURLMock).toHaveBeenCalledWith(blob)
    expect(anchorCapturado.download).toBe('funcionarios_entidad_1.csv')
    expect(anchorCapturado.href).toContain('blob:mock-url')
    expect(anchorClickMock).toHaveBeenCalledTimes(1)
    expect(document.body.contains(anchorCapturado)).toBe(false)

    appendSpy.mockRestore()
  })

  it('libera el Object URL (sin memory leak)', async () => {
    vi.useFakeTimers()
    const blob = new Blob(['[]'], { type: 'application/json' })

    descargarBlob(blob, 'funcionarios_entidad_1.json')
    expect(revokeObjectURLMock).not.toHaveBeenCalled()

    await vi.runAllTimersAsync()
    expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:mock-url')

    vi.useRealTimers()
  })
})
