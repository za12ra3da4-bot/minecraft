// =====================================================================
//  지형 — 높이맵, 강, 남쪽 만, 산맥, 해안, 터 닦기, 표면 블록, 바이옴
// =====================================================================
import { fbm, ridged, simplex, smooth, lerp, clamp, hash2 } from './noise.js';
import { S } from './registry.js';
import { HALF, N, SEA, height, surf, sub, waterTop, biome, B, col, inside } from './world.js';
import { CITY, CASTLE, VILLAGES, LAKE, LANDMARKS, RIVER } from './plan.js';

export const riverDist = new Float32Array(N * N).fill(1e9);
export const riverW = new Float32Array(N * N);
export const mountain = new Float32Array(N * N);

function catmull(pts, step = 1) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    const len = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
    const n = Math.max(2, Math.ceil(len / step));
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      const row = [f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])];
      for (let j = 2; j < p1.length; j++) row.push(lerp(p1[j], p2[j], t));
      out.push(row);
    }
  }
  out.push(pts[pts.length - 1].slice());
  return out;
}
export { catmull };

// 강 거리장
function stampRiver() {
  const path = catmull(RIVER, 1);
  // 강물이 구불구불하도록 살짝 흔든다
  for (const p of path) { p[0] += simplex(p[1] / 90, 3.3, 71) * 14; p[1] += simplex(p[0] / 90, 7.7, 72) * 8; }
  for (const [px, pz, w] of path) {
    const R = Math.ceil(w + 44);
    for (let dx = -R; dx <= R; dx++) for (let dz = -R; dz <= R; dz++) {
      const x = Math.round(px) + dx, z = Math.round(pz) + dz;
      if (!inside(x, z)) continue;
      const d = Math.hypot(x - px, z - pz), c = col(x, z);
      if (d < riverDist[c]) { riverDist[c] = d; riverW[c] = w; }
    }
  }
  return path;
}

