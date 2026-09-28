import { describe, expect, it } from 'vitest'
import { tonoPorEstadoAlerta, tonoPorPrioridad } from '../criticidad'

describe('tonoPorPrioridad', () => {
  it.each([
    ['critico', 'danger'],
    ['alto', 'warning'],
    ['medio', 'info'],
    ['bajo', 'neutral'],
  ])('mapea el valor real %s a %s', (prioridad, tono) => {
    expect(tonoPorPrioridad(prioridad)).toBe(tono)
  })

  it('nunca reconoce las formas femeninas inventadas ("critica"/"alta"/"media")', () => {
    expect(tonoPorPrioridad('critica')).toBe('neutral')
    expect(tonoPorPrioridad('alta')).toBe('neutral')
    expect(tonoPorPrioridad('media')).toBe('neutral')
  })
})

describe('tonoPorEstadoAlerta', () => {
  it.each([
    ['pendiente', 'warning'],
    ['enviada', 'success'],
    ['descartada', 'neutral'],
  ])('mapea el valor real %s a %s', (estado, tono) => {
    expect(tonoPorEstadoAlerta(estado)).toBe(tono)
  })
})
