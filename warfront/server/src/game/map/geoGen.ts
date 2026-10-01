import {
  CITY_TYPE_STATS,
  CellFlag,
  SEA_LEVEL_BYTE,
  Terrain,
  chaikin,
  clamp,
  decodeRLE,
  roundPoints,
  type CityDef,
  type CityType,
  type NationId,
  type ResourceKind,
  type RiverDef,
  type TerritoryDef,
} from '@warfront/shared';
import europe from '@warfront/shared/geo/europe.json';
import { N4, quantile, type MapContext } from './MapContext';
import { fbm } from './noise';
import { finaliseTerritories } from './territoryGen';

interface GeoTerritory {
  name: string;
  country: string;
  nation: NationId | null;
  province: string;
  city: { name: string; x: number; y: number; pop: number; capital: boolean } | null;
}

interface GeoData {
  bounds: { lonMin: number; lonMax: number; latMin: number; latMax: number };
  latRef: number;
  width: number;
  height: number;
  cellSize: number;
  cols: number;
  rows: number;
  grid: string;
  territories: GeoTerritory[];
  rivers: RiverDef[];
}

const DATASETS: Record<string, GeoData> = { europe: europe as GeoData };

/** Coastal water within this many cells of land can be crossed by boat. */
const SHALLOW_REACH = 3;

export interface GeoResult {
  rivers: RiverDef[];
  territories: TerritoryDef[];
  cities: CityDef[];
  home: (NationId | null)[];
  capitals: Map<NationId, number>;
}

export function geoDimensions(id: string): { width: number; height: number; cellSize: number } {
  const g = DATASETS[id];
  return { width: g.width, height: g.height, cellSize: g.cellSize };
}

