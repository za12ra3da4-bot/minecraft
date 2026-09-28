// =====================================================================
//  건축 도구 — 회전 가능한 지역 좌표계, 재료 섞기, 기본 도형
// =====================================================================
import { S, STATES, AIR } from '../registry.js';
import { set, get, H, inside, col, height, reserve } from '../world.js';
import { hash3, mulberry } from '../noise.js';

export const DIRS = { north: [0, -1], south: [0, 1], west: [-1, 0], east: [1, 0] };
export const OPP = { north: 'south', south: 'north', west: 'east', east: 'west' };
export const dirName = (dx, dz) => (dx > 0 ? 'east' : dx < 0 ? 'west' : dz > 0 ? 'south' : 'north');

// 재료 묶음: 이름 또는 [이름, 가중치] 목록 → 좌표 해시로 결정
export function mix(list, seed = 0) {
  const items = list.map(e => (Array.isArray(e) ? e : [e, 1]));
  const tot = items.reduce((a, b) => a + b[1], 0);
  const ids = items.map(([n]) => (typeof n === 'number' ? n : S(n)));
  return (x, y, z) => {
    let r = hash3(x, y, z, seed) * tot;
    for (let i = 0; i < items.length; i++) { r -= items[i][1]; if (r <= 0) return ids[i]; }
    return ids[ids.length - 1];
  };
}
export const one = n => { const id = typeof n === 'number' ? n : S(n); return () => id; };

// ── 지역 좌표계: 정면(front)이 f 방향. u = 오른쪽, v = 안쪽(뒤), y = 위
export class Frame {
  constructor(ox, oy, oz, front) {
    this.ox = ox; this.oy = oy; this.oz = oz; this.front = front;
    const [fx, fz] = DIRS[front];
    this.f = [fx, fz]; this.b = [-fx, -fz]; this.r = [-fz, fx];
  }
  w(u, v) { return [this.ox + u * this.r[0] + v * this.b[0], this.oz + u * this.r[1] + v * this.b[1]]; }
  dir(local) {
    const d = { front: this.f, back: this.b, right: this.r, left: [-this.r[0], -this.r[1]] }[local];
    return dirName(d[0], d[1]);
  }
  axis(local) { if (local === 'y') return 'y'; const d = local === 'u' ? this.r : this.b; return d[0] !== 0 ? 'x' : 'z'; }
  set(u, v, y, id) { if (id == null) return; const [x, z] = this.w(u, v); set(x, this.oy + y, z, typeof id === 'function' ? id(x, this.oy + y, z) : id); }
  get(u, v, y) { const [x, z] = this.w(u, v); return get(x, this.oy + y, z); }
  wx(u, v, y) { const [x, z] = this.w(u, v); return [x, this.oy + y, z]; }
  box(u0, v0, y0, u1, v1, y1, id) {
    for (let u = Math.min(u0, u1); u <= Math.max(u0, u1); u++) for (let v = Math.min(v0, v1); v <= Math.max(v0, v1); v++)
      for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++) this.set(u, v, y, id);
  }
  stairs(u, v, y, mat, localFacing, half = 'bottom') { this.set(u, v, y, S(`${mat}_stairs`, { facing: this.dir(localFacing), half })); }
  slab(u, v, y, mat, type = 'bottom') { this.set(u, v, y, S(`${mat}_slab`, { type })); }
  log(u, v, y, name, localAxis = 'y') { this.set(u, v, y, S(name, { axis: this.axis(localAxis) })); }
  trapdoor(u, v, y, wood, localFacing, open = true, half = 'bottom') { this.set(u, v, y, S(`${wood}_trapdoor`, { facing: this.dir(localFacing), half, open: String(open) })); }
  door(u, v, y, wood, localFacing, hinge = 'left') {
    const facing = this.dir(localFacing);
    this.set(u, v, y, S(`${wood}_door`, { facing, half: 'lower', hinge, open: 'false' }));
    this.set(u, v, y + 1, S(`${wood}_door`, { facing, half: 'upper', hinge, open: 'false' }));
  }
  lantern(u, v, y, hanging = false) { this.set(u, v, y, S('lantern', { hanging: String(hanging) })); }
}

// ── 둥근 탑 도구 (월드 좌표)
export function disc(cx, cz, r, fn) {
  const R = Math.ceil(r);
  for (let dx = -R; dx <= R; dx++) for (let dz = -R; dz <= R; dz++) {
    const d = Math.hypot(dx, dz);
    if (d <= r + 0.35) fn(cx + dx, cz + dz, d, dx, dz);
  }
}
// 원뿔 지붕: 층마다 반지름을 줄이며 계단 블록으로 테두리
export function coneRoof(cx, y0, cz, r, mat, steep = 1.6, tip = 'dark_oak_fence') {
  let y = y0;
  for (let rr = r; rr >= 0.5; rr -= 1 / steep) {
    const R = Math.ceil(rr);
    for (let dx = -R; dx <= R; dx++) for (let dz = -R; dz <= R; dz++) {
      const d = Math.hypot(dx, dz);
      if (d > rr + 0.3) continue;
      if (d > rr - 1.1) {
        // 가장자리: 중심을 향해 올라가는 계단
        const fdir = Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south');
        set(cx + dx, y, cz + dz, S(`${mat}_stairs`, { facing: fdir, half: 'bottom' }));
      } else set(cx + dx, y, cz + dz, S(matBlock(mat)));
    }
    y++;
  }
  set(cx, y, cz, S(matBlock(mat)));
  if (tip) { set(cx, y + 1, cz, S(tip)); set(cx, y + 2, cz, S(tip)); }
  return y;
}
export function matBlock(mat) {
  return {
    stone_brick: 'stone_bricks', mossy_stone_brick: 'mossy_stone_bricks', brick: 'bricks', deepslate_tile: 'deepslate_tiles', deepslate_brick: 'deepslate_bricks',
    oak: 'oak_planks', spruce: 'spruce_planks', dark_oak: 'dark_oak_planks', birch: 'birch_planks', cobblestone: 'cobblestone', polished_andesite: 'polished_andesite',
    mud_brick: 'mud_bricks', sandstone: 'sandstone', polished_deepslate: 'polished_deepslate', cobbled_deepslate: 'cobbled_deepslate', andesite: 'andesite',
    mossy_cobblestone: 'mossy_cobblestone', granite: 'granite', polished_blackstone_brick: 'polished_blackstone_bricks',
  }[mat] || mat;
}

// 땅 고르기: 발자국 아래를 기초 블록으로 채우고 위쪽은 비운다
export function foundation(x0, z0, x1, z1, y, id, clearTo = 8) {
  for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) for (let z = Math.min(z0, z1); z <= Math.max(z0, z1); z++) {
    if (!inside(x, z)) continue;
    const h = height[col(x, z)];
    for (let yy = Math.min(h, y) - 1; yy <= y; yy++) if (yy > h - 2 || yy <= y) set(x, yy, z, typeof id === 'function' ? id(x, yy, z) : id);
    for (let yy = y + 1; yy <= Math.max(h, y + clearTo); yy++) set(x, yy, z, AIR);
  }
}

export { S, STATES, AIR, set, get, H, reserve, mulberry, hash3 };
export { fill } from "../world.js";
