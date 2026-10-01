import { Terrain, chaikin, simplifyPolyline, type MapData, type MapGrids } from '@warfront/shared';

/** Shared border between two territories (a < b), smoothed. */
export interface BorderChain {
  a: number;
  b: number;
  points: number[];
}

export interface TerritoryGeometry {
  /** Closed rings per territory (flat world coordinates). */
  rings: number[][][];
  paths: Path2D[];
  borders: BorderChain[];
}

const COAST_REACH = 3;

/**
 * Extracts smooth, watertight territory outlines from the cell grid.
 * Borders are traced once per neighbouring pair, simplified and smoothed,
 * then reused by both territories so fills and lines always match.
 */
export function buildTerritoryGeometry(map: MapData, grids: MapGrids): TerritoryGeometry {
  const W = map.cols;
  const H = map.rows;
  const cs = map.cellSize;
  const count = map.territories.length;

  // Render grid: extend territories a little into the sea so fills reach the
  // drawn coastline (the water layer covers the rest).
  const g = new Int16Array(grids.territoryGrid);
  let frontier: number[] = [];
  for (let c = 0; c < W * H; c++) if (g[c] >= 0) frontier.push(c);
  for (let step = 0; step < COAST_REACH; step++) {
    const next: number[] = [];
    for (const c of frontier) {
      const x = c % W;
      const y = (c - x) / W;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (g[n] < 0 && grids.terrain[n] === Terrain.WATER) {
          g[n] = g[c];
          next.push(n);
        }
      }
    }
    frontier = next;
  }
  const id = (x: number, y: number): number => (x < 0 || y < 0 || x >= W || y >= H ? -1 : g[y * W + x]);
  const VW = W + 1;

  // Boundary edges with canonical direction P->Q and left/right labels.
  const eP: number[] = [];
  const eQ: number[] = [];
  const eL: number[] = [];
  const eR: number[] = [];
  for (let y = 0; y <= H; y++) {
    for (let x = 0; x < W; x++) {
      const above = id(x, y - 1);
      const below = id(x, y);
      if (above === below) continue;
      eP.push(y * VW + x);
      eQ.push(y * VW + x + 1);
      eL.push(below);
      eR.push(above);
    }
  }
  for (let x = 0; x <= W; x++) {
    for (let y = 0; y < H; y++) {
      const left = id(x - 1, y);
      const right = id(x, y);
      if (left === right) continue;
      eP.push(y * VW + x);
      eQ.push((y + 1) * VW + x);
      eL.push(left);
      eR.push(right);
    }
  }
  const edgeCount = eP.length;
  const incident = new Map<number, number[]>();
  for (let e = 0; e < edgeCount; e++) {
    for (const v of [eP[e], eQ[e]]) {
      let list = incident.get(v);
      if (!list) incident.set(v, (list = []));
      list.push(e);
    }
  }
  const pairKey = (e: number): number => {
    const a = Math.min(eL[e], eR[e]);
    const b = Math.max(eL[e], eR[e]);
    return (a + 2) * 65536 + (b + 2);
  };
  const isJunction = (v: number): boolean => {
    const list = incident.get(v)!;
    return list.length !== 2 || pairKey(list[0]) !== pairKey(list[1]);
  };

  interface Chain {
    verts: number[];
    left: number;
    right: number;
    closed: boolean;
  }
  const chains: Chain[] = [];
  const visited = new Uint8Array(edgeCount);
  const walk = (startV: number, startE: number): Chain => {
    const verts = [startV];
    let v = startV;
    let e = startE;
    const forward = eP[e] === v;
    const left = forward ? eL[e] : eR[e];
    const right = forward ? eR[e] : eL[e];
    for (;;) {
      visited[e] = 1;
      v = eP[e] === v ? eQ[e] : eP[e];
      verts.push(v);
      if (v === startV || isJunction(v)) break;
      const next = incident.get(v)!.find((x) => !visited[x]);
      if (next === undefined) break;
      e = next;
    }
    return { verts, left, right, closed: v === startV && !isJunction(startV) };
  };
  for (const [v, list] of incident) {
    if (!isJunction(v)) continue;
    for (const e of list) if (!visited[e]) chains.push(walk(v, e));
  }
  for (let e = 0; e < edgeCount; e++) if (!visited[e]) chains.push(walk(eP[e], e));

  // Smooth every chain once.
  const smoothed: number[][] = chains.map((ch) => {
    const pts: number[] = [];
    for (const v of ch.verts) pts.push((v % VW) * cs, Math.floor(v / VW) * cs);
    if (ch.closed) {
      pts.length -= 2;
      return chaikin(simplifyClosed(pts, cs * 0.55), 3, true);
    }
    return chaikin(simplifyPolyline(pts, cs * 0.55), 3, false);
  });

  const borders: BorderChain[] = [];
  chains.forEach((ch, i) => {
    if (ch.left >= 0 && ch.right >= 0) borders.push({ a: Math.min(ch.left, ch.right), b: Math.max(ch.left, ch.right), points: smoothed[i] });
  });

  // Assemble rings per territory: orient chains so the territory is on the left.
  const rings: number[][][] = Array.from({ length: count }, () => []);
  const byTerritory: { start: number; end: number; pts: number[]; closed: boolean }[][] = Array.from({ length: count }, () => []);
  chains.forEach((ch, i) => {
    const pts = smoothed[i];
    if (ch.left >= 0) byTerritory[ch.left].push({ start: ch.verts[0], end: ch.verts[ch.verts.length - 1], pts, closed: ch.closed });
    if (ch.right >= 0) byTerritory[ch.right].push({ start: ch.verts[ch.verts.length - 1], end: ch.verts[0], pts: reversePoints(pts), closed: ch.closed });
  });
  for (let t = 0; t < count; t++) {
    const parts = byTerritory[t];
    const used = new Uint8Array(parts.length);
    for (let i = 0; i < parts.length; i++) {
      if (used[i]) continue;
      used[i] = 1;
      if (parts[i].closed) {
        rings[t].push(parts[i].pts);
        continue;
      }
      const ring = parts[i].pts.slice();
      const first = parts[i].start;
      let end = parts[i].end;
      let guard = 0;
      while (end !== first && guard++ < parts.length) {
        const j = parts.findIndex((p, k) => !used[k] && p.start === end);
        if (j < 0) break;
        used[j] = 1;
        ring.push(...parts[j].pts.slice(2));
        end = parts[j].end;
      }
      rings[t].push(ring);
    }
  }

  const paths = rings.map((rs) => {
    const p = new Path2D();
    for (const r of rs) addRing(p, r);
    return p;
  });
  return { rings, paths, borders };
}

