// =====================================================================
//  성 알데릭 대성당 — 광장 동쪽.  입구: 서쪽(광장), 제단: 동쪽
//   x 44..134, z 44..88
// =====================================================================
import { S, AIR, mix, disc, coneRoof } from './lib.js';
import { set, get, col, height, reserved, H, setGround, surf } from '../world.js';
import { CITY } from '../plan.js';

const M = mix([['stone_bricks', 8], ['mossy_stone_bricks', 0.6], ['cracked_stone_bricks', 0.8], ['polished_andesite', 0.5]], 601);
const TRIM = S('polished_andesite'), CHIS = S('chiseled_stone_bricks');
const GLASS = ['red_stained_glass_pane', 'blue_stained_glass_pane', 'yellow_stained_glass_pane', 'purple_stained_glass_pane', 'cyan_stained_glass_pane', 'blue_stained_glass_pane'];
const inv = { north: 'south', south: 'north', east: 'west', west: 'east' };

function gothicWindow(x, y, z, h, out, axis, wide = 1, seed = 0) {
  // axis: 벽이 뻗은 방향 ('x' 또는 'z')
  for (let k = 0; k < h; k++) for (let w = -Math.floor(wide / 2); w <= Math.floor(wide / 2); w++) {
    const g = GLASS[(k + seed + Math.abs(w)) % GLASS.length];
    if (axis === 'x') set(x + w, y + k, z, S(g)); else set(x, y + k, z + w, S(g));
  }
  // 뾰족 아치 머리
  const hw = Math.floor(wide / 2);
  if (axis === 'x') { set(x - hw, y + h, z, S('stone_brick_stairs', { facing: 'east', half: 'top' })); set(x + hw, y + h, z, S('stone_brick_stairs', { facing: 'west', half: 'top' })); if (hw) set(x, y + h, z, S(GLASS[seed % GLASS.length])); set(x, y + h + 1, z, CHIS); }
  else { set(x, y + h, z - hw, S('stone_brick_stairs', { facing: 'south', half: 'top' })); set(x, y + h, z + hw, S('stone_brick_stairs', { facing: 'north', half: 'top' })); if (hw) set(x, y + h, z, S(GLASS[seed % GLASS.length])); set(x, y + h + 1, z, CHIS); }
}

function gableRoofX(x0, x1, z0, z1, y0, mat, fillGable) {
  // 용마루가 x 방향
  let y = y0;
  for (let l = 0; ; l++) {
    const a = z0 + l, b = z1 - l;
    if (a > b) break;
    for (let x = x0; x <= x1; x++) {
      if (a === b) { set(x, y, a, S('deepslate_tiles')); set(x, y + 1, a, S('deepslate_tile_slab')); }
      else { set(x, y, a, S(`${mat}_stairs`, { facing: 'south' })); set(x, y, b, S(`${mat}_stairs`, { facing: 'north' })); for (let z = a + 1; z < b; z++) if (x === x0 + 1 || x === x1 - 1) set(x, y, z, fillGable(x, y, z)); }
    }
    y++;
  }
  return y;
}
function gableRoofZ(z0, z1, x0, x1, y0, mat, fillGable) {
  let y = y0;
  for (let l = 0; ; l++) {
    const a = x0 + l, b = x1 - l;
    if (a > b) break;
    for (let z = z0; z <= z1; z++) {
      if (a === b) { set(a, y, z, S('deepslate_tiles')); set(a, y + 1, z, S('deepslate_tile_slab')); }
      else { set(a, y, z, S(`${mat}_stairs`, { facing: 'east' })); set(b, y, z, S(`${mat}_stairs`, { facing: 'west' })); for (let x = a + 1; x < b; x++) if (z === z0 + 1 || z === z1 - 1) set(x, y, z, fillGable(x, y, z)); }
    }
    y++;
  }
  return y;
}

function solidBox(x0, x1, z0, z1, yb, yt, hollow = true) {
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const e = x === x0 || x === x1 || z === z0 || z === z1;
    for (let y = yb - 4; y <= yt; y++) {
      if (y <= yb) { set(x, y, z, M(x, y, z)); continue; }
      if (e || !hollow) set(x, y, z, M(x, y, z));
      else set(x, y, z, AIR);
    }
  }
}

