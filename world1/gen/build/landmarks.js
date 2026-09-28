// =====================================================================
//  명소 — 마법사 탑 · 무너진 요새 · 구름 수도원 · 드워프 관문 · 등대 · 거석 원 · 감시탑
// =====================================================================
import { S, AIR, mix, Frame, disc, coneRoof } from './lib.js';
import { set, get, col, inside, height, surf, reserved, H, setGround, waterTop } from '../world.js';
import { house } from './house.js';
import { LANDMARKS } from '../plan.js';
import { mulberry, simplex, hash3 } from '../noise.js';

const leaves = n => S(n, { persistent: 'true' });
const faceTo = (dx, dz) => (Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south'));
function resv(x, z, r, v = 3) { disc(x, z, r, (xx, zz) => { if (inside(xx, zz)) reserved[col(xx, zz)] = v; }); }
function levelDisc(x, z, r, y, top = null, edge = 0) {
  disc(x, z, r + edge, (xx, zz, d) => {
    if (!inside(xx, zz)) return;
    const c = col(xx, zz);
    const wob = simplex(xx / 9, zz / 9, 1010) * Math.min(edge, 6) * 0.5;
    if (d <= r + wob) { setGround(xx, zz, y, top); reserved[c] = 3; return; }
    const t = Math.min(1, (d - r - wob) / Math.max(1, edge - wob));
    const k = t * t * (3 - 2 * t);
    const nh = Math.round(y + (height[c] - y) * k);
    if (nh !== height[c]) setGround(xx, zz, nh);
  });
}

// ── 마법사 탑
function wizardTower() {
  const { x, z } = LANDMARKS.wizard;
  const h = H(x, z);
  const M = mix([['deepslate_bricks', 5], ['polished_deepslate', 2], ['cobbled_deepslate', 1], ['deepslate_tiles', 1]], 1001);
  const TOP = h + 56;
  levelDisc(x, z, 12, h, S('moss_block'));
  disc(x, z, 7.2, (xx, zz, d) => {
    for (let y = h - 4; y <= TOP; y++) {
      if (d > 5.4) set(xx, y, zz, (y - h) % 9 === 0 ? S('polished_blackstone_bricks') : M(xx, y, zz));
      else set(xx, y, zz, (y - h) % 9 === 0 ? S('dark_oak_planks') : AIR);
    }
  });
  // 나선 창
  for (let y = h + 3; y < TOP - 4; y += 2) {
    const a = (y - h) * 0.42;
    const wx = Math.round(x + Math.cos(a) * 7), wz = Math.round(z + Math.sin(a) * 7);
    set(wx, y, wz, S('purple_stained_glass_pane')); set(wx, y + 1, wz, S('purple_stained_glass_pane'));
  }
  // 발코니 2단
  for (const by of [h + 20, h + 38]) {
    disc(x, z, 9.3, (xx, zz, d, dx, dz) => {
      if (d <= 7.2) return;
      set(xx, by, zz, S('polished_deepslate_slab', { type: 'top' }));
      if (d > 8.3) set(xx, by + 1, zz, S('iron_bars'));
      if (d > 7.3 && d < 8.3) set(xx, by - 1, zz, S('polished_deepslate_stairs', { facing: faceTo(dx, dz), half: 'top' }));
    });
    for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3; set(Math.round(x + Math.cos(a) * 8), by + 1, Math.round(z + Math.sin(a) * 8), S('lantern', { hanging: 'false' })); }
  }
  // 꼭대기: 흉벽 + 뾰족 지붕 + 수정
  disc(x, z, 8.3, (xx, zz, d, dx, dz) => {
    if (d <= 7.2) return;
    set(xx, TOP - 1, zz, S('polished_deepslate_stairs', { facing: faceTo(dx, dz), half: 'top' }));
    set(xx, TOP, zz, S('polished_blackstone_bricks'));
  });
  disc(x, z, 7.3, (xx, zz) => set(xx, TOP + 1, zz, S('dark_oak_planks')));
  const tip = coneRoof(x, TOP + 1, z, 8.6, 'deepslate_tile', 2.3, null);
  for (let k = 1; k <= 4; k++) set(x, tip + k, z, S('amethyst_block'));
  set(x, tip + 6, z, S('glowstone'));
  // 떠다니는 수정 조각
  const R = mulberry(4040);
  for (let k = 0; k < 9; k++) {
    const a = R() * Math.PI * 2, rr = 12 + R() * 7, yy = TOP - 10 + R() * 24;
    const cx = Math.round(x + Math.cos(a) * rr), cz = Math.round(z + Math.sin(a) * rr), cy = Math.round(yy);
    set(cx, cy, cz, S('amethyst_block')); set(cx, cy + 1, cz, S('amethyst_block')); if (R() < 0.5) set(cx + 1, cy, cz, S('amethyst_block'));
    set(cx, cy - 1, cz, S(R() < 0.5 ? 'glowstone' : 'amethyst_block'));
  }
  // 입구, 정원, 선착장
  for (let y = h + 1; y <= h + 3; y++) set(x, y, z + 7, AIR);
  set(x, h + 1, z + 7, S('dark_oak_door', { facing: 'north', half: 'lower', hinge: 'left', open: 'false' }));
  set(x, h + 2, z + 7, S('dark_oak_door', { facing: 'north', half: 'upper', hinge: 'left', open: 'false' }));
  set(x - 1, h + 3, z + 8, S('lantern', { hanging: 'false' })); set(x + 1, h + 3, z + 8, S('lantern', { hanging: 'false' }));
  for (let k = 0; k < 40; k++) {
    const a = R() * Math.PI * 2, rr = 8 + R() * 4, fx = Math.round(x + Math.cos(a) * rr), fz = Math.round(z + Math.sin(a) * rr);
    if (get(fx, H(fx, fz) + 1, fz) === AIR && !(waterTop[col(fx, fz)] > height[col(fx, fz)])) set(fx, H(fx, fz) + 1, fz, S(['allium', 'blue_orchid', 'lily_of_the_valley', 'azure_bluet'][k % 4]));
  }
  for (let t = 0; t < 34; t++) { const zz = z + 9 + t; if (!inside(x, zz)) break; for (let s = -1; s <= 1; s++) { const w = waterTop[col(x + s, zz)] > height[col(x + s, zz)]; if (w) set(x + s, 64, zz, S('dark_oak_planks')); else surf[col(x + s, zz)] = S('dirt_path'); } }
  resv(x, z, 16);
}

