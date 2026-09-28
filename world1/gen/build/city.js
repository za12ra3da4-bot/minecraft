// =====================================================================
//  왕도 알더미어 — 거리망, 거리를 따라 늘어선 집, 가로등, 뒤뜰
// =====================================================================
import { S, AIR, Frame, DIRS, mix } from './lib.js';
import { col, inside, height, reserved, H, set, get, surf } from '../world.js';
import { stroke, paveCell, PAVE, lampPost, samples } from './paint.js';
import { house } from './house.js';
import { CITY, CASTLE } from '../plan.js';
import { mulberry } from '../noise.js';
import { ringWall, roundTower, gatehouse } from './walls.js';

const C = CITY;
const castleZone = (x, z) => Math.hypot(x - CASTLE.x, (z - CASTLE.z) * 1.15) < 78;
const polar = (a, r) => [C.x + Math.cos(a * Math.PI / 180) * r, C.z + Math.sin(a * Math.PI / 180) * r];

function arcs(r, a0, a1, step = 4) {
  const out = []; let cur = [];
  for (let a = a0; a <= a1 + 0.01; a += step) {
    const p = polar(a, r);
    if (castleZone(p[0], p[1])) { if (cur.length > 1) out.push(cur); cur = []; continue; }
    cur.push(p);
  }
  if (cur.length > 1) out.push(cur);
  return out;
}

export function cityStreets() {
  const S_ = [];
  const add = (pts, w, kind) => S_.push({ pts, w, kind });
  add([[0, 8], [0, -79]], 7, 'main');
  add([[0, 70], [0, 236]], 7, 'main');
  add([[-34, 39], [-207, 39]], 7, 'main');
  add([[34, 39], [207, 39]], 7, 'main');
  for (const a of arcs(150, 0, 360, 3)) add(a, 5, 'ring');
  for (const a of arcs(96, 0, 180, 4)) add(a, 4, 'lane');
  for (const a of arcs(96, 180, 360, 4)) add(a, 4, 'lane');
  for (const a of arcs(190, 0, 360, 2)) add(a, 4, 'lane');
  for (const [ang, r0, r1] of [[60, 50, 190], [120, 50, 190], [150, 84, 190], [210, 76, 190], [330, 76, 190], [30, 142, 190], [240, 96, 190], [300, 96, 190], [15, 152, 190], [165, 100, 190], [195, 152, 190], [90 + 22, 152, 190], [90 - 22, 152, 190]]) {
    const pts = [];
    for (let r = r0; r <= r1; r += 4) { const p = polar(ang, r); if (castleZone(p[0], p[1])) break; pts.push(p); }
    if (pts.length > 1) add(pts, ang % 30 === 0 ? 5 : 4, ang % 30 === 0 ? 'ring' : 'lane');
  }
  // 좁은 골목 (격자 사이)
  const rr = mulberry(313);
  for (let i = 0; i < 26; i++) {
    const a = rr() * 360, r0 = 60 + rr() * 100;
    const b = a + (rr() < 0.5 ? 1 : -1) * (8 + rr() * 14);
    const pts = [];
    for (let t = 0; t <= 1.001; t += 0.1) { const p = polar(a + (b - a) * t, r0 + t * 10); if (!castleZone(p[0], p[1])) pts.push(p); }
    if (pts.length > 3) add(pts, 3, 'alley');
  }
  return S_;
}

export const paved = new Set();
export function paveStreets(streets) {
  for (const s of streets) {
    const mat = s.kind === 'main' || s.kind === 'ring' ? PAVE.main : PAVE.lane;
    stroke(s.pts, s.w, (x, z, d) => {
      if (Math.hypot(x - C.x, z - C.z) > C.R - 2.5 && s.kind !== 'main') return;
      if (paveCell(x, z, d > s.w / 2 - 0.8 && s.kind === 'main' ? S('polished_andesite') : mat, 1)) paved.add(col(x, z));
    });
  }
  rampSlabs(paved);
}

