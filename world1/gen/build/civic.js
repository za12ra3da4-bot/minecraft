// =====================================================================
//  광장 · 시청 · 여관 · 길드 회관 · 강 항구 · 배 · 돌다리
// =====================================================================
import { S, AIR, mix, Frame, disc, coneRoof, matBlock } from './lib.js';
import { set, get, col, height, surf, reserved, H, setGround, waterTop, inside } from '../world.js';
import { house, chimneys } from './house.js';
import { lampPost, PAVE } from './paint.js';
import { CITY, SQUARE } from '../plan.js';
import { mulberry } from '../noise.js';
import { riverDist } from '../terrain.js';

const Y = CITY.y;

// ── 광장
export function buildSquare() {
  const { x0, z0, x1, z1 } = SQUARE;
  const cx = 0, cz = 39;
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const c = col(x, z);
    setGround(x, z, Y);
    const d = Math.hypot(x - cx, z - cz);
    let b;
    const border = x <= x0 + 1 || x >= x1 - 1 || z <= z0 + 1 || z >= z1 - 1;
    if (border) b = S('stone_bricks');
    else if (Math.abs(Math.abs(x - cx) - Math.abs(z - cz)) <= 0.5 && d > 12) b = S('stone_bricks');
    else if (d < 22) b = [S('polished_andesite'), S('smooth_stone'), S('stone_bricks')][Math.floor(d / 2.5) % 3];
    else b = PAVE.plaza(x, Y, z);
    surf[c] = b;
    reserved[c] = 3;
  }
  // 분수
  disc(cx, cz, 9.3, (x, z, d) => {
    if (d > 8) { set(x, Y, z, S('stone_bricks')); set(x, Y + 1, z, S('stone_brick_slab')); }
    else { set(x, Y, z, S('water', { level: '0' })); set(x, Y - 1, z, S('water', { level: '0' })); set(x, Y - 2, z, S('stone_bricks')); }
  });
  disc(cx, cz, 2.4, (x, z) => { for (let y = Y - 1; y <= Y + 4; y++) set(x, y, z, S('stone_bricks')); });
  disc(cx, cz, 4.4, (x, z, d) => { if (d > 3.3) set(x, Y + 4, z, S('stone_brick_slab', { type: 'top' })); else if (d > 1.5) set(x, Y + 4, z, S('water', { level: '0' })); });
  disc(cx, cz, 1.3, (x, z) => { for (let y = Y + 4; y <= Y + 7; y++) set(x, y, z, S('polished_andesite')); });
  set(cx, Y + 8, cz, S('chiseled_stone_bricks')); set(cx, Y + 9, cz, S('gold_block')); set(cx, Y + 10, cz, S('water', { level: '0' }));
  for (const [dx, dz] of [[3, 0], [-3, 0], [0, 3], [0, -3]]) set(cx + dx, Y + 5, cz + dz, S('water', { level: '0' }));
  // 벤치 · 가로등 · 화단 나무
  for (const [dx, dz, f] of [[0, -13, 'south'], [0, 13, 'north'], [-13, 0, 'east'], [13, 0, 'west']]) {
    for (let k = -2; k <= 2; k++) set(cx + dx + (dz ? k : 0), Y + 1, cz + dz + (dx ? k : 0), S('dark_oak_stairs', { facing: f }));
  }
  for (const [dx, dz] of [[-11, -11], [11, -11], [-11, 11], [11, 11]]) lampPost(cx + dx, cz + dz);
  for (const [tx, tz] of [[x0 + 5, z0 + 5], [x1 - 5, z0 + 5], [x0 + 5, z1 - 5], [x1 - 5, z1 - 5]]) {
    disc(tx, tz, 2.4, (x, z, d) => { set(x, Y + 1, z, d > 1.4 ? S('stone_brick_slab') : S('grass_block')); if (d <= 1.4) set(x, Y, z, S('dirt')); });
    for (let y = Y + 2; y <= Y + 6; y++) set(tx, y, tz, S('oak_log', { axis: 'y' }));
    disc(tx, tz, 3.6, (x, z, d) => { for (let y = Y + 5; y <= Y + 9; y++) if (d + Math.abs(y - Y - 7) * 0.8 < 3.6 && get(x, y, z) === AIR) set(x, y, z, S(y === Y + 9 && d < 1 ? 'flowering_azalea_leaves' : 'oak_leaves', { persistent: 'true' })); });
  }
  // 시장 노점 (남·북 줄)
  const r = mulberry(77);
  const goods = ['hay_block', 'pumpkin', 'crafting_table', 'bookshelf', 'hay_block', 'pumpkin'];
  const cols = [['red_wool', 'white_wool'], ['blue_wool', 'white_wool'], ['yellow_wool', 'green_wool'], ['purple_wool', 'white_wool'], ['green_wool', 'white_wool'], ['red_wool', 'yellow_wool']];
  let i = 0;
  for (const [sz, face] of [[z0 + 4, 'south'], [z1 - 7, 'north']]) {
    for (let sx = x0 + 11; sx <= x1 - 14; sx += 7) {
      if (Math.abs(sx + 2 - cx) < 5) continue;
      const cc = cols[i % cols.length];
      for (const [px, pz] of [[sx, sz], [sx + 4, sz], [sx, sz + 3], [sx + 4, sz + 3]]) for (let y = Y + 1; y <= Y + 3; y++) set(px, y, pz, S('spruce_fence'));
      for (let px = sx - 1; px <= sx + 5; px++) for (let pz = sz - 1; pz <= sz + 4; pz++) {
        const edge = face === 'south' ? pz === sz + 4 : pz === sz - 1;
        set(px, Y + 4 + (edge ? 0 : 0), pz, S(cc[(px - sx + 10) % 2]));
      }
      const fz = face === 'south' ? sz + 3 : sz;
      for (let px = sx + 1; px <= sx + 3; px++) { set(px, Y + 1, fz, S('spruce_planks')); const gd = goods[(((px + i) % goods.length) + goods.length) % goods.length]; set(px, Y + 2, fz, S(gd, gd === 'hay_block' ? { axis: 'y' } : null)); }
      set(sx + 2, Y + 3, face === 'south' ? sz + 1 : sz + 2, S('lantern', { hanging: 'true' }));
      i++;
    }
  }
}

