// =====================================================================
//  월드 → 렌더용 메시 (Node 에서 실행, 결과를 render/cache 에 저장)
//   가까운 곳: 블록 모델 그대로 (계단·반블록·울타리·판유리·담장·문·덧창·랜턴·식물…)
//   먼 곳:     4칸 단위 LOD 높이 메시
//   node --max-old-space-size=12000 render/mesh.js <view> [<view> ...]
// =====================================================================
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '../gen/main.js';
import { STATES, resolveConn } from '../gen/registry.js';
import { getPlaced, terrainAt, get, HALF, height, waterTop, col, secGet, inside } from '../gen/world.js';
import { chimneys } from '../gen/build/house.js';
import { topOf, colorOf } from '../gen/mapimg.js';
import { TILE, COLS, ROWS, buildAtlasRGBA } from './tiles.js';
import { VIEWS } from './views.js';
import { writePNG } from './png.js';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const CACHE = path.join(ROOT, 'cache');
fs.mkdirSync(CACHE, { recursive: true });

// ── 블록 조회 (연결형 속성 확정)
const connMemo = new Map();
function B(x, y, z) {
  if (!inside(x, z) || y < -64 || y > 319) return 1;
  const p = getPlaced(x, y, z);
  if (!p) return terrainAt(x, y, z);
  if (STATES[p].def.conn) {
    const k = ((x + 2048) * 4096 + (z + 2048)) * 512 + (y + 64);
    let r = connMemo.get(k);
    if (r === undefined) { r = resolveConn(get, x, y, z, p); connMemo.set(k, r); }
    return r;
  }
  return p;
}
const full = id => id > 1 && STATES[id].def.full && STATES[id].def.cat === 'opaque' || (id > 1 && STATES[id].def.full && STATES[id].def.cat === 'emit');
const occ = id => id > 1 && STATES[id].def.full && (STATES[id].def.cat === 'opaque' || STATES[id].def.cat === 'emit');

// ── 출력 버퍼
class G {
  constructor() { this.p = []; this.n = []; this.uv = []; this.c = []; this.i = []; }
  get vc() { return this.p.length / 3; }
}
const groups = {};
const grp = name => (groups[name] ??= new G());

function tileOf(name) {
  const t = TILE[name];
  if (t === undefined) { missing.add(name); return TILE.stone; }
  return t;
}
const missing = new Set();
const ATW = COLS * 16, ATH = ROWS * 16;
function uvOf(tile, px, py) { // px,py: 0..16 (py 아래로)
  const cx = (tile % COLS) * 16, cy = Math.floor(tile / COLS) * 16;
  return [(cx + px) / ATW, 1 - (cy + py) / ATH];
}

// 면 하나 (정점 4개, 반시계). pts: [[x,y,z]*4] 1/16 단위, uvs: [[px,py]*4]
function quad(g, pts, nrm, tile, uvs, cols, flip = false) {
  const vi = g.vc;
  for (let k = 0; k < 4; k++) {
    g.p.push(pts[k][0], pts[k][1], pts[k][2]);
    g.n.push(nrm[0], nrm[1], nrm[2]);
    const [u, v] = uvOf(tile, Math.min(16, Math.max(0, uvs[k][0])), Math.min(16, Math.max(0, uvs[k][1])));
    g.uv.push(u, v);
    g.c.push(cols[k], cols[k], cols[k]);
  }
  if (flip) g.i.push(vi + 1, vi + 2, vi + 3, vi + 1, vi + 3, vi);
  else g.i.push(vi, vi + 1, vi + 2, vi, vi + 2, vi + 3);
}

