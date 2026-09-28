// =====================================================================
//  식생 — 바이옴별 나무와 풀·꽃
// =====================================================================
import { S, AIR } from './lib.js';
import { set, get, col, inside, height, surf, reserved, waterTop, biome, B, HALF, SEA } from '../world.js';
import { hash2, hash3, mulberry } from '../noise.js';

const L = n => S(n, { persistent: 'true' });
const LOG = (w, axis = 'y') => S(`${w}_log`, { axis });
function putLeaf(x, y, z, id) { if (get(x, y, z) === AIR) set(x, y, z, id); }

function oak(x, y, z, R, wood = 'oak') {
  const h = 4 + Math.floor(R() * 3);
  const lf = L(`${wood}_leaves`);
  for (let k = 1; k <= h; k++) set(x, y + k, z, LOG(wood));
  for (let dy = -2; dy <= 1; dy++) {
    const r = dy < 0 ? 2 : 1;
    for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
      if (Math.abs(dx) === r && Math.abs(dz) === r && (dy >= 0 || R() < 0.5)) continue;
      putLeaf(x + dx, y + h + dy, z + dz, lf);
    }
  }
  putLeaf(x, y + h + 1, z, lf);
}
function birch(x, y, z, R) { oak(x, y, z, R, 'birch'); set(x, y + 6, z, get(x, y + 6, z) === AIR ? AIR : get(x, y + 6, z)); }
function fancyOak(x, y, z, R) {
  const h = 8 + Math.floor(R() * 5);
  const lf = L('oak_leaves');
  for (let k = 1; k <= h; k++) set(x, y + k, z, LOG('oak'));
  const blobs = [[0, h, 0, 3]];
  const nb = 3 + Math.floor(R() * 3);
  for (let i = 0; i < nb; i++) {
    const a = R() * Math.PI * 2, len = 3 + R() * 3, by = y + h - 3 - Math.floor(R() * 3);
    for (let t = 1; t <= len; t++) set(Math.round(x + Math.cos(a) * t), Math.round(by + t * 0.5), Math.round(z + Math.sin(a) * t), LOG('oak', Math.abs(Math.cos(a)) > 0.7 ? 'x' : Math.abs(Math.sin(a)) > 0.7 ? 'z' : 'y'));
    blobs.push([Math.cos(a) * len, by + len * 0.5 - y, Math.sin(a) * len, 2.2 + R()]);
  }
  for (const [bx, by, bz, r] of blobs) for (let dx = -3; dx <= 3; dx++) for (let dz = -3; dz <= 3; dz++) for (let dy = -2; dy <= 2; dy++) {
    if (Math.hypot(dx, dy * 1.4, dz) > r) continue;
    putLeaf(Math.round(x + bx + dx), Math.round(y + by + dy), Math.round(z + bz + dz), lf);
  }
}
function spruce(x, y, z, R, snowy = false) {
  const h = 7 + Math.floor(R() * 6);
  const lf = L('spruce_leaves');
  for (let k = 1; k <= h; k++) set(x, y + k, z, LOG('spruce'));
  let r = 0;
  for (let k = h + 1; k >= 3; k--) {
    const rr = r;
    for (let dx = -rr; dx <= rr; dx++) for (let dz = -rr; dz <= rr; dz++) {
      if (Math.abs(dx) + Math.abs(dz) > rr + (rr > 1 ? 1 : 0)) continue;
      putLeaf(x + dx, y + k, z + dz, lf);
    }
    r = r >= Math.min(3, 1 + Math.floor((h + 1 - k) / 3)) ? (r > 1 ? r - 1 : r + 1) : r + 1;
  }
  putLeaf(x, y + h + 2, z, lf);
}
function megaSpruce(x, y, z, R) {
  const h = 18 + Math.floor(R() * 10);
  const lf = L('spruce_leaves');
  for (let k = 0; k <= h; k++) for (const [dx, dz] of [[0, 0], [1, 0], [0, 1], [1, 1]]) set(x + dx, y + k, z + dz, LOG('spruce'));
  for (let k = h + 2; k >= Math.floor(h * 0.45); k--) {
    const t = (h + 2 - k) / (h * 0.55);
    const rr = 0.8 + t * 4.2 * (k % 3 === 0 ? 0.75 : 1);
    for (let dx = -Math.ceil(rr); dx <= rr + 1; dx++) for (let dz = -Math.ceil(rr); dz <= rr + 1; dz++) {
      if (Math.hypot(dx - 0.5, dz - 0.5) > rr) continue;
      putLeaf(x + dx, y + k, z + dz, lf);
    }
  }
  for (let dx = -3; dx <= 4; dx++) for (let dz = -3; dz <= 4; dz++) if (inside(x + dx, z + dz) && hash2(x + dx, z + dz, 5) < 0.6 && reserved[col(x + dx, z + dz)] === 0) surf[col(x + dx, z + dz)] = S('podzol');
}
function darkOak(x, y, z, R) {
  const h = 6 + Math.floor(R() * 3);
  const lf = L('dark_oak_leaves');
  for (let k = 0; k <= h; k++) for (const [dx, dz] of [[0, 0], [1, 0], [0, 1], [1, 1]]) set(x + dx, y + k, z + dz, LOG('dark_oak'));
  for (let i = 0; i < 3; i++) { const a = R() * Math.PI * 2; for (let t = 1; t <= 3; t++) set(Math.round(x + 0.5 + Math.cos(a) * (t + 1)), y + h - 2 + t, Math.round(z + 0.5 + Math.sin(a) * (t + 1)), LOG('dark_oak')); }
  for (let dy = -1; dy <= 2; dy++) {
    const rr = dy === 2 ? 2.5 : dy === -1 ? 3.5 : 4.6;
    for (let dx = -5; dx <= 6; dx++) for (let dz = -5; dz <= 6; dz++) if (Math.hypot(dx - 0.5, dz - 0.5) <= rr - R() * 0.6) putLeaf(x + dx, y + h + dy, z + dz, lf);
  }
}
function bush(x, y, z, R, wood = 'oak') {
  set(x, y + 1, z, LOG(wood));
  const lf = L(R() < 0.3 ? 'azalea_leaves' : `${wood}_leaves`);
  for (let dx = -1; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) for (let dy = 1; dy <= 2; dy++) if (!(Math.abs(dx) === 1 && Math.abs(dz) === 1 && dy === 2) && R() < 0.85) putLeaf(x + dx, y + dy, z + dz, lf);
}

