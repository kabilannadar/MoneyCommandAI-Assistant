import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load .env so we can read BACKEND_URL at config time.
  // BACKEND_URL is a *build-time / dev-server-only* variable (no VITE_ prefix),
  // so it is never exposed to the browser bundle.
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.BACKEND_URL || 'http://127.0.0.1:8002'

  const proxyConfig = {
    target: backendTarget,
    changeOrigin: true,
    configure: (proxy) => {
      proxy.on('error', (err) => {
        if (err.code === 'ECONNRESET' || err.code === 'ECONNABORTED') {
          return;
        }
        if (err.code === 'ECONNREFUSED') {
          console.warn(`[Vite Proxy] Backend offline at ${backendTarget}`);
          return;
        }
        console.error('[Vite Proxy] Error:', err);
      });
    }
  }

  const wsProxyConfig = {
    ...proxyConfig,
    ws: true,
  }

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/chat': proxyConfig,
        '/api': proxyConfig,
        '/auth': proxyConfig,
        '/agent/login': proxyConfig,
        '/agent/register': proxyConfig,
        '/agent/logout': proxyConfig,
        '/agent/users': proxyConfig,
        '/admin/login': proxyConfig,
        '/admin/logout': proxyConfig,
        '/admin/me': proxyConfig,
        '/admin/agents': proxyConfig,
        '/admin/config': proxyConfig,
        '/admin/users': proxyConfig,
        '/socket.io': wsProxyConfig,
      },
    },
  }
})
