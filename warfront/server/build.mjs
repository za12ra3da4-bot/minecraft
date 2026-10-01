// Bundles the server (including the shared workspace package) into dist/index.js.
import { build } from 'esbuild';

await build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node20',
  outfile: 'dist/index.js',
  sourcemap: true,
  // Real npm dependencies stay external, the TypeScript workspace package is bundled.
  external: ['express', 'socket.io', 'dotenv'],
  banner: { js: "import { createRequire } from 'module'; const require = createRequire(import.meta.url);" },
});
console.log('server built -> dist/index.js');
