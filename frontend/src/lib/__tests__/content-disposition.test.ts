import { describe, expect, it } from 'vitest'
import { extraerNombreArchivo } from '../content-disposition'

describe('extraerNombreArchivo', () => {
  it('extrae el nombre real que envía el backend (sin comillas)', () => {
    expect(extraerNombreArchivo('attachment; filename=funcionarios_entidad_1.csv')).toBe(
      'funcionarios_entidad_1.csv',
    )
  })

  it('soporta la forma con comillas por si el backend cambiara', () => {
    expect(extraerNombreArchivo('attachment; filename="funcionarios_entidad_1.json"')).toBe(
      'funcionarios_entidad_1.json',
    )
  })

  it('devuelve null cuando no hay header (nunca inventa un nombre aquí)', () => {
    expect(extraerNombreArchivo(undefined)).toBeNull()
    expect(extraerNombreArchivo(null)).toBeNull()
  })

  it('devuelve null cuando el header no trae filename', () => {
    expect(extraerNombreArchivo('inline')).toBeNull()
  })
})
