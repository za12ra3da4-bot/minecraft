import { CellFlag, Terrain, hash2 } from '@warfront/shared';
import { MinHeap } from '../util/MinHeap';
import { fbm } from './noise';
import { N4, N8, cellAtWorld, type MapContext } from './MapContext';

export interface TerritoryDraft {
  id: number;
  cells: number;
  neighbors: number[];
  cx: number;
  cy: number;
  coastal: boolean;
  terrain: Terrain;
  riverside: boolean;
}

export interface TerritoryResult {
  drafts: TerritoryDraft[];
  /** Territory id of each nation slot's capital (same order as def.nations). */
  capitalTerritories: number[];
}

/**
 * Grows territories from Poisson-disc seeds with a multi-source Dijkstra.
 * Rivers are expensive to cross, so borders tend to follow them.
 */
export function generateTerritories(ctx: MapContext): TerritoryResult {
  const { def, cols, rows, cs, rng } = ctx;
  const total = cols * rows;
  const landCells: number[] = [];
  for (let c = 0; c < total; c++) if (ctx.terrain[c] !== Terrain.WATER) landCells.push(c);
  const area = landCells.length / def.territoryCount;
  const minDist = Math.sqrt(area) * 0.82;

  // Seeds: capitals first, then Poisson-disc samples.
  const seeds: number[] = [];
  const capitalSeedIdx: number[] = [];
  for (const slot of def.nations) {
    const target = cellAtWorld(ctx, slot.anchor[0] * def.width, slot.anchor[1] * def.height);
    const tx = target >= 0 ? target % cols : Math.floor(slot.anchor[0] * cols);
    const ty = target >= 0 ? Math.floor(target / cols) : Math.floor(slot.anchor[1] * rows);
    let best = landCells[0];
    let bestD = Infinity;
    for (const c of landCells) {
      const d = (c % cols - tx) ** 2 + (Math.floor(c / cols) - ty) ** 2;
      if (d < bestD && !seeds.includes(c)) {
        bestD = d;
        best = c;
      }
    }
    capitalSeedIdx.push(seeds.length);
    seeds.push(best);
  }
  const candidates = rng.shuffle(landCells.slice());
  const seedXY: [number, number][] = seeds.map((c) => [c % cols, Math.floor(c / cols)]);
  const minD2 = minDist * minDist;
  for (const c of candidates) {
    if (seeds.length >= def.territoryCount) break;
    const x = c % cols;
    const y = (c - x) / cols;
    let ok = true;
    for (const [sx, sy] of seedXY) {
      if ((sx - x) ** 2 + (sy - y) ** 2 < minD2) {
        ok = false;
        break;
      }
    }
    if (ok) {
      seeds.push(c);
      seedXY.push([x, y]);
    }
  }

  // Multi-source Dijkstra.
  const owner = ctx.territory;
  owner.fill(-1);
  const dist = new Float32Array(total).fill(Infinity);
  const heap = new MinHeap();
  const warpScale = Math.sqrt(area) * cs * 1.3;
  const costMul = new Float32Array(total);
  for (const c of landCells) {
    const x = c % cols;
    const y = (c - x) / cols;
    const low = fbm((x * cs) / warpScale, (y * cs) / warpScale, def.seed + 901, 3) * 0.5 + 0.5;
    let terrainCost = 0;
    if (ctx.terrain[c] === Terrain.HILLS) terrainCost = 0.5;
    else if (ctx.terrain[c] === Terrain.FOREST) terrainCost = 0.25;
    costMul[c] = 1 + low * 1.1 + hash2(x, y, def.seed) * 0.5 + terrainCost;
  }
  seeds.forEach((c, i) => {
    dist[c] = 0;
    owner[c] = i;
    heap.push(c, 0);
  });
  while (heap.size) {
    const d0 = heap.peekPriority();
    const c = heap.pop();
    if (d0 > dist[c]) continue;
    const x = c % cols;
    const y = (c - x) / cols;
    const riverHere = (ctx.flags[c] & CellFlag.RIVER) !== 0;
    for (const [dx, dy, w] of N8) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const n = ny * cols + nx;
      if (ctx.terrain[n] === Terrain.WATER) continue;
      const riverThere = (ctx.flags[n] & CellFlag.RIVER) !== 0;
      const nd = d0 + w * costMul[n] + (riverHere !== riverThere ? 5 : 0);
      if (nd < dist[n]) {
        dist[n] = nd;
        owner[n] = owner[c];
        heap.push(n, nd);
      }
    }
  }

  // Merge tiny territories into their best neighbour.
  const protectedIds = new Set(capitalSeedIdx);
  for (let pass = 0; pass < 6; pass++) {
    const sizes = new Map<number, number>();
    for (const c of landCells) sizes.set(owner[c], (sizes.get(owner[c]) ?? 0) + 1);
    let changed = false;
    for (const [id, size] of sizes) {
      if (size >= area * 0.3 || protectedIds.has(id)) continue;
      const shared = new Map<number, number>();
      for (const c of landCells) {
        if (owner[c] !== id) continue;
        const x = c % cols;
        const y = (c - x) / cols;
        for (const [dx, dy] of N4) {
          const nx = x + dx;
          const ny = y + dy;
          if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
          const o = owner[ny * cols + nx];
          if (o >= 0 && o !== id) shared.set(o, (shared.get(o) ?? 0) + 1);
        }
      }
      let target = -1;
      let best = 0;
      for (const [o, cnt] of shared) if (cnt > best) ((best = cnt), (target = o));
      if (target < 0) continue;
      for (const c of landCells) if (owner[c] === id) owner[c] = target;
      changed = true;
    }
    if (!changed) break;
  }

  // Compact ids.
  const remap = new Map<number, number>();
  for (const c of landCells) {
    if (!remap.has(owner[c])) remap.set(owner[c], remap.size);
  }
  for (const c of landCells) owner[c] = remap.get(owner[c])!;
  const count = remap.size;
  const capitalTerritories = capitalSeedIdx.map((i) => remap.get(i) ?? 0);

  // Territory statistics.
  const cellsCount = new Array<number>(count).fill(0);
  const sumX = new Array<number>(count).fill(0);
  const sumY = new Array<number>(count).fill(0);
  const neighbors = Array.from({ length: count }, () => new Set<number>());
  const coastal = new Array<boolean>(count).fill(false);
  const riverside = new Array<boolean>(count).fill(false);
  const terrainCounts = Array.from({ length: count }, () => [0, 0, 0, 0, 0]);
  const borderDist = new Int32Array(total).fill(-1);
  const queue: number[] = [];
  for (const c of landCells) {
    const t = owner[c];
    const x = c % cols;
    const y = (c - x) / cols;
    cellsCount[t]++;
    sumX[t] += x;
    sumY[t] += y;
    terrainCounts[t][ctx.terrain[c]]++;
    if (ctx.flags[c] & CellFlag.COAST) coastal[t] = true;
    if (ctx.flags[c] & CellFlag.RIVER) riverside[t] = true;
    let border = false;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) {
        border = true;
        continue;
      }
      const o = owner[ny * cols + nx];
      if (o !== t) border = true;
      if (o >= 0 && o !== t) neighbors[t].add(o);
    }
    if (border) {
      borderDist[c] = 0;
      queue.push(c);
    }
  }
  for (let qi = 0; qi < queue.length; qi++) {
    const c = queue[qi];
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const n = ny * cols + nx;
      if (owner[n] === owner[c] && borderDist[n] < 0) {
        borderDist[n] = borderDist[c] + 1;
        queue.push(n);
      }
    }
  }
  const bestCell = new Array<number>(count).fill(-1);
  const bestScore = new Array<number>(count).fill(-Infinity);
  for (const c of landCells) {
    const t = owner[c];
    const x = c % cols;
    const y = (c - x) / cols;
    const mx = sumX[t] / cellsCount[t];
    const my = sumY[t] / cellsCount[t];
    // Prefer the deepest cell, break ties toward the centroid; avoid rivers for towns.
    const river = ctx.flags[c] & CellFlag.RIVER ? 1.5 : 0;
    const score = borderDist[c] - Math.hypot(x - mx, y - my) * 0.08 - river;
    if (score > bestScore[t]) {
      bestScore[t] = score;
      bestCell[t] = c;
    }
  }

  const drafts: TerritoryDraft[] = [];
  for (let t = 0; t < count; t++) {
    const c = bestCell[t];
    const x = c % cols;
    const y = (c - x) / cols;
    const tc = terrainCounts[t];
    let dom: Terrain = Terrain.PLAINS;
    for (const k of [Terrain.FOREST, Terrain.HILLS, Terrain.MARSH] as Terrain[]) if (tc[k] > tc[dom]) dom = k;
    drafts.push({
      id: t,
      cells: cellsCount[t],
      neighbors: [...neighbors[t]].sort((a, b) => a - b),
      cx: (x + 0.5) * cs,
      cy: (y + 0.5) * cs,
      coastal: coastal[t],
      terrain: dom,
      riverside: riverside[t],
    });
  }
  return { drafts, capitalTerritories };
}
