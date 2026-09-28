// =====================================================================
//  복셀 → 메시 (보이는 면만, 꼭짓점 AO)
// =====================================================================
import * as THREE from 'three';
import { TC, TR, h3 } from './textures.js';
import { V, SX, SY, SZ, OX, OZ, BL, OPAQ, G } from './world.js';

const DIRS = [
  { n: [1, 0, 0], u: [0, 0, -1], v: [0, 1, 0], f: 'side' },
  { n: [-1, 0, 0], u: [0, 0, 1], v: [0, 1, 0], f: 'side' },
  { n: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0], f: 'side' },
  { n: [0, 0, -1], u: [-1, 0, 0], v: [0, 1, 0], f: 'side' },
  { n: [0, 1, 0], u: [0, 0, 1], v: [1, 0, 0], f: 'top' },
  { n: [0, -1, 0], u: [1, 0, 0], v: [0, 0, 1], f: 'bot' },
];
const AO = [0.32, 0.56, 0.78, 1.0];

export function buildMeshes() {
  const stride = SY * SZ;
  const at = (x, y, z) => {
    if (x < -OX || x >= SX - OX || y < 0 || y >= SY || z < -OZ || z >= SZ - OZ) return 0;
    return V[(x + OX) * stride + y * SZ + (z + OZ)];
  };
  const solid = (x, y, z) => OPAQ[at(x, y, z)];
  const buf = {};
  const B = g => (buf[g] ??= { p: [], n: [], uv: [], c: [], i: [] });
  const eps = 0.02;

  for (let xi = 0; xi < SX; xi++) for (let y = 0; y < SY; y++) {
    const base = xi * stride + y * SZ;
    for (let zi = 0; zi < SZ; zi++) {
      const id = V[base + zi];
      if (!id) continue;
      const x = xi - OX, z = zi - OZ;
      const bl = BL[id];
      for (const D of DIRS) {
        const nb = at(x + D.n[0], y + D.n[1], z + D.n[2]);
        if (nb && (OPAQ[nb] || nb === id)) continue;
        const tile = D.f === 'top' ? bl.top : (D.f === 'bot' ? bl.bot : bl.side);
        const col = tile % TC, row = Math.floor(tile / TC);
        const u0 = (col + eps) / TC, u1 = (col + 1 - eps) / TC;
        const v0 = 1 - (row + 1 - eps) / TR, v1 = 1 - (row + eps) / TR;
        const s = [x, y, z];
        for (let k = 0; k < 3; k++) { if (D.n[k] > 0) s[k] += 1; if (D.u[k] < 0) s[k] += 1; if (D.v[k] < 0) s[k] += 1; }
        const cx = x + D.n[0], cy = y + D.n[1], cz = z + D.n[2];
        const tint = 0.95 + h3(x, y, z, 77) * 0.07;
        const g = B(bl.g);
        const vi = g.p.length / 3;
        const ao = [];
        for (const [i, j] of [[0, 0], [1, 0], [1, 1], [0, 1]]) {
          const du = i ? 1 : -1, dv = j ? 1 : -1;
          const s1 = solid(cx + du * D.u[0], cy + du * D.u[1], cz + du * D.u[2]);
          const s2 = solid(cx + dv * D.v[0], cy + dv * D.v[1], cz + dv * D.v[2]);
          const cr = solid(cx + du * D.u[0] + dv * D.v[0], cy + du * D.u[1] + dv * D.v[1], cz + du * D.u[2] + dv * D.v[2]);
          const a = (s1 && s2) ? 0 : 3 - (s1 + s2 + cr);
          ao.push(a);
          g.p.push(s[0] + i * D.u[0] + j * D.v[0], s[1] + i * D.u[1] + j * D.v[1], s[2] + i * D.u[2] + j * D.v[2]);
          g.n.push(D.n[0], D.n[1], D.n[2]);
          g.uv.push(i ? u1 : u0, j ? v1 : v0);
          const l = (bl.g === G.EMIT ? Math.max(0.8, AO[a]) : AO[a]) * tint;
          g.c.push(l, l, l);
        }
        if (ao[0] + ao[2] > ao[1] + ao[3]) g.i.push(vi, vi + 1, vi + 2, vi, vi + 2, vi + 3);
        else g.i.push(vi + 1, vi + 2, vi + 3, vi + 1, vi + 3, vi);
      }
    }
  }
  const out = {};
  for (const g in buf) {
    const b = buf[g];
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(b.p, 3));
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(b.n, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(b.c, 3));
    geo.setIndex(new THREE.Uint32BufferAttribute(b.i, 1));
    geo.computeBoundingSphere();
    out[g] = geo;
  }
  return out;
}
