// =====================================================================
//  성 밖 도로 — 지형을 따라가되 높이를 부드럽게, 물을 만나면 다리
// =====================================================================
import { S, mix } from './lib.js';
import { height, waterTop, col, inside, setGround, reserved, H, surf } from '../world.js';
import { ROADS, CITY } from '../plan.js';
import { catmull } from '../terrain.js';
import { samples, PAVE, lampPost } from './paint.js';
import { stoneBridge } from './civic.js';
import { simplex, hash2 } from '../noise.js';

const wet = (x, z) => inside(x, z) && waterTop[col(x, z)] > height[col(x, z)];
export const roadCells = new Set();

export function buildRoads() {
  let bridges = 0;
  for (const R of ROADS) {
    let pts = catmull(R.pts, 2);
    pts = pts.map((p, i) => (i === 0 || i === pts.length - 1) ? p : [p[0] + simplex(p[1] / 70, 0.3, 91) * 5, p[1] + simplex(p[0] / 70, 0.7, 92) * 5]);
    const sm = samples(pts, 1);
    const hs = sm.map(s => H(s[0], s[1]));
    const target = hs.map((_, i) => { let a = 0, n = 0; for (let k = -10; k <= 10; k++) { const j = i + k; if (j >= 0 && j < hs.length) { a += hs[j]; n++; } } return Math.round(a / n); });
    // 물 구간 → 다리
    let run = null;
    for (let i = 0; i < sm.length; i++) {
      const w = wet(Math.round(sm[i][0]), Math.round(sm[i][1]));
      if (w && run === null) run = i;
      if ((!w || i === sm.length - 1) && run !== null) {
        const i0 = Math.max(0, run - 4), i1 = Math.min(sm.length - 1, i + 3);
        if (i - run >= 2) {
          const deck = Math.max(66, H(sm[i0][0], sm[i0][1]) + 1, H(sm[i1][0], sm[i1][1]) + 1);
          stoneBridge(Math.round(sm[i0][0]), Math.round(sm[i0][1]), Math.round(sm[i1][0]), Math.round(sm[i1][1]), R.w + 2, deck);
          bridges++;
        }
        run = null;
      }
    }
    const done = new Set();
    for (let i = 0; i < sm.length; i++) {
      const [px, pz, tx, tz] = sm[i];
      if (Math.hypot(px - CITY.x, pz - CITY.z) < CITY.R + 8) continue;
      for (let off = -R.w / 2; off <= R.w / 2 + 0.01; off += 0.5) {
        const x = Math.round(px - tz * off), z = Math.round(pz + tx * off);
        if (!inside(x, z)) continue;
        const c = col(x, z);
        if (done.has(c)) continue;
        done.add(c);
        if (reserved[c] >= 2 || wet(x, z)) continue;
        const h = height[c], t = target[i];
        if (Math.abs(h - t) <= 3) setGround(x, z, t);
        const edge = Math.abs(off) > R.w / 2 - 0.9;
        if (!edge || hash2(x, z, 7) < 0.55) { surf[c] = edge ? PAVE.edge(x, t, z) : PAVE.road(x, t, z); }
        reserved[c] = Math.max(reserved[c], 1);
        roadCells.add(c);
      }
      if (i % 48 === 24) {
        const side = (i / 48) % 2 ? 1 : -1;
        const x = Math.round(px - tz * side * (R.w / 2 + 1.5)), z = Math.round(pz + tx * side * (R.w / 2 + 1.5));
        if (inside(x, z) && reserved[col(x, z)] === 0 && !wet(x, z)) lampPost(x, z, 'wood');
      }
    }
  }
  return bridges;
}
