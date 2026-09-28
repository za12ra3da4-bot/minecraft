// =====================================================================
//  마을 4곳 — 풍차 농촌 · 어촌 · 산악 마을 · 숲속 마을
// =====================================================================
import { S, AIR, mix, Frame, disc, coneRoof, DIRS } from './lib.js';
import { set, get, col, inside, height, surf, reserved, H, setGround, waterTop } from '../world.js';
import { house } from './house.js';
import { lineHousesGeneric } from './city.js';
import { stroke, paveCell, samples, lampPost } from './paint.js';
import { VILLAGES, ROADS, LAKE } from '../plan.js';
import { catmull } from '../terrain.js';
import { mulberry, simplex } from '../noise.js';

const PAVE_V = mix([['dirt_path', 6], ['gravel', 1], ['coarse_dirt', 1.2], ['cobblestone', 0.6]], 901);
const wet = (x, z) => inside(x, z) && waterTop[col(x, z)] > height[col(x, z)];
const leaves = n => S(n, { persistent: 'true' });

function villageLanes(v, r, n, seed) {
  const R = mulberry(seed);
  const lanes = [];
  const a0 = R() * Math.PI * 2;
  for (let k = 0; k < n; k++) {
    const a = a0 + k * Math.PI * 2 / n + (R() - 0.5) * 0.5;
    const L = v.r * (0.75 + R() * 0.2);
    const mid = a + (R() - 0.5) * 0.5;
    const pts = catmull([[v.x + Math.cos(a) * 8, v.z + Math.sin(a) * 8], [v.x + Math.cos(mid) * L * 0.55, v.z + Math.sin(mid) * L * 0.55], [v.x + Math.cos(a) * L, v.z + Math.sin(a) * L]], 2);
    lanes.push({ pts, w: 3, kind: 'lane' });
  }
  // 광장 둘레 고리길
  const ring = [];
  for (let t = 0; t <= 360; t += 12) ring.push([v.x + Math.cos(t * Math.PI / 180) * (v.r * 0.42), v.z + Math.sin(t * Math.PI / 180) * (v.r * 0.42)]);
  lanes.push({ pts: ring, w: 3, kind: 'lane' });
  // 계획 도로 중 마을 안 부분
  for (const Rd of ROADS) {
    const pts = catmull(Rd.pts, 2).filter(p => Math.hypot(p[0] - v.x, p[1] - v.z) < v.r * 0.95);
    if (pts.length > 3) lanes.push({ pts, w: Rd.w, kind: 'road' });
  }
  for (const l of lanes) if (l.kind !== 'road') stroke(l.pts, l.w, (x, z) => { if (!wet(x, z) && Math.hypot(x - v.x, z - v.z) < v.r) paveCell(x, z, PAVE_V, 1); });
  return lanes;
}

function green(v, well = true) {
  disc(v.x, v.z, 8.3, (x, z, d) => {
    const c = col(x, z);
    if (d > 7) surf[c] = PAVE_V(x, 0, z); else surf[c] = S('grass_block');
    reserved[c] = 3;
  });
  const h = H(v.x, v.z);
  if (well) {
    disc(v.x, v.z, 1.9, (x, z, d) => {
      if (d < 1) { set(x, h, z, S('water', { level: '0' })); set(x, h - 1, z, S('water', { level: '0' })); set(x, h - 2, z, S('water', { level: '0' })); }
      else { set(x, h, z, S('cobblestone')); set(x, h + 1, z, S('cobblestone_wall')); }
    });
    for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) for (let y = h + 2; y <= h + 3; y++) set(v.x + dx * 2, y, v.z + dz * 2, S('oak_fence'));
    for (let dx = -2; dx <= 2; dx++) { set(v.x + dx, h + 4, v.z - 2, S('spruce_stairs', { facing: 'south' })); set(v.x + dx, h + 4, v.z + 2, S('spruce_stairs', { facing: 'north' })); for (let dz = -1; dz <= 1; dz++) set(v.x + dx, h + 4 + (dz === 0 ? 1 : 0), v.z + dz, S(dz === 0 ? 'spruce_slab' : 'spruce_stairs', dz === 0 ? { type: 'bottom' } : { facing: dz < 0 ? 'south' : 'north' })); }
    set(v.x, h + 3, v.z, S('chain', { axis: 'y' }));
  }
  for (const [dx, dz] of [[6, 0], [-6, 0], [0, 6], [0, -6]]) {
    const x = v.x + dx, z = v.z + dz, hh = H(x, z);
    set(x, hh + 1, z, S(['poppy', 'dandelion', 'cornflower', 'oxeye_daisy'][(dx + dz + 12) % 4]));
  }
}

