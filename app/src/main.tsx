/**
 * Arnés de desarrollo (`npm run dev`). No se empaqueta: la librería que consume
 * el portafolio sigue siendo `src/mount.tsx`.
 *
 * Monta la aplicación completa en `#raiz` y resuelve la base de la API igual que
 * el resto del portafolio: `window.PORTFOLIO_COMERCIAL_API` o, en su defecto,
 * `http://127.0.0.1:8010/api/v1/comercial/m5`.
 */

import { createRoot } from 'react-dom/client';

import { AplicacionComercial } from './App';
import { baseApi } from './api';
import './estilos.css';

const host = document.getElementById('raiz');
if (host) {
  createRoot(host).render(<AplicacionComercial apiBase={baseApi()} />);
}
