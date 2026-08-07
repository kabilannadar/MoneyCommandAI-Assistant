import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { Analytics } from '@vercel/analytics/react'

if (window.self !== window.top) {
  document.documentElement.classList.add('in-iframe');
}

const path = window.location.pathname;

if (path.startsWith('/admin')) {
  // Mount admin panel into its own root — fully isolated from the
  // global #root flex/width constraints defined in index.css
  const AdminPanel = lazy(() => import('./pages/AdminPanel/AdminPanel.jsx'));
  const adminEl = document.getElementById('admin-root');
  if (adminEl) {
    adminEl.style.display = 'block'; // make it visible
    createRoot(adminEl).render(
      <StrictMode>
        <Suspense fallback={<div style={{ padding: '2rem', fontFamily: 'Inter,sans-serif' }}>Loading...</div>}>
          <AdminPanel />
          <Analytics />
        </Suspense>
      </StrictMode>
    );
  }
} else {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
      <Analytics />
    </StrictMode>,
  );
}
