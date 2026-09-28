// =====================================================================
//  스팀펑크 공중 기어 섬 — 복셀 월드 생성
// =====================================================================
import { T, h3, mulberry } from './textures.js';

// ── 격자
export const SX = 400, SY = 256, SZ = 400, OX = 200, OZ = 200;
export const V = new Uint8Array(SX * SY * SZ);
const inb = (x, y, z) => x >= -OX && x < SX - OX && y >= 0 && y < SY && z >= -OZ && z < SZ - OZ;
export const idx = (x, y, z) => ((x + OX) * SY + y) * SZ + (z + OZ);
export function set(x, y, z, b) { x = Math.round(x); y = Math.round(y); z = Math.round(z); if (inb(x, y, z)) V[idx(x, y, z)] = b; }
export function get(x, y, z) { x = Math.round(x); y = Math.round(y); z = Math.round(z); return inb(x, y, z) ? V[idx(x, y, z)] : 0; }
function setE(x, y, z, b) { if (!get(x, y, z)) set(x, y, z, b); }
function box(x0, y0, z0, x1, y1, z1, b) { for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) for (let z = z0; z <= z1; z++) set(x, y, z, b); }

// ── 블록 정의
export const G = { OPAQ: 0, METAL: 1, CUT: 2, GLASS: 3, WATER: 4, EMIT: 5 };
export const BL = [null];
export const B = {};
function defB(name, tiles, g = G.OPAQ) {
  const t = Array.isArray(tiles) ? tiles : [tiles, tiles, tiles];
  B[name] = BL.length;
  BL.push({ name, top: T[t[0]], side: T[t[1]], bot: T[t[2]], g });
}
defB('STONE', 'stone'); defB('COBBLE', 'cobble'); defB('SBRICK', 'sbrick'); defB('DEEP', 'deep'); defB('DIRT', 'dirt');
defB('GRASS', ['grass_top', 'grass_side', 'dirt']); defB('FLOWER', ['flower', 'grass_side', 'dirt']); defB('PATH', ['path', 'dirt', 'dirt']);
defB('SPRUCE', 'pl_spruce'); defB('DARK', 'pl_dark'); defB('OAK', 'pl_oak'); defB('LOG', ['log_top', 'log_side', 'log_top']);
defB('COPPER', 'copper', G.METAL); defB('CUTCOP', 'cutcop', G.METAL); defB('WEATH', 'weath', G.METAL); defB('OXID', 'oxid');
defB('GOLD', 'gold', G.METAL); defB('IRON', 'iron', G.METAL); defB('BRASS', 'brass', G.METAL); defB('DIRON', 'diron', G.METAL);
defB('GLASS', 'glass', G.GLASS); defB('WINDOW', 'window', G.EMIT); defB('WINDIM', 'window_dim');
defB('WOOL', 'wool'); defB('PLASTER', 'plaster'); defB('LEAVES', 'leaves', G.CUT); defB('LAMP', 'lamp', G.EMIT);
defB('BRICKS', 'bricks'); defB('WATER', 'water', G.WATER); defB('FOAM', 'foam', G.WATER); defB('BLACK', 'black');
defB('RED', 'red'); defB('BROWN', 'brown'); defB('CANVAS', 'canvas');
defB('ROOFR', 'roof_red'); defB('ROOFT', 'roof_teal'); defB('ROOFC', 'roof_cop', G.METAL);
defB('POLISH', 'polish'); defB('MOSSY', 'mossy'); defB('CRYSTAL', 'crystal', G.EMIT); defB('GRATE', 'grate', G.CUT);
defB('HAY', ['hay_top', 'hay_side', 'hay_top']); defB('DTILES', 'dtiles');
export const OPAQ = new Uint8Array(256);
BL.forEach((b, i) => { if (b && (b.g === G.OPAQ || b.g === G.METAL || b.g === G.EMIT)) OPAQ[i] = 1; });

const {
  STONE, COBBLE, SBRICK, DEEP, DIRT, GRASS, FLOWER, PATH, SPRUCE, DARK, OAK, LOG, COPPER, CUTCOP, WEATH, OXID, GOLD, IRON,
  BRASS, DIRON, GLASS, WINDOW, WINDIM, WOOL, PLASTER, LEAVES, LAMP, BRICKS, WATER, FOAM, BLACK, RED, BROWN, CANVAS,
  ROOFR, ROOFT, ROOFC, POLISH, MOSSY, CRYSTAL, GRATE, HAY, DTILES,
} = B;