const FACES = {
  // 각 면: 법선, 면 위 4점을 만드는 함수 (박스 from/to → 점), uv 함수
  east: { n: [1, 0, 0], d: [1, 0, 0] }, west: { n: [-1, 0, 0], d: [-1, 0, 0] },
  up: { n: [0, 1, 0], d: [0, 1, 0] }, down: { n: [0, -1, 0], d: [0, -1, 0] },
  south: { n: [0, 0, 1], d: [0, 0, 1] }, north: { n: [0, 0, -1], d: [0, 0, -1] },
};
// 박스의 한 면 → 4점(반시계, 바깥에서 볼 때) + uv
function faceGeom(face, f, t) {
  const [x0, y0, z0] = f, [x1, y1, z1] = t;
  switch (face) {
    case 'east': return { p: [[x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1]], uv: [[16 - z1, 16 - y0], [16 - z0, 16 - y0], [16 - z0, 16 - y1], [16 - z1, 16 - y1]] };
    case 'west': return { p: [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]], uv: [[z0, 16 - y0], [z1, 16 - y0], [z1, 16 - y1], [z0, 16 - y1]] };
    case 'south': return { p: [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], uv: [[x0, 16 - y0], [x1, 16 - y0], [x1, 16 - y1], [x0, 16 - y1]] };
    case 'north': return { p: [[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]], uv: [[16 - x1, 16 - y0], [16 - x0, 16 - y0], [16 - x0, 16 - y1], [16 - x1, 16 - y1]] };
    case 'up': return { p: [[x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0]], uv: [[x0, z1], [x1, z1], [x1, z0], [x0, z0]] };
    case 'down': return { p: [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], uv: [[x0, z0], [x1, z0], [x1, z1], [x0, z1]] };
  }
}
const FACE_NAMES = ['east', 'west', 'up', 'down', 'south', 'north'];
const NB = { east: [1, 0, 0], west: [-1, 0, 0], up: [0, 1, 0], down: [0, -1, 0], south: [0, 0, 1], north: [0, 0, -1] };
const SHADE = { up: 1, down: 0.62, north: 0.86, south: 0.86, east: 0.93, west: 0.93 };

// 박스 하나 출력. texOf(face) → 타일 이름. 블록 경계에 닿은 면은 불투명 이웃이면 생략
function emitBox(g, x, y, z, f, t, texOf, opts = {}) {
  for (const face of FACE_NAMES) {
    if (opts.skip && opts.skip.includes(face)) continue;
    const onEdge = (face === 'east' && t[0] === 16) || (face === 'west' && f[0] === 0) || (face === 'up' && t[1] === 16) || (face === 'down' && f[1] === 0) || (face === 'south' && t[2] === 16) || (face === 'north' && f[2] === 0);
    if (onEdge) { const d = NB[face]; if (occ(B(x + d[0], y + d[1], z + d[2]))) continue; }
    const gm = faceGeom(face, f, t);
    const pts = gm.p.map(p => [x * 16 + p[0], y * 16 + p[1], z * 16 + p[2]]);
    const l = opts.light ?? 1;
    quad(g, pts, FACES[face].n, tileOf(texOf(face)), gm.uv, [l, l, l, l]);
  }
}

// 풀 큐브 (AO 포함)
const AOV = [0.42, 0.62, 0.8, 1.0];
function emitCube(g, x, y, z, texOf, tint = 1) {
  for (const face of FACE_NAMES) {
    const d = NB[face];
    const nb = B(x + d[0], y + d[1], z + d[2]);
    if (occ(nb)) continue;
    if (g === groups.cutout && nb > 1 && STATES[nb].def.leaves && STATES[nb].name === STATES[B(x, y, z)].name && face !== 'up' && face !== 'down') continue;
    const gm = faceGeom(face, [0, 0, 0], [16, 16, 16]);
    // AO: 면 바깥쪽 칸의 이웃 3개
    const cx = x + d[0], cy = y + d[1], cz = z + d[2];
    const ao = SIMPLE ? [tint, tint, tint, tint] : gm.p.map(p => {
      const sx = p[0] ? 1 : -1, sy = p[1] ? 1 : -1, sz = p[2] ? 1 : -1;
      const axes = [[sx, 0, 0], [0, sy, 0], [0, 0, sz]].filter((a, k) => d[k] === 0);
      const s1 = occ(B(cx + axes[0][0], cy + axes[0][1], cz + axes[0][2])) ? 1 : 0;
      const s2 = occ(B(cx + axes[1][0], cy + axes[1][1], cz + axes[1][2])) ? 1 : 0;
      const c = occ(B(cx + axes[0][0] + axes[1][0], cy + axes[0][1] + axes[1][1], cz + axes[0][2] + axes[1][2])) ? 1 : 0;
      return AOV[s1 && s2 ? 0 : 3 - (s1 + s2 + c)] * tint;
    });
    const pts = gm.p.map(p => [x * 16 + p[0], y * 16 + p[1], z * 16 + p[2]]);
    quad(g, pts, FACES[face].n, tileOf(texOf(face)), gm.uv, ao, ao[0] + ao[2] < ao[1] + ao[3]);
  }
}

