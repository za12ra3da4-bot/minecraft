/**
 * Builds the real-world "Europe 1812" map data from Natural Earth (public domain).
 *
 *   NE_DIR=/path/to/natural-earth-geojson node scripts/geo/build-europe.mjs
 *
 * NE_DIR must contain (from github.com/nvkelso/natural-earth-vector/geojson):
 *   ne_10m_admin_1_states_provinces.geojson, ne_10m_populated_places_simple.geojson,
 *   ne_10m_rivers_lake_centerlines.geojson, ne_10m_lakes.geojson
 *
 * Output: shared/src/data/geo/europe.json (committed, so the game needs no download).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const NE_DIR = process.env.NE_DIR;
if (!NE_DIR) throw new Error('Set NE_DIR to the Natural Earth geojson directory');
const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../../shared/src/data/geo/europe.json');

// ---------------------------------------------------------------- projection
const BOUNDS = { lonMin: -11, lonMax: 44, latMin: 34.5, latMax: 63 };
const LAT_REF = 50;
const WIDTH = 4800;
const CELL = 16;
const K = WIDTH / ((BOUNDS.lonMax - BOUNDS.lonMin) * Math.cos((LAT_REF * Math.PI) / 180));
const HEIGHT = Math.round(((BOUNDS.latMax - BOUNDS.latMin) * K) / CELL) * CELL;
const COLS = WIDTH / CELL;
const ROWS = HEIGHT / CELL;
const project = (lon, lat) => [(lon - BOUNDS.lonMin) * Math.cos((LAT_REF * Math.PI) / 180) * K, (BOUNDS.latMax - lat) * K];

// ---------------------------------------------------------------- nations (1815, approximated by modern units)
// Europe in June 1812, approximated with modern provinces.
const COUNTRY_NATION = {
  GBR: 'britain', IRL: 'britain', IMN: 'britain', JEY: 'britain', GGY: 'britain', MLT: 'britain',
  FRA: 'france', BEL: 'france', NLD: 'france', LUX: 'france', MCO: 'france', SVN: 'france',
  ESP: 'spain', AND: 'spain', PRT: 'portugal',
  DNK: 'denmark', NOR: 'denmark', SWE: 'sweden',
  AUT: 'austria', CZE: 'austria', SVK: 'austria', HUN: 'austria', HRV: 'austria',
  RUS: 'russia', BLR: 'russia', LTU: 'russia', LVA: 'russia', EST: 'russia', FIN: 'russia', ALD: 'russia', MDA: 'russia', UKR: 'russia',
  TUR: 'ottoman', GRC: 'ottoman', BGR: 'ottoman', SRB: 'ottoman', BIH: 'ottoman', MKD: 'ottoman', ALB: 'ottoman', MNE: 'ottoman', KOS: 'ottoman', CYP: 'ottoman', CYN: 'ottoman', ROU: 'ottoman',
  POL: 'warsaw', DEU: 'rhine', ITA: 'italy',
};
const PROVINCE_NATION = {
  DEU: { Brandenburg: 'prussia', Berlin: 'prussia', 'Mecklenburg-Vorpommern': 'prussia', 'Rheinland-Pfalz': 'france', Saarland: 'france', Bremen: 'france', Hamburg: 'france', 'Schleswig-Holstein': 'denmark' },
  POL: { 'West Pomeranian': 'prussia', Pomeranian: 'prussia', 'Warmian-Masurian': 'prussia', 'Lower Silesian': 'prussia', Opole: 'prussia', Silesian: 'prussia', Lubusz: 'prussia' },
  RUS: { Kaliningrad: 'prussia' },
  UKR: { "L'viv": 'austria', "Ternopil'": 'austria', "Ivano-Frankivs'k": 'austria', Chernivtsi: 'austria', Transcarpathia: 'austria' },
};
const REGION_NATION = {
  ITA: { Piemonte: 'france', "Valle d'Aosta": 'france', Liguria: 'france', Toscana: 'france', Lazio: 'france', Umbria: 'france',
    Abruzzo: 'naples', Molise: 'naples', Apulia: 'naples', Basilicata: 'naples', Calabria: 'naples', Campania: 'naples', Sicily: null, Sardegna: null },
};
/** Nation of a province in 1812 (null = playable but unclaimed). */
function nationOf(p) {
  const a3 = p.adm0_a3;
  const byName = PROVINCE_NATION[a3]?.[p.name];
  if (byName !== undefined) return byName;
  const byRegion = REGION_NATION[a3];
  if (byRegion && p.region in byRegion) return byRegion[p.region];
  // Transylvania, Banat and Bukovina belonged to Austria.
  if (a3 === 'ROU' && ((p.longitude < 25.4 && p.latitude > 45.2) || p.latitude > 47.4)) return 'austria';
  return COUNTRY_NATION[a3] ?? null;
}
/** Playable but unclaimed at start. */
const NEUTRAL = new Set(['CHE', 'LIE', 'SMR', 'VAT']);
const CAPITALS = {
  france: 'Paris', britain: 'London', prussia: 'Berlin', austria: 'Vienna', russia: 'St. Petersburg', spain: 'Madrid',
  portugal: 'Lisbon', sweden: 'Stockholm', denmark: 'Kobenhavn', ottoman: 'Istanbul', warsaw: 'Warsaw',
  rhine: 'Munich', italy: 'Milan', naples: 'Naples',
};
const TARGET_TERRITORIES = 270;