// ── 노이즈
function vnoise(x, z, s) {
  const xi = Math.floor(x), zi = Math.floor(z), fx = x - xi, fz = z - zi;
  const u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
  const a = h3(xi, 0, zi, s), b = h3(xi + 1, 0, zi, s), c = h3(xi, 0, zi + 1, s), d = h3(xi + 1, 0, zi + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function fbm(x, z, s) { let t = 0, a = 0.5, f = 1; for (let i = 0; i < 4; i++) { t += a * vnoise(x * f, z * f, s + i); f *= 2; a *= 0.5; } return t / 0.9375; }
const rnd = mulberry(20260928);
const TAU = Math.PI * 2;

// ── 기어 윤곽 (사다리꼴 톱니)
function gearR(th, R, teeth, depth) {
  const f = (((th / TAU) * teeth) % 1 + 1) % 1;
  let k;
  if (f < 0.12) k = f / 0.12; else if (f < 0.48) k = 1; else if (f < 0.6) k = 1 - (f - 0.48) / 0.12; else k = 0;
  return R + depth * k;
}

// 외부로 내보내는 장면 정보
export const smoke = [];   // {x,y,z,dark,n}
export const mist = [];
export const cams = {};
export const IY = 112;          // 본섬 지면 높이
export const CLOUD_Y = 26;      // 구름 바다

// =====================================================================
//  세운 톱니바퀴.  axis: 'x' → z-y 평면, 'z' → x-y 평면
// =====================================================================
function standingGear(cx, cy, cz, R, teeth, axis, ringB = CUTCOP, spokeB = BRASS, thick = 2, rot = 0) {
  const maxR = R + 2.2;
  for (let u = -Math.ceil(maxR); u <= maxR; u++) for (let v = -Math.ceil(maxR); v <= maxR; v++) {
    const d = Math.hypot(u, v), th = Math.atan2(v, u) + rot;
    if (d > gearR(th, R, teeth, 2)) continue;
    const ring = d > R - 2.2, hub = d < 2.2;
    const a6 = ((th % (TAU / 6)) + TAU / 6) % (TAU / 6);
    const spoke = Math.min(a6, TAU / 6 - a6) * d < 1.0;
    if (!(ring || hub || spoke)) continue;
    const b = hub ? GOLD : (ring ? (d > R ? ringB : ringB) : spokeB);
    for (let w = 0; w < thick; w++) {
      if (axis === 'x') set(cx + w, cy + v, cz + u, b); else set(cx + u, cy + v, cz + w, b);
    }
    if (hub && d < 1) for (let w = -1; w < thick + 1; w++) { if (axis === 'x') set(cx + w, cy + v, cz + u, DIRON); else set(cx + u, cy + v, cz + w, DIRON); }
  }
}

// =====================================================================
//  떠 있는 기어 섬 (본섬 / 위성섬 공용)
// =====================================================================
function gearIsland(cx, cy, cz, R, teeth, o = {}) {
  const TD = o.td ?? 5, BAND = o.band ?? 4, depthMax = o.depth ?? 40, sd = o.seed ?? 1;
  const inner = R - BAND;
  const M = Math.ceil(R + TD + 1);
  const cols = [];
  for (let x = -M; x <= M; x++) for (let z = -M; z <= M; z++) {
    const d = Math.hypot(x, z), th = Math.atan2(z, x);
    const edge = gearR(th, R, teeth, TD);
    if (d > edge) continue;
    const X = cx + x, Z = cz + z;
    const tooth = d > R, band = !tooth && d > inner;
    const disc = o.disc ?? 6;
    if (tooth || band) {
      for (let y = cy - disc; y <= cy; y++) {
        let b = CUTCOP;
        if (y === cy - Math.floor(disc / 2)) b = BRASS;
        if (tooth) b = (d > edge - 1.3) ? ((y === cy || y === cy - disc) ? GOLD : COPPER) : COPPER;
        if (band && d > R - 1 && (y === cy - 1 || y === cy - disc + 1) && Math.round(th * R) % 3 === 0) b = DIRON;
        set(X, y, Z, b);
      }
      if (band) set(X, cy + 1, Z, (d > R - 1 || d < inner + 1) ? BRASS : CUTCOP);
    } else {
      set(X, cy, Z, h3(X, 0, Z, 5) < 0.05 ? FLOWER : GRASS);
      for (let y = cy - 3; y < cy; y++) set(X, y, Z, DIRT);
      for (let y = cy - disc; y < cy - 3; y++) set(X, y, Z, STONE);
    }
    // 아래 암반
    const wob = fbm(X * 0.08, Z * 0.08, sd) * 4;
    if (d < R - 1 - wob) {
      const k = 1 - d / R;
      const depth = Math.round(4 + depthMax * Math.pow(k, 1.45) + fbm(X * 0.12, Z * 0.12, sd + 3) * 9 * k);
      const top = cy - disc - 1;
      for (let y = top; y >= top - depth; y--) {
        const t = (top - y) / Math.max(1, depth);
        let b = t < 0.1 ? (h3(X, y, Z, 3) < 0.35 ? MOSSY : STONE) : (t < 0.5 ? STONE : DEEP);
        if (b === STONE && h3(Math.floor(X / 4), Math.floor(y / 4), Math.floor(Z / 4), 11) < 0.18) b = COBBLE;
        const hv = h3(X, y, Z, 9);
        if (hv < 0.012) b = OXID; else if (hv < 0.0145 && t > 0.45) b = CRYSTAL; else if (hv > 0.992) b = BRASS;
        set(X, y, Z, b);
      }
      cols.push([X, Z, top - depth, d]);
    }
  }
  // 종유석
  const nSt = o.stal ?? 40;
  for (let i = 0; i < nSt; i++) {
    const c = cols[Math.floor(rnd() * cols.length)];
    if (!c || c[3] > R - 6) continue;
    const L = Math.round((6 + rnd() * 24) * (0.4 + (1 - c[3] / R)));
    const r0 = 1.5 + rnd() * 2.5;
    for (let t = 0; t < L; t++) {
      const r = r0 * (1 - t / L) + 0.3;
      for (let a = -Math.ceil(r); a <= r; a++) for (let b = -Math.ceil(r); b <= r; b++) {
        if (a * a + b * b > r * r) continue;
        set(c[0] + a, c[2] - t, c[1] + b, t / L > 0.55 ? DEEP : (h3(c[0] + a, t, c[1] + b, 4) < 0.03 ? CRYSTAL : STONE));
      }
    }
  }
  return { cx, cy, cz, R, inner, cols };
}

// =====================================================================
//  건물
// =====================================================================
function house(x0, z0, w, d, floors, roofB, y0 = IY + 1, o = {}) {
  const hh = floors * 4;
  const x1 = x0 + w - 1, z1 = z0 + d - 1;
  const stoneBase = o.stoneBase ?? rnd() < 0.5;
  box(x0, y0 - 1, z0, x1, y0 - 1, z1, SBRICK);
  for (let y = 0; y < hh; y++) for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const ex = x === x0 || x === x1, ez = z === z0 || z === z1;
    if (!ex && !ez) continue;
    let b = PLASTER;
    if (y < 4 && stoneBase) b = SBRICK;
    const corner = ex && ez;
    const post = ez ? (x - x0) % 3 === 0 : (z - z0) % 3 === 0;
    if (corner) b = LOG;
    else if (y % 4 === 3) b = DARK;
    else if (post && !(y < 4 && stoneBase)) b = DARK;
    else if ((y % 4 === 1 || y % 4 === 2) && !post) b = h3(x, y, z, 21) < 0.78 ? WINDOW : WINDIM;
    set(x, y0 + y, z, b);
  }
  // 문 + 문등
  const dx = x0 + Math.floor(w / 2);
  set(dx, y0, z0, DARK); set(dx, y0 + 1, z0, DARK);
  set(dx + 1, y0 + 2, z0 - 1, LAMP);
  // 박공 지붕
  const alongX = w >= d;
  const yr = y0 + hh;
  if (alongX) {
    for (let l = 0; ; l++) {
      const zA = z0 - 1 + l, zB = z1 + 1 - l;
      if (zA > zB) break;
      for (let x = x0 - 1; x <= x1 + 1; x++) { set(x, yr + l, zA, roofB); set(x, yr + l, zB, roofB); }
      for (let z = zA + 1; z < zB; z++) { set(x0, yr + l, z, l % 3 === 2 ? DARK : PLASTER); set(x1, yr + l, z, l % 3 === 2 ? DARK : PLASTER); }
      if (l === 1 && zB - zA > 4) { set(x0, yr + l, Math.round((zA + zB) / 2), WINDOW); set(x1, yr + l, Math.round((zA + zB) / 2), WINDOW); }
    }
  } else {
    for (let l = 0; ; l++) {
      const xA = x0 - 1 + l, xB = x1 + 1 - l;
      if (xA > xB) break;
      for (let z = z0 - 1; z <= z1 + 1; z++) { set(xA, yr + l, z, roofB); set(xB, yr + l, z, roofB); }
      for (let x = xA + 1; x < xB; x++) { set(x, yr + l, z0, l % 3 === 2 ? DARK : PLASTER); set(x, yr + l, z1, l % 3 === 2 ? DARK : PLASTER); }
      if (l === 1 && xB - xA > 4) { set(Math.round((xA + xB) / 2), yr + l, z0, WINDOW); set(Math.round((xA + xB) / 2), yr + l, z1, WINDOW); }
    }
  }
  // 굴뚝
  if (o.chimney ?? rnd() < 0.6) {
    const cx = alongX ? x1 - 1 : x0 + 1, cz = alongX ? z0 + 1 : z1 - 1;
    const top = yr + Math.ceil(Math.min(w, d) / 2) + 2;
    for (let y = yr - 1; y <= top; y++) set(cx, y, cz, BRICKS);
    smoke.push({ x: cx, y: top + 1, z: cz, dark: false, n: 9 });
  }
}

function bigOak(x, y, z) {
  const h = 6 + Math.floor(rnd() * 3);
  for (let j = 1; j <= h; j++) set(x, y + j, z, LOG);
  const blobs = [[0, h, 0, 3.6]];
  for (let i = 0; i < 4; i++) blobs.push([Math.round((rnd() - 0.5) * 5), h - 1 + Math.round(rnd() * 2), Math.round((rnd() - 0.5) * 5), 2.2 + rnd() * 1.3]);
  for (const [bx, by, bz, r] of blobs) {
    for (let a = -Math.ceil(r); a <= r; a++) for (let b = -Math.ceil(r); b <= r; b++) for (let c = -Math.ceil(r); c <= r; c++) {
      if (a * a + b * b * 1.3 + c * c > r * r) continue;
      setE(x + bx + a, y + by + b, z + bz + c, LEAVES);
    }
    if (bx || bz) for (let t = 0; t <= 1; t += 0.25) set(x + bx * t, y + h - 2 + (by - h + 2) * t, z + bz * t, LOG);
  }
}
function spruceTree(x, y, z) {
  const h = 8 + Math.floor(rnd() * 5);
  for (let j = 1; j <= h; j++) set(x, y + j, z, LOG);
  for (let j = 3; j <= h + 1; j++) {
    const r = Math.max(0.6, (h + 1 - j) * 0.38 + ((j % 2) ? 0.6 : 0));
    for (let a = -Math.ceil(r); a <= r; a++) for (let c = -Math.ceil(r); c <= r; c++) if (a * a + c * c <= r * r) setE(x + a, y + j, z + c, LEAVES);
  }
  set(x, y + h + 2, z, LEAVES);
}

function lampPost(x, z, y = IY) {
  for (let j = 1; j <= 4; j++) set(x, y + j, z, DIRON);
  set(x, y + 5, z, LAMP);
  set(x, y + 6, z, DIRON);
}

// =====================================================================
//  시계탑
// =====================================================================
function clockTower() {
  const y0 = IY + 1;
  // 기단 13×13 + 아치 입구
  for (let y = 0; y < 8; y++) for (let x = -6; x <= 6; x++) for (let z = -6; z <= 6; z++) {
    if (Math.abs(x) !== 6 && Math.abs(z) !== 6) continue;
    const s = Math.abs(x) === 6 ? z : x;
    if (Math.abs(s) <= 1 && y <= 3) continue;
    if (Math.abs(s) <= 1 && y === 4) { set(x, y0 + y, z, BRASS); continue; }
    let b = SBRICK;
    if (Math.abs(x) >= 5 && Math.abs(z) >= 5) b = POLISH;
    if (y === 7) b = CUTCOP;
    set(x, y0 + y, z, b);
  }
  box(-5, y0 + 7, -5, 5, y0 + 7, 5, CUTCOP);
  // 몸통 9×9
  const sh0 = y0 + 8, sh1 = y0 + 40;
  for (let y = sh0; y <= sh1; y++) for (let x = -4; x <= 4; x++) for (let z = -4; z <= 4; z++) {
    if (Math.abs(x) !== 4 && Math.abs(z) !== 4) continue;
    const rel = y - sh0;
    let b = SBRICK;
    const c = Math.abs(x) === 4 && Math.abs(z) === 4;
    const nearC = (Math.abs(x) === 4 && Math.abs(z) >= 3) || (Math.abs(z) === 4 && Math.abs(x) >= 3);
    if (nearC) b = c ? BRASS : POLISH;
    else if (rel % 8 === 0) b = CUTCOP;
    else if (rel % 8 >= 3 && rel % 8 <= 6 && (Math.abs(x) === 4 ? Math.abs(z) <= 1 : Math.abs(x) <= 1)) b = (Math.abs(x) + Math.abs(z)) % 2 ? WINDOW : DARK;
    set(x, y, z, b);
  }
  // 모서리 버팀벽
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) for (let y = sh0; y <= sh0 + 20; y++) {
    const off = y - sh0 < 10 ? 1 : 0;
    set(sx * (5 + off), y, sz * 4, SBRICK); set(sx * 4, y, sz * (5 + off), SBRICK);
  }
  // 시계 층 11×11
  const c0 = sh1 + 1, c1 = sh1 + 13;
  for (let y = c0; y <= c1; y++) for (let x = -5; x <= 5; x++) for (let z = -5; z <= 5; z++) {
    if (Math.abs(x) !== 5 && Math.abs(z) !== 5) continue;
    let b = POLISH;
    if (Math.abs(x) === 5 && Math.abs(z) === 5) b = GOLD;
    else if (y === c0 || y === c1) b = CUTCOP;
    set(x, y, z, b);
  }
  // 시계판 4면
  const fy = c0 + 6;
  const faces = [[0, 1, 6], [0, -1, -6], [1, 1, 6], [1, -1, -6]];
  const faceSet = (ax, off, a, b, blk) => { if (ax === 0) set(a, fy + b, off, blk); else set(off, fy + b, a, blk); };
  for (const [ax, sgn, off] of faces) {
    for (let a = -6; a <= 6; a++) for (let b = -6; b <= 6; b++) {
      const r = Math.hypot(a, b);
      if (r > 5.9) continue;
      faceSet(ax, off, a, b, r > 4.8 ? GOLD : (r > 4.3 ? BRASS : PLASTER));
    }
    for (let hr = 0; hr < 12; hr++) {
      const th = hr / 12 * TAU;
      faceSet(ax, off, Math.round(Math.sin(th) * 3.6), Math.round(Math.cos(th) * 3.6), hr % 3 === 0 ? BLACK : DIRON);
    }
    const o2 = off + sgn;
    // 바늘: 10시 10분
    for (let t = 0; t <= 2.6; t += 0.5) faceSet(ax, o2, Math.round(-Math.sin(TAU * 10 / 12) * t * -sgn), Math.round(Math.cos(TAU * 10 / 12) * t), BLACK);
    for (let t = 0; t <= 3.8; t += 0.5) faceSet(ax, o2, Math.round(Math.sin(TAU * 2 / 12) * t * sgn), Math.round(Math.cos(TAU * 2 / 12) * t), BLACK);
    faceSet(ax, o2, 0, 0, GOLD);
  }
  // 종루 (열린 아치 + 빛)
  const b0 = c1 + 1, b1 = c1 + 6;
  for (let y = b0; y <= b1; y++) for (let x = -5; x <= 5; x++) for (let z = -5; z <= 5; z++) {
    if (Math.abs(x) !== 5 && Math.abs(z) !== 5) continue;
    const s = Math.abs(x) === 5 ? z : x;
    if (Math.abs(s) <= 3 && y < b1 && y > b0) continue;
    set(x, y, z, Math.abs(s) >= 4 ? BRASS : CUTCOP);
  }
  box(-5, b0, -5, 5, b0, 5, DTILES);
  box(-1, b0 + 1, -1, 1, b0 + 3, 1, LAMP);
  // 지붕 (가파른 산화 구리 피라미드)
  let yy = b1 + 1;
  for (let r = 7; r >= 0; r--) {
    const reps = r > 5 ? 1 : 2;
    for (let q = 0; q < reps; q++) {
      for (let x = -r; x <= r; x++) for (let z = -r; z <= r; z++) if (Math.abs(x) === r || Math.abs(z) === r || r === 0) set(x, yy, z, r === 7 ? CUTCOP : ROOFT);
      yy++;
    }
  }
  // 첨탑 + 작은 기어
  for (let j = 0; j < 10; j++) set(0, yy + j, 0, j === 9 ? LAMP : GOLD);
  for (let a = -2; a <= 2; a++) for (let c = -2; c <= 2; c++) { const r = Math.hypot(a, c); if (r > 1.5 && r < 2.6) set(a, yy + 4, c, GOLD); }
  // 몸통 앞 거대 기어 (+x, +z 면)
  standingGear(5, sh0 + 16, 0, 5, 10, 'x', GOLD, CUTCOP, 1, 0.1);
  standingGear(0, sh0 + 16, 5, 5, 10, 'z', GOLD, CUTCOP, 1, 0.25);
  standingGear(-6, sh0 + 16, 0, 5, 10, 'x', GOLD, CUTCOP, 1, 0.1);
  standingGear(0, sh0 + 16, -6, 5, 10, 'z', GOLD, CUTCOP, 1, 0.25);
  return yy + 10;
}