// 16단위 박스 회전 (북쪽 기준 → facing)
function rot(box, facing) {
  const [[x0, y0, z0], [x1, y1, z1]] = box;
  const r = (x, z) => facing === 'east' ? [16 - z, x] : facing === 'south' ? [16 - x, 16 - z] : facing === 'west' ? [z, 16 - x] : [x, z];
  const a = r(x0, z0), b = r(x1, z1);
  return [[Math.min(a[0], b[0]), y0, Math.min(a[1], b[1])], [Math.max(a[0], b[0]), y1, Math.max(a[1], b[1])]];
}
function crossQuads(g, x, y, z, tile, kind = 'cross', h = 16, off = [0, 0, 0]) {
  const X = x * 16 + off[0], Y = y * 16 + off[1], Z = z * 16 + off[2];
  const planes = kind === 'crop'
    ? [[[4, 0], [4, 16]], [[12, 16], [12, 0]], [[0, 4], [16, 4]], [[16, 12], [0, 12]]]
    : [[[1.5, 1.5], [14.5, 14.5]], [[1.5, 14.5], [14.5, 1.5]]];
  for (const [[ax, az], [bx, bz]] of planes) {
    const pts = [[X + ax, Y, Z + az], [X + bx, Y, Z + bz], [X + bx, Y + h, Z + bz], [X + ax, Y + h, Z + az]];
    const nx = bz - az, nz = -(bx - ax), nl = Math.hypot(nx, nz);
    quad(g, pts, [nx / nl, 0, nz / nl], tile, [[0, 16], [16, 16], [16, 16 - h], [0, 16 - h]], [1, 1, 1, 1]);
  }
}

// 먼 거리 청크: 작은 소품은 생략하고 AO 도 생략
let SIMPLE = false;
const SMALL = new Set(['cross', 'crop', 'flat', 'carpet', 'pot', 'lantern', 'chain', 'trapdoor', 'door', 'pane', 'fence', 'wall']);

