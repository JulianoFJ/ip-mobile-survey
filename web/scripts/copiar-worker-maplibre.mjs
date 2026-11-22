// O MapLibre 6 carrega o worker por uma URL montada em tempo de execução, que o webpack do
// Next não detecta: sem isto o mapa fica em branco (o estilo nunca é processado). Copia o
// worker e o módulo compartilhado que ele importa para public/maplibre/, na mesma versão
// instalada. Roda antes do dev e do build (ver package.json).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const dist = join(dirname(require.resolve("maplibre-gl/package.json")), "dist");
const destino = join(process.cwd(), "public", "maplibre");
mkdirSync(destino, { recursive: true });
for (const f of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) copyFileSync(join(dist, f), join(destino, f));
console.log(`worker do MapLibre copiado para ${destino}`);