// =====================================================================
//  공장 지구
// =====================================================================
function factory(x0, z0, x1, z1) {
  const y0 = IY + 1, H = 10;
  box(x0, IY, z0, x1, IY, z1, DTILES);
  for (let y = 0; y < H; y++) for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const ex = x === x0 || x === x1, ez = z === z0 || z === z1;
    if (!ex && !ez) continue;
    const pillar = ez ? (x - x0) % 4 === 0 : (z - z0) % 4 === 0;
    let b = BRICKS;
    if (pillar || (ex && ez)) b = DIRON;
    else if (y === H - 1 || y === 0) b = SBRICK;
    else if (y >= 3 && y <= 7) b = (y === 5) ? DARK : WINDOW;
    set(x, y0 + y, z, b);
  }
  // 톱니 지붕 (x 방향 반복)
  const ry = y0 + H;
  for (let x = x0; x <= x1; x++) {
    const p = (x - x0) % 6;
    for (let z = z0; z <= z1; z++) {
      for (let j = 0; j <= p; j++) {
        const top = j === p;
        if (top) set(x, ry + j, z, ROOFT);
        if (p === 5 && !top) set(x, ry + j, z, z % 2 ? WINDOW : DIRON);
      }
      if (p === 5) set(x, ry + 5, z, ROOFT);
    }
  }
  // 굴뚝 3개
  for (let i = 0; i < 3; i++) {
    const cx = x0 + 4 + i * Math.floor((x1 - x0 - 8) / 2), cz = z1 - 3;
    const top = y0 + 30 + i * 3;
    for (let y = ry; y <= top; y++) for (let a = -1; a <= 1; a++) for (let c = -1; c <= 1; c++) {
      set(cx + a, y, cz + c, (y - ry) % 7 === 0 ? DIRON : BRICKS);
    }
    for (let a = -2; a <= 2; a++) for (let c = -2; c <= 2; c++) if (Math.abs(a) === 2 || Math.abs(c) === 2) set(cx + a, top, cz + c, DIRON);
    set(cx, top, cz, BLACK);
    smoke.push({ x: cx, y: top + 1, z: cz, dark: true, n: 16 });
  }
  // 앞면 톱니바퀴 한 쌍 (맞물림)
  standingGear(Math.round((x0 + x1) / 2) - 5, y0 + 7, z0 - 2, 6, 12, 'z', CUTCOP, BRASS, 2, 0);
  standingGear(Math.round((x0 + x1) / 2) + 5, y0 + 4, z0 - 2, 4, 8, 'z', GOLD, CUTCOP, 2, 0.2);
  // 보일러 (세운 원통)
  const bx = Math.round((x0 + x1) / 2), bz = z0 - 8;
  for (let y = 0; y < 10; y++) for (let a = -3; a <= 3; a++) for (let c = -3; c <= 3; c++) {
    const r = Math.hypot(a, c);
    if (r > 3.3) continue;
    set(bx + a, y0 + y, bz + c, y % 3 === 0 ? BRASS : COPPER);
  }
  for (let a = -2; a <= 2; a++) for (let c = -2; c <= 2; c++) if (Math.hypot(a, c) < 2.4) set(bx + a, y0 + 10, bz + c, CUTCOP);
  for (let y = y0 + 10; y < y0 + 16; y++) set(bx, y, bz, DIRON);
  smoke.push({ x: bx, y: y0 + 16, z: bz, dark: false, n: 10 });
  // 보일러 → 공장 파이프
  for (let z = bz + 3; z <= z0; z++) { set(bx - 2, y0 + 6, z, COPPER); set(bx + 2, y0 + 3, z, COPPER); }
}