// ── 시청: 광장 서쪽, 정면 동쪽
export function buildTownHall() {
  const info = house(-40, Y, 10, 'east', 25, 24, { style: 'stone', floors: 3, frontGable: false, chimney: true, seed: 7001, doorU: 12 });
  // 시계탑 (정면 가운데, 앞으로 2칸)
  const F = new Frame(-40, Y, 10, 'east');
  const M = mix([['stone_bricks', 7], ['mossy_stone_bricks', 0.7], ['cracked_stone_bricks', 0.7]], 702);
  const top = 34;
  for (let u = 9; u <= 15; u++) for (let v = -3; v <= 3; v++) for (let y = 1; y <= top; y++) {
    const e = u === 9 || u === 15 || v === -3 || v === 3;
    const corner = (u === 9 || u === 15) && (v === -3 || v === 3);
    if (e) F.set(u, v, y, corner ? S('polished_andesite') : (y % 8 === 0 ? S('polished_andesite') : M));
    else F.set(u, v, y, y % 8 === 0 ? S('spruce_planks') : AIR);
  }
  // 아치 입구
  for (let u = 11; u <= 13; u++) for (let y = 1; y <= 4; y++) F.set(u, -3, y, AIR);
  F.stairs(11, -3, 4, 'stone_brick', 'right', 'top'); F.stairs(13, -3, 4, 'stone_brick', 'left', 'top');
  // 시계판 (정면)
  for (let du = -2; du <= 2; du++) for (let dy = -2; dy <= 2; dy++) {
    const d = Math.hypot(du, dy);
    if (d > 2.6) continue;
    F.set(12 + du, -4, 26 + dy, d > 1.9 ? S('gold_block') : S('calcite'));
  }
  F.set(12, -5, 26, S('black_wool')); F.set(12, -5, 27, S('black_wool')); F.set(13, -5, 26, S('black_wool'));
  // 종루 + 지붕
  for (let u = 10; u <= 14; u += 2) for (const v of [-3, 3]) for (let y = top - 6; y <= top - 2; y++) F.set(u + 0, v, y, u === 12 ? AIR : F.get(u, v, y));
  for (let y = top - 6; y <= top - 2; y++) { F.set(9, 0, y, AIR); F.set(15, 0, y, AIR); F.set(12, -3, y, AIR); F.set(12, 3, y, AIR); }
  F.set(12, 0, top - 3, S('gold_block'));
  for (let l = 0; l < 7; l++) for (let u = 8 + l; u <= 16 - l; u++) for (let v = -4 + l; v <= 4 - l; v++) {
    const e = u === 8 + l || u === 16 - l || v === -4 + l || v === 4 - l;
    if (!e) continue;
    if (u === 16 - l && u === 8 + l) { F.set(u, v, top + 1 + l, S('deepslate_tiles')); continue; }
    F.stairs(u, v, top + 1 + l, 'deepslate_tile', u === 8 + l ? 'right' : u === 16 - l ? 'left' : v === -4 + l ? 'back' : 'front');
  }
  F.set(12, 0, top + 8, S('deepslate_tiles')); F.set(12, 0, top + 9, S('dark_oak_fence')); F.set(12, 0, top + 10, S('gold_block'));
  // 깃발
  for (const u of [5, 19]) for (let y = 7; y <= 14; y++) F.set(u, -1, y, S(y % 4 === 0 ? 'yellow_wool' : 'blue_wool'));
  for (let x = -40; x >= -66; x--) for (let z = 8; z <= 36; z++) reserved[col(x, z)] = 3;
  return info;
}