function emitBlock(x, y, z, id) {
  const st = STATES[id], d = st.def, pr = st.props;
  if (d.model === 'none') return;
  if (SIMPLE && SMALL.has(d.model)) return;
  const tex = d.tex;
  const T3 = face => (face === 'up' ? tex.top : face === 'down' ? tex.bottom : tex.side);
  const g = grp(d.cat === 'cutout' ? 'cutout' : d.cat === 'trans' ? (st.name === 'water' ? 'water' : 'trans') : d.cat === 'emit' ? 'emit' : 'opaque');
  switch (d.model) {
    case 'cube': {
      if (d.h) { emitBox(g, x, y, z, [0, 0, 0], [16, d.h, 16], T3); break; }
      emitCube(g, x, y, z, T3);
      break;
    }
    case 'column': {
      const ax = pr.axis || 'y';
      const texOf = face => {
        const endFace = (ax === 'y' && (face === 'up' || face === 'down')) || (ax === 'x' && (face === 'east' || face === 'west')) || (ax === 'z' && (face === 'north' || face === 'south'));
        return endFace ? tex.top : tex.side;
      };
      emitCube(g, x, y, z, texOf);
      break;
    }
    case 'slab': {
      const t = pr.type || 'bottom';
      if (t === 'double') emitCube(g, x, y, z, T3);
      else emitBox(g, x, y, z, [0, t === 'top' ? 8 : 0, 0], [16, t === 'top' ? 16 : 8, 16], T3);
      break;
    }
    case 'stairs': {
      const top = pr.half === 'top';
      emitBox(g, x, y, z, [0, top ? 8 : 0, 0], [16, top ? 16 : 8, 16], T3);
      const b = rot([[0, top ? 0 : 8, 0], [16, top ? 8 : 16, 8]], pr.facing || 'north');
      emitBox(g, x, y, z, b[0], b[1], T3);
      break;
    }
    case 'fence': {
      emitBox(g, x, y, z, [6, 0, 6], [10, 16, 10], T3);
      for (const dn of ['north', 'south', 'east', 'west']) if (pr[dn] === 'true') {
        for (const [y0, y1] of [[12, 15], [6, 9]]) { const b = rot([[7, y0, 0], [9, y1, 6]], dn); emitBox(g, x, y, z, b[0], b[1], T3); }
      }
      break;
    }
    case 'pane': {
      const any = ['north', 'south', 'east', 'west'].some(k => pr[k] === 'true');
      emitBox(g, x, y, z, [7, 0, 7], [9, 16, 9], () => tex.side);
      for (const dn of ['north', 'south', 'east', 'west']) if (pr[dn] === 'true' || !any) {
        const b = rot([[7, 0, 0], [9, 16, 7]], dn); emitBox(g, x, y, z, b[0], b[1], () => tex.side);
      }
      break;
    }
    case 'wall': {
      if (pr.up !== 'false') emitBox(g, x, y, z, [4, 0, 4], [12, 16, 12], T3);
      for (const dn of ['north', 'south', 'east', 'west']) if (pr[dn] && pr[dn] !== 'none') {
        const b = rot([[5, 0, 0], [11, pr[dn] === 'tall' ? 16 : 14, 8]], dn); emitBox(g, x, y, z, b[0], b[1], T3);
      }
      break;
    }
    case 'cross': {
      let t = tex.side;
      crossQuads(g, x, y, z, tileOf(t));
      break;
    }
    case 'crop': crossQuads(g, x, y, z, tileOf(tex.side), 'crop'); break;
    case 'lantern': {
      const hang = pr.hanging === 'true';
      const o = hang ? 1 : 0;
      emitBox(g, x, y, z, [5, o, 5], [11, 7 + o, 11], () => 'lantern', { light: 1 });
      emitBox(grp('opaque'), x, y, z, [6, 7 + o, 6], [10, 9 + o, 10], () => 'polished_blackstone_bricks');
      if (hang) emitBox(grp('cutout'), x, y, z, [7.5, 9 + o, 7.5], [8.5, 16, 8.5], () => 'chain');
      break;
    }
    case 'chain': emitBox(g, x, y, z, [7, 0, 7], [9, 16, 9], () => 'chain'); break;
    case 'trapdoor': {
      let b;
      if (pr.open === 'true') b = { north: [[0, 0, 13], [16, 16, 16]], south: [[0, 0, 0], [16, 16, 3]], west: [[13, 0, 0], [16, 16, 16]], east: [[0, 0, 0], [3, 16, 16]] }[pr.facing];
      else b = pr.half === 'top' ? [[0, 13, 0], [16, 16, 16]] : [[0, 0, 0], [16, 3, 16]];
      emitBox(g, x, y, z, b[0], b[1], () => tex.side);
      break;
    }
    case 'door': {
      const b = { east: [[0, 0, 0], [3, 16, 16]], west: [[13, 0, 0], [16, 16, 16]], south: [[0, 0, 0], [16, 16, 3]], north: [[0, 0, 13], [16, 16, 16]] }[pr.facing];
      emitBox(g, x, y, z, b[0], b[1], () => (pr.half === 'upper' ? tex.top : tex.side));
      break;
    }
    case 'flat': emitBox(g, x, y, z, [0, 0, 0], [16, 0.25, 16], () => tex.side, { skip: ['down', 'north', 'south', 'east', 'west'] }); break;
    case 'carpet': emitBox(grp('opaque'), x, y, z, [0, 0, 0], [16, 1, 16], () => tex.side); break;
    case 'pot': {
      emitBox(grp('opaque'), x, y, z, [5, 0, 5], [11, 6, 11], () => 'flower_pot');
      crossQuads(grp('cutout'), x, y, z, tileOf(tex.side), 'cross', 10, [0, 5, 0]);
      break;
    }
    case 'water': {
      const above = B(x, y + 1, z);
      const top = STATES[above].name === 'water' ? 16 : 14;
      for (const face of FACE_NAMES) {
        if (face === 'down') continue;
        const dd = NB[face];
        const nb = B(x + dd[0], y + dd[1], z + dd[2]);
        if (nb > 1 && (STATES[nb].name === 'water' || occ(nb))) continue;
        if (face === 'up' && top === 16) continue;
        const gm = faceGeom(face, [0, 0, 0], [16, top, 16]);
        const pts = gm.p.map(p => [x * 16 + p[0], y * 16 + p[1], z * 16 + p[2]]);
        quad(g, pts, FACES[face].n, tileOf('water'), gm.uv, [1, 1, 1, 1]);
      }
      break;
    }
  }
}