// =====================================================================
//  엔진 프로펠러 (섬 옆면, 바깥쪽을 향함).  dir: '+z','-z','-x','+x'
// =====================================================================
function engine(R, dir, y) {
  const s = dir[0] === '+' ? 1 : -1, ax = dir[1];
  const P = (r, u, v, b) => { if (ax === 'z') set(u, y + v, s * r, b); else set(s * r, y + v, u, b); };
  const r0 = R - 6, r1 = R + 10;
  for (let r = r0; r <= r1; r++) for (let u = -5; u <= 5; u++) for (let v = -5; v <= 5; v++) {
    const d = Math.hypot(u, v);
    const rad = r > r1 - 3 ? 5 - (r - (r1 - 3)) * 0.6 : 5;
    if (d > rad) continue;
    if (d < rad - 1.2 && r < r1) continue;
    P(r, u, v, (r - r0) % 5 === 0 ? BRASS : (d > rad - 0.6 ? CUTCOP : IRON));
  }
  // 흡기구 그레이트
  for (let u = -3; u <= 3; u++) for (let v = -3; v <= 3; v++) if (Math.hypot(u, v) < 3.5) P(r1, u, v, GRATE);
  // 프로펠러 (X자 4날)
  const pr = r1 + 2;
  for (let t = -13; t <= 13; t++) for (let w = -1; w <= 1; w++) {
    const k = Math.abs(t) < 2 ? 0 : 1;
    const b = Math.abs(t) > 11 ? BRASS : DARK;
    P(pr, Math.round((t + w * 0.7) * 0.707), Math.round((t - w * 0.7) * 0.707), k ? b : BRASS);
    P(pr, Math.round((t + w * 0.7) * 0.707), Math.round((-t + w * 0.7) * 0.707), k ? b : BRASS);
  }
  for (let r = r1; r <= pr + 1; r++) P(r, 0, 0, GOLD);
  // 받침대
  for (let t = 0; t < 10; t++) { P(r0 + 3 + t * 0.4, -6 - t * 0.5, -5 - t, DIRON); P(r0 + 3 + t * 0.4, 6 + t * 0.5, -5 - t, DIRON); }
  // 배기관
  for (let v = 5; v < 16; v++) P(r0 + 4, 3, v, v % 4 === 0 ? BRASS : COPPER);
  P(r0 + 4, 3, 16, BLACK);
  const sp = ax === 'z' ? { x: 3, z: s * (r0 + 4) } : { x: s * (r0 + 4), z: 3 };
  smoke.push({ x: sp.x, y: y + 17, z: sp.z, dark: true, n: 12 });
}

