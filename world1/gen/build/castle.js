// =====================================================================
//  알더미어 성 — 언덕 꼭대기 (0, -112), 지면 y=100
// =====================================================================
import { S, AIR, mix, Frame, disc, coneRoof, matBlock } from './lib.js';
import { set, get, col, inside, height, surf, reserved, H, setGround } from '../world.js';
import { WALL_MIX, roundTower, gatehouse } from './walls.js';
import { house } from './house.js';
import { CASTLE } from '../plan.js';

const Y = CASTLE.top;
const KEEPMIX = mix([['stone_bricks', 7], ['mossy_stone_bricks', 0.8], ['cracked_stone_bricks', 1], ['polished_andesite', 0.4]], 501);

function hipRoof(x0, z0, x1, z1, y0, mat, maxL = 99) {
  let y = y0;
  for (let l = 0; l < maxL; l++) {
    const a0 = x0 + l, a1 = x1 - l, b0 = z0 + l, b1 = z1 - l;
    if (a0 > a1 || b0 > b1) break;
    for (let x = a0; x <= a1; x++) for (let z = b0; z <= b1; z++) {
      const e = x === a0 || x === a1 || z === b0 || z === b1;
      if (!e) continue;
      let f;
      if (a0 === a1 || b0 === b1) { set(x, y, z, S(matBlock(mat))); continue; }
      if (x === a0) f = 'east'; else if (x === a1) f = 'west'; else if (z === b0) f = 'south'; else f = 'north';
      set(x, y, z, S(`${mat}_stairs`, { facing: f, half: 'bottom' }));
    }
    y++;
  }
  return y;
}

function crenel(x0, z0, x1, z1, y, mat = KEEPMIX, corbel = true) {
  for (let x = x0 - 1; x <= x1 + 1; x++) for (let z = z0 - 1; z <= z1 + 1; z++) {
    const e = x === x0 - 1 || x === x1 + 1 || z === z0 - 1 || z === z1 + 1;
    if (!e) continue;
    const f = x === x0 - 1 ? 'east' : x === x1 + 1 ? 'west' : z === z0 - 1 ? 'south' : 'north';
    if (corbel) set(x, y - 1, z, S('stone_brick_stairs', { facing: f, half: 'top' }));
    set(x, y, z, mat(x, y, z));
    if ((x + z) % 2 === 0) { set(x, y + 1, z, mat(x, y + 1, z)); set(x, y + 2, z, S('stone_brick_slab')); } else set(x, y + 1, z, S('stone_brick_slab'));
  }
}

// 아치 창 (세로 창 + 머리 계단). 벽면 좌표와 바깥 방향
function lancet(x, y, z, h, outDir, glass = 'glass_pane') {
  for (let k = 0; k < h; k++) set(x, y + k, z, S(glass));
  const inv = { north: 'south', south: 'north', east: 'west', west: 'east' }[outDir];
  set(x, y + h, z, S('stone_brick_stairs', { facing: inv, half: 'top' }));
}

