// =====================================================================
//  월드 저장소
//   - 지형: 열(column)마다 높이 · 표면 블록 · 물 높이
//   - 구조물: 16³ 섹션 단위 희소 배열 (0 = 지형 그대로)
// =====================================================================
import { S, STATES, AIR } from './registry.js';
import { hash3 } from './noise.js';

export const HALF = 1008;                 // 월드 범위 x,z ∈ [-1008, 1008)
export const N = HALF * 2;
export const MIN_Y = -64, MAX_Y = 319;
export const SEA = 63;
export const CH = N / 16;                 // 126 청크

export const height = new Int16Array(N * N);   // 지표 블록의 y
export const surf = new Uint16Array(N * N);     // 지표 블록 id
export const sub = new Uint16Array(N * N);      // 지표 아래 3칸 블록 id
export const waterTop = new Int16Array(N * N).fill(-999);
export const biome = new Uint8Array(N * N);
export const reserved = new Uint8Array(N * N);  // 구조물 · 도로가 쓴 칸 (나무 금지)
export const BIOMES = ['plains', 'forest', 'birch_forest', 'dark_forest', 'taiga', 'snowy_slopes', 'jagged_peaks', 'stony_peaks', 'meadow',
  'river', 'beach', 'ocean', 'deep_ocean', 'flower_forest', 'windswept_hills', 'grove', 'swamp', 'sunflower_plains', 'old_growth_spruce_taiga'];
export const B = Object.fromEntries(BIOMES.map((b, i) => [b, i]));

export const col = (x, z) => (x + HALF) * N + (z + HALF);
export const inside = (x, z) => x >= -HALF && x < HALF && z >= -HALF && z < HALF;

const STONE = S('stone'), DEEP = S('deepslate'), BEDROCK = S('bedrock'), WATER = S('water', { level: '0' });
const ANDESITE = S('andesite'), GRANITE = S('granite'), TUFF = S('tuff');

// 지형이 채우는 블록
export function terrainAt(x, y, z) {
  if (!inside(x, z)) return AIR;
  const c = col(x, z);
  const h = height[c];
  if (y > h) return y <= waterTop[c] ? WATER : AIR;
  if (y === h) return surf[c];
  if (y >= h - 3) return sub[c];
  if (y === MIN_Y) return BEDROCK;
  if (y < 0) return DEEP;
  if (y > h - 12) {
    const v = hash3(x >> 2, y >> 2, z >> 2, 5);
    if (v < 0.08) return ANDESITE; if (v < 0.12) return GRANITE; if (v < 0.14) return TUFF;
  }
  return STONE;
}

// ── 구조물 섹션
const sections = new Map();
const secKey = (cx, sy, cz) => ((cx + 64) * 128 + (cz + 64)) * 32 + (sy + 4);
export function secGet(cx, sy, cz) { return sections.get(secKey(cx, sy, cz)); }
export function sectionCount() { return sections.size; }

export function set(x, y, z, id) {
  x = Math.round(x); y = Math.round(y); z = Math.round(z);
  if (!inside(x, z) || y < MIN_Y || y > MAX_Y) return;
  const k = secKey(x >> 4, y >> 4, z >> 4);
  let s = sections.get(k);
  if (!s) { s = new Uint16Array(4096); sections.set(k, s); }
  s[((y & 15) << 8) | ((z & 15) << 4) | (x & 15)] = id;
}
export function getPlaced(x, y, z) {
  const s = sections.get(secKey(x >> 4, y >> 4, z >> 4));
  return s ? s[((y & 15) << 8) | ((z & 15) << 4) | (x & 15)] : 0;
}
export function get(x, y, z) {
  x = Math.round(x); y = Math.round(y); z = Math.round(z);
  if (!inside(x, z) || y < MIN_Y || y > MAX_Y) return AIR;
  const p = getPlaced(x, y, z);
  return p || terrainAt(x, y, z);
}
export const isEmpty = (x, y, z) => { const b = get(x, y, z); return b === AIR || STATES[b].name === 'water' || STATES[b].def.model === 'cross'; };
export function setIfAir(x, y, z, id) { if (get(x, y, z) === AIR) set(x, y, z, id); }
export function fill(x0, y0, z0, x1, y1, z1, id) {
  for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++)
    for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
      for (let z = Math.min(z0, z1); z <= Math.max(z0, z1); z++) set(x, y, z, id);
}
export const H = (x, z) => (inside(x, z) ? height[col(Math.round(x), Math.round(z))] : SEA - 20);
export const wet = (x, z) => inside(x, z) && waterTop[col(Math.round(x), Math.round(z))] >= height[col(Math.round(x), Math.round(z))] + 1;
export function reserve(x0, z0, x1, z1, v = 1) {
  for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) for (let z = Math.min(z0, z1); z <= Math.max(z0, z1); z++)
    if (inside(x, z)) reserved[col(x, z)] = v;
}
export const isReserved = (x, z) => inside(x, z) && reserved[col(Math.round(x), Math.round(z))] > 0;

// 지표 높이를 강제로 바꾼다 (터 닦기)
export function setGround(x, z, h, top = null) {
  if (!inside(x, z)) return;
  const c = col(x, z);
  height[c] = h;
  if (top !== null) surf[c] = top;
  if (waterTop[c] <= h) waterTop[c] = -999;
}