// ── 무너진 요새
function ruins() {
  const { x, z } = LANDMARKS.ruins;
  const R = mulberry(5050);
  let hs = 0; for (let k = 0; k < 9; k++) hs += H(x + (k % 3 - 1) * 20, z + (Math.floor(k / 3) - 1) * 20);
  const g = Math.round(hs / 9);
  for (let xx = x - 34; xx <= x + 34; xx++) for (let zz = z - 34; zz <= z + 34; zz++) { if (!inside(xx, zz)) continue; const c = col(xx, zz); height[c] = Math.round(height[c] * 0.3 + g * 0.7); if (waterTop[c] <= height[c]) waterTop[c] = -999; reserved[c] = 3; surf[c] = hash3(xx, 0, zz, 5) < 0.25 ? S('moss_block') : hash3(xx, 1, zz, 5) < 0.3 ? S('coarse_dirt') : S('grass_block'); }
  const M = mix([['mossy_cobblestone', 4], ['mossy_stone_bricks', 3], ['cracked_stone_bricks', 3], ['cobblestone', 2], ['stone_bricks', 1]], 1002);
  const X0 = x - 28, X1 = x + 28, Z0 = z - 28, Z1 = z + 28;
  for (let xx = X0; xx <= X1; xx++) for (let zz = Z0; zz <= Z1; zz++) {
    const onW = xx <= X0 + 2 || xx >= X1 - 2 || zz <= Z0 + 2 || zz >= Z1 - 2;
    if (!onW) continue;
    const t = (xx + zz * 3) * 0.08;
    let top = 4 + Math.round(8 * (0.5 + 0.5 * simplex(xx / 9, zz / 9, 77)));
    if (simplex(xx / 5, zz / 5, 78) > 0.45) top = 0; // 무너진 틈
    const hh = H(xx, zz);
    for (let y = hh - 2; y <= hh + top; y++) set(xx, y, zz, M(xx, y, zz));
    if (top > 3 && (xx + zz) % 2 === 0 && (xx === X0 || xx === X1 || zz === Z0 || zz === Z1)) set(xx, hh + top + 1, zz, S('mossy_cobblestone_wall'));
  }
  for (const [tx, tz] of [[X0, Z0], [X1, Z0], [X0, Z1], [X1, Z1]]) {
    const tt = 8 + Math.floor(R() * 12);
    disc(tx, tz, 5.3, (xx, zz, d) => {
      const hh = H(xx, zz), jag = tt - Math.floor(R() * 5);
      for (let y = hh - 2; y <= hh + jag; y++) set(xx, y, zz, d > 3.2 ? M(xx, y, zz) : AIR);
    });
  }
  // 안쪽 본성 폐허
  for (let xx = x - 10; xx <= x + 10; xx++) for (let zz = z - 8; zz <= z + 8; zz++) {
    const e = xx === x - 10 || xx === x + 10 || zz === z - 8 || zz === z + 8;
    if (!e) continue;
    const top = 3 + Math.round(10 * Math.max(0, simplex(xx / 6, zz / 6, 79) + 0.3));
    const hh = H(xx, zz);
    for (let y = hh; y <= hh + top; y++) set(xx, y, zz, M(xx, y, zz));
    if (top > 6 && (xx === x || zz === z)) { set(xx, hh + 5, zz, AIR); set(xx, hh + 6, zz, AIR); }
  }
  // 무너진 들보, 잔해, 거미줄, 나무
  for (let k = 0; k < 6; k++) { const bx = x - 8 + Math.floor(R() * 16), bz = z - 6 + Math.floor(R() * 12), hh = H(bx, bz); for (let t = 0; t < 5; t++) set(bx + t, hh + 1 + (t < 2 ? 1 : 0), bz, S('stripped_dark_oak_log', { axis: 'x' })); }
  for (let k = 0; k < 40; k++) { const bx = X0 + 3 + Math.floor(R() * 50), bz = Z0 + 3 + Math.floor(R() * 50), hh = H(bx, bz); set(bx, hh + 1, bz, M(bx, hh + 1, bz)); if (R() < 0.4) set(bx + 1, hh + 1, bz, S('cobblestone_slab')); if (R() < 0.3) set(bx, hh + 2, bz, S('mossy_cobblestone_slab')); }
  for (let k = 0; k < 18; k++) { const bx = x - 9 + Math.floor(R() * 18), bz = z - 7 + Math.floor(R() * 14), hh = H(bx, bz); if (get(bx, hh + 1, bz) === AIR) set(bx, hh + 1 + Math.floor(R() * 3), bz, S('cobweb')); }
  for (const [tx, tz] of [[x - 18, z + 14], [x + 16, z - 18], [x + 4, z + 20]]) {
    const hh = H(tx, tz);
    for (let y = hh + 1; y <= hh + 6; y++) set(tx, y, tz, S('oak_log', { axis: 'y' }));
    disc(tx, tz, 3.4, (xx, zz, d) => { for (let y = hh + 5; y <= hh + 8; y++) if (d + Math.abs(y - hh - 6.5) < 3.6 && get(xx, y, zz) === AIR) set(xx, y, zz, leaves('oak_leaves')); });
  }
}

