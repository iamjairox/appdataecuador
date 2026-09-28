import { setupServer } from 'msw/node'

/** Servidor MSW compartido -- cada test agrega sus propios handlers con `server.use(...)`. */
export const server = setupServer()
