import { defineConfig } from 'vite'
import solidPlugin from 'vite-plugin-solid'

export default defineConfig({
  plugins: [solidPlugin()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
    },
    // Rewrite /m/* to / so the SPA handles routing in dev.
    // Vite won't fall back to index.html for paths with extensions (e.g. /m/abc.png).
    configureServer(server) {
      server.middlewares.use('/m', (_req, _res, next) => {
        _req.url = '/'
        next()
      })
    },
  },
  build: {
    outDir: 'dist',
    target: 'esnext',
  },
})