// =====================================================================
//  비행선
// =====================================================================
function airship(cx, cy, cz, L, axis, sgn, pal) {
  const put = (a, b, c, blk) => {
    if (axis === 'x') set(cx + sgn * a, cy + b, cz + c, blk); else set(cx + c, cy + b, cz + sgn * a, blk);
  };
  const rx = L / 2, ry = L / 5.2;
  // 기구
  for (let a = -Math.ceil(rx); a <= rx; a++) for (let b = -Math.ceil(ry); b <= ry; b++) for (let c = -Math.ceil(ry); c <= ry; c++) {
    const e = (a * a) / (rx * rx) + (b * b + c * c) / (ry * ry);
    if (e > 1) continue;
    const e2 = ((Math.abs(a) + 1) ** 2) / (rx * rx) + (b * b + c * c) / (ry * ry);
    const rr = Math.hypot(b, c) + 1;
    const e3 = (a * a) / (rx * rx) + (rr * rr) / (ry * ry);
    if (e2 <= 1 && e3 <= 1) continue;
    let blk = pal.env;
    if (Math.round(a) % 6 === 0) blk = CUTCOP;
    if (Math.abs(c) < 0.8 && b > 0) blk = pal.stripe;
    if (Math.abs(b) < 0.8 && Math.abs(Math.round(a)) % 6 !== 0) blk = pal.stripe2 ?? pal.env;
    if (a > rx - 2.5) blk = BRASS;
    if (a < -rx + 1.5) blk = BRASS;
    put(a, b, c, blk);
  }
  // 꼬리 날개 4장
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8 - i; j++) {
    const a = -rx + 1 + i, h = ry - 2 + j;
    const edge = j === 7 - i || i === 0;
    const blk = edge ? DARK : pal.fin;
    put(a, h, 0, blk); put(a, -h, 0, blk); put(a, 0, h, blk); put(a, 0, -h, blk);
  }
  // 곤돌라 선체
  const gl = Math.round(L * 0.62), hl = gl / 2, gb = -Math.round(ry) - 6;
  const hw = a => Math.max(1, Math.round(3.6 * (1 - Math.pow(Math.abs(a) / (hl + 1), 2.4))));
  for (let a = -Math.floor(hl); a <= hl; a++) {
    const w = hw(a);
    for (let c = -w; c <= w; c++) {
      put(a, gb, c, Math.abs(c) === w ? SPRUCE : OAK);
      if (Math.abs(c) === w) { put(a, gb + 1, c, SPRUCE); put(a, gb - 1, c, BRASS); }
      if (Math.abs(c) < w) put(a, gb - 1, c, DARK);
      if (Math.abs(c) < w - 1) put(a, gb - 2, c, DARK);
    }
    if (w > 2) put(a, gb - 3, 0, DARK);
    if (Math.abs(a) % 3 === 0) { put(a, gb + 2, w, DIRON); put(a, gb + 2, -w, DIRON); }
  }
  // 선실 (뒤쪽)
  const ca0 = -Math.floor(hl) + 2, ca1 = ca0 + 8;
  for (let a = ca0; a <= ca1; a++) for (let c = -2; c <= 2; c++) for (let b = 1; b <= 4; b++) {
    if (Math.abs(c) === 2 || a === ca0 || a === ca1) {
      const win = b >= 2 && b <= 3 && (a - ca0) % 2 === 1 && Math.abs(c) === 2;
      put(a, gb + b, c, win ? WINDOW : SPRUCE);
    }
  }
  for (let a = ca0 - 1; a <= ca1 + 1; a++) for (let c = -3; c <= 3; c++) put(a, gb + 5, c, pal.roof ?? ROOFC);
  put(ca0 + 2, gb + 6, 1, BLACK); put(ca0 + 2, gb + 7, 1, BLACK);
  // 뱃머리
  for (let t = 0; t < 5; t++) put(Math.floor(hl) + 1 + t, gb + 1 + Math.floor(t / 2), 0, DARK);
  put(Math.floor(hl) + 1, gb + 2, 0, LAMP);
  put(ca0 - 1, gb + 2, 0, LAMP);
  // 옆 프로펠러
  for (const sc of [1, -1]) {
    for (let c = 4; c <= 8; c++) put(0, gb, sc * c, DIRON);
    for (let a = -2; a <= 2; a++) put(a, gb, sc * 9, BRASS);
    for (let t = -3; t <= 3; t++) { put(-3, gb + t, sc * 9, DARK); put(-3, gb, sc * 9 + t, DARK); }
  }
  // 뒤 프로펠러
  const pa = -Math.floor(hl) - 2;
  for (let t = -5; t <= 5; t++) { put(pa, gb + 1 + Math.round(t * 0.7), Math.round(t * 0.7), DARK); put(pa, gb + 1 + Math.round(t * 0.7), -Math.round(t * 0.7), DARK); }
  put(pa + 1, gb + 1, 0, BRASS);
  // 삭구
  const top = -Math.round(ry) + 1;
  for (const [a, c] of [[hl - 3, 2], [hl - 3, -2], [-hl + 3, 2], [-hl + 3, -2], [0, 3], [0, -3]]) {
    for (let b = gb + 2; b <= top; b++) put(Math.round(a), b, c, DIRON);
  }
  // 깃발
  for (let b = 6; b <= 10; b++) put(ca0, gb + b, 0, DARK);
  for (let a = 1; a <= 3; a++) for (let b = 8; b <= 10; b++) put(ca0 - a, gb + b, 0, pal.flag ?? RED);
  smoke.push({ x: axis === 'x' ? cx + sgn * (ca0 + 2) : cx + 1, y: cy + gb + 8, z: axis === 'x' ? cz + 1 : cz + sgn * (ca0 + 2), dark: false, n: 6 });
  const w2 = (a, b, c) => axis === 'x' ? [cx + sgn * a, cy + b, cz + c] : [cx + c, cy + b, cz + sgn * a];
  return { bow: w2(Math.floor(hl) - 1, gb + 2.62, 0), stern: w2(ca1 + 1, gb + 2.62, 0), deckY: cy + gb, dir: axis === 'x' ? [sgn, 0, 0] : [0, 0, sgn] };
}