export function buildCastle() {
  const X0 = -40, X1 = 40, Z0 = -146, Z1 = -80;
  // 1) 평탄화 (올리기만)
  for (let x = X0 - 7; x <= X1 + 7; x++) for (let z = Z0 - 7; z <= Z1 + 5; z++) {
    const c = col(x, z);
    if (height[c] < Y) setGround(x, z, Y, S('grass_block'));
    else { height[c] = Y; }
    const inner = x > X0 + 3 && x < X1 - 3 && z > Z0 + 3 && z < Z1 - 3;
    if (inner) surf[c] = (Math.abs(x) <= 3 || Math.abs(z + 113) <= 2) ? S('cobblestone') : ((x * 7 + z * 3) % 11 === 0 ? S('coarse_dirt') : S('grass_block'));
    reserved[c] = 3;
  }
  // 2) 외벽 (두께 4, 높이 16)
  const TOP = Y + 16;
  for (let x = X0; x <= X1; x++) for (let z = Z0; z <= Z1; z++) {
    const onW = x <= X0 + 3 || x >= X1 - 3 || z <= Z0 + 3 || z >= Z1 - 3;
    if (!onW) continue;
    for (let y = Y - 12; y <= TOP; y++) set(x, y, z, WALL_MIX(x, y, z));
    const outer = x === X0 || x === X1 || z === Z0 || z === Z1;
    const inner = x === X0 + 3 || x === X1 - 3 || z === Z0 + 3 || z === Z1 - 3;
    if (outer) {
      if ((x + z) % 2 === 0) { set(x, TOP + 1, z, WALL_MIX(x, TOP + 1, z)); set(x, TOP + 2, z, S('stone_brick_slab')); } else set(x, TOP + 1, z, S('stone_brick_slab'));
      if ((x + z) % 10 === 0) { set(x, TOP - 5, z, AIR); set(x, TOP - 6, z, AIR); }
    } else if (inner) set(x, TOP + 1, z, S('stone_brick_wall'));
  }
  // 바깥 코벨
  for (let x = X0 - 1; x <= X1 + 1; x++) for (let z = Z0 - 1; z <= Z1 + 1; z++) {
    const e = x === X0 - 1 || x === X1 + 1 || z === Z0 - 1 || z === Z1 + 1;
    if (!e) continue;
    const f = x === X0 - 1 ? 'east' : x === X1 + 1 ? 'west' : z === Z0 - 1 ? 'south' : 'north';
    set(x, TOP - 1, z, S('stone_brick_stairs', { facing: f, half: 'top' }));
  }
  // 3) 탑
  for (const [tx, tz] of [[X0, Z0], [X1, Z0], [X0, Z1], [X1, Z1]]) roundTower(tx, tz, 7, Y + 30, { base: Y, roof: 'cone', roofMat: 'deepslate_tile', steep: 1.15, banner: [0, 8], bannerColor: 'red_wool' });
  roundTower(0, Z0, 6, Y + 26, { base: Y, roof: 'cone', roofMat: 'deepslate_tile', steep: 1.2 });
  roundTower(X0, -113, 6, Y + 24, { base: Y });
  roundTower(X1, -113, 6, Y + 24, { base: Y });
  // 4) 성문 (남쪽)
  gatehouse(0, Z1 - 2, 'south', { base: Y, banner: 'red_wool' });

  // 5) 본성 (Keep)
  const kx0 = -15, kx1 = 15, kz0 = -136, kz1 = -106, KT = Y + 44;
  for (let x = kx0; x <= kx1; x++) for (let z = kz0; z <= kz1; z++) {
    const edge = x === kx0 || x === kx1 || z === kz0 || z === kz1;
    for (let y = Y - 2; y <= KT; y++) {
      const rel = y - Y;
      if (edge) {
        let b = KEEPMIX(x, y, z);
        if (rel % 9 === 0 && rel > 0) b = S('polished_andesite');
        set(x, y, z, b);
      } else set(x, y, z, rel % 9 === 0 ? S('spruce_planks') : AIR);
    }
  }
  // 벽 기둥(버트레스) + 창
  for (let i = kx0 + 4; i <= kx1 - 4; i += 5) for (let y = Y; y <= KT - 2; y++) { set(i, y, kz0 - 1, KEEPMIX(i, y, kz0 - 1)); set(i, y, kz1 + 1, KEEPMIX(i, y, kz1 + 1)); }
  for (let i = kz0 + 4; i <= kz1 - 4; i += 5) for (let y = Y; y <= KT - 2; y++) { set(kx0 - 1, y, i, KEEPMIX(kx0 - 1, y, i)); set(kx1 + 1, y, i, KEEPMIX(kx1 + 1, y, i)); }
  for (let fl = 1; fl <= 4; fl++) {
    const y = Y + fl * 9 - 6;
    for (let i = kx0 + 6; i <= kx1 - 6; i += 5) { lancet(i + 0, y, kz0, 4, 'north'); lancet(i + 0, y, kz1, 4, 'south'); }
    for (let i = kz0 + 6; i <= kz1 - 6; i += 5) { lancet(kx0, y, i + 0, 4, 'west'); lancet(kx1, y, i + 0, 4, 'east'); }
  }
  crenel(kx0, kz0, kx1, kz1, KT + 1);
  // 높은 지붕 (중앙)
  hipRoof(kx0 + 2, kz0 + 2, kx1 - 2, kz1 - 2, KT + 1, 'deepslate_tile');
  // 모서리 첨탑
  for (const [cx, cz] of [[kx0, kz0], [kx1, kz0], [kx0, kz1], [kx1, kz1]]) {
    disc(cx, cz, 4.2, (x, z, d) => { for (let y = Y + 20; y <= KT + 8; y++) set(x, y, z, d > 2.8 ? KEEPMIX(x, y, z) : AIR); });
    disc(cx, cz, 5.2, (x, z, d, dx, dz) => { if (d > 4.3) set(x, Y + 19, z, S('stone_brick_stairs', { facing: Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south'), half: 'top' })); });
    for (let q = 0; q < 4; q++) { const a = q * Math.PI / 2 + Math.PI / 4; set(Math.round(cx + Math.cos(a) * 4), KT, Math.round(cz + Math.sin(a) * 4), S('glass_pane')); set(Math.round(cx + Math.cos(a) * 4), KT + 1, Math.round(cz + Math.sin(a) * 4), S('glass_pane')); }
    coneRoof(cx, KT + 9, cz, 5.4, 'deepslate_tile', 1.05, 'dark_oak_fence');
  }
  // 정문 + 계단 + 깃발
  for (let x = -2; x <= 2; x++) for (let y = Y + 1; y <= Y + 7; y++) set(x, y, kz1, (Math.abs(x) === 2 && y > Y + 5) || (Math.abs(x) === 1 && y > Y + 6) ? KEEPMIX(x, y, kz1) : AIR);
  set(-1, Y + 1, kz1, S('dark_oak_door', { facing: 'north', half: 'lower', hinge: 'left', open: 'false' }));
  set(-1, Y + 2, kz1, S('dark_oak_door', { facing: 'north', half: 'upper', hinge: 'left', open: 'false' }));
  set(1, Y + 1, kz1, S('dark_oak_door', { facing: 'north', half: 'lower', hinge: 'right', open: 'false' }));
  set(1, Y + 2, kz1, S('dark_oak_door', { facing: 'north', half: 'upper', hinge: 'right', open: 'false' }));
  set(0, Y + 1, kz1, AIR); set(0, Y + 2, kz1, AIR);
  for (let x = -3; x <= 3; x++) { set(x, Y + 8, kz1 + 1, S('stone_brick_stairs', { facing: 'north', half: 'top' })); }
  for (let z = kz1 + 1; z <= kz1 + 3; z++) for (let x = -3; x <= 3; x++) set(x, Y + 1, z, S('polished_andesite_slab'));
  for (const x of [-6, 6]) for (let y = Y + 12; y <= Y + 30; y++) { set(x, y, kz1 + 1, S(y % 6 === 0 ? 'yellow_wool' : 'red_wool')); }
  for (const x of [-4, 4]) { set(x, Y + 5, kz1 + 1, S('dark_oak_fence')); set(x, Y + 4, kz1 + 1, S('lantern', { hanging: 'true' })); }
  // 실내 조명
  for (let fl = 0; fl < 5; fl++) for (const [x, z] of [[-6, -128], [6, -128], [-6, -114], [6, -114]]) set(x, Y + fl * 9 + 8, z, S('lantern', { hanging: 'true' }));

  // 6) 대연회장 (동쪽) — 앞면 서쪽(마당)
  house(19, Y, -94, 'west', 33, 16, { style: 'stone', floors: 3, frontGable: false, chimney: true, seed: 9001 });
  // 7) 예배당 (서쪽)
  house(-21, Y, -122, 'east', 22, 12, { style: 'stone', floors: 2, frontGable: false, chimney: false, seed: 9002 });
  // 예배당 종탑
  for (let x = -27; x <= -23; x++) for (let z = -100; z <= -96; z++) for (let y = Y; y <= Y + 22; y++) {
    const e = x === -27 || x === -23 || z === -100 || z === -96;
    set(x, y, z, e ? (y > Y + 16 && (x === -25 || z === -98) ? AIR : KEEPMIX(x, y, z)) : AIR);
  }
  hipRoof(-28, -101, -22, -95, Y + 23, 'deepslate_tile');
  set(-25, Y + 20, -98, S('gold_block'));
  // 8) 마구간 (북쪽 벽 안쪽, 본성 서쪽)
  for (let x = -34; x <= -18; x++) {
    for (let z = Z0 + 4; z <= Z0 + 9; z++) {
      set(x, Y, z, z < Z0 + 8 ? S('hay_block', { axis: 'y' }) : S('coarse_dirt'));
      if (z === Z0 + 9 && (x + 34) % 4 === 0) for (let y = Y + 1; y <= Y + 4; y++) set(x, y, z, S('spruce_log', { axis: 'y' }));
      if (z === Z0 + 9 && (x + 34) % 4 !== 0) set(x, Y + 1, z, S('spruce_fence'));
    }
    for (let z = Z0 + 4; z <= Z0 + 10; z++) set(x, Y + 5 + (z <= Z0 + 6 ? 1 : 0) - (z >= Z0 + 9 ? 1 : 0), z, S('spruce_stairs', { facing: 'north', half: 'bottom' }));
  }
  // 9) 우물
  disc(-10, -92, 2.3, (x, z, d) => { set(x, Y, z, d < 1.3 ? S('water', { level: '0' }) : S('stone_bricks')); if (d >= 1.3) set(x, Y + 1, z, S('stone_brick_wall')); set(x, Y - 1, z, d < 1.3 ? S('water', { level: '0' }) : S('stone_bricks')); });
  for (const [x, z] of [[-12, -94], [-8, -94], [-12, -90], [-8, -90]]) for (let y = Y + 1; y <= Y + 4; y++) set(x, y, z, S('spruce_fence'));
  for (let x = -13; x <= -7; x++) for (let z = -95; z <= -89; z++) set(x, Y + 5, z, S('spruce_slab'));
  // 10) 훈련장 허수아비
  for (const [x, z] of [[26, -88], [29, -88], [32, -88]]) { set(x, Y + 1, z, S('spruce_fence')); set(x, Y + 2, z, S('hay_block', { axis: 'y' })); set(x, Y + 3, z, S('pumpkin')); }
  // 마당 나무
  for (const [x, z] of [[24, -84], [-20, -86]]) {
    for (let y = Y + 1; y <= Y + 5; y++) set(x, y, z, S('oak_log', { axis: 'y' }));
    disc(x, z, 3.2, (xx, zz, d) => { for (let y = Y + 4; y <= Y + 7; y++) if (d + Math.abs(y - Y - 5.5) * 0.9 < 3.4 && get(xx, y, zz) === AIR) set(xx, y, zz, S('oak_leaves', { persistent: 'true' })); });
  }
}