const read = (f) => JSON.parse(readFileSync(resolve(NE_DIR, f), 'utf8'));

function bboxOf(geom) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.type === 'MultiPolygon' ? geom.coordinates : [];
  for (const p of polys) for (const ring of p) for (const [lon, lat] of ring) {
    x0 = Math.min(x0, lon); x1 = Math.max(x1, lon); y0 = Math.min(y0, lat); y1 = Math.max(y1, lat);
  }
  return [x0, y0, x1, y1];
}
const inBounds = ([x0, y0, x1, y1]) => x1 >= BOUNDS.lonMin - 1 && x0 <= BOUNDS.lonMax + 1 && y1 >= BOUNDS.latMin - 1 && y0 <= BOUNDS.latMax + 1;

/** Scanline rasterisation (even-odd) of a polygon geometry into grid cells. */
function rasterize(geom, grid, value) {
  const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
  for (const poly of polys) {
    const rings = poly.map((ring) => ring.map(([lon, lat]) => project(lon, lat)));
    let minY = Infinity, maxY = -Infinity;
    for (const r of rings) for (const [, y] of r) { minY = Math.min(minY, y); maxY = Math.max(maxY, y); }
    const r0 = Math.max(0, Math.floor(minY / CELL));
    const r1 = Math.min(ROWS - 1, Math.ceil(maxY / CELL));
    for (let row = r0; row <= r1; row++) {
      const cy = (row + 0.5) * CELL;
      const xs = [];
      for (const r of rings) {
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const [xi, yi] = r[i];
          const [xj, yj] = r[j];
          if ((yi > cy) !== (yj > cy)) xs.push(xi + ((cy - yi) / (yj - yi)) * (xj - xi));
        }
      }
      xs.sort((a, b) => a - b);
      for (let k = 0; k + 1 < xs.length; k += 2) {
        const c0 = Math.max(0, Math.ceil(xs[k] / CELL - 0.5));
        const c1 = Math.min(COLS - 1, Math.floor(xs[k + 1] / CELL - 0.5));
        for (let c = c0; c <= c1; c++) grid[row * COLS + c] = value;
      }
    }
  }
}

