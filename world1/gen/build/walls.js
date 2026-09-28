// =====================================================================
//  성벽 · 원형 망루 · 성문 누각
// =====================================================================
import { S, AIR, mix, Frame, disc, coneRoof, dirName } from './lib.js';
import { set, get, col, inside, height, reserved, reserve, H } from '../world.js';

export const WALL_MIX = mix([['stone_bricks', 6], ['mossy_stone_bricks', 1.2], ['cracked_stone_bricks', 1.2], ['andesite', 0.6], ['cobblestone', 1]], 401);
const inward = (dx, dz) => dirName(Math.abs(dx) > Math.abs(dz) ? -Math.sign(dx) : 0, Math.abs(dx) > Math.abs(dz) ? 0 : -Math.sign(dz));

// 둥근 망루. roof: 'cone' | 'flat'
export function roundTower(cx, cz, r, top, o = {}) {
  const base = o.base ?? H(cx, cz);
  const mat = o.mat ?? WALL_MIX;
  const inner = r - 2.2;
  disc(cx, cz, r + 0.2, (x, z, d) => {
    const h = Math.min(H(x, z), base);
    for (let y = h - 3; y <= top; y++) {
      if (d > inner) set(x, y, z, mat(x, y, z));
      else set(x, y, z, (y - base) % 7 === 0 || y === top ? S('spruce_planks') : AIR);
    }
    reserved[col(x, z)] = 3;
  });
  // 코벨 + 총안
  disc(cx, cz, r + 1.2, (x, z, d, dx, dz) => {
    if (d <= r + 0.3) return;
    set(x, top - 1, z, S('stone_brick_stairs', { facing: inward(dx, dz), half: 'top' }));
    set(x, top, z, mat(x, top, z));
    const a = Math.atan2(dz, dx), k = Math.round(a * (r + 1) / 1.0);
    if (k % 2 === 0) { set(x, top + 1, z, mat(x, top + 1, z)); set(x, top + 2, z, S('stone_brick_slab', { type: 'bottom' })); }
    else set(x, top + 1, z, S('stone_brick_slab', { type: 'bottom' }));
  });
  // 화살 구멍
  for (let q = 0; q < 8; q++) {
    const a = q * Math.PI / 4 + (o.rot ?? 0);
    const x = Math.round(cx + Math.cos(a) * r), z = Math.round(cz + Math.sin(a) * r);
    for (const yy of [base + 5, base + 6, top - 6, top - 5]) set(x, yy, z, AIR);
  }
  if (o.roof === 'cone') {
    disc(cx, cz, r + 0.3, (x, z) => set(x, top + 1, z, S('spruce_planks')));
    coneRoof(cx, top + 1, cz, r + 1.4, o.roofMat ?? 'deepslate_tile', o.steep ?? 1.4, 'dark_oak_fence');
  }
  if (o.banner) {
    for (let y = top - 3; y > top - 10; y--) set(cx + (o.banner[0] || 0), y, cz + (o.banner[1] || 0), S(o.bannerColor ?? 'red_wool'));
  }
}

// 원형 성벽
export function ringWall(cx, cz, R, o = {}) {
  const T = o.thick ?? 5, hh = o.height ?? 13, half = T / 2;
  const mat = o.mat ?? WALL_MIX;
  const tops = new Map();
  for (let x = Math.floor(cx - R - half - 2); x <= cx + R + half + 2; x++) for (let z = Math.floor(cz - R - half - 2); z <= cz + R + half + 2; z++) {
    if (!inside(x, z)) continue;
    const dx = x - cx, dz = z - cz, d = Math.hypot(dx, dz);
    if (Math.abs(d - R) > half + 1.3) continue;
    const g = H(x, z);
    // 성벽 윗면 높이는 주변 평균 지면 기준 (계단처럼 튀지 않게)
    const a = Math.atan2(dz, dx);
    const key = Math.round(a * R / 3);
    let top = tops.get(key);
    if (top === undefined) { let s = 0, n = 0; for (let t = -2; t <= 2; t++) { const aa = (key + t) * 3 / R; s += H(cx + Math.cos(aa) * R, cz + Math.sin(aa) * R); n++; } top = Math.round(s / n) + hh; tops.set(key, top); }
    if (Math.abs(d - R) <= half) {
      for (let y = g - 3; y <= top; y++) set(x, y, z, mat(x, y, z));
      reserved[col(x, z)] = 3;
      const outer = d > R + half - 1, innerE = d < R - half + 1;
      const arc = Math.round(a * R);
      if (outer) {
        if (arc % 2 === 0) { set(x, top + 1, z, mat(x, top + 1, z)); set(x, top + 2, z, S('stone_brick_slab')); }
        else set(x, top + 1, z, S('stone_brick_slab'));
        if (arc % 9 === 0) { set(x, top - 4, z, AIR); set(x, top - 5, z, AIR); }
      } else if (innerE) set(x, top + 1, z, S('stone_brick_wall'));
      else set(x, top, z, S(arc % 5 === 0 ? 'polished_andesite' : 'stone_bricks'));
    } else if (d > R + half && d <= R + half + 1.3) {
      // 바깥 코벨
      set(x, top - 1, z, S('stone_brick_stairs', { facing: inward(dx, dz), half: 'top' }));
      if (Math.round(a * R) % 2 === 0) set(x, top - 2, z, S('stone_brick_stairs', { facing: inward(dx, dz), half: 'top' }));
    }
  }
  return tops;
}