function windmill(x, z, face = 'south') {
  const h = H(x, z);
  disc(x, z, 5.2, (xx, zz) => { setGround(xx, zz, h, S('coarse_dirt')); reserved[col(xx, zz)] = 3; });
  disc(x, z, 4.3, (xx, zz, d) => {
    for (let y = h - 2; y <= h + 13; y++) {
      const shell = d > 3.1;
      const b = y <= h + 3 ? S('cobblestone') : (y % 5 === 0 ? S('stripped_spruce_log', { axis: 'y' }) : S('white_terracotta'));
      set(xx, y, zz, shell ? b : (y === h ? S('spruce_planks') : AIR));
    }
  });
  const [fx, fz] = DIRS[face];
  // 문, 창
  set(x + fx * 4, h + 1, z + fz * 4, S('spruce_door', { facing: face === 'south' ? 'north' : 'south', half: 'lower', hinge: 'left', open: 'false' }));
  set(x + fx * 4, h + 2, z + fz * 4, S('spruce_door', { facing: face === 'south' ? 'north' : 'south', half: 'upper', hinge: 'left', open: 'false' }));
  for (const [ax, az] of [[4, 0], [-4, 0], [0, -4]]) set(x + ax, h + 8, z + az, S('glass_pane'));
  coneRoof(x, h + 14, z, 5.4, 'spruce', 1.1, null);
  // 날개 축 + 날개 4장
  const hx = x + fx * 5, hz = z + fz * 5, hy = h + 12;
  set(hx, hy, hz, S('dark_oak_log', { axis: fx ? 'x' : 'z' }));
  set(hx - fx, hy, hz - fz, S('dark_oak_log', { axis: fx ? 'x' : 'z' }));
  const px = fz !== 0 ? 1 : 0, pz = fx !== 0 ? 1 : 0; // 날개 평면 가로축
  const P = (l, y, id) => set(hx + fx + px * l, hy + y, hz + fz + pz * l, id);
  P(0, 0, S('dark_oak_log', { axis: fx ? 'x' : 'z' }));
  // '+' 모양 날개 4장: 가운데 살 + 한쪽으로 3칸 폭 돛 (격자 테두리)
  for (const [ax, ay, sx, sy] of [[1, 0, 0, 1], [-1, 0, 0, -1], [0, 1, -1, 0], [0, -1, 1, 0]]) {
    for (let t = 1; t <= 12; t++) {
      P(ax * t, ay * t, S('stripped_spruce_log', { axis: ax ? (px ? 'x' : 'z') : 'y' }));
      if (t < 3) continue;
      for (let s = 1; s <= 3; s++) {
        const edge = s === 3 || t === 3 || t === 12 || t % 3 === 0;
        P(ax * t + sx * s, ay * t + sy * s, edge ? S('spruce_fence') : S('white_wool'));
      }
    }
  }
}

function fields(v, seed, count = 14) {
  const R = mulberry(seed);
  let made = 0;
  for (let t = 0; t < 400 && made < count; t++) {
    const a = R() * Math.PI * 2, rr = v.r * (0.75 + R() * 1.0);
    const W = 13 + Math.floor(R() * 8), D = 9 + Math.floor(R() * 5);
    const x0 = Math.round(v.x + Math.cos(a) * rr - W / 2), z0 = Math.round(v.z + Math.sin(a) * rr - D / 2);
    let ok = true, hs = [];
    for (let x = x0 - 1; x <= x0 + W && ok; x++) for (let z = z0 - 1; z <= z0 + D; z++) {
      if (!inside(x, z) || reserved[col(x, z)] !== 0 || wet(x, z)) { ok = false; break; }
      hs.push(height[col(x, z)]);
    }
    if (!ok) continue;
    hs.sort((p, q) => p - q);
    const hm = hs[hs.length >> 1];
    if (hs[hs.length - 1] - hs[0] > 3) continue;
    const crop = ['wheat', 'wheat', 'carrots', 'potatoes'][Math.floor(R() * 4)];
    for (let x = x0 - 1; x <= x0 + W; x++) for (let z = z0 - 1; z <= z0 + D; z++) {
      setGround(x, z, hm, S('grass_block'));
      reserved[col(x, z)] = 3;
      const edge = x === x0 - 1 || x === x0 + W || z === z0 - 1 || z === z0 + D;
      if (edge) { if (!((x === x0 + (W >> 1)) && z === z0 - 1)) set(x, hm + 1, z, S('oak_fence')); continue; }
      if ((z - z0) % 5 === 2) set(x, hm, z, S('water', { level: '0' }));
      else { set(x, hm, z, S('farmland', { moisture: '7' })); set(x, hm + 1, z, S(crop, { age: '7' })); }
    }
    // 건초 더미 · 허수아비
    set(x0 - 2, hm + 1, z0, S('hay_block', { axis: 'y' })); set(x0 - 2, hm + 1, z0 + 1, S('hay_block', { axis: 'x' })); set(x0 - 2, hm + 2, z0, S('hay_block', { axis: 'y' }));
    const sx = x0 + 3, sz = z0 + 3;
    if ((sz - z0) % 5 !== 2) { set(sx, hm + 1, sz, S('spruce_fence')); set(sx, hm + 2, sz, S('hay_block', { axis: 'y' })); set(sx, hm + 3, sz, S('pumpkin')); set(sx - 1, hm + 2, sz, S('spruce_fence')); set(sx + 1, hm + 2, sz, S('spruce_fence')); }
    made++;
  }
  return made;
}