// 한 칸 높이차가 나는 포장 칸에 돌계단을 놓아 걸어 올라가는 계단길로
export function rampSlabs(cells, mat = 'stone_brick') {
  const DN = { '1,0': 'east', '-1,0': 'west', '0,1': 'south', '0,-1': 'north' };
  for (const c of cells) {
    const x = Math.floor(c / 2016) - 1008, z = (c % 2016) - 1008;
    const h = height[c];
    let up = null, ups = 0;
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const n = col(x + dx, z + dz);
      if (cells.has(n) && height[n] === h + 1) { ups++; if (!up) up = DN[dx + ',' + dz]; }
    }
    if (!up || get(x, h + 1, z) !== AIR) continue;
    // 두 방향 이상이 높으면(모서리) 반블록, 아니면 오르막 쪽을 향한 계단
    set(x, h + 1, z, ups >= 2 ? S(`${mat}_slab`, { type: 'bottom' }) : S(`${mat}_stairs`, { facing: up, half: 'bottom' }));
  }
}

export function cityWalls() {
  const tops = ringWall(C.x, C.z, C.R, { height: 13 });
  const wallTop = a => { const key = Math.round((a * Math.PI / 180) * C.R / 3); return tops.get(key) ?? (C.y + 13); };
  let n = 0;
  for (let a = 15; a < 360; a += 30) {
    const [x, z] = polar(a, C.R);
    roundTower(Math.round(x), Math.round(z), 6.5, wallTop(a) + 9, { roof: n++ % 2 ? 'cone' : 'flat', roofMat: 'deepslate_tile', steep: 1.3, rot: a });
  }
  gatehouse(205, 39, 'east', { base: C.y });
  gatehouse(-205, 39, 'west', { base: C.y });
  gatehouse(0, 235, 'south', { base: H(0, 235) });
}

// 거리 양옆에 집 줄 세우기 (도시·마을 공용)
//  cfg: allow(x,z) 허용 영역, style(x,z,r), floors(style,x,z,r), big(x,z), shop(street,r), w:[최소,최대], dMax, dMin, gap(r), setback
export function lineHousesGeneric(streets, cfg) {
  const r = mulberry(cfg.seed ?? 4242);
  let count = 0;
  for (const s of streets) {
    const halfW = s.w / 2;
    const pts = samples(s.pts, 1);
    for (const side of [-1, 1]) {
      let i = cfg.startOffset ? Math.floor(r() * 4) : 0;
      while (i < pts.length) {
        const [px, pz, tx, tz] = pts[i];
        const nx = side * -tz, nz = side * tx;
        const off = halfW + 1.5 + (cfg.setback ? Math.floor(r() * cfg.setback) : 0);
        const cx = px + nx * off, cz = pz + nz * off;
        // 정면 방향: 집 → 길 (= -n), 축에 맞춤
        const fx = -nx, fz = -nz;
        const front = Math.abs(fx) > Math.abs(fz) ? (fx > 0 ? 'east' : 'west') : (fz > 0 ? 'south' : 'north');
        const big = cfg.big ? cfg.big(cx, cz) : 0;
        const [w0, w1] = cfg.w ?? [7, 11];
        const w = w0 + Math.floor(r() * (w1 - w0 + 1 + big));
        let placed = false;
        for (let tryW = w; tryW >= Math.max(5, w0 - 1) && !placed; tryW -= 2) {
          for (let d = (cfg.dMax ?? 13) + big * 2; d >= (cfg.dMin ?? 7) && !placed; d -= 2) {
            const [dfx, dfz] = DIRS[front];
            const rx = -dfz, rz = dfx;               // Frame 의 u 방향
            const ox = Math.round(cx - rx * (tryW - 1) / 2), oz = Math.round(cz - rz * (tryW - 1) / 2);
            const F = new Frame(ox, 0, oz, front);
            let ok = true, hmin = 999, hmax = -999;
            for (let u = -1; u <= tryW && ok; u++) for (let v = 0; v < d; v++) {
              const [x, z] = F.w(u, v);
              if (!inside(x, z)) { ok = false; break; }
              const rv = reserved[col(x, z)];
              if (u === -1 || u === tryW) { if (cfg.gapRequired && rv >= 2) { ok = false; break; } continue; }
              if (rv !== 0 || !cfg.allow(x, z)) { ok = false; break; }
              const h = height[col(x, z)]; hmin = Math.min(hmin, h); hmax = Math.max(hmax, h);
            }
            if (!ok || hmax - hmin > (cfg.maxSlope ?? 4)) continue;
            const [fxw, fzw] = F.w(Math.floor(tryW / 2), -1);
            const oy = Math.max(H(fxw, fzw), hmin);
            const style = cfg.style(cx, cz, r);
            const floors = cfg.floors(style, cx, cz, r);
            house(ox, oy, oz, front, tryW, d, { style, floors, seed: (ox * 31 + oz * 17) ^ 0x5bd1, shop: cfg.shop ? cfg.shop(s, r) && floors >= 2 : false });
            // 발자국만 예약 (이웃집은 벽을 맞댈 수 있게)
            for (let u = 0; u < tryW; u++) for (let v = 0; v < d; v++) { const [x, z] = F.w(u, v); reserved[col(x, z)] = 2; }
            count++;
            placed = true;
            const gap = cfg.gap ? cfg.gap(r) : (r() < 0.6 ? 0 : r() < 0.7 ? 1 : 3);
            i += tryW + gap;
          }
        }
        if (!placed) i += 2;
      }
    }
  }
  return count;
}

