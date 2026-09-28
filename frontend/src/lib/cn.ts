/** Concatenador mínimo de clases (evita añadir `clsx`/`tailwind-merge` solo para esto). */
export function cn(...clases: Array<string | false | null | undefined>): string {
  return clases.filter(Boolean).join(' ')
}
