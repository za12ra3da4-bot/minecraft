// =====================================================================
//  길 그리기 도구 — 선을 굵게 칠하고, 지표 블록을 포장재로 바꾼다
// =====================================================================
import { S, STATES } from '../registry.js';
import { col, inside, height, surf, reserved, set, get, waterTop } from '../world.js';
import { mix } from './lib.js';

export function samples(pts, step = 0.5) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[i + 1];
    const len = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.ceil(len / step));
    const tx = (bx - ax) / len, tz = (bz - az) / len;
    for (let k = 0; k < n; k++) out.push([ax + (bx - ax) * k / n, az + (bz - az) * k / n, tx, tz, i]);
  }
  const [lx, lz] = pts[pts.length - 1];
  if (out.length) out.push([lx, lz, out[out.length - 1][2], out[out.length - 1][3], pts.length - 2]);
  return out;
}

// 굵은 선의 칸들을 한 번씩 fn(x, z, 중심선까지 거리, 표본)
export function stroke(pts, w, fn) {
  const seen = new Set();
  const r = w / 2;
  for (const s of samples(pts, 0.5)) {
    const R = Math.ceil(r);
    for (let dx = -R; dx <= R; dx++) for (let dz = -R; dz <= R; dz++) {
      const x = Math.round(s[0]) + dx, z = Math.round(s[1]) + dz;
      if (!inside(x, z)) continue;
      const d = Math.abs((x - s[0]) * -s[3] + (z - s[1]) * s[2]);
      const along = (x - s[0]) * s[2] + (z - s[1]) * s[3];
      if (d > r || Math.abs(along) > 0.6) continue;
      const k = col(x, z);
      if (seen.has(k)) continue;
      seen.add(k);
      fn(x, z, d, s);
    }
  }
  return seen;
}

export const PAVE = {
  main: mix([['stone_bricks', 5], ['cobblestone', 3], ['andesite', 2], ['polished_andesite', 1], ['mossy_cobblestone', 0.6], ['cracked_stone_bricks', 0.6], ['gravel', 0.3]], 301),
  lane: mix([['cobblestone', 5], ['gravel', 1], ['andesite', 1], ['mossy_cobblestone', 1], ['dirt_path', 1.2], ['coarse_dirt', 0.5]], 302),
  plaza: mix([['polished_andesite', 3], ['stone_bricks', 3], ['andesite', 1], ['smooth_stone', 1]], 303),
  road: mix([['dirt_path', 7], ['coarse_dirt', 1.5], ['gravel', 1.2], ['cobblestone', 0.3]], 304),
  edge: mix([['gravel', 2], ['coarse_dirt', 2], ['cobblestone', 1], ['dirt_path', 1]], 305),
};

// 지표 한 칸을 포장 (건물 칸은 건너뜀)
export function paveCell(x, z, mat, level = 1) {
  if (!inside(x, z)) return false;
  const c = col(x, z);
  if (reserved[c] >= 2) return false;
  if (waterTop[c] > height[c]) return false;
  const h = height[c];
  surf[c] = typeof mat === 'function' ? mat(x, h, z) : mat;
  if (reserved[c] < level) reserved[c] = level;
  return true;
}

// 가로등: 돌 받침 + 울타리 기둥 + 등
export function lampPost(x, z, style = 'city') {
  if (!inside(x, z)) return;
  const h = height[col(x, z)];
  if (style === 'city') {
    set(x, h + 1, z, S('stone_brick_wall'));
    set(x, h + 2, z, S('dark_oak_fence')); set(x, h + 3, z, S('dark_oak_fence'));
    set(x, h + 4, z, S('lantern', { hanging: 'false' }));
  } else {
    set(x, h + 1, z, S('spruce_fence')); set(x, h + 2, z, S('spruce_fence'));
    set(x, h + 3, z, S('lantern', { hanging: 'false' }));
  }
  reserved[col(x, z)] = 3;
}