export function lineHouses(streets) {
  const limit = C.R - 11;
  return lineHousesGeneric(streets, {
    seed: 4242,
    allow: (x, z) => Math.hypot(x - C.x, z - C.z) <= limit && !castleZone(x, z),
    big: (x, z) => (Math.hypot(x - C.x, z - C.z) < 110 ? 1 : 0),
    style: (x, z, r) => {
      const d = Math.hypot(x - C.x, z - C.z), q = r();
      if (z < -20 && Math.abs(x) < 120) return q < 0.45 ? 'stone' : q < 0.75 ? 'brick' : 'tudor';
      if (d < 95) return q < 0.45 ? 'tudor' : q < 0.62 ? 'stone' : q < 0.77 ? 'brick' : 'burgher';
      if (d < 150) return q < 0.42 ? 'tudor' : q < 0.72 ? 'burgher' : q < 0.82 ? 'brick' : q < 0.9 ? 'stone' : 'cottage';
      return q < 0.34 ? 'tudor' : q < 0.6 ? 'burgher' : q < 0.9 ? 'cottage' : 'stone';
    },
    floors: (style, x, z, r) => {
      const d = Math.hypot(x - C.x, z - C.z);
      return style === 'cottage' ? 1 + (r() < 0.5 ? 1 : 0) : (d < 100 ? 3 + (r() < 0.35 ? 1 : 0) : 2 + (r() < 0.45 ? 1 : 0));
    },
    shop: (s, r) => s.kind === 'main' && r() < 0.4,
  });
}

export function streetLamps(streets) {
  for (const s of streets) {
    if (s.kind !== 'main' && s.kind !== 'ring') continue;
    const pts = samples(s.pts, 1);
    for (let i = 6; i < pts.length; i += 15) {
      const [px, pz, tx, tz] = pts[i];
      const side = (Math.floor(i / 15) % 2) ? 1 : -1;
      const x = Math.round(px + side * -tz * (s.w / 2 - 0.5)), z = Math.round(pz + side * tx * (s.w / 2 - 0.5));
      if (inside(x, z) && reserved[col(x, z)] === 1 && get(x, height[col(x, z)] + 1, z) === AIR) lampPost(x, z);
    }
  }
}