function spireTower(x0, x1, z0, z1, yb, yt, spireH, sides) {
  solidBox(x0, x1, z0, z1, yb, yt);
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  // 층마다 띠, 모서리 버팀
  for (let y = yb + 8; y <= yt; y += 10) for (let x = x0 - 1; x <= x1 + 1; x++) for (let z = z0 - 1; z <= z1 + 1; z++) {
    const e = x === x0 - 1 || x === x1 + 1 || z === z0 - 1 || z === z1 + 1;
    if (e) set(x, y, z, S('stone_brick_slab', { type: 'top' }));
  }
  for (const [x, z] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1]]) for (let y = yb; y <= yt + 3; y++) { set(x, y, z, M(x, y, z)); }
  for (const [x, z] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1]]) { set(x, yt + 4, z, S('stone_brick_wall')); set(x, yt + 5, z, S('stone_brick_wall')); set(x, yt + 6, z, S('dark_oak_fence')); }
  // 종루 창 (각 면 2개, 긴 아치)
  for (const s of sides) {
    for (const off of [-2, 2]) {
      if (s === 'north') { for (let y = yt - 9; y <= yt - 3; y++) set(Math.round(cx + off), y, z0, AIR); set(Math.round(cx + off), yt - 2, z0, CHIS); }
      if (s === 'south') { for (let y = yt - 9; y <= yt - 3; y++) set(Math.round(cx + off), y, z1, AIR); set(Math.round(cx + off), yt - 2, z1, CHIS); }
      if (s === 'west') { for (let y = yt - 9; y <= yt - 3; y++) set(x0, y, Math.round(cz + off), AIR); set(x0, yt - 2, Math.round(cz + off), CHIS); }
      if (s === 'east') { for (let y = yt - 9; y <= yt - 3; y++) set(x1, y, Math.round(cz + off), AIR); set(x1, yt - 2, Math.round(cz + off), CHIS); }
    }
  }
  // 흉벽
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const e = x === x0 || x === x1 || z === z0 || z === z1;
    if (e && (x + z) % 2 === 0) set(x, yt + 1, z, M(x, yt + 1, z));
    else if (e) set(x, yt + 1, z, S('stone_brick_slab'));
    else set(x, yt, z, S('stone_bricks'));
  }
  // 첨탑
  const r = (x1 - x0) / 2 - 0.6;
  const top = coneRoof(Math.round(cx), yt + 1, Math.round(cz), r, 'deepslate_tile', spireH / r, null);
  set(Math.round(cx), top + 1, Math.round(cz), S('gold_block'));
  for (let k = 2; k <= 5; k++) set(Math.round(cx), top + k, Math.round(cz), S('gold_block'));
  set(Math.round(cx) - 1, top + 4, Math.round(cz), S('gold_block')); set(Math.round(cx) + 1, top + 4, Math.round(cz), S('gold_block'));
  return top;
}