// ---------------------------------------------------------------- provinces
console.log(`grid ${COLS}x${ROWS}, world ${WIDTH}x${HEIGHT}`);
const admin = read('ne_10m_admin_1_states_provinces.geojson').features.filter((f) => f.geometry && inBounds(bboxOf(f.geometry)));
const provGrid = new Int32Array(COLS * ROWS).fill(-1);
const provinces = admin.map((f, i) => {
  rasterize(f.geometry, provGrid, i);
  const p = f.properties;
  const a3 = p.adm0_a3;
  const nation = nationOf(p);
  return { name: p.name_en || p.name, region: p.region || '', country: a3, nation, theater: nation !== null || NEUTRAL.has(a3) || a3 === 'ITA' };
});

// Lakes are water even inside provinces.
const lakes = read('ne_10m_lakes.geojson').features.filter((f) => f.properties.scalerank <= 5 && f.geometry && inBounds(bboxOf(f.geometry)));
for (const f of lakes) rasterize(f.geometry, provGrid, -1);

// ---------------------------------------------------------------- regions (territories)
const total = COLS * ROWS;
const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const region = new Int32Array(total).fill(-1);
// Start with one region per province (theater only).
for (let c = 0; c < total; c++) if (provGrid[c] >= 0 && provinces[provGrid[c]].theater) region[c] = provGrid[c];

function regionSizes() {
  const sizes = new Map();
  for (let c = 0; c < total; c++) if (region[c] >= 0) sizes.set(region[c], (sizes.get(region[c]) ?? 0) + 1);
  return sizes;
}
let sizes = regionSizes();
const landCells = [...sizes.values()].reduce((a, b) => a + b, 0);
const T = landCells / TARGET_TERRITORIES;
console.log(`theater land cells ${landCells}, target territory size ${T.toFixed(0)}`);

const places = read('ne_10m_populated_places_simple.geojson').features
  .map((f) => ({ name: f.properties.nameascii || f.properties.name, display: f.properties.name, pop: f.properties.pop_max || 0, a3: f.properties.adm0_a3, capital: f.properties.adm0cap === 1, lon: f.properties.longitude, lat: f.properties.latitude }))
  .filter((p) => p.lon >= BOUNDS.lonMin && p.lon <= BOUNDS.lonMax && p.lat >= BOUNDS.latMin && p.lat <= BOUNDS.latMax)
  .map((p) => {
    const [x, y] = project(p.lon, p.lat);
    return { ...p, x, y, cell: Math.floor(y / CELL) * COLS + Math.floor(x / CELL) };
  })
  .sort((a, b) => b.pop - a.pop);

// Split oversized regions with seeds at their largest cities.
let nextRegion = provinces.length;
for (const [id, size] of [...sizes]) {
  if (size < T * 2.1) continue;
  const k = Math.round(size / T);
  const cells = [];
  for (let c = 0; c < total; c++) if (region[c] === id) cells.push(c);
  const seeds = places.filter((p) => region[p.cell] === id).slice(0, k).map((p) => p.cell);
  // Farthest-point sampling for the remaining seeds.
  while (seeds.length < k) {
    let best = cells[0], bestD = -1;
    for (const c of cells) {
      const x = c % COLS, y = Math.floor(c / COLS);
      let d = Infinity;
      for (const s of seeds) d = Math.min(d, (s % COLS - x) ** 2 + (Math.floor(s / COLS) - y) ** 2);
      if (d > bestD) { bestD = d; best = c; }
    }
    seeds.push(best);
  }
  // Multi-source BFS restricted to the region.
  const queue = [];
  seeds.forEach((s, i) => { region[s] = i === 0 ? id : nextRegion + i - 1; queue.push(s); });
  const mark = new Set(seeds);
  for (let q = 0; q < queue.length; q++) {
    const c = queue[q];
    const x = c % COLS, y = Math.floor(c / COLS);
    for (const [dx, dy] of N4) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= COLS || ny >= ROWS) continue;
      const n = ny * COLS + nx;
      if (region[n] !== id || mark.has(n)) continue;
      mark.add(n);
      region[n] = region[c];
      queue.push(n);
    }
  }
  for (let i = 1; i < seeds.length; i++) provinces[nextRegion + i - 1] = { ...provinces[id] };
  nextRegion += seeds.length - 1;
}

