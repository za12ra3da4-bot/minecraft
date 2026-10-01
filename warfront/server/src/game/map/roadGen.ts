import {
  CellFlag,
  Terrain,
  chaikin,
  roundPoints,
  simplifyPolyline,
  type BridgeDef,
  type CityDef,
  type RoadDef,
  type TerritoryDef,
} from '@warfront/shared';
import { MinHeap } from '../util/MinHeap';
import { N8, cellAtWorld, cellCenter, type MapContext } from './MapContext';

export interface RoadResult {
  roads: RoadDef[];
  bridges: BridgeDef[];
}

/** Road network: minimum spanning tree over neighbouring towns plus extra links between cities. */
export function generateRoads(ctx: MapContext, territories: TerritoryDef[], cities: CityDef[]): RoadResult {
  const { rng } = ctx;
  const edges: { a: number; b: number; w: number }[] = [];
  for (const t of territories) {
    for (const n of t.neighbors) {
      if (n <= t.id) continue;
      edges.push({ a: t.id, b: n, w: Math.hypot(t.cx - territories[n].cx, t.cy - territories[n].cy) });
    }
  }
  edges.sort((x, y) => x.w - y.w);
  const parent = territories.map((_, i) => i);
  const find = (i: number): number => {
    while (parent[i] !== i) i = parent[i] = parent[parent[i]];
    return i;
  };
  const isTown = (t: number): boolean => cities[territories[t].cityId!].type !== 'VILLAGE';
  const chosen: { a: number; b: number }[] = [];
  for (const e of edges) {
    const ra = find(e.a);
    const rb = find(e.b);
    if (ra !== rb) {
      parent[ra] = rb;
      chosen.push(e);
    } else if ((isTown(e.a) && isTown(e.b) && rng.chance(0.7)) || rng.chance(0.08)) {
      chosen.push(e);
    }
  }
  // Major roads first so minor roads reuse them.
  chosen.sort((x, y) => Number(isTown(y.a) && isTown(y.b)) - Number(isTown(x.a) && isTown(x.b)));

  const roads: RoadDef[] = [];
  const bridges: BridgeDef[] = [];
  for (const e of chosen) {
    const ta = territories[e.a];
    const tb = territories[e.b];
    const path = roadPath(ctx, cellAtWorld(ctx, ta.cx, ta.cy), cellAtWorld(ctx, tb.cx, tb.cy));
    if (!path) continue;
    const pts: number[] = [];
    for (let i = 0; i < path.length; i++) {
      const c = path[i];
      const [x, y] = cellCenter(ctx, c);
      pts.push(x, y);
      if (ctx.flags[c] & CellFlag.RIVER && !(ctx.flags[c] & CellFlag.BRIDGE)) {
        ctx.flags[c] |= CellFlag.BRIDGE;
        const [px, py] = cellCenter(ctx, path[Math.max(0, i - 1)]);
        const [nx, ny] = cellCenter(ctx, path[Math.min(path.length - 1, i + 1)]);
        bridges.push({ x, y, angle: Math.round(Math.atan2(ny - py, nx - px) * 100) / 100 });
      }
      ctx.flags[c] |= CellFlag.ROAD;
    }
    pts[0] = ta.cx;
    pts[1] = ta.cy;
    pts[pts.length - 2] = tb.cx;
    pts[pts.length - 1] = tb.cy;
    const smooth = chaikin(simplifyPolyline(pts, ctx.cs * 0.5), 2);
    roads.push({ points: roundPoints(smooth), major: isTown(e.a) && isTown(e.b) });
  }
  return { roads, bridges };
}

function roadPath(ctx: MapContext, start: number, goal: number): number[] | null {
  const { cols, rows } = ctx;
  if (start < 0 || goal < 0) return null;
  const gx = goal % cols;
  const gy = Math.floor(goal / cols);
  const sx = start % cols;
  const sy = Math.floor(start / cols);
  const margin = 14;
  const minX = Math.max(0, Math.min(sx, gx) - margin);
  const maxX = Math.min(cols - 1, Math.max(sx, gx) + margin);
  const minY = Math.max(0, Math.min(sy, gy) - margin);
  const maxY = Math.min(rows - 1, Math.max(sy, gy) + margin);
  const g = new Map<number, number>();
  const came = new Map<number, number>();
  const heap = new MinHeap();
  g.set(start, 0);
  heap.push(start, 0);
  const minCost = 0.35;
  while (heap.size) {
    const c = heap.pop();
    if (c === goal) break;
    const gc = g.get(c)!;
    const x = c % cols;
    const y = (c - x) / cols;
    for (const [dx, dy, w] of N8) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < minX || ny < minY || nx > maxX || ny > maxY) continue;
      const n = ny * cols + nx;
      const t = ctx.terrain[n];
      if (t === Terrain.WATER) continue;
      const f = ctx.flags[n];
      let cost = t === Terrain.HILLS ? 2.6 : t === Terrain.FOREST ? 1.8 : t === Terrain.MARSH ? 3 : 1;
      if (f & CellFlag.ROAD) cost = minCost;
      if (f & CellFlag.RIVER && !(f & CellFlag.BRIDGE)) cost += 12;
      const ng = gc + cost * w;
      if (ng < (g.get(n) ?? Infinity)) {
        g.set(n, ng);
        came.set(n, c);
        const h = Math.hypot(nx - gx, ny - gy) * minCost;
        heap.push(n, ng + h);
      }
    }
  }
  if (!came.has(goal) && start !== goal) return null;
  const path = [goal];
  let cur = goal;
  while (cur !== start) {
    cur = came.get(cur)!;
    path.push(cur);
  }
  return path.reverse();
}