const TREE = {
  [B.forest]: [0.018, [['oak', 55], ['fancy', 15], ['birch', 25], ['bush', 5]]],
  [B.birch_forest]: [0.02, [['birch', 85], ['oak', 10], ['bush', 5]]],
  [B.dark_forest]: [0.03, [['dark', 60], ['fancy', 15], ['oak', 15], ['bush', 10]]],
  [B.flower_forest]: [0.009, [['oak', 50], ['birch', 30], ['fancy', 20]]],
  [B.old_growth_spruce_taiga]: [0.022, [['mega', 35], ['spruce', 60], ['bush_s', 5]]],
  [B.taiga]: [0.016, [['spruce', 90], ['bush_s', 10]]],
  [B.grove]: [0.013, [['spruce', 100]]],
  [B.windswept_hills]: [0.003, [['spruce', 60], ['oak', 40]]],
  [B.meadow]: [0.0007, [['oak', 60], ['fancy', 40]]],
  [B.plains]: [0.0012, [['oak', 50], ['fancy', 30], ['bush', 20]]],
  [B.sunflower_plains]: [0.0012, [['oak', 60], ['bush', 40]]],
  [B.snowy_slopes]: [0.0015, [['spruce', 100]]],
};
const GROUND = {
  [B.plains]: [['short_grass', 0.2], ['tall_grass', 0.025], ['dandelion', 0.008], ['poppy', 0.008], ['oxeye_daisy', 0.004], ['cornflower', 0.004]],
  [B.sunflower_plains]: [['short_grass', 0.22], ['tall_grass', 0.03], ['dandelion', 0.02], ['oxeye_daisy', 0.01]],
  [B.meadow]: [['short_grass', 0.32], ['tall_grass', 0.05], ['allium', 0.02], ['cornflower', 0.03], ['azure_bluet', 0.03], ['oxeye_daisy', 0.02], ['dandelion', 0.02], ['poppy', 0.02]],
  [B.flower_forest]: [['short_grass', 0.08], ['red_tulip', 0.04], ['orange_tulip', 0.04], ['white_tulip', 0.04], ['allium', 0.05], ['lily_of_the_valley', 0.05], ['cornflower', 0.04], ['azure_bluet', 0.04], ['oxeye_daisy', 0.04], ['lilac', 0.01], ['rose_bush', 0.01]],
  [B.forest]: [['short_grass', 0.14], ['fern', 0.02], ['poppy', 0.004], ['dandelion', 0.004]],
  [B.birch_forest]: [['short_grass', 0.16], ['fern', 0.01], ['lily_of_the_valley', 0.006]],
  [B.dark_forest]: [['short_grass', 0.07], ['fern', 0.04]],
  [B.taiga]: [['fern', 0.12], ['large_fern', 0.015], ['short_grass', 0.05], ['sweet_berry_bush', 0.012]],
  [B.old_growth_spruce_taiga]: [['fern', 0.14], ['large_fern', 0.02], ['sweet_berry_bush', 0.01]],
  [B.grove]: [['fern', 0.05]],
  [B.windswept_hills]: [['short_grass', 0.08]],
};
const TALL = new Set(['tall_grass', 'large_fern', 'lilac', 'rose_bush']);