/** Builds a map from real-world data (Natural Earth) instead of procedural shapes. */
export function generateGeo(ctx: MapContext): GeoResult {
  const geo = DATASETS[ctx.def.geo!];
  const { cols, rows, cs, def } = ctx;
  const total = cols * rows;
  const grid = decodeRLE(geo.grid, new Int16Array(total));
  const k = geo.width / ((geo.bounds.lonMax - geo.bounds.lonMin) * Math.cos((geo.latRef * Math.PI) / 180));
  const project = (lon: number, lat: number): [number, number] => [
    (lon - geo.bounds.lonMin) * Math.cos((geo.latRef * Math.PI) / 180) * k,
    (geo.bounds.latMax - lat) * k,
  ];

  // Terrain and theatre.
  for (let c = 0; c < total; c++) {
    const g = grid[c];
    ctx.territory[c] = g >= 0 ? g : -1;
    ctx.terrain[c] = g >= 0 ? Terrain.PLAINS : Terrain.WATER;
    if (g === -2) ctx.flags[c] |= CellFlag.OUTSIDE;
  }

  // Relief: noise plus real mountain ranges.
  const mountains = (def.mountains ?? []).map((m) => {
    const [x, y] = project(m.lon, m.lat);
    const [x2, y2] = project(m.lon + m.rx, m.lat - m.ry);
    return { x, y, rx: Math.abs(x2 - x), ry: Math.abs(y2 - y), weight: m.weight };
  });
  const vcols = cols + 1;
  for (let j = 0; j <= rows; j++) {
    for (let i = 0; i <= cols; i++) {
      const x = i * cs;
      const y = j * cs;
      let r = fbm(x / (def.noiseScale * 0.42), y / (def.noiseScale * 0.42), def.seed + 77, 4) * 0.5 + 0.35;
      for (const m of mountains) {
        const d = Math.hypot((x - m.x) / m.rx, (y - m.y) / m.ry);
        if (d < 1) r += m.weight * (1 - d * d) * (0.75 + 0.5 * fbm(x / 120, y / 120, def.seed + 3, 2));
      }
      ctx.relief[j * vcols + i] = clamp(r, 0, 1);
    }
  }

  // Hills & forests on theatre land.
  const landRelief: number[] = [];
  const cellRelief = new Float32Array(total);
  for (let c = 0; c < total; c++) {
    const x = c % cols;
    const y = (c - x) / cols;
    const v = y * vcols + x;
    cellRelief[c] = (ctx.relief[v] + ctx.relief[v + 1] + ctx.relief[v + vcols] + ctx.relief[v + vcols + 1]) / 4;
    if (ctx.territory[c] >= 0) landRelief.push(cellRelief[c]);
  }
  const hillCut = quantile(landRelief, 1 - def.hillShare);
  const forestNoise: number[] = [];
  for (let c = 0; c < total; c++) {
    if (ctx.territory[c] < 0) continue;
    if (cellRelief[c] >= hillCut) ctx.terrain[c] = Terrain.HILLS;
    else forestNoise.push(fbm((c % cols) * cs / 260, Math.floor(c / cols) * cs / 260, def.seed + 311, 4));
  }
  const forestCut = quantile(forestNoise, 1 - def.forestShare);
  for (let c = 0; c < total; c++) {
    if (ctx.terrain[c] !== Terrain.PLAINS) continue;
    if (fbm((c % cols) * cs / 260, Math.floor(c / cols) * cs / 260, def.seed + 311, 4) >= forestCut) ctx.terrain[c] = Terrain.FOREST;
  }

  // Distance to land for every water cell: coast flags, shallow straits, sea depth.
  const isLandish = (c: number): boolean => grid[c] !== -1;
  const seaDist = new Int32Array(total).fill(-1);
  const queue: number[] = [];
  for (let c = 0; c < total; c++) {
    if (isLandish(c)) {
      seaDist[c] = 0;
      queue.push(c);
    }
  }
  for (let q = 0; q < queue.length; q++) {
    const c = queue[q];
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const n = ny * cols + nx;
      if (seaDist[n] >= 0) continue;
      seaDist[n] = seaDist[c] + 1;
      queue.push(n);
    }
  }
  // Shallow water: reachable within SHALLOW_REACH of theatre land.
  const theatreDist = new Int32Array(total).fill(-1);
  const q2: number[] = [];
  for (let c = 0; c < total; c++) if (ctx.territory[c] >= 0) ((theatreDist[c] = 0), q2.push(c));
  for (let q = 0; q < q2.length; q++) {
    const c = q2[q];
    if (theatreDist[c] >= SHALLOW_REACH) continue;
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const n = ny * cols + nx;
      if (theatreDist[n] >= 0 || grid[n] !== -1) continue;
      theatreDist[n] = theatreDist[c] + 1;
      ctx.flags[n] |= CellFlag.SHALLOW;
      q2.push(n);
    }
  }
  for (let c = 0; c < total; c++) {
    if (ctx.territory[c] < 0) continue;
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx >= 0 && ny >= 0 && nx < cols && ny < rows && grid[ny * cols + nx] === -1) {
        ctx.flags[c] |= CellFlag.COAST;
        break;
      }
    }
  }

  // Vertex heights from the cell land mask, relief and sea depth.
  for (let j = 0; j <= rows; j++) {
    for (let i = 0; i <= cols; i++) {
      let land = 0;
      let n = 0;
      let depth = 0;
      for (const [dx, dy] of [[-1, -1], [0, -1], [-1, 0], [0, 0]] as const) {
        const cx = i + dx;
        const cy = j + dy;
        if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) continue;
        const c = cy * cols + cx;
        n++;
        if (isLandish(c)) land++;
        else depth = Math.max(depth, seaDist[c]);
      }
      const v = j * vcols + i;
      const f = n ? land / n : 0;
      let h: number;
      if (f >= 0.5) h = SEA_LEVEL_BYTE + 2 + (f - 0.5) * 16 + ctx.relief[v] * 150;
      else h = SEA_LEVEL_BYTE - 2 - (0.5 - f) * 10 - Math.min(40, depth * 4);
      ctx.heights[v] = Math.round(clamp(h, 0, 255));
    }
  }

  // Rivers.
  const rivers = geo.rivers.map((r) => ({ width: r.width, points: roundPoints(chaikin(r.points, 2)) }));
  for (const r of rivers) {
    for (let i = 2; i < r.points.length; i += 2) {
      const ax = r.points[i - 2];
      const ay = r.points[i - 1];
      const bx = r.points[i];
      const by = r.points[i + 1];
      const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / (cs * 0.3)));
      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        const cx = Math.floor((ax + (bx - ax) * t) / cs);
        const cy = Math.floor((ay + (by - ay) * t) / cs);
        if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) continue;
        const c = cy * cols + cx;
        if (ctx.territory[c] >= 0) {
          ctx.flags[c] |= CellFlag.RIVER;
          if (ctx.terrain[c] === Terrain.HILLS) ctx.terrain[c] = Terrain.PLAINS;
        }
      }
    }
  }

  // Territories.
  const count = geo.territories.length;
  const drafts = finaliseTerritories(ctx, count);
  addSeaNeighbours(ctx, drafts.map((d) => d.neighbors));

  const home = geo.territories.map((t) => t.nation);
  const capitals = new Map<NationId, number>();
  const cities: CityDef[] = [];
  const territories: TerritoryDef[] = [];
  const types: CityType[] = geo.territories.map((t, i) => {
    const pop = t.city?.pop ?? 0;
    if (t.city?.capital) return 'CAPITAL';
    if (pop >= 250_000) {
      if (drafts[i].coastal) return 'PORT';
      return drafts[i].terrain === Terrain.HILLS || pop > 1_500_000 ? 'INDUSTRIAL_CITY' : 'CITY';
    }
    return 'VILLAGE';
  });
  // Every playable nation gets at least three production towns.
  const nations = new Set(home.filter((n): n is NationId => n !== null));
  for (const n of nations) {
    const own = geo.territories.map((t, i) => ({ t, i })).filter(({ t }) => t.nation === n);
    let producing = own.filter(({ i }) => types[i] !== 'VILLAGE').length;
    for (const { i } of own.sort((a, b) => (b.t.city?.pop ?? 0) - (a.t.city?.pop ?? 0))) {
      if (producing >= 3) break;
      if (types[i] === 'VILLAGE') {
        types[i] = drafts[i].coastal ? 'PORT' : 'CITY';
        producing++;
      }
    }
  }

  geo.territories.forEach((t, i) => {
    const d = drafts[i];
    const type = types[i];
    // City position: real location if it lies inside the territory, else the territory centre.
    let x = d.cx;
    let y = d.cy;
    if (t.city) {
      const cx = Math.floor(t.city.x / cs);
      const cy = Math.floor(t.city.y / cs);
      if (cx >= 0 && cy >= 0 && cx < cols && cy < rows && ctx.territory[cy * cols + cx] === i) {
        x = t.city.x;
        y = t.city.y;
      }
    }
    const cityId = cities.length;
    cities.push({ id: cityId, name: t.name, type, territoryId: i, x, y });
    if (type === 'CAPITAL' && t.nation) capitals.set(t.nation, cityId);
    const stats = CITY_TYPE_STATS[type];
    const pop = t.city?.pop ?? 0;
    const population = Math.round(clamp(18_000 + Math.sqrt(pop) * 55 + d.cells * 60, 16_000, 320_000) / 100) * 100;
    const resource = pickResource(d.terrain, d.coastal, y > def.height * 0.62, i);
    const industry = Math.round(2 + Math.sqrt(pop) / 450 + stats.industry * 1.5 + (resource === 'IRON' || resource === 'COAL' ? 3 : 0));
    territories.push({
      id: i,
      name: t.name,
      cx: d.cx,
      cy: d.cy,
      neighbors: d.neighbors,
      population,
      industry,
      resource,
      cityId,
      cells: d.cells,
      coastal: d.coastal,
      terrain: d.terrain,
    });
    const radius = type === 'CAPITAL' ? 2 : type === 'VILLAGE' ? 0 : 1;
    for (let oy = -radius; oy <= radius; oy++) {
      for (let ox = -radius; ox <= radius; ox++) {
        const cx = Math.floor(x / cs) + ox;
        const cy = Math.floor(y / cs) + oy;
        if (cx >= 0 && cy >= 0 && cx < cols && cy < rows && ctx.territory[cy * cols + cx] === i) ctx.flags[cy * cols + cx] |= CellFlag.TOWN;
      }
    }
  });
  return { rivers, territories, cities, home, capitals };
}