// Merge undersized regions into same-country neighbours (prefer the same admin region).
for (let pass = 0; pass < 60; pass++) {
  sizes = regionSizes();
  const order = [...sizes].filter(([, s]) => s < T * 0.55).sort((a, b) => a[1] - b[1]);
  if (!order.length) break;
  const merged = new Set();
  for (const [id] of order) {
    if (merged.has(id)) continue;
    const nb = new Map();
    for (let c = 0; c < total; c++) {
      if (region[c] !== id) continue;
      const x = c % COLS, y = Math.floor(c / COLS);
      for (const [dx, dy] of N4) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= COLS || ny >= ROWS) continue;
        const o = region[ny * COLS + nx];
        if (o >= 0 && o !== id && provinces[o].country === provinces[id].country && provinces[o].nation === provinces[id].nation) nb.set(o, (nb.get(o) ?? 0) + 1);
      }
    }
    if (!nb.size) continue;
    let target = -1, bestScore = Infinity;
    for (const [o, shared] of nb) {
      if (merged.has(o)) continue;
      const sameRegion = provinces[o].region && provinces[o].region === provinces[id].region;
      const score = (sizes.get(o) ?? 0) * (sameRegion ? 0.5 : 1) - shared * 2;
      if (score < bestScore) { bestScore = score; target = o; }
    }
    if (target < 0) continue;
    for (let c = 0; c < total; c++) if (region[c] === id) region[c] = target;
    merged.add(id);
    merged.add(target);
  }
}
// Tiny isolated islands are dropped from play.
sizes = regionSizes();
for (const [id, s] of sizes) if (s < 6) for (let c = 0; c < total; c++) if (region[c] === id) region[c] = -1;

// Compact ids, name territories after their largest city.
const ids = [...regionSizes().keys()];
const compact = new Map(ids.map((id, i) => [id, i]));
const grid = new Int16Array(total).fill(-1);
for (let c = 0; c < total; c++) {
  if (region[c] >= 0) grid[c] = compact.get(region[c]);
  else if (provGrid[c] >= 0) grid[c] = -2; // land outside the theatre
}
const territories = ids.map((id) => ({ name: '', country: provinces[id].country, nation: provinces[id].nation, province: provinces[id].name, city: null }));
const ENGLISH = { Kobenhavn: 'Copenhagen' };
const capitalNames = new Set(Object.values(CAPITALS));
const used = new Set();
for (const p of [...places].sort((a, b) => Number(capitalNames.has(b.name)) - Number(capitalNames.has(a.name)) || b.pop - a.pop)) {
  let t = grid[p.cell];
  // Coastal capitals can fall on a water cell: snap to the nearest land cell.
  if (t < 0 && capitalNames.has(p.name)) {
    const px = p.cell % COLS, py = Math.floor(p.cell / COLS);
    let best = Infinity;
    for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
      const x = px + dx, y = py + dy;
      if (x < 0 || y < 0 || x >= COLS || y >= ROWS) continue;
      const g = grid[y * COLS + x];
      if (g >= 0 && dx * dx + dy * dy < best && territories[g].nation && CAPITALS[territories[g].nation] === p.name) { best = dx * dx + dy * dy; t = g; }
    }
  }
  if (t < 0 || territories[t].city) continue;
  if (used.has(p.name)) continue;
  used.add(p.name);
  const nation = territories[t].nation;
  territories[t].city = { name: p.name, x: Math.round(p.x), y: Math.round(p.y), pop: p.pop, capital: nation ? CAPITALS[nation] === p.name : false };
}