function church(x, z, front) {
  const h = H(x, z);
  house(x, h, z, front, 11, 17, { style: 'stone', floors: 2, frontGable: true, chimney: false, seed: x * 13 + z });
  const F = new Frame(x, h, z, front);
  // 정면 종탑 (가운데)
  for (let u = 3; u <= 7; u++) for (let v = -4; v <= 0; v++) for (let y = 1; y <= 20; y++) {
    const e = u === 3 || u === 7 || v === -4 || v === 0;
    F.set(u, v, y, e ? (y > 14 && (u === 5 || v === -2) ? AIR : S(y % 7 === 0 ? 'polished_andesite' : 'stone_bricks')) : AIR);
  }
  F.set(5, -4, 1, AIR); F.set(5, -4, 2, AIR);
  F.door(5, -4, 1, 'dark_oak', 'back');
  F.set(5, -2, 16, S('gold_block'));
  for (let l = 0; l < 6; l++) for (let u = 2 + l; u <= 8 - l; u++) for (let v = -5 + l; v <= 1 - l; v++) {
    const e = u === 2 + l || u === 8 - l || v === -5 + l || v === 1 - l;
    if (!e) continue;
    if (2 + l === 8 - l) { F.set(u, v, 21 + l, S('deepslate_tiles')); continue; }
    F.stairs(u, v, 21 + l, 'deepslate_tile', u === 2 + l ? 'right' : u === 8 - l ? 'left' : v === -5 + l ? 'back' : 'front');
  }
  F.set(5, -2, 27, S('deepslate_tiles')); F.set(5, -2, 28, S('dark_oak_fence')); F.set(5, -2, 29, S('gold_block'));
  F.set(4, -2, 29, S('gold_block')); F.set(6, -2, 29, S('gold_block')); F.set(5, -2, 30, S('gold_block'));
}

function smallBoat(x, z, dir) {
  const F = new Frame(x, 63, z, dir);
  for (let v = -3; v <= 3; v++) {
    const bw = Math.abs(v) === 3 ? 0 : 1;
    for (let u = -bw; u <= bw; u++) F.set(u, v, -1, S('spruce_planks'));
    for (const u of [-bw - 1, bw + 1]) F.set(u, v, 0, S('oak_planks'));
    if (Math.abs(v) === 3) F.set(0, v, 0, S('oak_planks'));
  }
  F.set(0, 0, 0, S('spruce_slab', { type: 'bottom' }));
  F.set(0, 1, 0, S('spruce_fence')); F.set(0, 1, 1, S('spruce_fence')); F.set(0, 1, 2, S('white_wool')); F.set(0, 1, 3, S('white_wool'));
}

function pier(x, z, dx, dz, L = 16) {
  const px = -dz, pz = dx;
  for (let t = 0; t <= L; t++) for (let s = -1; s <= 1; s++) {
    const xx = Math.round(x + dx * t + px * s), zz = Math.round(z + dz * t + pz * s);
    set(xx, 64, zz, S('spruce_planks'));
    if (Math.abs(s) === 1 && t % 3 === 0) { for (let y = 56; y <= 63; y++) set(xx, y, zz, S('spruce_log', { axis: 'y' })); set(xx, 65, zz, S('spruce_fence')); }
    if (inside(xx, zz)) reserved[col(xx, zz)] = 3;
  }
  const ex = Math.round(x + dx * L), ez = Math.round(z + dz * L);
  set(ex, 65, ez, S('spruce_fence')); set(ex, 66, ez, S('spruce_fence')); set(ex, 67, ez, S('lantern', { hanging: 'false' }));
  return [Math.round(x + dx * (L - 4) + px * 4), Math.round(z + dz * (L - 4) + pz * 4)];
}