// ── 절두체
function camBasis(v) {
  const [px, py, pz] = v.pos, [tx, ty, tz] = v.tgt;
  let f = [tx - px, ty - py, tz - pz]; const fl = Math.hypot(...f); f = f.map(a => a / fl);
  let r = [f[2] * 0 - f[1] * 0, 0, 0];
  r = [-f[2], 0, f[0]]; const rl = Math.hypot(...r); r = r.map(a => a / rl);
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  return { f, r, u };
}
function inFrustum(v, B0, x0, y0, z0, x1, y1, z1) {
  const { f, r, u } = B0;
  const tv = Math.tan((v.fov * Math.PI / 180) / 2) * 1.08, th = tv * v.aspect;
  const corners = [];
  for (const x of [x0, x1]) for (const y of [y0, y1]) for (const z of [z0, z1]) {
    const d = [x - v.pos[0], y - v.pos[1], z - v.pos[2]];
    const cz = d[0] * f[0] + d[1] * f[1] + d[2] * f[2];
    const cx = d[0] * r[0] + d[1] * r[1] + d[2] * r[2];
    const cy = d[0] * u[0] + d[1] * u[1] + d[2] * u[2];
    corners.push([cx, cy, cz]);
  }
  const outside = test => corners.every(test);
  if (outside(c => c[2] < 0)) return false;
  if (outside(c => c[0] > c[2] * th)) return false;
  if (outside(c => c[0] < -c[2] * th)) return false;
  if (outside(c => c[1] > c[2] * tv)) return false;
  if (outside(c => c[1] < -c[2] * tv)) return false;
  return true;
}

function columnTop(x, z) {
  const c = col(x, z);
  let t = Math.max(height[c], waterTop[c]);
  for (let sy = 19; sy >= 0; sy--) if (secGet(x >> 4, sy, z >> 4)) { t = Math.max(t, sy * 16 + 15); break; }
  return t;
}