export function generateTerrain() {
  const path = stampRiver();
  const GRASS = S('grass_block'), DIRT = S('dirt'), SAND = S('sand'), SANDSTONE = S('sandstone'), GRAVEL = S('gravel'), STONE = S('stone');
  const SNOW = S('snow_block'), PODZOL = S('podzol'), COARSE = S('coarse_dirt'), CLAY = S('clay'), ANDESITE = S('andesite'), MOSS = S('moss_block');

  // 마을 중심 높이 (터 닦기 전 기본 지형에서)
  const base = (x, z) => 75 + 9 * fbm(x / 420, z / 420, 1, 4) + 4 * fbm(x / 95, z / 95, 2, 3);
  for (const v of VILLAGES) v.y = Math.max(66, Math.round(base(v.x, v.z)));
  VILLAGES.find(v => v.id === 'highpass').y = 112;
  VILLAGES.find(v => v.id === 'cove').y = 65;

  for (let x = -HALF; x < HALF; x++) for (let z = -HALF; z < HALF; z++) {
    const c = col(x, z);
    let h = base(x, z);
    // 서쪽 구릉
    const hw = smooth(-230, -650, x);
    h += hw * (10 + 14 * fbm(x / 210, z / 210, 5, 4));
    // 북쪽 산맥
    const m = smooth(-360, -640, z + simplex(x / 300, 0.5, 9) * 90) * clamp(0.8 + 0.4 * fbm(x / 500, z / 500, 11, 3), 0, 1);
    mountain[c] = m;
    h += m * (26 + 128 * ridged(x / 270, z / 270, 13, 5));
    // 도시 터
    const dc = Math.hypot(x - CITY.x, z - CITY.z);
    if (dc < 270) h = lerp(h, CITY.y + (dc > CITY.R + 10 ? simplex(x / 70, z / 70, 41) * 1.2 : 0), smooth(270, CITY.R + 12, dc));
    const dk = Math.hypot((x - CASTLE.x) * 1.0, (z - CASTLE.z) * 1.15);
    if (dk < 105) h = lerp(h, CASTLE.top, smooth(105, 52, dk));
    // 마을 터
    for (const v of VILLAGES) {
      const dv = Math.hypot(x - v.x, z - v.z);
      if (dv < v.r + 50) h = lerp(h, v.y + simplex(x / 40, z / 40, 51) * 0.8, smooth(v.r + 50, v.r - 5, dv));
    }
    // 강 계곡 · 협곡
    const rd = riverDist[c], rw = riverW[c];
    if (rd < rw) {
      h = Math.min(h, 57 + (rd / rw) * 4.5 + simplex(x / 12, z / 12, 3));
    } else if (rd < rw + 44) {
      const bank = 65.5 + (rd - rw) * (0.5 + m * 1.8);
      h = Math.min(h, lerp(bank, h, smooth(rw + 6, rw + 44, rd) * (1 - m * 0.4)));
    }
    // 남쪽 만 (바다와 이어진 호수)
    const dl = Math.hypot(x - LAKE.x, z - LAKE.z) + simplex(x / 110, z / 110, 21) * 38;
    if (dl < LAKE.r + 40) {
      const t = smooth(LAKE.r + 40, LAKE.r - 70, dl);
      h = lerp(h, 42 + 6 * fbm(x / 60, z / 60, 22, 2), t);
    }
    // 마법사 섬
    const di = Math.hypot(x - LANDMARKS.wizard.x, z - LANDMARKS.wizard.z) + simplex(x / 20, z / 20, 23) * 5;
    if (di < 46) h = Math.max(h, lerp(62, 71 + (46 - di) * 0.12, smooth(46, 30, di)));
    // 바다 가장자리
    const e = HALF - Math.max(Math.abs(x), Math.abs(z)) + simplex(x / 140, z / 140, 31) * 55;
    if (e < 170) h = lerp(h, 36, smooth(170, 30, e));
    height[c] = Math.round(h);
  }
  // 등대 곶
  const L = LANDMARKS.lighthouse;
  for (let x = L.x - 40; x <= L.x + 40; x++) for (let z = L.z - 40; z <= L.z + 40; z++) {
    const d = Math.hypot(x - L.x, z - L.z) + simplex(x / 15, z / 15, 61) * 5;
    if (d < 36 && inside(x, z)) { const c = col(x, z); height[c] = Math.max(height[c], Math.round(lerp(60, 74, smooth(36, 16, d)))); }
  }

  // ── 물 · 표면 · 바이옴
  for (let x = -HALF; x < HALF; x++) for (let z = -HALF; z < HALF; z++) {
    const c = col(x, z), h = height[c];
    if (h < SEA) waterTop[c] = SEA;
    const m = mountain[c];
    // 경사
    const hx = height[col(Math.min(HALF - 1, x + 1), z)] - height[col(Math.max(-HALF, x - 1), z)];
    const hz = height[col(x, Math.min(HALF - 1, z + 1))] - height[col(x, Math.max(-HALF, z - 1))];
    const slope = Math.hypot(hx, hz) / 2;
    const n1 = hash2(x, z, 3);
    let top = GRASS, und = DIRT, bio = B.plains;
    const rd = riverDist[c];
    if (h < SEA) {
      top = h < SEA - 6 ? (n1 < 0.3 ? GRAVEL : SAND) : (rd < 40 ? (n1 < 0.4 ? GRAVEL : n1 < 0.55 ? CLAY : SAND) : SAND);
      und = top === GRAVEL ? GRAVEL : SAND;
      bio = h < 44 ? B.deep_ocean : (rd < riverW[c] + 3 ? B.river : B.ocean);
    } else if (h <= SEA + 1 && rd > 16) {
      top = SAND; und = SANDSTONE; bio = B.beach;
    } else if (m > 0.25 && h > 150 + simplex(x / 30, z / 30, 71) * 10) {
      top = slope > 2.2 ? STONE : SNOW; und = slope > 2.2 ? STONE : SNOW; bio = h > 175 ? B.jagged_peaks : B.snowy_slopes;
    } else if (m > 0.2 && slope > 1.7) {
      top = n1 < 0.7 ? STONE : ANDESITE; und = STONE; bio = h > 120 ? B.stony_peaks : B.windswept_hills;
    } else if (m > 0.3 && h > 105) {
      top = n1 < 0.15 ? COARSE : GRASS; bio = B.grove;
    } else {
      // 숲 · 평야 바이옴
      const f = fbm(x / 260, z / 260, 81, 3);
      if (x < -320 + simplex(x / 200, z / 200, 82) * 80) {
        if (z < -250 + simplex(x / 150, z / 150, 83) * 90) bio = B.old_growth_spruce_taiga;
        else if (f > 0.25) bio = B.dark_forest;
        else if (f < -0.25) bio = B.birch_forest;
        else bio = B.forest;
      } else if (m > 0.12) bio = B.taiga;
      else if (Math.hypot(x + 210, z - 610) < 170) bio = B.flower_forest;
      else if (f > 0.35 && Math.hypot(x - CITY.x, z - CITY.z) > 300) bio = B.forest;
      else if (f < -0.35) bio = B.meadow;
      else if (f < -0.2) bio = B.sunflower_plains;
      if (bio === B.old_growth_spruce_taiga || bio === B.taiga) top = n1 < 0.35 ? PODZOL : n1 < 0.45 ? COARSE : GRASS;
      if (bio === B.dark_forest && n1 < 0.08) top = MOSS;
      if (rd < riverW[c] + 3) { top = n1 < 0.5 ? SAND : GRAVEL; und = top; bio = B.river; }
      if (slope > 3 && h > 80) { top = STONE; und = STONE; }
    }
    surf[c] = top; sub[c] = und; biome[c] = bio;
  }
  return { riverPath: path };
}