// 빈터: 뒤뜰 정원, 채소밭, 나무, 헛간
export function cityGardens() {
  const r = mulberry(5151);
  const G = 5;
  let n = 0;
  for (let x0 = C.x - C.R; x0 < C.x + C.R; x0 += G) for (let z0 = C.z - C.R; z0 < C.z + C.R; z0 += G) {
    let ok = true, hmin = 999, hmax = -999;
    for (let x = x0; x < x0 + G && ok; x++) for (let z = z0; z < z0 + G; z++) {
      if (!inside(x, z) || reserved[col(x, z)] !== 0 || Math.hypot(x - C.x, z - C.z) > C.R - 5 || castleZone(x, z)) { ok = false; break; }
      const h = height[col(x, z)]; hmin = Math.min(hmin, h); hmax = Math.max(hmax, h);
    }
    if (!ok || hmax - hmin > 2) continue;
    const q = r();
    const cx = x0 + 2, cz = z0 + 2, h = height[col(cx, cz)];
    if (q < 0.34) {
      // 작은 나무
      const t = r() < 0.6 ? 'oak' : r() < 0.5 ? 'birch' : 'spruce';
      const th = 4 + Math.floor(r() * 3);
      for (let y = h + 1; y <= h + th; y++) set(cx, y, cz, S(`${t}_log`, { axis: 'y' }));
      for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) for (let dy = -1; dy <= 2; dy++) {
        const rad = t === 'spruce' ? 2 - dy * 0.6 : 2.4 - Math.abs(dy - 0.3) * 0.5;
        if (Math.hypot(dx, dz) <= rad && get(cx + dx, h + th + dy, cz + dz) === AIR) set(cx + dx, h + th + dy, cz + dz, S(`${t}_leaves`, { persistent: 'true' }));
      }
      set(cx, h + th + (t === 'spruce' ? 3 : 2), cz, S(`${t}_leaves`, { persistent: 'true' }));
    } else if (q < 0.55) {
      // 채소밭
      const crop = ['wheat', 'carrots', 'potatoes'][Math.floor(r() * 3)];
      for (let x = x0; x < x0 + G; x++) for (let z = z0; z < z0 + G; z++) {
        const edge = x === x0 || x === x0 + G - 1 || z === z0 || z === z0 + G - 1;
        const hh = height[col(x, z)];
        if (edge) set(x, hh + 1, z, S('oak_fence'));
        else if (x === cx && z === cz) set(x, hh, z, S('water', { level: '0' }));
        else { set(x, hh, z, S('farmland', { moisture: '7' })); set(x, hh + 1, z, S(crop, { age: '7' })); }
      }
    } else if (q < 0.65) {
      // 헛간
      house(x0 + 4, h, z0 + 4, r() < 0.5 ? 'north' : 'south', 5, 5, { style: 'cottage', floors: 1, chimney: false, frontGable: true, seed: x0 * 7 + z0 });
      for (let x = x0 - 1; x <= x0 + G; x++) for (let z = z0 - 1; z <= z0 + G; z++) if (inside(x, z)) reserved[col(x, z)] = 2;
      n++; continue;
    } else {
      // 풀밭 + 꽃 + 덤불
      for (let x = x0; x < x0 + G; x++) for (let z = z0; z < z0 + G; z++) {
        const hh = height[col(x, z)], q2 = r();
        if (q2 < 0.1) set(x, hh + 1, z, S('oak_leaves', { persistent: 'true' }));
        else if (q2 < 0.35) set(x, hh + 1, z, S('short_grass'));
        else if (q2 < 0.45) set(x, hh + 1, z, S(['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'allium', 'azure_bluet'][Math.floor(r() * 6)]));
      }
    }
    for (let x = x0; x < x0 + G; x++) for (let z = z0; z < z0 + G; z++) reserved[col(x, z)] = 2;
    n++;
  }
  return n;
}