export function meshView(v) {
  for (const k of Object.keys(groups)) delete groups[k];
  const basis = camBasis(v);
  const det = new Set();
  const R = v.detail, R2 = Math.max(R, v.far ?? 1150);
  const c0 = -HALF / 16, c1 = HALF / 16 - 1;
  let blocks = 0;
  for (let cx = c0; cx <= c1; cx++) for (let cz = c0; cz <= c1; cz++) {
    const x0 = cx * 16, z0 = cz * 16;
    const dx = Math.max(x0 - v.pos[0], 0, v.pos[0] - (x0 + 16)), dz = Math.max(z0 - v.pos[2], 0, v.pos[2] - (z0 + 16));
    const dist = Math.hypot(dx, dz);
    if (dist > R2) continue;
    let yMin = 999, yMax = -64;
    for (let x = x0; x < x0 + 16; x++) for (let z = z0; z < z0 + 16; z++) { const c = col(x, z); yMin = Math.min(yMin, height[c]); yMax = Math.max(yMax, columnTop(x, z)); }
    if (!inFrustum(v, basis, x0, yMin - 20, z0, x0 + 16, yMax + 1, z0 + 16)) continue;
    det.add(cx * 1000 + cz);
    SIMPLE = dist > R;
    // 이 청크에서 구조물이 놓인 가장 낮은 섹션 (땅을 파낸 굴·문은 지표보다 아래에 있다)
    let placedLow = 9999;
    for (let sy = -4; sy < 20; sy++) if (secGet(cx, sy, cz)) { placedLow = sy * 16; break; }
    for (let x = x0; x < x0 + 16; x++) for (let z = z0; z < z0 + 16; z++) {
      const c = col(x, z);
      const h = height[c];
      let lo = h;
      for (const [ax, az] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (inside(x + ax, z + az)) lo = Math.min(lo, height[col(x + ax, z + az)] + 1);
      if (placedLow < lo) lo = Math.max(placedLow, lo - 64);
      const hi = columnTop(x, z);
      for (let y = Math.max(lo - 1, -63); y <= hi; y++) {
        const id = B(x, y, z);
        if (id <= 1) continue;
        emitBlock(x, y, z, id); blocks++;
      }
    }
  }
  SIMPLE = false;
  // LOD
  const S = 4, lod = grp('lod'), lodW = grp('lodwater');
  const hs = new Map();
  const cellTop = (i, j) => {
    const key = i * 10000 + j;
    let r = hs.get(key);
    if (!r) {
      const x = -HALF + i * S + 2, z = -HALF + j * S + 2;
      const [y, id] = topOf(x, z);
      r = { y: y + 1, c: colorOf(id), w: STATES[id].name === 'water' };
      hs.set(key, r);
    }
    return r;
  };
  const n = v.noLod ? 0 : (2 * HALF) / S;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const x = -HALF + i * S, z = -HALF + j * S;
    if (det.has((x >> 4) * 1000 + (z >> 4))) continue;
    const t = cellTop(i, j);
    const X = x * 16, Z = z * 16, Y = t.y * 16, s = S * 16;
    const g = t.w ? lodW : lod;
    const cc = t.c.map(q => q / 255);
    const vi = g.vc;
    for (const [px, pz] of [[0, s], [s, s], [s, 0], [0, 0]]) { g.p.push(X + px, Y, Z + pz); g.n.push(0, 1, 0); g.uv.push(0, 0); g.c.push(...cc); }
    g.i.push(vi, vi + 1, vi + 2, vi, vi + 2, vi + 3);
    // 옆 치마
    for (const [di, dj, face] of [[1, 0, 'east'], [-1, 0, 'west'], [0, 1, 'south'], [0, -1, 'north']]) {
      if (i + di < 0 || j + dj < 0 || i + di >= n || j + dj >= n) continue;
      const nt = cellTop(i + di, j + dj);
      if (nt.y >= t.y) continue;
      const f = [0, nt.y * 16 - Y, 0], tt = [0, 0, 0];
      const x0 = di === 1 ? s : 0, z0 = dj === 1 ? s : 0;
      let pts;
      if (di) pts = di > 0 ? [[x0, nt.y * 16 - Y, s], [x0, nt.y * 16 - Y, 0], [x0, 0, 0], [x0, 0, s]] : [[0, nt.y * 16 - Y, 0], [0, nt.y * 16 - Y, s], [0, 0, s], [0, 0, 0]];
      else pts = dj > 0 ? [[0, nt.y * 16 - Y, s], [s, nt.y * 16 - Y, s], [s, 0, s], [0, 0, s]] : [[s, nt.y * 16 - Y, 0], [0, nt.y * 16 - Y, 0], [0, 0, 0], [s, 0, 0]];
      const vj = lod.vc;
      for (const p of pts) { lod.p.push(X + p[0], Y + p[1], Z + p[2]); lod.n.push(...FACES[face].n); lod.uv.push(0, 0); lod.c.push(...cc.map(q => q * 0.8)); }
      lod.i.push(vj, vj + 1, vj + 2, vj, vj + 2, vj + 3);
    }
  }
  // 저장
  const meta = { view: v, groups: {}, tiles: TILE, chimneys: chimneys.filter(([x, y, z]) => Math.hypot(x - v.pos[0], z - v.pos[2]) < R && ((x * 73 + z * 131 + y * 7) & 1023) < 330) };
  const parts = [];
  let off = 0;
  const pushArr = (arr) => { const pad = (4 - (off % 4)) % 4; if (pad) { parts.push(Buffer.alloc(pad)); off += pad; } const b = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength); parts.push(b); const o = off; off += b.length; return o; };
  let faces = 0;
  for (const [name, g] of Object.entries(groups)) {
    if (!g.i.length) continue;
    faces += g.i.length / 6;
    meta.groups[name] = {
      count: g.vc, icount: g.i.length,
      p: pushArr(Int16Array.from(g.p)), n: pushArr(Int8Array.from(g.n, a => Math.round(a * 127))),
      uv: pushArr(Uint16Array.from(g.uv, a => Math.round(Math.min(1, Math.max(0, a)) * 65535))),
      c: pushArr(Uint8Array.from(g.c, a => Math.round(Math.min(1, a) * 255))),
      i: pushArr(Uint32Array.from(g.i)),
    };
  }
  fs.writeFileSync(path.join(CACHE, v.name + '.bin'), Buffer.concat(parts));
  fs.writeFileSync(path.join(CACHE, v.name + '.json'), JSON.stringify(meta));
  return { blocks, faces, chunks: det.size };
}