function pick(list, r) { const tot = list.reduce((a, b) => a + b[1], 0); let q = r * tot; for (const [n, w] of list) { q -= w; if (q <= 0) return n; } return list[0][0]; }
const okGround = id => id === S('grass_block') || id === S('podzol') || id === S('coarse_dirt') || id === S('moss_block') || id === S('dirt');

export function buildNature() {
  const R = mulberry(777);
  let trees = 0;
  const G = 3;
  const GRASS = S('grass_block'), SNOW = S('snow_block');
  // 나무
  for (let x0 = -HALF; x0 < HALF; x0 += G) for (let z0 = -HALF; z0 < HALF; z0 += G) {
    const x = x0 + Math.floor(hash2(x0, z0, 11) * G), z = z0 + Math.floor(hash2(x0, z0, 12) * G);
    if (!inside(x, z)) continue;
    const c = col(x, z);
    const t = TREE[biome[c]];
    if (!t) continue;
    if (hash2(x0, z0, 13) > t[0] * G * G) continue;
    if (reserved[c] !== 0 || waterTop[c] > height[c]) continue;
    const s = surf[c];
    if (!(okGround(s) || (s === SNOW && biome[c] === B.snowy_slopes))) continue;
    const h = height[c];
    let steep = false;
    for (const [dx, dz] of [[2, 0], [-2, 0], [0, 2], [0, -2]]) if (inside(x + dx, z + dz) && Math.abs(height[col(x + dx, z + dz)] - h) > 2) steep = true;
    if (steep) continue;
    let near = false;
    for (let dx = -2; dx <= 2 && !near; dx++) for (let dz = -2; dz <= 2; dz++) if (inside(x + dx, z + dz) && reserved[col(x + dx, z + dz)] >= 1 && reserved[col(x + dx, z + dz)] !== 4) { near = true; break; }
    if (near) continue;
    const kind = pick(t[1], R());
    if (s === GRASS || s === SNOW) surf[c] = S('dirt');
    if (kind === 'oak') oak(x, h, z, R);
    else if (kind === 'birch') oak(x, h, z, R, 'birch');
    else if (kind === 'fancy') fancyOak(x, h, z, R);
    else if (kind === 'spruce') spruce(x, h, z, R);
    else if (kind === 'mega') megaSpruce(x, h, z, R);
    else if (kind === 'dark') darkOak(x, h, z, R);
    else if (kind === 'bush') bush(x, h, z, R);
    else if (kind === 'bush_s') bush(x, h, z, R, 'spruce');
    for (let dx = -1; dx <= 2; dx++) for (let dz = -1; dz <= 2; dz++) if (inside(x + dx, z + dz) && reserved[col(x + dx, z + dz)] === 0) reserved[col(x + dx, z + dz)] = 4;
    trees++;
  }
  // 풀 · 꽃 · 사탕수수 · 연잎
  let plants = 0;
  const SAND = S('sand');
  for (let x = -HALF + 1; x < HALF - 1; x++) for (let z = -HALF + 1; z < HALF - 1; z++) {
    const c = col(x, z);
    const h = height[c];
    if (waterTop[c] > h) {
      if (waterTop[c] - h === 1 && hash2(x, z, 21) < 0.02 && (biome[c] === B.river || biome[c] === B.ocean)) { set(x, waterTop[c] + 1, z, S('lily_pad')); plants++; }
      continue;
    }
    if (reserved[c] >= 1 && reserved[c] !== 4) continue;
    const s = surf[c];
    const r = hash2(x, z, 23);
    // 물가 사탕수수
    if ((s === SAND || s === GRASS) && h === SEA && r < 0.05) {
      let nearW = false;
      for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (waterTop[col(x + dx, z + dz)] > height[col(x + dx, z + dz)]) nearW = true;
      if (nearW) { const n = 1 + Math.floor(hash2(x, z, 24) * 3); for (let k = 1; k <= n; k++) set(x, h + k, z, S('sugar_cane', { age: '0' })); plants++; continue; }
    }
    if (s !== GRASS && s !== S('podzol')) continue;
    const g = GROUND[biome[c]];
    if (!g) continue;
    if (get(x, h + 1, z) !== AIR) continue;
    let q = r;
    for (const [n, p] of g) {
      if (q < p) {
        if (TALL.has(n)) { if (get(x, h + 2, z) !== AIR) break; set(x, h + 1, z, S(n, { half: 'lower' })); set(x, h + 2, z, S(n, { half: 'upper' })); }
        else if (n === 'sweet_berry_bush') set(x, h + 1, z, S(n, { age: '3' }));
        else set(x, h + 1, z, S(n));
        plants++;
        break;
      }
      q -= p;
    }
  }
  return { trees, plants };
}