function giantTree(x, z) {
  const h = H(x, z);
  const TH = 24;
  for (let y = h - 1; y <= h + TH; y++) disc(x, z, y < h + 4 ? 2.6 : 1.8, (xx, zz) => set(xx, y, zz, S('dark_oak_log', { axis: 'y' })));
  // 뿌리
  for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; for (let t = 2; t <= 6; t++) set(Math.round(x + Math.cos(a) * t), h + Math.max(0, 3 - t) , Math.round(z + Math.sin(a) * t), S('dark_oak_log', { axis: Math.abs(Math.cos(a)) > 0.7 ? 'x' : 'z' })); }
  // 가지 + 수관
  const R = mulberry(x * 7 + z);
  const blobs = [[0, TH + 2, 0, 9]];
  for (let k = 0; k < 7; k++) {
    const a = k * Math.PI * 2 / 7 + R();
    const L = 7 + R() * 5, by = h + 14 + R() * 8;
    for (let t = 0; t <= L; t++) set(Math.round(x + Math.cos(a) * t), Math.round(by + t * 0.45), Math.round(z + Math.sin(a) * t), S('dark_oak_log', { axis: Math.abs(Math.cos(a)) > 0.7 ? 'x' : 'z' }));
    blobs.push([Math.cos(a) * L, by + L * 0.45 - h + 1, Math.sin(a) * L, 5 + R() * 2]);
  }
  for (const [bx, by, bz, r] of blobs) {
    const cx = x + bx, cy = h + by, cz = z + bz;
    for (let dx = -Math.ceil(r); dx <= r; dx++) for (let dz = -Math.ceil(r); dz <= r; dz++) for (let dy = -Math.ceil(r * 0.6); dy <= r * 0.7; dy++) {
      const d = Math.hypot(dx, dy * 1.5, dz);
      if (d > r) continue;
      const xx = Math.round(cx + dx), yy = Math.round(cy + dy), zz = Math.round(cz + dz);
      if (get(xx, yy, zz) === AIR) set(xx, yy, zz, leaves(R() < 0.06 ? 'flowering_azalea_leaves' : 'dark_oak_leaves'));
    }
  }
  // 나무 위 전망대
  disc(x, z, 6.3, (xx, zz, d) => { if (d > 2.7) { set(xx, h + 12, zz, S('spruce_planks')); if (d > 5.4) set(xx, h + 13, zz, S('spruce_fence')); } });
  for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3; set(Math.round(x + Math.cos(a) * 5), h + 11, Math.round(z + Math.sin(a) * 5), S('lantern', { hanging: 'true' })); }
  // 나선 계단 대신 사다리 모양 울타리 기둥
  for (let y = h + 1; y <= h + 11; y++) set(x + 3, y, z, S('spruce_fence'));
  disc(x, z, 7, (xx, zz) => { reserved[col(xx, zz)] = 3; });
}

