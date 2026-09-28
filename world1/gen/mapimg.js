// =====================================================================
//  위에서 내려다본 지도 PNG (블록 1개 = 1픽셀, 음영 포함)
// =====================================================================
import fs from 'node:fs';
import zlib from 'node:zlib';
import { STATES } from './registry.js';
import { HALF, N, height, waterTop, col, secGet, getPlaced, terrainAt } from './world.js';

const C = {
  grass_block: [104, 150, 62], dirt: [134, 96, 67], coarse_dirt: [120, 88, 60], podzol: [102, 74, 42], sand: [219, 207, 163], sandstone: [216, 203, 155],
  gravel: [136, 128, 126], clay: [160, 166, 179], stone: [125, 125, 125], andesite: [136, 136, 136], snow_block: [245, 250, 252], moss_block: [89, 109, 45],
  water: [52, 96, 190], dirt_path: [148, 122, 72], cobblestone: [120, 120, 120], stone_bricks: [122, 121, 122], mossy_stone_bricks: [115, 121, 105],
  polished_andesite: [132, 134, 133], spruce_planks: [114, 84, 50], oak_planks: [162, 130, 78], dark_oak_planks: [66, 43, 20], deepslate_tiles: [54, 54, 55],
  deepslate_tile_stairs: [54, 54, 55], dark_oak_stairs: [66, 43, 20], spruce_stairs: [104, 76, 45], brick_stairs: [150, 90, 75], bricks: [150, 90, 75],
  oak_leaves: [62, 108, 38], spruce_leaves: [52, 84, 52], birch_leaves: [96, 132, 64], dark_oak_leaves: [48, 88, 28], farmland: [96, 62, 38],
  wheat: [180, 160, 60], hay_block: [180, 150, 40], white_terracotta: [210, 178, 161], calcite: [224, 225, 221],
};
export const colorOf = id => {
  const st = STATES[id];
  if (C[st.name]) return C[st.name];
  const n = st.name;
  if (n.includes('leaves')) return [60, 100, 40];
  if (n.includes('stairs') || n.includes('slab')) return C[n.replace(/_(stairs|slab)$/, 's')] || C[n.replace(/_(stairs|slab)$/, '')] || [120, 110, 100];
  if (n.includes('planks') || n.includes('log')) return [110, 80, 50];
  if (n.includes('glass')) return [170, 200, 220];
  return [128, 128, 128];
};

function png(w, h, rgb) {
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; rgb.copy(raw, y * (w * 3 + 1) + 1, y * w * 3, (y + 1) * w * 3); }
  const crcT = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
  const crc = b => { let c = -1; for (const v of b) c = crcT[(c ^ v) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
  const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const cr = Buffer.alloc(4); cr.writeUInt32BE(crc(td)); return Buffer.concat([l, td, cr]); };
  const ih = Buffer.alloc(13); ih.writeUInt32BE(w, 0); ih.writeUInt32BE(h, 4); ih[8] = 8; ih[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', zlib.deflateSync(raw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}

// 각 열의 가장 높은 블록
export function topOf(x, z) {
  const c = col(x, z);
  let y = Math.max(height[c], waterTop[c]), id = terrainAt(x, y, z);
  for (let sy = 19; sy >= (y >> 4); sy--) {
    const s = secGet(x >> 4, sy, z >> 4);
    if (!s) continue;
    for (let yy = sy * 16 + 15; yy >= sy * 16 && yy > y - 1; yy--) {
      const p = getPlaced(x, yy, z);
      if (p > 1) { if (yy >= y) return [yy, p]; break; }
      if (p === 1 && yy <= y) { /* 파낸 곳 */ }
    }
  }
  return [y, id];
}

export function writeMap(file, scale = 1) {
  const w = N / scale, rgb = Buffer.alloc(w * w * 3);
  const top = new Int16Array(w * w);
  for (let i = 0; i < w; i++) for (let j = 0; j < w; j++) {
    const x = -HALF + i * scale, z = -HALF + j * scale;
    const [y, id] = topOf(x, z);
    top[j * w + i] = y;
    let c = colorOf(id);
    const wt = waterTop[col(x, z)];
    if (STATES[id].name === 'water') { const d = wt - height[col(x, z)]; const k = Math.max(0.45, 1 - d * 0.035); c = [c[0] * k, c[1] * k, c[2] * k + 20 * (1 - k)]; }
    const o = (j * w + i) * 3; rgb[o] = c[0]; rgb[o + 1] = c[1]; rgb[o + 2] = c[2];
  }
  // 음영 (북서쪽 빛)
  for (let j = 1; j < w; j++) for (let i = 1; i < w; i++) {
    const d = top[j * w + i] - top[(j - 1) * w + i - 1];
    const k = Math.max(0.6, Math.min(1.35, 1 + d * 0.06));
    const o = (j * w + i) * 3;
    for (let q = 0; q < 3; q++) rgb[o + q] = Math.max(0, Math.min(255, rgb[o + q] * k));
  }
  fs.writeFileSync(file, png(w, w, rgb));
}