export function buildTavern() {
  // 여관 "황금 그리핀" — 동쪽 대로 북쪽, 정면 남쪽
  house(62, Y, 30, 'south', 22, 18, { style: 'tudor', floors: 3, frontGable: false, chimney: true, seed: 7101, jetty: true });
  const F = new Frame(62, Y, 30, 'south');
  // 간판 들보 + 매달린 금 간판
  F.log(4, -2, 7, 'dark_oak_log', 'v'); F.log(4, -3, 7, 'dark_oak_log', 'v');
  F.set(4, -3, 6, S('chain', { axis: 'y' })); F.set(4, -3, 5, S('gold_block'));
  // 바깥 테이블
  for (const u of [3, 8, 13, 18]) { F.set(u, -3, 1, S('spruce_fence')); F.set(u, -3, 2, S('spruce_slab', { type: 'bottom' })); F.stairs(u - 1, -3, 1, 'spruce', 'right'); F.stairs(u + 1, -3, 1, 'spruce', 'left'); }
  for (let x = 40; x <= 63; x++) for (let z = 10; z <= 33; z++) reserved[col(x, z)] = 3;
  // 길드 회관 — 서쪽 대로 남쪽, 정면 북쪽
  house(-64, Y, 46, 'north', 24, 19, { style: 'brick', floors: 3, frontGable: false, chimney: true, seed: 7201 });
  for (let x = -66; x <= -38; x++) for (let z = 44; z <= 68; z++) reserved[col(x, z)] = 3;
}

