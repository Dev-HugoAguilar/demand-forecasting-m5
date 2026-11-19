import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Dos artefactos del mismo proyecto con una sola configuración:
 *
 * - `npm run dev` sirve `index.html` + `src/main.tsx`: un host de desarrollo real
 *   que monta la aplicación en el navegador. Requiere la API del portafolio en
 *   `http://127.0.0.1:8010/api/v1/comercial/m5` (o `window.PORTFOLIO_COMERCIAL_API`).
 * - `npm run build` compila la librería ESM `dist/app.js` (+ `dist/app.css`) con
 *   `mount`/`unmount` para que el portafolio la cargue con `import()` dinámico.
 *
 * Todo se escribe dentro de `app/`: el artefacto queda en `app/dist` y nada se
 * publica fuera del repositorio. `src/ui/Segmentado.tsx` es una copia local del
 * selector segmentado, así que el bundle no sale de esta carpeta.
 */
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // En modo librería Vite no reemplaza NODE_ENV; sin esto se empaquetaría React
  // en su build de desarrollo. Solo aplica al artefacto: el host de desarrollo
  // conserva las comprobaciones de React.
  ...(command === 'build'
    ? { define: { 'process.env.NODE_ENV': JSON.stringify('production') } }
    : {}),
  resolve: {
    dedupe: ['react', 'react-dom', 'react/jsx-runtime'],
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2020',
    minify: 'esbuild',
    cssCodeSplit: false,
    assetsInlineLimit: 0,
    sourcemap: false,
    lib: {
      entry: 'src/mount.tsx',
      formats: ['es'],
      fileName: () => 'app.js',
    },
    rollupOptions: {
      output: {
        assetFileNames: (info) =>
          (info.names?.[0] ?? info.name ?? '').endsWith('.css') ? 'app.css' : 'app.[ext]',
      },
    },
  },
}));