export function buildCathedral() {
  const B = CITY.y;
  // 터
  for (let x = 38; x <= 140; x++) for (let z = 40; z <= 92; z++) { setGround(x, z, B, S('stone_bricks')); surf[col(x, z)] = (x + z) % 3 ? S('polished_andesite') : S('stone_bricks'); reserved[col(x, z)] = 3; }

  // ── 신랑(nave) x 58..122, z 58..74, 벽 높이 26
  const NT = B + 26;
  solidBox(58, 122, 58, 74, B, NT);
  // ── 측랑 z 50..57 / 75..82, 높이 15
  const AT = B + 15;
  solidBox(58, 122, 50, 58, B, AT); solidBox(58, 122, 74, 82, B, AT);
  for (let x = 59; x <= 121; x++) for (let y = B + 1; y <= AT; y++) { set(x, y, 58, AIR); set(x, y, 74, AIR); } // 아케이드 열기
  for (let x = 60; x <= 120; x += 6) for (let y = B + 1; y <= AT; y++) { set(x, y, 58, M(x, y, 58)); set(x, y, 74, M(x, y, 74)); } // 기둥
  // 측랑 외팔 지붕 (한쪽 경사)
  for (let x = 57; x <= 123; x++) {
    for (let k = 0; k <= 8; k++) { set(x, AT + 1 + Math.floor(k * 0.9), 49 + k, S('deepslate_tile_stairs', { facing: 'south' })); set(x, AT + 1 + Math.floor(k * 0.9), 83 - k, S('deepslate_tile_stairs', { facing: 'north' })); }
  }
  // 창: 측랑 벽, 고창(clerestory)
  let sd = 0;
  for (let x = 63; x <= 117; x += 6) {
    gothicWindow(x, B + 4, 50, 7, 'north', 'x', 1, sd); gothicWindow(x, B + 4, 82, 7, 'south', 'x', 1, sd + 2);
    gothicWindow(x, B + 16, 58, 7, 'north', 'x', 3, sd + 1); gothicWindow(x, B + 16, 74, 7, 'south', 'x', 3, sd + 3);
    sd++;
  }
  // 비연 버트레스
  for (let x = 60; x <= 120; x += 6) {
    for (const [pz, dz] of [[47, 1], [85, -1]]) {
      for (let y = B - 2; y <= B + 21; y++) { set(x, y, pz, M(x, y, pz)); set(x, y, pz + dz, M(x, y, pz + dz)); }
      set(x, B + 22, pz, S('stone_brick_wall')); set(x, B + 23, pz, S('stone_brick_wall')); set(x, B + 24, pz, S('dark_oak_fence'));
      // 아치: 기둥 꼭대기 → 신랑 벽
      for (let k = 0; k <= 9; k++) {
        const z = pz + dz * (2 + k), y = B + 19 + Math.round(k * 0.55);
        const wall = dz > 0 ? 58 : 74;
        if ((dz > 0 && z >= wall) || (dz < 0 && z <= wall)) break;
        set(x, y, z, M(x, y, z));
        set(x, y - 1, z, S('stone_brick_stairs', { facing: dz > 0 ? 'south' : 'north', half: 'top' }));
      }
    }
  }
  // 신랑 지붕 (가파른 박공)
  gableRoofX(57, 123, 57, 75, NT + 1, 'deepslate_tile', M);

  // ── 익랑(transept) x 100..112, z 42..90
  const TT = B + 26;
  solidBox(100, 112, 42, 90, B, TT);
  for (let z = 43; z <= 89; z++) for (let y = B + 1; y <= TT - 1; y++) for (let x = 101; x <= 111; x++) set(x, y, z, AIR);
  gableRoofZ(41, 91, 99, 113, TT + 1, 'deepslate_tile', M);
  // 익랑 끝 장미창
  for (const zz of [42, 90]) {
    disc(106, 0, 4.6, (x, dz, d) => { const y = B + 17 + dz; const g = d < 1.2 ? 'yellow_stained_glass_pane' : (Math.round(Math.atan2(dz, x - 106) * 4 / Math.PI) % 2 ? 'blue_stained_glass_pane' : 'red_stained_glass_pane'); set(x, y, zz, d > 4 ? CHIS : S(g)); });
    gothicWindow(103, B + 4, zz, 8, zz < 60 ? 'north' : 'south', 'x', 1, 1); gothicWindow(109, B + 4, zz, 8, zz < 60 ? 'north' : 'south', 'x', 1, 3);
    for (let x = 104; x <= 108; x++) for (let y = B + 1; y <= B + 5; y++) set(x, y, zz, (x === 104 || x === 108) || y === B + 5 ? M(x, y, zz) : AIR);
  }

  // ── 교차부 탑 + 첨탑
  const top = spireTower(100, 112, 60, 72, TT, B + 44, 26, ['north', 'south', 'east', 'west']);

  // ── 앱스(apse) 동쪽 반원
  disc(122, 66, 9.3, (x, z, d) => {
    if (x < 122) return;
    for (let y = B - 3; y <= B + 22; y++) set(x, y, z, d > 8 ? M(x, y, z) : (y <= B ? M(x, y, z) : AIR));
  });
  for (let q = -3; q <= 3; q++) { const a = q * 0.42; const x = Math.round(122 + Math.cos(a) * 9), z = Math.round(66 + Math.sin(a) * 9); for (let y = B + 6; y <= B + 15; y++) set(x, y, z, S(GLASS[(q + 3 + y) % GLASS.length])); }
  let yy = B + 23;
  for (let r = 10.2; r > 0.4; r -= 0.8) {
    disc(122, 66, r, (x, z, d, dx, dz) => {
      if (x < 122) return;
      set(x, yy, z, d > r - 1.1 ? S('deepslate_tile_stairs', { facing: Math.abs(dx) >= Math.abs(dz) ? 'west' : (dz > 0 ? 'north' : 'south') }) : S('deepslate_tiles'));
    });
    yy++;
  }

  // ── 서쪽 정면: 쌍탑 + 정문 + 장미창
  const WT = B + 46;
  spireTower(44, 54, 47, 57, B, WT, 26, ['north', 'west']);
  spireTower(44, 54, 75, 85, B, WT, 26, ['south', 'west']);
  solidBox(44, 58, 57, 75, B, B + 30);
  for (let x = 45; x <= 57; x++) for (let z = 58; z <= 74; z++) for (let y = B + 1; y <= B + 29; y++) set(x, y, z, AIR);
  // 정면 박공
  for (let l = 0; l <= 9; l++) for (let z = 57 + l; z <= 75 - l; z++) set(44, B + 31 + l, z, (z === 57 + l || z === 75 - l) ? S('stone_brick_stairs', { facing: z === 57 + l ? 'south' : 'north' }) : M(44, B + 31 + l, z));
  set(44, B + 41, 66, CHIS); set(44, B + 42, 66, S('gold_block')); set(44, B + 43, 66, S('gold_block')); set(44, B + 44, 66, S('gold_block')); set(44, B + 43, 65, S('gold_block')); set(44, B + 43, 67, S('gold_block'));
  // 장미창 (반지름 6)
  disc(66, 0, 6.4, (zc, dy, d) => {
    const z = zc, y = B + 21 + dy;
    const a = Math.atan2(dy, z - 66);
    let g;
    if (d > 5.8) g = CHIS;
    else if (d < 1.3) g = S('yellow_stained_glass_pane');
    else if (Math.abs(((a * 8 / Math.PI) % 2 + 2) % 2 - 1) < 0.25) g = S('stone_brick_wall');
    else g = S(d < 3.5 ? 'red_stained_glass_pane' : (Math.floor(a * 8 / Math.PI + 8) % 2 ? 'blue_stained_glass_pane' : 'purple_stained_glass_pane'));
    set(44, y, z, g);
  });
  // 정문: 계단식 아치
  for (let depth = 0; depth < 4; depth++) {
    const x = 44 + depth, hw = 5 - depth, h = 12 - depth;
    for (let z = 66 - hw; z <= 66 + hw; z++) for (let y = B + 1; y <= B + h; y++) {
      const inArch = Math.abs(z - 66) < hw || y < B + h - 2;
      if (inArch) set(x, y, z, AIR);
    }
    for (let z = 66 - hw; z <= 66 + hw; z++) set(x, B + h + 1, z, depth % 2 ? CHIS : TRIM);
    for (let y = B + 1; y <= B + h; y++) { set(x, y, 66 - hw - 1, depth % 2 ? TRIM : M(x, y, 66 - hw - 1)); set(x, y, 66 + hw + 1, depth % 2 ? TRIM : M(x, y, 66 + hw + 1)); }
  }
  for (let z = 64; z <= 68; z++) for (let y = B + 1; y <= B + 3; y++) set(48, y, z, S('dark_oak_planks'));
  for (const [z, hinge] of [[65, 'left'], [67, 'right']]) { set(48, B + 1, z, S('dark_oak_door', { facing: 'east', half: 'lower', hinge, open: 'false' })); set(48, B + 2, z, S('dark_oak_door', { facing: 'east', half: 'upper', hinge, open: 'false' })); }
  set(48, B + 1, 66, AIR); set(48, B + 2, 66, AIR);
  // 입구 계단 + 등
  for (let z = 58; z <= 74; z++) { set(42, B + 1, z, S('stone_brick_slab')); set(43, B + 1, z, S('stone_brick_slab', { type: 'top' })); }
  for (const z of [56, 76]) { set(41, B + 1, z, S('stone_brick_wall')); set(41, B + 2, z, S('dark_oak_fence')); set(41, B + 3, z, S('lantern', { hanging: 'false' })); }

  // ── 실내: 바닥, 제단, 신도석, 샹들리에
  for (let x = 59; x <= 121; x++) for (let z = 51; z <= 81; z++) if (get(x, B + 1, z) === AIR) set(x, B, z, ((x + z) % 2) ? S('polished_andesite') : S('calcite'));
  for (let x = 64; x <= 96; x += 2) for (const z of [60, 61, 62, 63, 69, 70, 71, 72]) set(x, B + 1, z, S('dark_oak_stairs', { facing: 'east' }));
  for (let z = 63; z <= 69; z++) { set(118, B + 1, z, S('polished_andesite')); set(119, B + 1, z, S('polished_andesite')); }
  set(118, B + 2, 66, S('gold_block'));
  for (const x of [70, 82, 94, 106]) { for (let y = B + 14; y <= B + 24; y++) set(x, y, 66, S('chain', { axis: 'y' })); set(x, B + 13, 66, S('lantern', { hanging: 'true' })); }
  return top;
}