for (const t of territories) {
  if (t.city && ENGLISH[t.city.name]) t.city.name = ENGLISH[t.city.name];
  t.name = t.city ? t.city.name : t.province;
  if (used.has(t.name) && !t.city) t.name = `${t.province}`;
}
const missing = Object.entries(CAPITALS).filter(([, name]) => !territories.some((t) => t.city?.capital && (t.city.name === name || t.city.name === ENGLISH[name])));
if (missing.length) console.warn('capitals not placed:', missing);

// ---------------------------------------------------------------- rivers
const rivers = read('ne_10m_rivers_lake_centerlines.geojson').features
  .filter((f) => f.properties.featurecla?.startsWith('River') && f.properties.scalerank <= 7 && f.geometry && inBounds(bboxOfLines(f.geometry)))
  .flatMap((f) => {
    const lines = f.geometry.type === 'LineString' ? [f.geometry.coordinates] : f.geometry.coordinates;
    const width = Math.max(3, 9 - f.properties.scalerank);
    return lines.map((line) => ({ width, points: simplify(line.map(([lon, lat]) => project(lon, lat)).flat(), 3).map((v) => Math.round(v * 10) / 10) }));
  })
  .filter((r) => r.points.length >= 6);
function bboxOfLines(g) {
  const lines = g.type === 'LineString' ? [g.coordinates] : g.coordinates;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const l of lines) for (const [lon, lat] of l) { x0 = Math.min(x0, lon); x1 = Math.max(x1, lon); y0 = Math.min(y0, lat); y1 = Math.max(y1, lat); }
  return [x0, y0, x1, y1];
}
function simplify(pts, eps) {
  const n = pts.length / 2;
  if (n <= 2) return pts;
  const keep = new Uint8Array(n); keep[0] = keep[n - 1] = 1;
  const stack = [[0, n - 1]];
  while (stack.length) {
    const [a, b] = stack.pop();
    let maxD = -1, idx = -1;
    for (let i = a + 1; i < b; i++) {
      const [ax, ay, bx, by, px, py] = [pts[a * 2], pts[a * 2 + 1], pts[b * 2], pts[b * 2 + 1], pts[i * 2], pts[i * 2 + 1]];
      const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
      const t = l2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l2)) : 0;
      const d = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2;
      if (d > maxD) { maxD = d; idx = i; }
    }
    if (maxD > eps * eps) { keep[idx] = 1; stack.push([a, idx], [idx, b]); }
  }
  const out = [];
  for (let i = 0; i < n; i++) if (keep[i]) out.push(pts[i * 2], pts[i * 2 + 1]);
  return out;
}

// ---------------------------------------------------------------- encode
function encodeRLE(values) {
  const out = [];
  const varint = (v) => { v >>>= 0; while (v >= 0x80) { out.push((v & 0x7f) | 0x80); v >>>= 7; } out.push(v); };
  let i = 0;
  while (i < values.length) {
    const v = values[i];
    let run = 1;
    while (i + run < values.length && values[i + run] === v) run++;
    varint(v >= 0 ? v * 2 : -v * 2 - 1);
    varint(run);
    i += run;
  }
  return Buffer.from(out).toString('base64');
}

const data = {
  source: 'Natural Earth 1:10m (public domain)',
  bounds: BOUNDS,
  latRef: LAT_REF,
  width: WIDTH,
  height: HEIGHT,
  cellSize: CELL,
  cols: COLS,
  rows: ROWS,
  /** Territory id per cell, -1 water, -2 land outside the theatre. */
  grid: encodeRLE(grid),
  territories,
  rivers,
};
writeFileSync(OUT, JSON.stringify(data));
const byNation = {};
for (const t of territories) byNation[t.nation ?? 'neutral'] = (byNation[t.nation ?? 'neutral'] ?? 0) + 1;
console.log(`territories ${territories.length}`, byNation, `rivers ${rivers.length}`, `size ${(JSON.stringify(data).length / 1024).toFixed(0)} KB`);