// ── 구름 수도원
function monastery() {
  const { x, z } = LANDMARKS.monastery;
  let hs = 0, n = 0; disc(x, z, 30, (xx, zz) => { hs += H(xx, zz); n++; });
  const g = Math.round(hs / n);
  levelDisc(x, z, 40, g, S('grass_block'), 18);
  // 낮은 담장
  disc(x, z, 38.5, (xx, zz, d) => { if (d > 37.3) { set(xx, g + 1, zz, S('cobblestone')); set(xx, g + 2, zz, S('cobblestone_wall')); } });
  // 교회 (정면 남쪽) + 종탑
  house(x + 5, g, z - 6, 'south', 11, 22, { style: 'stone', floors: 2, frontGable: true, chimney: false, seed: 6001 });
  for (let dx = -3; dx <= 2; dx++) for (let dz = -3; dz <= 2; dz++) for (let y = g - 2; y <= g + 28; y++) {
    const e = dx === -3 || dx === 2 || dz === -3 || dz === 2;
    const X = x - 9 + dx, Z = z - 12 + dz;
    set(X, y, Z, e ? (y > g + 22 && (dx === 0 || dz === 0) ? AIR : S(y % 8 === 0 ? 'polished_andesite' : 'stone_bricks')) : AIR);
  }
  for (let l = 0; l < 5; l++) for (let dx = -4 + l; dx <= 3 - l; dx++) for (let dz = -4 + l; dz <= 3 - l; dz++) {
    const e = dx === -4 + l || dx === 3 - l || dz === -4 + l || dz === 3 - l;
    if (e) set(x - 9 + dx, g + 29 + l, z - 12 + dz, S('deepslate_tile_stairs', { facing: dx === -4 + l ? 'east' : dx === 3 - l ? 'west' : dz === -4 + l ? 'south' : 'north' }));
  }
  set(x - 9, g + 34, z - 12, S('gold_block')); set(x - 10, g + 34, z - 12, S('gold_block')); set(x - 9, g + 35, z - 12, S('gold_block'));
  // 회랑(클로이스터): 중앙 정원 둘레 아케이드
  const cx = x - 4, cz = z + 14, R2 = 10;
  for (let dx = -R2; dx <= R2; dx++) for (let dz = -R2; dz <= R2; dz++) {
    const X = cx + dx, Z = cz + dz;
    const ring = Math.max(Math.abs(dx), Math.abs(dz));
    if (ring === R2) { for (let y = g + 1; y <= g + 4; y++) set(X, y, Z, S('stone_bricks')); }
    else if (ring === R2 - 3) { if ((dx + dz) % 3 === 0) for (let y = g + 1; y <= g + 3; y++) set(X, y, Z, S('stone_brick_wall')); set(X, g + 4, Z, S('stone_bricks')); }
    if (ring >= R2 - 3 && ring <= R2) { set(X, g, Z, S('polished_andesite')); set(X, g + 5 + (ring >= R2 - 1 ? 0 : 1) - (ring === R2 ? 1 : 0), Z, S('spruce_stairs', { facing: Math.abs(dx) >= Math.abs(dz) ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south') })); }
    if (ring < R2 - 3) { surf[col(X, Z)] = (dx === 0 || dz === 0) ? S('gravel') : S('grass_block'); if (ring > 1 && (dx !== 0 && dz !== 0) && hash3(X, 0, Z, 9) < 0.35) set(X, g + 1, Z, S(['lily_of_the_valley', 'poppy', 'azure_bluet', 'rose_bush'][Math.floor(hash3(X, 1, Z, 9) * 3)])); }
  }
  disc(cx, cz, 1.5, (X, Z) => { set(X, g, Z, S('water', { level: '0' })); });
  for (const [dx, dz] of [[-4, -4], [4, 4]]) { for (let y = g + 1; y <= g + 5; y++) set(cx + dx, y, cz + dz, S('birch_log', { axis: 'y' })); disc(cx + dx, cz + dz, 2.5, (X, Z, d) => { for (let y = g + 4; y <= g + 7; y++) if (d + Math.abs(y - g - 5.5) < 2.8 && get(X, y, Z) === AIR) set(X, y, Z, leaves('birch_leaves')); }); }
  // 숙소
  house(x + 30, g, z + 2, 'west', 17, 9, { style: 'stone', floors: 2, frontGable: false, seed: 6002 });
}

// ── 드워프 관문: 산에 새긴 거대한 문
function dwarfGate() {
  const { x, z } = LANDMARKS.dwarf;
  const g = Math.max(H(x, z + 26), 70);
  const zf = z;
  // 앞마당 평탄화, 뒤쪽 암벽 세우기
  for (let xx = x - 64; xx <= x + 64; xx++) for (let zz = zf - 70; zz <= zf + 46; zz++) {
    if (!inside(xx, zz)) continue;
    const c = col(xx, zz);
    const dx = xx - x, dz = zz - zf;
    if (dz > 0) {
      // 앞마당: 반원형 평지, 가장자리는 원래 지형과 섞임
      const d = Math.hypot(dx * 0.85, dz);
      if (d < 30) { height[c] = g; surf[c] = Math.abs(dx) < 6 ? S('polished_andesite') : (hash3(xx, 0, zz, 12) < 0.25 ? S('cobblestone') : S('gravel')); waterTop[c] = -999; reserved[c] = 3; }
      else if (d < 46) { const t = (d - 30) / 16, k = t * t * (3 - 2 * t); height[c] = Math.round(g + (height[c] - g) * k); }
    } else {
      // 문 뒤로 솟은 암벽 (옆·뒤로 갈수록 산과 섞임)
      const e = Math.max(0, Math.abs(dx) - 22) + Math.max(0, -dz - 34) * 0.6;
      const want = g + 46 + simplex(xx / 13, zz / 13, 1011) * 7 - e * 1.5;
      if (height[c] < want) { height[c] = Math.round(want); surf[c] = hash3(xx, 1, zz, 12) < 0.3 ? S('andesite') : (height[c] > 160 && e > 4 ? S('snow_block') : S('stone')); }
      if (Math.abs(dx) < 26 && -dz < 40) reserved[c] = 3;
    }
  }
  const P = mix([['polished_deepslate', 3], ['deepslate_bricks', 3], ['deepslate_tiles', 1]], 1003);
  // 정면 부조 (z = zf 평면)
  for (let xx = x - 24; xx <= x + 24; xx++) for (let y = g - 2; y <= g + 36; y++) {
    const dx = xx - x;
    let b = null;
    if (Math.abs(Math.abs(dx) - 12) <= 1 || Math.abs(Math.abs(dx) - 20) <= 1) b = S('polished_blackstone_bricks');
    else if (y === g + 30 || y === g + 31) b = S('chiseled_stone_bricks');
    else if (y > g + 31) b = (Math.abs(dx) + y) % 4 === 0 ? S('gold_block') : P(xx, y, zf);
    else b = P(xx, y, zf);
    set(xx, y, zf, b);
    set(xx, y, zf - 1, P(xx, y, zf - 1));
  }
  // 거대한 문 (아치, 폭 11, 높이 18) — 두 칸 들어가서
  for (let xx = x - 5; xx <= x + 5; xx++) for (let y = g + 1; y <= g + 18; y++) {
    const dx = xx - x;
    const arch = y - g <= 14 || Math.hypot(dx, (y - g - 14) * 1.3) <= 5.6;
    if (!arch) continue;
    set(xx, y, zf, AIR); set(xx, y, zf - 1, AIR);
    set(xx, y, zf - 2, dx === 0 ? S('gold_block') : ((y + dx) % 5 === 0 ? S('gold_block') : S('dark_oak_planks')));
  }
  // 계단
  for (let s = 0; s < 6; s++) for (let xx = x - 8 + s; xx <= x + 8 - s; xx++) set(xx, g + 1 + Math.floor(s / 2), zf + 7 - s, S(s % 2 ? 'polished_deepslate_slab' : 'polished_deepslate'));
  // 수호 석상 2개
  for (const sx of [-16, 16]) {
    const X = x + sx, Z = zf + 3;
    for (let xx = X - 3; xx <= X + 3; xx++) for (let zz = Z - 2; zz <= Z + 2; zz++) for (let y = g + 1; y <= g + 3; y++) set(xx, y, zz, S('polished_blackstone_bricks'));
    for (const lx of [-1, 1]) for (let y = g + 4; y <= g + 9; y++) set(X + lx, y, Z, S('polished_deepslate'));
    for (let xx = X - 2; xx <= X + 2; xx++) for (let zz = Z - 1; zz <= Z + 1; zz++) for (let y = g + 10; y <= g + 17; y++) set(xx, y, zz, S('deepslate_bricks'));
    for (let xx = X - 1; xx <= X + 1; xx++) for (let zz = Z - 1; zz <= Z + 1; zz++) for (let y = g + 18; y <= g + 20; y++) set(xx, y, zz, S('polished_deepslate'));
    for (let xx = X - 1; xx <= X + 1; xx++) for (let y = g + 15; y <= g + 18; y++) set(xx, y, Z + 2, S('polished_andesite')); // 수염
    set(X - 1, g + 21, Z, S('gold_block')); set(X, g + 21, Z, S('gold_block')); set(X + 1, g + 21, Z, S('gold_block')); set(X, g + 22, Z, S('gold_block'));
    for (let y = g + 10; y <= g + 24; y++) set(X + 3 * Math.sign(sx), y, Z + 1, S('dark_oak_log', { axis: 'y' }));
    for (let dx = -1; dx <= 1; dx++) for (let y = g + 22; y <= g + 24; y++) set(X + 3 * Math.sign(sx) + dx, y, Z + 1, S('iron_bars'));
  }
  // 화로
  for (const sx of [-8, 8]) { set(x + sx, g + 1, zf + 9, S('polished_blackstone_bricks')); set(x + sx, g + 2, zf + 9, S('polished_blackstone_brick_wall')); set(x + sx, g + 3, zf + 9, S('shroomlight')); }
  // 굴: 산 안쪽 대전당
  for (let zz = zf - 3; zz >= zf - 38; zz--) for (let xx = x - 4; xx <= x + 4; xx++) for (let y = g + 1; y <= g + 9; y++) {
    set(xx, y, zz, (Math.abs(xx - x) === 4 || y === g + 9) ? P(xx, y, zz) : AIR);
    if (Math.abs(xx - x) === 4 && (zz % 6 === 0) && y === g + 5) set(xx, y, zz, S('shroomlight'));
  }
}

// ── 등대
function lighthouse() {
  const { x, z } = LANDMARKS.lighthouse;
  const h = H(x, z);
  levelDisc(x, z, 10, h, S('grass_block'));
  const TOP = h + 32;
  disc(x, z, 5.3, (xx, zz, d) => { for (let y = h - 3; y <= TOP; y++) set(xx, y, zz, d > 3.9 ? S(Math.floor((y - h) / 5) % 2 ? 'red_wool' : 'calcite') : AIR); });
  disc(x, z, 7.3, (xx, zz, d, dx, dz) => { if (d > 5.3) { set(xx, TOP, zz, S('polished_andesite_slab', { type: 'top' })); set(xx, TOP - 1, zz, S('stone_brick_stairs', { facing: faceTo(dx, dz), half: 'top' })); } if (d > 6.3) set(xx, TOP + 1, zz, S('iron_bars')); });
  disc(x, z, 5.3, (xx, zz) => set(xx, TOP, zz, S('polished_andesite')));
  disc(x, z, 3.4, (xx, zz, d) => { for (let y = TOP + 1; y <= TOP + 5; y++) set(xx, y, zz, d > 2.4 ? S('glass') : (d < 1.5 && y <= TOP + 3 ? S('glowstone') : AIR)); });
  set(x, TOP + 3, z, S('sea_lantern'));
  coneRoof(x, TOP + 6, z, 4.2, 'deepslate_tile', 1.3, 'dark_oak_fence');
  for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3; set(Math.round(x + Math.cos(a) * 4), h + 8 + k * 4, Math.round(z + Math.sin(a) * 4), S('glass_pane')); }
  set(x, h + 1, z - 4, AIR); set(x, h + 2, z - 4, AIR);
  set(x, h + 1, z - 4, S('spruce_door', { facing: 'south', half: 'lower', hinge: 'left', open: 'false' })); set(x, h + 2, z - 4, S('spruce_door', { facing: 'south', half: 'upper', hinge: 'left', open: 'false' }));
  house(x + 14, h, z - 6, 'west', 7, 7, { style: 'fisher', floors: 1, seed: 6101 });
  resv(x, z, 12);
}

// ── 거석 원
function henge() {
  const { x, z } = LANDMARKS.henge;
  const g = H(x, z);
  levelDisc(x, z, 19, g, S('grass_block'));
  const M = mix([['stone', 3], ['andesite', 2], ['mossy_cobblestone', 1], ['cobblestone', 1]], 1004);
  const tops = [];
  for (let k = 0; k < 12; k++) {
    const a = k * Math.PI / 6;
    const sx = Math.round(x + Math.cos(a) * 14), sz = Math.round(z + Math.sin(a) * 14);
    const th = 6 + (k % 3);
    for (let y = g + 1; y <= g + th; y++) { set(sx, y, sz, M(sx, y, sz)); if (Math.abs(Math.cos(a)) > 0.7) set(sx, y, sz + 1, M(sx, y, sz + 1)); else set(sx + 1, y, sz, M(sx + 1, y, sz)); }
    tops.push([sx, sz, g + th]);
  }
  for (let k = 0; k < 12; k += 2) {
    const [ax, az, ay] = tops[k], [bx, bz, by] = tops[k + 1];
    const y = Math.min(ay, by) + 1;
    const n = Math.max(Math.abs(bx - ax), Math.abs(bz - az));
    for (let t = 0; t <= n; t++) set(Math.round(ax + (bx - ax) * t / n), y, Math.round(az + (bz - az) * t / n), M(ax, y, az + t));
  }
  for (let dx = -1; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) set(x + dx, g + 1, z + dz, S(dx === 0 && dz === 0 ? 'chiseled_stone_bricks' : 'polished_andesite'));
  set(x, g + 2, z, S('lantern', { hanging: 'false' }));
  disc(x, z, 17.4, (xx, zz, d) => { if (d > 16.4) surf[col(xx, zz)] = S('dirt_path'); });
}

// ── 감시탑
function watchtower(x, z) {
  const h = H(x, z);
  const M = mix([['cobblestone', 4], ['stone_bricks', 3], ['mossy_cobblestone', 1]], 1005);
  for (let dx = -3; dx <= 3; dx++) for (let dz = -3; dz <= 3; dz++) {
    const e = Math.abs(dx) === 3 || Math.abs(dz) === 3;
    for (let y = h - 3; y <= h + 16; y++) set(x + dx, y, z + dz, e ? M(x + dx, y, z + dz) : (y === h + 8 || y === h + 16 ? S('spruce_planks') : AIR));
    if (inside(x + dx, z + dz)) reserved[col(x + dx, z + dz)] = 3;
  }
  for (let dx = -4; dx <= 4; dx++) for (let dz = -4; dz <= 4; dz++) {
    const e = Math.abs(dx) === 4 || Math.abs(dz) === 4;
    if (!e) continue;
    set(x + dx, h + 15, z + dz, S('stone_brick_stairs', { facing: faceTo(dx, dz), half: 'top' }));
    set(x + dx, h + 16, z + dz, M(x + dx, h + 16, z + dz));
    if ((dx + dz) % 2 === 0) set(x + dx, h + 17, z + dz, S('spruce_fence'));
  }
  for (const [dx, dz] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) for (let y = h + 17; y <= h + 19; y++) set(x + dx, y, z + dz, S('spruce_fence'));
  for (let l = 0; l < 4; l++) for (let dx = -4 + l; dx <= 4 - l; dx++) for (let dz = -4 + l; dz <= 4 - l; dz++) {
    const e = Math.abs(dx) === 4 - l || Math.abs(dz) === 4 - l;
    if (e) set(x + dx, h + 20 + l, z + dz, S('spruce_stairs', { facing: faceTo(dx, dz) }));
  }
  set(x, h + 24, z, S('spruce_planks')); set(x, h + 18, z, S('lantern', { hanging: 'false' }));
  for (const y of [h + 5, h + 12]) for (const [dx, dz] of [[3, 0], [-3, 0], [0, 3], [0, -3]]) set(x + dx, y, z + dz, AIR);
  set(x, h + 1, z + 3, AIR); set(x, h + 2, z + 3, AIR);
  set(x, h + 1, z + 3, S('spruce_door', { facing: 'north', half: 'lower', hinge: 'left', open: 'false' })); set(x, h + 2, z + 3, S('spruce_door', { facing: 'north', half: 'upper', hinge: 'left', open: 'false' }));
  for (let y = h + 8; y <= h + 14; y++) set(x + 2, y, z - 4, S('red_wool'));
}

export function buildLandmarks() {
  wizardTower(); ruins(); monastery(); dwarfGate(); lighthouse(); henge();
  for (const t of LANDMARKS.towers) watchtower(t.x, t.z);
}