function pickResource(terrain: Terrain, coastal: boolean, southern: boolean, seed: number): ResourceKind {
  const r = ((seed * 2654435761) >>> 0) / 4294967296;
  if (terrain === Terrain.HILLS) return r < 0.5 ? 'IRON' : 'COAL';
  if (terrain === Terrain.FOREST) return r < 0.75 ? 'TIMBER' : 'HORSES';
  if (southern && r < 0.3) return 'WINE';
  if (coastal && r < 0.45) return 'GRAIN';
  if (r < 0.62) return 'GRAIN';
  if (r < 0.82) return 'HORSES';
  return 'COAL';
}

/** Territories facing each other across a crossable strait become neighbours. */
function addSeaNeighbours(ctx: MapContext, neighbors: number[][]): void {
  const { cols, rows } = ctx;
  const total = cols * rows;
  const origin = new Int32Array(total).fill(-1);
  const queue: number[] = [];
  for (let c = 0; c < total; c++) {
    if (ctx.territory[c] >= 0 && ctx.flags[c] & CellFlag.COAST) {
      origin[c] = ctx.territory[c];
      queue.push(c);
    }
  }
  const pairs = new Set<string>();
  for (let q = 0; q < queue.length; q++) {
    const c = queue[q];
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy] of N4) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const n = ny * cols + nx;
      if (!(ctx.flags[n] & CellFlag.SHALLOW)) {
        if (ctx.territory[n] >= 0 && origin[c] !== ctx.territory[n] && !(ctx.flags[c] & CellFlag.COAST && ctx.territory[c] >= 0)) {
          pairs.add(`${Math.min(origin[c], ctx.territory[n])}:${Math.max(origin[c], ctx.territory[n])}`);
        }
        continue;
      }
      if (origin[n] >= 0) {
        if (origin[n] !== origin[c]) pairs.add(`${Math.min(origin[n], origin[c])}:${Math.max(origin[n], origin[c])}`);
        continue;
      }
      origin[n] = origin[c];
      queue.push(n);
    }
  }
  for (const p of pairs) {
    const [a, b] = p.split(':').map(Number);
    if (!neighbors[a].includes(b)) neighbors[a].push(b);
    if (!neighbors[b].includes(a)) neighbors[b].push(a);
  }
}