function simplifyClosed(pts: number[], eps: number): number[] {
  if (pts.length < 8) return pts;
  // Split the loop at its midpoint so RDP keeps both halves.
  const mid = Math.floor(pts.length / 4) * 2;
  const a = simplifyPolyline(pts.slice(0, mid + 2), eps);
  const b = simplifyPolyline([...pts.slice(mid), pts[0], pts[1]], eps);
  return [...a.slice(0, -2), ...b.slice(0, -2)];
}

function reversePoints(pts: number[]): number[] {
  const out: number[] = new Array(pts.length);
  for (let i = 0; i < pts.length; i += 2) {
    out[pts.length - 2 - i] = pts[i];
    out[pts.length - 1 - i] = pts[i + 1];
  }
  return out;
}

export function addRing(p: Path2D, ring: number[]): void {
  if (ring.length < 6) return;
  p.moveTo(ring[0], ring[1]);
  for (let i = 2; i < ring.length; i += 2) p.lineTo(ring[i], ring[i + 1]);
  p.closePath();
}

export function addPolyline(p: Path2D, pts: number[]): void {
  if (pts.length < 4) return;
  p.moveTo(pts[0], pts[1]);
  for (let i = 2; i < pts.length; i += 2) p.lineTo(pts[i], pts[i + 1]);
}