// ── 배 (코그선). 뱃머리 방향 dir: 'north'|'south'|'east'|'west'
export function ship(x, z, dir, L = 22, o = {}) {
  const wl = 63;
  const F = new Frame(x, wl, z, dir); // u: 우현, v: 선미 방향(뒤)
  const half = L / 2;
  for (let v = -half; v <= half; v++) {
    const t = Math.abs(v) / half;
    const beam = Math.max(1, Math.round(3.4 * Math.sqrt(1 - Math.min(1, t) ** 2.6)));
    const bow = v < 0 ? (t > 0.7 ? Math.round((t - 0.7) * 10) : 0) : (t > 0.75 ? Math.round((t - 0.75) * 8) : 0);
    for (let u = -beam; u <= beam; u++) {
      const edge = Math.abs(u) === beam;
      F.set(u, v, -1, S('dark_oak_planks'));
      if (Math.abs(u) < beam) F.set(u, v, 0, S('spruce_planks'));
      if (edge) for (let y = 0; y <= 2 + bow; y++) F.set(u, v, y, S(y === 1 ? 'dark_oak_planks' : 'spruce_planks'));
      if (Math.abs(u) < beam - 0) F.set(u, v, -2, S('dark_oak_planks'));
    }
    if (Math.abs(v) >= half - 1) for (let u = -beam; u <= beam; u++) for (let y = 0; y <= 2 + bow; y++) F.set(u, v, y, S('spruce_planks'));
  }
  // 선미루 (뒤 갑판 성)
  for (let v = Math.round(half) - 5; v <= Math.round(half) - 1; v++) for (let u = -2; u <= 2; u++) {
    F.set(u, v, 3, S('spruce_planks'));
    if (Math.abs(u) === 2 || v === Math.round(half) - 5) F.set(u, v, 4, S('spruce_fence'));
  }
  for (let u = -1; u <= 1; u++) F.set(u, Math.round(half) - 5, 1, S('spruce_door', { facing: F.dir('front'), half: 'lower', hinge: 'left', open: 'false' })), F.set(u, Math.round(half) - 5, 2, u === 0 ? S('spruce_door', { facing: F.dir('front'), half: 'upper', hinge: 'left', open: 'false' }) : S('spruce_planks'));
  // 돛대 + 돛
  const mv = -1;
  for (let y = 0; y <= 17; y++) F.set(0, mv, y, S('spruce_log', { axis: 'y' }));
  F.log(-5, mv, 15, 'spruce_log', 'u'); for (let u = -4; u <= 4; u++) F.log(u, mv, 15, 'spruce_log', 'u');
  const sail = o.sail ?? ['white_wool', 'red_wool'];
  for (let u = -4; u <= 4; u++) for (let y = 7; y <= 14; y++) F.set(u, mv - (Math.abs(u) < 3 && y > 8 && y < 14 ? 1 : 0), y, S(sail[(Math.abs(u) <= 1 && o.stripe !== false) ? 1 : 0]));
  for (let u = -1; u <= 1; u++) F.set(u, mv, 18, S('spruce_slab')); F.set(0, mv, 19, S('spruce_fence')); F.set(0, mv, 20, S(sail[1]));
  // 뱃머리 기울어진 돛대, 등
  for (let k = 1; k <= 4; k++) F.set(0, -half - k, 2 + Math.floor(k / 2), S('spruce_fence'));
  F.lantern(0, Math.round(half) - 1, 5, false);
}

// ── 돌다리 (x 방향 또는 z 방향)
export function stoneBridge(ax, az, bx, bz, w = 7, deck = 68) {
  const L = Math.round(Math.hypot(bx - ax, bz - az));
  const tx = (bx - ax) / L, tz = (bz - az) / L;
  const nx = -tz, nz = tx;
  const M = mix([['stone_bricks', 5], ['mossy_stone_bricks', 1], ['cracked_stone_bricks', 1]], 801);
  for (let i = 0; i <= L; i++) {
    const cx = ax + tx * i, cz = az + tz * i;
    const arch = (i % 12);
    const pier = arch <= 2 || arch >= 11;
    for (let k = -Math.floor(w / 2); k <= Math.floor(w / 2); k++) {
      const x = Math.round(cx + nx * k), z = Math.round(cz + nz * k);
      const g = H(x, z);
      // 아치 아래 공간
      const archTop = pier ? deck - 1 : deck - 1 - Math.round(4 * Math.sin(((arch - 2) / 9) * Math.PI) * 0.9) - 1;
      const bottom = pier ? Math.min(g, 56) : archTop;
      for (let y = bottom; y <= deck; y++) set(x, y, z, M(x, y, z));
      if (!pier) set(x, archTop, z, S('stone_brick_stairs', { facing: Math.abs(tx) > Math.abs(tz) ? (arch < 6 ? (tx > 0 ? 'east' : 'west') : (tx > 0 ? 'west' : 'east')) : (arch < 6 ? (tz > 0 ? 'south' : 'north') : (tz > 0 ? 'north' : 'south')), half: 'top' }));
      set(x, deck, z, S(Math.abs(k) === Math.floor(w / 2) ? 'stone_bricks' : 'polished_andesite'));
      if (Math.abs(k) === Math.floor(w / 2)) { set(x, deck + 1, z, S('stone_brick_wall')); if (i % 12 === 0) { set(x, deck + 2, z, S('stone_brick_wall')); set(x, deck + 3, z, S('lantern', { hanging: 'false' })); } }
      else for (let y = deck + 1; y <= deck + 4; y++) set(x, y, z, AIR);
      if (inside(x, z)) reserved[col(x, z)] = 3;
    }
  }
}