// 성문 누각. (x,z): 성벽 위 중심, out: 바깥 방향
export function gatehouse(x, z, out, o = {}) {
  const base = o.base ?? H(x, z);
  // 지역 좌표: 정면 = 바깥. u: -10..10, v: -4(바깥) .. 9(안)
  const F = new Frame(x, base, z, out);
  const mat = o.mat ?? WALL_MIX;
  const topC = 17, topT = 25;
  // 몸체
  for (let u = -10; u <= 10; u++) for (let v = -4; v <= 9; v++) {
    const tower = Math.abs(u) >= 4 && (v <= 3);
    const top = tower ? topT : topC;
    if (!tower && (v > 7 || Math.abs(u) > 8)) continue;
    const [wx, wz] = F.w(u, v);
    const g = H(wx, wz);
    for (let y = g - base - 3; y <= top; y++) F.set(u, v, y, mat);
    reserved[col(wx, wz)] = 3;
  }
  // 통로 + 아치
  for (let u = -2; u <= 2; u++) for (let v = -5; v <= 10; v++) {
    const [wx, wz] = F.w(u, v);
    const g = H(wx, wz) - base;
    const archTop = Math.abs(u) === 2 ? 6 : 8;
    for (let y = Math.max(1, g + 1); y <= archTop; y++) F.set(u, v, y, AIR);
    F.set(u, v, Math.max(0, g), S('stone_bricks'));
  }
  for (const v of [-4, 7]) {
    F.stairs(-2, v, 6, 'stone_brick', 'right', 'top'); F.stairs(2, v, 6, 'stone_brick', 'left', 'top');
    F.stairs(-1, v, 8, 'stone_brick', 'right', 'top'); F.stairs(1, v, 8, 'stone_brick', 'left', 'top');
    for (let u = -3; u <= 3; u++) F.set(u, v, 9, S('chiseled_stone_bricks'));
  }
  // 올려진 내리닫이 창살
  for (let u = -1; u <= 1; u++) for (let y = 7; y <= 8; y++) F.set(u, -2, y, S('iron_bars'));
  for (let u = -2; u <= 2; u++) F.set(u, -2, 6, S('iron_bars'));
  // 흉벽 (중앙부)
  for (let u = -3; u <= 3; u++) for (const v of [-4, 7]) {
    if ((u + 10) % 2 === 0) { F.set(u, v, topC + 1, mat); F.set(u, v, topC + 2, S('stone_brick_slab')); } else F.set(u, v, topC + 1, S('stone_brick_slab'));
  }
  // 양쪽 탑: 코벨 + 흉벽 + 뾰족 지붕
  for (const s of [-1, 1]) {
    const u0 = s < 0 ? -10 : 4, u1 = s < 0 ? -4 : 10;
    for (let u = u0 - 1; u <= u1 + 1; u++) for (let v = -5; v <= 4; v++) {
      const edge = u === u0 - 1 || u === u1 + 1 || v === -5 || v === 4;
      if (!edge) continue;
      const fac = u === u0 - 1 ? 'right' : u === u1 + 1 ? 'left' : v === -5 ? 'back' : 'front';
      F.stairs(u, v, topT - 1, 'stone_brick', fac, 'top');
      F.set(u, v, topT, mat);
      if ((u + v) % 2 === 0) F.set(u, v, topT + 1, mat); else F.slab(u, v, topT + 1, 'stone_brick');
    }
    // 피라미드 지붕
    for (let l = 0; l < 6; l++) {
      for (let u = u0 + l; u <= u1 - l; u++) for (let v = -4 + l; v <= 3 - l; v++) {
        const e = u === u0 + l || u === u1 - l || v === -4 + l || v === 3 - l;
        if (!e) continue;
        const fac = u === u0 + l ? 'right' : u === u1 - l ? 'left' : v === -4 + l ? 'back' : 'front';
        F.stairs(u, v, topT + 2 + l, 'deepslate_tile', fac);
      }
    }
    const cu = (u0 + u1) / 2;
    F.set(cu, -0.5, topT + 8, S('deepslate_tiles'));
    F.set(cu, 0, topT + 8, S('deepslate_tiles'));
    F.set(cu, 0, topT + 9, S('dark_oak_fence')); F.set(cu, 0, topT + 10, S('dark_oak_fence'));
    // 화살 구멍, 창
    for (const y of [8, 13, 18]) { F.set(s * 7, -4, y, AIR); F.set(s * 7, -4, y + 1, AIR); }
    // 깃발 천
    for (let y = 12; y <= 20; y++) F.set(s * 7, -5, y, S(o.banner ?? 'red_wool'));
    F.set(s * 7, -5, 21, S('dark_oak_fence'));
  }
  // 문 위 문장(금)
  F.set(0, -4, 11, S('gold_block')); F.set(-1, -4, 11, S('yellow_wool')); F.set(1, -4, 11, S('yellow_wool'));
  // 등불
  for (const u of [-3, 3]) { F.set(u, -5, 5, S('dark_oak_fence')); F.lantern(u, -5, 4, true); F.set(u, 10, 5, S('dark_oak_fence')); F.lantern(u, 10, 4, true); }
}
