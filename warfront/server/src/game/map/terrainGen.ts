import { CellFlag, SEA_LEVEL_BYTE, Terrain, clamp } from '@warfront/shared';
import { fbm } from './noise';
import { N4, quantile, type MapContext } from './MapContext';

function smooth(t: number): number {
  return t * t * (3 - 2 * t);
}

function smoothstep(a: number, b: number, x: number): number {
  return smooth(clamp((x - a) / (b - a), 0, 1));
}

/** Elevation, land/sea, hills, forests and coast flags. */
export function generateTerrain(ctx: MapContext): void {
  const { def, cols, rows, cs } = ctx;
  const vcols = cols + 1;
  const seed = def.seed;

  let rMin = Infinity;
  let rMax = -Infinity;
  for (let j = 0; j <= rows; j++) {
    for (let i = 0; i <= cols; i++) {
      const x = i * cs;
      const y = j * cs;
      const nx = x / def.width;
      const ny = y / def.height;
      let shape = def.baseLand;
      for (const s of def.landShapes) {
        const dx = (nx - s.x) / s.rx;
        const dy = (ny - s.y) / s.ry;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < 1) shape += s.weight * smooth(1 - d);
      }
      const edge = Math.max(Math.abs(2 * nx - 1), Math.abs(2 * ny - 1));
      const n = fbm(x / def.noiseScale, y / def.noiseScale, seed, 5);
      const e = shape + n * 0.42 - def.edgeFalloff * smoothstep(0.76, 1.0, edge) * 1.3;
      const v = j * vcols + i;
      ctx.elev[v] = e;
      const r = fbm(x / (def.noiseScale * 0.42), y / (def.noiseScale * 0.42), seed + 77, 4);
      ctx.relief[v] = r;
      if (r < rMin) rMin = r;
      if (r > rMax) rMax = r;
    }
  }
  const rSpan = rMax - rMin || 1;
  for (let v = 0; v < ctx.relief.length; v++) ctx.relief[v] = (ctx.relief[v] - rMin) / rSpan;

  // Cells: land / water.
  const cellE = new Float32Array(cols * rows);
  const cellR = new Float32Array(cols * rows);
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const v = y * vcols + x;
      const e = (ctx.elev[v] + ctx.elev[v + 1] + ctx.elev[v + vcols] + ctx.elev[v + vcols + 1]) / 4;
      const r = (ctx.relief[v] + ctx.relief[v + 1] + ctx.relief[v + vcols] + ctx.relief[v + vcols + 1]) / 4;
      const c = y * cols + x;
      cellE[c] = e;
      cellR[c] = r;
      ctx.terrain[c] = e > 0 ? Terrain.PLAINS : Terrain.WATER;
    }
  }

  keepLargestLandmass(ctx);

  // Hills and forests by quantile so every map gets a predictable mix.
  const landRelief: number[] = [];
  const forestNoise = new Float32Array(cols * rows);
  const landForest: number[] = [];
  for (let c = 0; c < cols * rows; c++) {
    if (ctx.terrain[c] === Terrain.WATER) continue;
    const x = (c % cols) * cs;
    const y = Math.floor(c / cols) * cs;
    landRelief.push(cellR[c]);
    const f = fbm(x / (def.noiseScale * 0.3), y / (def.noiseScale * 0.3), seed + 311, 4);
    forestNoise[c] = f;
  }
  const hillCut = quantile(landRelief, 1 - def.hillShare);
  for (let c = 0; c < cols * rows; c++) {
    if (ctx.terrain[c] === Terrain.WATER) continue;
    if (cellR[c] >= hillCut) ctx.terrain[c] = Terrain.HILLS;
    else landForest.push(forestNoise[c]);
  }
  const forestCut = quantile(landForest, 1 - def.forestShare / Math.max(0.05, 1 - def.hillShare));
  for (let c = 0; c < cols * rows; c++) {
    if (ctx.terrain[c] === Terrain.PLAINS && forestNoise[c] >= forestCut) ctx.terrain[c] = Terrain.FOREST;
  }

  // Coast flags.
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const c = y * cols + x;
      if (ctx.terrain[c] === Terrain.WATER) continue;
      for (const [dx, dy] of N4) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
        if (ctx.terrain[ny * cols + nx] === Terrain.WATER) {
          ctx.flags[c] |= CellFlag.COAST;
          break;
        }
      }
    }
  }

  // Height bytes at vertices, made consistent with the final land mask.
  for (let j = 0; j <= rows; j++) {
    for (let i = 0; i <= cols; i++) {
      const v = j * vcols + i;
      let land = 0;
      let total = 0;
      for (const [dx, dy] of [[-1, -1], [0, -1], [-1, 0], [0, 0]] as const) {
        const cx = i + dx;
        const cy = j + dy;
        if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) continue;
        total++;
        if (ctx.terrain[cy * cols + cx] !== Terrain.WATER) land++;
      }
      const e = ctx.elev[v];
      let h: number;
      if (e <= 0) h = clamp(SEA_LEVEL_BYTE - 4 + e * 110, 0, SEA_LEVEL_BYTE - 1);
      else {
        const lift = 0.2 * Math.min(e, 0.6) / 0.6 + 0.8 * ctx.relief[v];
        h = clamp(SEA_LEVEL_BYTE + 2 + lift * (255 - SEA_LEVEL_BYTE - 2), SEA_LEVEL_BYTE + 1, 255);
      }
      if (land === 0 && h >= SEA_LEVEL_BYTE) h = SEA_LEVEL_BYTE - 6;
      if (land === total && total > 0 && h < SEA_LEVEL_BYTE) h = SEA_LEVEL_BYTE + 3;
      ctx.heights[v] = Math.round(h);
    }
  }
}

/** Removes islands so every land cell is reachable by land. */
function keepLargestLandmass(ctx: MapContext): void {
  const { cols, rows } = ctx;
  const comp = new Int32Array(cols * rows).fill(-1);
  const sizes: number[] = [];
  const stack: number[] = [];
  for (let c = 0; c < cols * rows; c++) {
    if (ctx.terrain[c] === Terrain.WATER || comp[c] >= 0) continue;
    const id = sizes.length;
    let size = 0;
    stack.push(c);
    comp[c] = id;
    while (stack.length) {
      const cur = stack.pop()!;
      size++;
      const x = cur % cols;
      const y = (cur - x) / cols;
      for (const [dx, dy] of N4) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
        const n = ny * cols + nx;
        if (ctx.terrain[n] !== Terrain.WATER && comp[n] < 0) {
          comp[n] = id;
          stack.push(n);
        }
      }
    }
    sizes.push(size);
  }
  let best = 0;
  for (let i = 1; i < sizes.length; i++) if (sizes[i] > sizes[best]) best = i;
  for (let c = 0; c < cols * rows; c++) {
    if (comp[c] >= 0 && comp[c] !== best) ctx.terrain[c] = Terrain.WATER;
  }
}