// ── 항구 (동문 밖, 강 서안)
export function buildHarbor(riverPath) {
  // 강 서쪽 둑 위치 찾기: 각 z 에서 물이 시작되는 x
  const bank = z => { for (let x = 208; x < 320; x++) if (inside(x, z) && waterTop[col(x, z)] > height[col(x, z)]) return x; return 240; };
  const r = mulberry(91);
  // 부두: 둑을 따라 널판 산책로 + 잔교
  for (let z = -40; z <= 115; z++) {
    const bx = bank(z);
    for (let x = bx - 3; x <= bx; x++) { if (!inside(x, z)) continue; setGround(x, z, Math.max(height[col(x, z)], 64)); surf[col(x, z)] = S('spruce_planks'); reserved[col(x, z)] = 3; }
    set(bx + 1, 64, z, S('spruce_planks')); set(bx + 1, 63, z, S('spruce_log', { axis: 'y' }));
    if (z % 4 === 0) set(bx + 1, 65, z, S('spruce_fence'));
    if ((z + 40) % 22 === 0 && z > -35 && z < 110) {
      // 잔교
      for (let x = bx + 1; x <= bx + 9; x++) for (let dz = -1; dz <= 1; dz++) {
        set(x, 64, z + dz, S('spruce_planks'));
        if (Math.abs(dz) === 1 && x % 3 === 0) for (let y = 55; y <= 63; y++) set(x, y, z + dz, S('spruce_log', { axis: 'y' }));
        if (Math.abs(dz) === 1 && x % 3 === 0) set(x, 65, z + dz, S('spruce_fence'));
      }
      set(bx + 9, 66, z, S('spruce_fence')); set(bx + 9, 67, z, S('lantern', { hanging: 'false' })); set(bx + 9, 65, z, S('spruce_fence'));
    }
    if (z % 11 === 0) lampPost(bx - 3, z, 'wood');
  }
  // 창고 (둑과 성벽 사이)
  const spots = [[-36, 12], [-18, 13], [58, 12], [76, 14], [96, 12]];
  for (const [z, w] of spots) {
    const bx = bank(z);
    const front = bx - 5;
    house(front, 72, z, 'east', w, 11, { style: r() < 0.5 ? 'brick' : 'stone', floors: 2, frontGable: true, chimney: false, seed: 8000 + z });
  }
  // 배 3척
  ship(bank(10) + 16, 10, 'north', 24, { sail: ['white_wool', 'red_wool'] });
  ship(bank(80) + 15, 80, 'south', 20, { sail: ['white_wool', 'blue_wool'] });
  ship(bank(-25) + 14, -25, 'north', 18, { sail: ['white_wool', 'yellow_wool'], stripe: false });
  // 기중기
  const cz = 45, cx = bank(cz) - 1;
  for (let y = 65; y <= 76; y++) set(cx, y, cz, S('spruce_log', { axis: 'y' }));
  for (let x = cx; x <= cx + 8; x++) set(x, 77, cz, S('spruce_log', { axis: 'x' }));
  for (let y = 70; y <= 76; y++) set(cx + 8, y, cz, S('chain', { axis: 'y' }));
  set(cx + 8, 69, cz, S('hay_block', { axis: 'y' }));
  for (let k = 1; k <= 5; k++) set(cx + k, 77 - k, cz, S('spruce_fence'));
  return bank;
}