if (fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  generate();
  const atlas = buildAtlasRGBA();
  writePNG(path.join(CACHE, 'atlas.png'), atlas.W, atlas.H, atlas.buf, 4);
  const names = process.argv.slice(2);
  for (const nm of names.length ? names : Object.keys(VIEWS)) {
    const v = { name: nm, aspect: 16 / 9, ...structuredClone(VIEWS[nm]) };
    // stand: 카메라를 근처의 '서 있을 수 있는 땅'(지붕·물 제외)으로 옮기고 눈높이로
    if (v.stand) {
      const x0 = Math.round(v.pos[0]), z0 = Math.round(v.pos[2]);
      let found = null;
      for (let r = 0; r <= 20 && !found; r++) for (let dx = -r; dx <= r && !found; dx++) for (let dz = -r; dz <= r; dz++) {
        if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
        const x = x0 + dx, z = z0 + dz;
        const [y, id] = topOf(x, z);
        const st = STATES[id];
        if (st.name === 'water') continue;
        const plant = st.def.model === 'cross' || st.def.model === 'crop';
        const floor = plant ? y - 1 : y;
        if (floor > height[col(x, z)] + 1) continue;
        found = [x + 0.5, floor + 2.62, z + 0.5];
        break;
      }
      if (found) v.pos = found;
    }
    // '+22' 처럼 문자열 y 는 그 지점 지면(구조물 포함)으로부터의 높이
    for (const p of [v.pos, v.tgt]) if (typeof p[1] === 'string') p[1] = topOf(Math.round(p[0]), Math.round(p[2]))[0] + parseFloat(p[1]);
    const g0 = topOf(Math.round(v.pos[0]), Math.round(v.pos[2]))[0];
    if (v.pos[1] < g0 + 2.5) v.pos[1] = g0 + 2.5;
    const t = performance.now();
    const r = meshView(v);
    console.log(`[mesh] ${nm}: 청크 ${r.chunks}, 블록 ${r.blocks}, 면 ${r.faces} (${((performance.now() - t) / 1000).toFixed(1)}s)`);
  }
  if (missing.size) console.log('[mesh] 없는 텍스처:', [...missing].join(', '));
}