// =====================================================================
//  쇠사슬 다리
// =====================================================================
function bridge(p0, p1) {
  const n = Math.ceil(Math.hypot(p1[0] - p0[0], p1[2] - p0[2]));
  const dx = (p1[0] - p0[0]) / n, dz = (p1[2] - p0[2]) / n;
  const px = -dz, pz = dx; const pl = Math.hypot(px, pz); const nx = px / pl, nz = pz / pl;
  for (let i = 0; i <= n; i++) {
    const t = i / n, sag = Math.sin(t * Math.PI) * n * 0.07;
    const x = p0[0] + dx * i, z = p0[2] + dz * i, y = p0[1] + (p1[1] - p0[1]) * t - sag;
    for (let w = -1; w <= 1; w++) set(x + nx * w, y, z + nz * w, i % 5 === 0 ? DARK : SPRUCE);
    const chainY = y + 3 + Math.sin(t * Math.PI) * n * 0.03;
    set(x + nx * 2, chainY, z + nz * 2, DIRON); set(x - nx * 2, chainY, z - nz * 2, DIRON);
    if (i % 3 === 0) for (let h = y + 1; h < chainY; h++) { set(x + nx * 2, h, z + nz * 2, DIRON); set(x - nx * 2, h, z - nz * 2, DIRON); }
    if (i % 12 === 6) set(x + nx * 2, chainY + 1, z + nz * 2, LAMP);
  }
}

