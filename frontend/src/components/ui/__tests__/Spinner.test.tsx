import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Spinner } from '../Spinner'

/**
 * FASE 3.6 -- Bloque 2: `label=""` (usado dentro de `StatCard` para no
 * duplicar visualmente el label de la tarjeta) dejaba el `role="status"`
 * sin ningún texto que un lector de pantalla pudiera anunciar. Regresión:
 * debe seguir sin texto visible, pero ahora con `aria-label="Cargando"`.
 */
describe('Spinner', () => {
  it('con label="" no muestra texto visible pero sí anuncia el estado de carga (aria-label)', () => {
    render(<Spinner label="" />)
    const estado = screen.getByRole('status')

    expect(estado).toHaveAccessibleName('Cargando')
    expect(estado.querySelector('span')).toHaveTextContent('')
  })

  it('con un label real, el texto visible se anuncia por el contenido del `role="status"` (sin aria-label redundante)', () => {
    render(<Spinner label="Cargando entidades…" />)
    const estado = screen.getByRole('status')

    expect(estado).toHaveTextContent('Cargando entidades…')
    expect(estado).not.toHaveAttribute('aria-label')
  })

  it('sin label, usa el texto por defecto "Cargando…"', () => {
    render(<Spinner />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando…')
  })
})