function keep(x, z) {
  const h = H(x, z);
  const M = mix([['stone_bricks', 5], ['cobblestone', 2], ['mossy_stone_bricks', 1]], 911);
  for (let dx = -4; dx <= 4; dx++) for (let dz = -4; dz <= 4; dz++) {
    const e = Math.abs(dx) === 4 || Math.abs(dz) === 4;
    for (let y = h - 3; y <= h + 20; y++) set(x + dx, y, z + dz, e ? M(x + dx, y, z + dz) : (y % 6 === 0 ? S('spruce_planks') : AIR));
    reserved[col(x + dx, z + dz)] = 3;
  }
  for (let dx = -5; dx <= 5; dx++) for (let dz = -5; dz <= 5; dz++) {
    const e = Math.abs(dx) === 5 || Math.abs(dz) === 5;
    if (!e) continue;
    set(x + dx, h + 19, z + dz, S('stone_brick_stairs', { facing: Math.abs(dx) === 5 ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south'), half: 'top' }));
    set(x + dx, h + 20, z + dz, M(x + dx, h + 20, z + dz));
    if ((dx + dz) % 2 === 0) set(x + dx, h + 21, z + dz, M(x + dx, h + 21, z + dz)); else set(x + dx, h + 21, z + dz, S('stone_brick_slab'));
  }
  for (const [dx, dz] of [[4, 0], [-4, 0], [0, 4], [0, -4]]) for (const y of [h + 8, h + 9, h + 14, h + 15]) set(x + dx, y, z + dz, S('glass_pane'));
  set(x, h + 1, z + 4, AIR); set(x, h + 2, z + 4, AIR);
  set(x, h + 1, z + 4, S('spruce_door', { facing: 'north', half: 'lower', hinge: 'left', open: 'false' }));
  set(x, h + 2, z + 4, S('spruce_door', { facing: 'north', half: 'upper', hinge: 'left', open: 'false' }));
  for (let y = h + 12; y <= h + 18; y++) set(x + 1, y, z + 5, S('blue_wool'));
}

export function buildVillages() {
  let total = 0;
  for (const v of VILLAGES) {
    const seed = Math.abs(v.x * 131 + v.z * 7);
    green(v, v.kind !== 'forest');
    if (v.kind === 'forest') giantTree(v.x, v.z);
    if (v.kind === 'mountain') keep(v.x + 14, v.z - 12);
    if (v.kind === 'farm') { church(v.x + 18, v.z - 30, 'south'); windmill(v.x - 70, v.z + 40, 'south'); windmill(v.x + 64, v.z + 58, 'west'); }
    const lanes = villageLanes(v, v.r, v.kind === 'fish' ? 4 : 5, seed);
    const style = {
      farm: (x, z, r) => { const q = r(); return q < 0.55 ? 'cottage' : q < 0.8 ? 'tudor' : 'burgher'; },
      fish: (x, z, r) => (r() < 0.8 ? 'fisher' : 'cottage'),
      mountain: (x, z, r) => (r() < 0.85 ? 'mountain' : 'stone'),
      forest: (x, z, r) => { const q = r(); return q < 0.5 ? 'cottage' : q < 0.8 ? 'mountain' : 'fisher'; },
    }[v.kind];
    const n = lineHousesGeneric(lanes, {
      seed, allow: (x, z) => Math.hypot(x - v.x, z - v.z) < v.r * 0.97 && !wet(x, z),
      w: v.kind === 'fish' ? [5, 8] : [6, 9], dMax: 10, dMin: 6, setback: 3, startOffset: true,
      gap: r => 2 + Math.floor(r() * 5), maxSlope: 3, gapRequired: true,
      style, floors: (st, x, z, r) => (st === 'cottage' || st === 'fisher' ? 1 + (r() < 0.35 ? 1 : 0) : 1 + (r() < 0.6 ? 1 : 0)),
    });
    total += n;
    if (v.kind === 'farm') fields(v, seed + 1, 16);
    if (v.kind === 'fish') {
      const dx = LAKE.x - v.x, dz = LAKE.z - v.z, L = Math.hypot(dx, dz);
      const ux = dx / L, uz = dz / L;
      for (const off of [-24, 0, 24]) {
        // 물가 찾기
        let x = v.x - uz * off, z = v.z + ux * off;
        for (let t = 0; t < 120 && !wet(Math.round(x), Math.round(z)); t++) { x += ux; z += uz; }
        const b = pier(x - ux * 2, z - uz * 2, ux, uz, 16);
        smallBoat(b[0], b[1], Math.abs(ux) > Math.abs(uz) ? (ux > 0 ? 'east' : 'west') : (uz > 0 ? 'south' : 'north'));
      }
    }
    for (const l of lanes) {
      const sm = samples(l.pts, 1);
      for (let i = 10; i < sm.length; i += 22) {
        const [px, pz, tx, tz] = sm[i];
        const x = Math.round(px - tz * (l.w / 2 + 1)), z = Math.round(pz + tx * (l.w / 2 + 1));
        if (inside(x, z) && reserved[col(x, z)] === 0 && !wet(x, z)) lampPost(x, z, 'wood');
      }
    }
  }
  return total;
}

// ── 도로변 농가: 농가 + 헛간 + 밭 + 울타리 목장 (+ 가끔 풍차)
function areaFree(x0, z0, x1, z1, maxSlope = 3) {
  let hmin = 999, hmax = -999;
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    if (!inside(x, z) || reserved[col(x, z)] !== 0 || wet(x, z)) return null;
    const h = height[col(x, z)]; hmin = Math.min(hmin, h); hmax = Math.max(hmax, h);
  }
  return hmax - hmin <= maxSlope ? { hmin, hmax } : null;
}
function pasture(x0, z0, W, D) {
  const a = areaFree(x0 - 1, z0 - 1, x0 + W, z0 + D, 3);
  if (!a) return false;
  for (let x = x0; x < x0 + W; x++) for (let z = z0; z < z0 + D; z++) {
    const h = height[col(x, z)];
    const edge = x === x0 || x === x0 + W - 1 || z === z0 || z === z0 + D - 1;
    if (edge && !(x === x0 + 2 && z === z0)) set(x, h + 1, z, S('spruce_fence'));
    reserved[col(x, z)] = 3;
  }
  const h = height[col(x0 + 2, z0 + 2)];
  set(x0 + 2, h + 1, z0 + 2, S('hay_block', { axis: 'y' })); set(x0 + 3, h + 1, z0 + 2, S('hay_block', { axis: 'x' }));
  set(x0 + W - 3, h, z0 + D - 3, S('water', { level: '0' })); set(x0 + W - 4, h, z0 + D - 3, S('water', { level: '0' }));
  return true;
}
export function buildFarmsteads(cityX, cityZ, cityR) {
  const R = mulberry(8181);
  let n = 0;
  for (const Rd of ROADS) {
    const sm = samples(catmull(Rd.pts, 2), 1);
    for (let i = 40; i < sm.length - 30; i += 70 + Math.floor(R() * 60)) {
      const [px, pz, tx, tz] = sm[i];
      if (Math.hypot(px - cityX, pz - cityZ) < cityR + 70) continue;
      if (VILLAGES.some(v => Math.hypot(px - v.x, pz - v.z) < v.r + 70)) continue;
      const side = R() < 0.5 ? 1 : -1;
      const off = Rd.w / 2 + 10 + R() * 10;
      const cx = Math.round(px - tz * side * off), cz = Math.round(pz + tx * side * off);
      // 농가는 길을 향한다
      const fx = tz * side, fz = -tx * side;
      const front = Math.abs(fx) > Math.abs(fz) ? (fx > 0 ? 'east' : 'west') : (fz > 0 ? 'south' : 'north');
      const a = areaFree(cx - 12, cz - 12, cx + 12, cz + 12, 3);
      if (!a) continue;
      const hy = a.hmax;
      const w = 7 + Math.floor(R() * 3), d = 7 + Math.floor(R() * 3);
      const F = new Frame(0, 0, 0, front);
      const [rx, rz] = [F.r[0], F.r[1]];
      const ox = Math.round(cx - rx * (w - 1) / 2), oz = Math.round(cz - rz * (w - 1) / 2);
      house(ox, hy, oz, front, w, d, { style: R() < 0.6 ? 'cottage' : 'tudor', floors: 2, seed: ox * 7 + oz });
      // 헛간 (옆으로)
      const bx = Math.round(cx + rx * (w / 2 + 8)), bz = Math.round(cz + rz * (w / 2 + 8));
      const b2 = areaFree(Math.min(bx, bx - rx * 9) - 7, Math.min(bz, bz - rz * 9) - 7, Math.max(bx, bx - rx * 9) + 7, Math.max(bz, bz - rz * 9) + 7, 3);
      if (b2) house(bx, b2.hmax, bz, front, 9, 13, { style: 'cottage', floors: 2, frontGable: true, chimney: false, seed: bx * 3 + bz });
      // 밭 · 목장 · 풍차
      fields({ x: cx, z: cz, r: 22 }, i * 7 + n, 3);
      pasture(Math.round(cx - rx * 20) - 6, Math.round(cz - rz * 20) - 5, 13, 11);
      if (R() < 0.25) { const mx = Math.round(cx - fx * 16), mz = Math.round(cz - fz * 16); if (areaFree(mx - 6, mz - 6, mx + 6, mz + 6, 2)) windmill(mx, mz, front); }
      // 오솔길: 농가 문 → 길
      const [dx0, dz0] = [Math.round(cx + fx * 1), Math.round(cz + fz * 1)];
      for (let t = 0; t <= off; t++) { const x = Math.round(dx0 + fx * t), z = Math.round(dz0 + fz * t); if (inside(x, z) && reserved[col(x, z)] === 0 && !wet(x, z)) { surf[col(x, z)] = PAVE_V(x, 0, z); reserved[col(x, z)] = 1; } }
      n++;
    }
  }
  return n;
}