// =====================================================================
//  조립
// =====================================================================
export function buildWorld() {
  const R = 58, TEETH = 20, BAND = 5, INNER = R - BAND;
  const occ = new Uint8Array(SX * SZ);
  const O = (x, z) => (x + OX) * SZ + (z + OZ);
  const spokeAt = (x, z) => {
    for (let k = 0; k < 6; k++) {
      const a = k * Math.PI / 3, along = x * Math.cos(a) + z * Math.sin(a), perp = -x * Math.sin(a) + z * Math.cos(a);
      if (along > 12 && Math.abs(perp) <= 2.5) return { k, perp, along };
    }
    return null;
  };
  const sectorOf = (x, z) => Math.floor((((Math.atan2(z, x) + TAU) % TAU)) / (Math.PI / 3));

  const main = gearIsland(0, IY, 0, R, TEETH, { td: 6, band: BAND, depth: 52, seed: 1, stal: 70, disc: 6 });

  // 광장 · 도로
  for (let x = -INNER; x <= INNER; x++) for (let z = -INNER; z <= INNER; z++) {
    const d = Math.hypot(x, z);
    if (d > INNER) continue;
    let top = null;
    if (d <= 14) {
      top = d > 12.8 ? SBRICK : POLISH;
      const m = (((Math.atan2(z, x) / (Math.PI / 4)) % 1) + 1) % 1;
      if (d > 6 && d < 12.5 && (m < 0.07 || m > 0.93)) top = BRASS;
      if (Math.abs(d - 9.8) < 0.55) top = GOLD;
      occ[O(x, z)] = 1;
    }
    const sp = spokeAt(x, z);
    if (sp) { top = Math.abs(sp.perp) <= 1.5 ? SBRICK : POLISH; occ[O(x, z)] = 1; }
    if (d > INNER - 3) { top = SBRICK; occ[O(x, z)] = 1; }
    if (top) set(x, IY, z, top);
  }
  // 가로등
  for (let k = 0; k < 6; k++) {
    const a = k * Math.PI / 3;
    for (let r = 18; r < INNER - 3; r += 9) for (const s of [-3.5, 3.5]) {
      const x = Math.round(Math.cos(a) * r - Math.sin(a) * s), z = Math.round(Math.sin(a) * r + Math.cos(a) * s);
      lampPost(x, z); occ[O(x, z)] = 1;
    }
  }
  for (let i = 0; i < 36; i++) {
    const a = (i + 0.5) / 36 * TAU;
    const x = Math.round(Math.cos(a) * (INNER - 4)), z = Math.round(Math.sin(a) * (INNER - 4));
    if (!spokeAt(x, z)) { lampPost(x, z); occ[O(x, z)] = 1; }
  }

  const towerTop = clockTower();

  // 공장 (섹터 1, 90° 방향)
  factory(-13, 24, 13, 40);
  for (let x = -14; x <= 14; x++) for (let z = 13; z <= 41; z++) occ[O(x, z)] = 2;

  // 공원 + 연못 + 폭포 (섹터 3)
  const wf = 212.4 / 360 * TAU;
  const pcx = Math.cos(wf) * 32, pcz = Math.sin(wf) * 32;
  for (let x = -12; x <= 12; x++) for (let z = -12; z <= 12; z++) {
    const e = (x * x) / 49 + (z * z) / 30;
    const X = Math.round(pcx + x), Z = Math.round(pcz + z);
    if (e <= 1) { set(X, IY, Z, WATER); set(X, IY - 1, Z, WATER); occ[O(X, Z)] = 2; }
    else if (e <= 1.35) { set(X, IY, Z, POLISH); occ[O(X, Z)] = 2; }
  }
  // 개울 → 기어 틈 → 폭포
  const ux = Math.cos(wf), uz = Math.sin(wf), vx = -uz, vz = ux;
  for (let r = 38; r <= R + 1; r += 0.5) for (let w = -1.5; w <= 1.5; w += 0.5) {
    const X = Math.round(ux * r + vx * w), Z = Math.round(uz * r + vz * w);
    set(X, IY, Z, WATER); set(X, IY + 1, Z, 0); set(X, IY + 2, Z, 0);
    if (r > INNER) { set(X, IY - 1, Z, WATER); }
    occ[O(X, Z)] = 2;
    if (Math.abs(w) === 1.5 && r < INNER) set(Math.round(ux * r + vx * w * 1.4), IY, Math.round(uz * r + vz * w * 1.4), POLISH);
  }
  for (let y = IY; y >= CLOUD_Y + 2; y--) {
    const r = R + 1.5 + Math.floor((IY - y) / 16) * 0.6;
    for (let w = -1.5; w <= 1.5; w += 0.5) for (let dr = 0; dr <= 1; dr++) {
      const X = Math.round(ux * (r + dr) + vx * w), Z = Math.round(uz * (r + dr) + vz * w);
      if (!get(X, y, Z)) set(X, y, Z, (y < CLOUD_Y + 10 && h3(X, y, Z, 2) < 0.35) ? FOAM : WATER);
    }
  }
  mist.push({ x: ux * (R + 3), y: CLOUD_Y + 6, z: uz * (R + 3) });
  // 공원 나무
  for (let t = 0; t < 400; t++) {
    const a = (180 + rnd() * 60) / 360 * TAU, r = 16 + rnd() * (INNER - 20);
    const x = Math.round(Math.cos(a) * r), z = Math.round(Math.sin(a) * r);
    let ok = true;
    for (let i = -2; i <= 2 && ok; i++) for (let j = -2; j <= 2; j++) if (occ[O(x + i, z + j)]) { ok = false; break; }
    if (!ok || get(x, IY, z) !== GRASS && get(x, IY, z) !== FLOWER) continue;
    if (rnd() < 0.5) bigOak(x, IY, z); else spruceTree(x, IY, z);
    for (let i = -3; i <= 3; i++) for (let j = -3; j <= 3; j++) occ[O(x + i, z + j)] = 2;
  }
  // 정자
  const gzx = Math.round(Math.cos(197 / 360 * TAU) * 24), gzz = Math.round(Math.sin(197 / 360 * TAU) * 24);
  box(gzx - 3, IY, gzz - 3, gzx + 3, IY, gzz + 3, POLISH);
  for (const [a, c] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) for (let j = 1; j <= 4; j++) set(gzx + a, IY + j, gzz + c, BRASS);
  for (let a = -4; a <= 4; a++) for (let c = -4; c <= 4; c++) for (let j = 0; j <= 4; j++) {
    const r = Math.hypot(a, c, j * 1.1);
    if (r <= 4.5 && r > 3.4) set(gzx + a, IY + 5 + j, gzz + c, ROOFT);
  }
  set(gzx, IY + 10, gzz, GOLD); set(gzx, IY + 4, gzz, LAMP);

  // 시장 노점 (섹터 2)
  for (let i = 0; i < 6; i++) {
    const a = (132 + i * 8) / 360 * TAU, r = 42;
    const x = Math.round(Math.cos(a) * r), z = Math.round(Math.sin(a) * r);
    let ok = true;
    for (let p = -2; p <= 2; p++) for (let q = -2; q <= 2; q++) if (occ[O(x + p, z + q)]) ok = false;
    if (!ok) continue;
    for (const [p, q] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) for (let j = 1; j <= 3; j++) set(x + p, IY + j, z + q, SPRUCE);
    for (let p = -2; p <= 2; p++) for (let q = -2; q <= 2; q++) set(x + p, IY + 4, z + q, (p + 2) % 2 ? (i % 2 ? RED : BROWN) : CANVAS);
    set(x, IY + 1, z, i % 2 ? HAY : OAK);
    for (let p = -2; p <= 2; p++) for (let q = -2; q <= 2; q++) occ[O(x + p, z + q)] = 2;
  }

  // 부두 (0° 방향, +x) — 바큇살 도로가 그대로 이어진다
  for (let x = INNER - 2; x <= R + 28; x++) for (let z = -4; z <= 4; z++) {
    set(x, IY, z, x > R + 6 ? SPRUCE : SBRICK);
    set(x, IY + 1, z, 0);
    if (x > R && (x % 4 === 0)) set(x, IY - 1, z, DARK);
    if (Math.abs(z) === 4 && x > R) { if (x % 2 === 0) set(x, IY + 1, z, DIRON); set(x, IY + 2, z, SPRUCE); }
  }
  for (let x = R + 4; x <= R + 28; x += 6) for (let t = 1; t <= 10; t++) { set(x - t * 0.8, IY - t, -3, DIRON); set(x - t * 0.8, IY - t, 3, DIRON); }
  lampPost(R + 28, -4); lampPost(R + 28, 4); lampPost(R + 16, -4); lampPost(R + 16, 4);
  // 크레인
  for (let y = 1; y <= 14; y++) { set(R + 10, IY + y, -6, DIRON); set(R + 11, IY + y, -6, y % 3 ? 0 : DIRON); }
  for (let z = -6; z <= 12; z++) set(R + 10, IY + 15, z, z % 3 ? DIRON : BRASS);
  for (let y = IY + 9; y <= IY + 14; y++) set(R + 10, y, 10, DIRON);
  box(R + 9, IY + 7, 9, R + 11, IY + 8, 11, SPRUCE);

  // 주거 지구 (섹터 0, 2, 4, 5)
  const roofs = [ROOFR, ROOFT, ROOFC, ROOFR];
  for (let t = 0; t < 3000; t++) {
    const w = 7 + Math.floor(rnd() * 4), d = 6 + Math.floor(rnd() * 3);
    const a = rnd() * TAU, r = 17 + rnd() * (INNER - 21);
    const x0 = Math.round(Math.cos(a) * r - w / 2), z0 = Math.round(Math.sin(a) * r - d / 2);
    let ok = true;
    for (let x = x0 - 1; x <= x0 + w && ok; x++) for (let z = z0 - 1; z <= z0 + d; z++) {
      if (occ[O(x, z)] || Math.hypot(x, z) > INNER - 4) { ok = false; break; }
      const s = sectorOf(x, z); if (s === 1 || s === 3) { ok = false; break; }
    }
    if (!ok) continue;
    const fl = rnd() < 0.25 ? 3 : (rnd() < 0.6 ? 2 : 1);
    house(x0, z0, w, d, fl, roofs[Math.floor(rnd() * roofs.length)]);
    for (let x = x0 - 1; x <= x0 + w; x++) for (let z = z0 - 1; z <= z0 + d; z++) occ[O(x, z)] = 2;
  }
  // 빈 녹지에 작은 나무
  for (let t = 0; t < 600; t++) {
    const a = rnd() * TAU, r = 16 + rnd() * (INNER - 20);
    const x = Math.round(Math.cos(a) * r), z = Math.round(Math.sin(a) * r);
    let ok = true;
    for (let i = -2; i <= 2 && ok; i++) for (let j = -2; j <= 2; j++) if (occ[O(x + i, z + j)]) { ok = false; break; }
    if (!ok) continue;
    if (rnd() < 0.6) bigOak(x, IY, z); else spruceTree(x, IY, z);
    for (let i = -3; i <= 3; i++) for (let j = -3; j <= 3; j++) occ[O(x + i, z + j)] = 2;
  }

  // 섬 아래 매달린 등불
  for (let i = 0; i < 26; i++) {
    const a = i / 26 * TAU + 0.1, r = R - 10 - (i % 3) * 7;
    const x = Math.round(Math.cos(a) * r), z = Math.round(Math.sin(a) * r);
    let y = IY - 7; while (get(x, y, z) && y > 0) y--;
    const L = 3 + (i * 7) % 9;
    for (let j = 0; j < L; j++) set(x, y - j, z, DIRON);
    set(x, y - L, z, LAMP); set(x, y - L - 1, z, DIRON);
  }

  // 엔진 3기
  engine(R, '+z', IY - 14);
  engine(R, '-z', IY - 14);
  engine(R, '-x', IY - 14);

  // 위성섬
  const s1 = gearIsland(-128, IY - 18, -62, 17, 12, { td: 3, band: 3, depth: 22, seed: 7, stal: 12, disc: 4 });
  {
    const cx = -128, cz = -62, y = IY - 17;
    for (let a = -7; a <= 7; a++) for (let c = -7; c <= 7; c++) for (let j = 0; j <= 7; j++) {
      const r = Math.hypot(a, c, j);
      if (r <= 7.4 && r > 6.3) set(cx + a, y + j, cz + c, (Math.abs(a - c) <= 1 && j > 2) ? GLASS : ROOFC);
    }
    for (let a = -7; a <= 7; a++) for (let c = -7; c <= 7; c++) if (Math.hypot(a, c) <= 7.4 && Math.hypot(a, c) > 6.3) set(cx + a, y - 1, cz + c, SBRICK);
    for (let t = 0; t < 12; t++) for (let q = -1; q <= 1; q++) set(cx + 2 + t * 0.7, y + 6 + t * 0.6, cz + 2 + t * 0.7 + q * 0.5, t > 10 ? GOLD : BRASS);
    lampPost(cx + 9, cz - 3, IY - 18); lampPost(cx - 9, cz + 3, IY - 18);
    spruceTree(cx - 8, IY - 18, cz - 8); bigOak(cx + 6, IY - 18, cz + 9);
  }
  const s2 = gearIsland(150, IY - 26, 62, 15, 12, { td: 3, band: 3, depth: 20, seed: 11, stal: 10, disc: 4 });
  {
    const cx = 150, cz = 62, y0 = IY - 25;
    for (let j = 0; j < 36; j++) for (let a = -4; a <= 4; a++) for (let c = -4; c <= 4; c++) {
      const r = Math.hypot(a, c), rad = 3.8 - j * 0.035;
      if (r > rad || r < rad - 1.2) continue;
      set(cx + a, y0 + j, cz + c, (Math.floor(j / 5) % 2) ? RED : PLASTER);
    }
    for (let a = -5; a <= 5; a++) for (let c = -5; c <= 5; c++) if (Math.hypot(a, c) <= 5.2) set(cx + a, y0 + 36, cz + c, DIRON);
    for (let j = 37; j <= 41; j++) for (let a = -3; a <= 3; a++) for (let c = -3; c <= 3; c++) { const r = Math.hypot(a, c); if (r <= 3.2 && r > 2.2) set(cx + a, y0 + j, cz + c, GLASS); }
    box(cx - 1, y0 + 37, cz - 1, cx + 1, y0 + 40, cz + 1, LAMP);
    for (let j = 0; j <= 3; j++) for (let a = -4; a <= 4; a++) for (let c = -4; c <= 4; c++) { const r = Math.hypot(a, c, j * 1.3); if (r <= 4.2 && r > 3.1) set(cx + a, y0 + 42 + j, cz + c, ROOFC); }
    set(cx, y0 + 47, cz, GOLD); set(cx, y0 + 48, cz, GOLD);
    house(cx + 5, cz - 9, 7, 6, 1, ROOFT, y0, { chimney: true });
  }
  const s3 = gearIsland(22, IY + 30, -150, 17, 12, { td: 3, band: 3, depth: 22, seed: 17, stal: 12, disc: 4 });
  {
    const cx = 22, cz = -150, y = IY + 30;
    for (let x = -10; x <= 2; x++) for (let z = -8; z <= 8; z++) { if (Math.hypot(x, z) > 13) continue; set(cx + x, y, cz + z, (z % 3 === 0) ? WATER : (x % 2 ? DIRT : PATH)); if (z % 3 !== 0) setE(cx + x, y + 1, cz + z, (x + z) % 4 === 0 ? HAY : 0); }
    house(cx + 4, cz - 5, 8, 7, 1, ROOFR, y + 1, { chimney: true, stoneBase: false });
    for (let j = 1; j <= 18; j++) set(cx + 10, y + j, cz + 6, DIRON);
    for (let t = -7; t <= 7; t++) { set(cx + 11, y + 18 + t, cz + 6, t === 0 ? BRASS : CANVAS); set(cx + 11, y + 18, cz + 6 + t, t === 0 ? BRASS : CANVAS); }
    bigOak(cx - 4, y, cz + 11);
  }
  gearIsland(-112, IY - 44, 118, 11, 9, { td: 2, band: 2, depth: 18, seed: 23, stal: 8, disc: 3 });
  bigOak(-112, IY - 44, 118);

  // 떠다니는 바위 조각
  for (let i = 0; i < 12; i++) {
    const a = rnd() * TAU, r = 110 + rnd() * 80, x = Math.cos(a) * r, z = Math.sin(a) * r, y = IY - 40 + rnd() * 90;
    const s = 1.5 + rnd() * 3;
    for (let p = -4; p <= 4; p++) for (let q = -6; q <= 2; q++) for (let w = -4; w <= 4; w++) {
      const k = (p * p + w * w) / (s * s) + (q < 0 ? (q * q) / (s * s * 2.5) : (q * q) / (s * s * 0.3));
      if (k <= 1) set(x + p, y + q, z + w, q === 0 || q === 1 && k < 0.3 ? GRASS : (h3(p, q, w, i) < 0.03 ? CRYSTAL : (q < -2 ? DEEP : STONE)));
    }
  }

  // 다리
  bridge([-R + 4, IY, -24], [-114, IY - 18, -55]);
  bridge([46, IY, 30], [137, IY - 26, 56]);

  // 비행선
  const ships = {};
  ships.docked = airship(R + 16, IY + 14, 16, 40, 'x', 1, { env: CANVAS, stripe: BROWN, fin: RED, roof: ROOFC });
  ships.hero = airship(-44, IY + 34, 92, 46, 'x', 1, { env: WOOL, stripe: RED, stripe2: RED, fin: RED, roof: ROOFT, flag: RED });
  ships.b = airship(96, IY + 36, -58, 34, 'z', -1, { env: CANVAS, stripe: CUTCOP, fin: BROWN, roof: ROOFR });
  ships.c = airship(-40, IY + 78, -126, 30, 'x', -1, { env: WOOL, stripe: OXID, fin: OXID, roof: ROOFC });
  ships.d = airship(150, IY + 64, 8, 24, 'z', 1, { env: CANVAS, stripe: RED, fin: RED, roof: ROOFT });
  ships.e = airship(-150, IY + 30, 24, 26, 'z', -1, { env: WOOL, stripe: BROWN, fin: BROWN, roof: ROOFR });

  cams.ships = ships;
  cams.towerTop = towerTop;
  cams.R = R;
  cams.wf = wf;
}
