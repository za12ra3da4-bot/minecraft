import { CellFlag, TERRAIN_SPEED, Terrain } from '@warfront/shared';
import type { GeneratedMap } from './map/MapGenerator';
import { MinHeap } from './util/MinHeap';

const NAV_FACTOR = 2;
const DIRS: [number, number, number][] = [
  [1, 0, 1],
  [-1, 0, 1],
  [0, 1, 1],
  [0, -1, 1],
  [1, 1, Math.SQRT2],
  [-1, 1, Math.SQRT2],
  [1, -1, Math.SQRT2],
  [-1, -1, Math.SQRT2],
];

/**
 * A* over a coarse navigation grid (2x2 map cells per node). Costs are
 * travel time, so roads are preferred and rivers are avoided unless bridged.
 */
export class Pathfinder {
  readonly cols: number;
  readonly rows: number;
  readonly size: number;
  private readonly cost: Float32Array;
  private readonly g: Float32Array;
  private readonly came: Int32Array;
  private readonly stamp: Uint32Array;
  private readonly closed: Uint32Array;
  private generation = 0;
  private readonly heap = new MinHeap();
  private readonly minCost: number;

  constructor(private map: GeneratedMap) {
    const { cols, rows } = map.data;
    this.cols = Math.ceil(cols / NAV_FACTOR);
    this.rows = Math.ceil(rows / NAV_FACTOR);
    this.size = this.cols * this.rows;
    this.cost = new Float32Array(this.size);
    this.g = new Float32Array(this.size);
    this.came = new Int32Array(this.size);
    this.stamp = new Uint32Array(this.size);
    this.closed = new Uint32Array(this.size);
    this.minCost = 1 / TERRAIN_SPEED.ROAD;

    for (let ny = 0; ny < this.rows; ny++) {
      for (let nx = 0; nx < this.cols; nx++) {
        let land = 0;
        let shallow = 0;
        let total = 0;
        let sum = 0;
        let road = false;
        let river = false;
        let bridge = false;
        for (let oy = 0; oy < NAV_FACTOR; oy++) {
          for (let ox = 0; ox < NAV_FACTOR; ox++) {
            const cx = nx * NAV_FACTOR + ox;
            const cy = ny * NAV_FACTOR + oy;
            if (cx >= cols || cy >= rows) continue;
            total++;
            const c = cy * cols + cx;
            const t = map.terrain[c] as Terrain;
            if (t === Terrain.WATER) {
              if (map.flags[c] & CellFlag.SHALLOW) shallow++;
              continue;
            }
            land++;
            sum += 1 / terrainSpeed(t);
            const f = map.flags[c];
            if (f & CellFlag.ROAD) road = true;
            if (f & CellFlag.RIVER) river = true;
            if (f & CellFlag.BRIDGE) bridge = true;
          }
        }
        const i = ny * this.cols + nx;
        if ((land + shallow) * 2 < total || land + shallow === 0) {
          this.cost[i] = Infinity;
          continue;
        }
        if (land * 2 < total || land === 0) {
          // Strait or channel: crossed slowly by boat.
          this.cost[i] = 1 / TERRAIN_SPEED.SEA;
          continue;
        }
        let c = sum / land;
        if (road) c = Math.min(c, 1 / TERRAIN_SPEED.ROAD);
        if (river && !bridge) c += 1 / TERRAIN_SPEED.RIVER_CROSSING - 1;
        this.cost[i] = c;
      }
    }
  }

  private navIndex(x: number, y: number): number {
    const cs = this.map.data.cellSize * NAV_FACTOR;
    const nx = Math.max(0, Math.min(this.cols - 1, Math.floor(x / cs)));
    const ny = Math.max(0, Math.min(this.rows - 1, Math.floor(y / cs)));
    return ny * this.cols + nx;
  }

  private navCenter(i: number): [number, number] {
    const cs = this.map.data.cellSize * NAV_FACTOR;
    const nx = i % this.cols;
    const ny = (i - nx) / this.cols;
    return [(nx + 0.5) * cs, (ny + 0.5) * cs];
  }

  passable(x: number, y: number): boolean {
    return this.cost[this.navIndex(x, y)] !== Infinity;
  }

  /** Nearest passable nav node (spiral search), or -1. */
  private snap(i: number): number {
    if (this.cost[i] !== Infinity) return i;
    const x0 = i % this.cols;
    const y0 = (i - x0) / this.cols;
    for (let r = 1; r <= 8; r++) {
      let best = -1;
      let bestD = Infinity;
      for (let dy = -r; dy <= r; dy++) {
        for (let dx = -r; dx <= r; dx++) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
          const x = x0 + dx;
          const y = y0 + dy;
          if (x < 0 || y < 0 || x >= this.cols || y >= this.rows) continue;
          const j = y * this.cols + x;
          if (this.cost[j] === Infinity) continue;
          const d = dx * dx + dy * dy;
          if (d < bestD) {
            bestD = d;
            best = j;
          }
        }
      }
      if (best >= 0) return best;
    }
    return -1;
  }

  /**
   * Returns flat waypoints [x0,y0,...] from (sx,sy) to (tx,ty), or null if
   * unreachable. The first waypoint is the first point to walk to.
   */
  findPath(sx: number, sy: number, tx: number, ty: number): number[] | null {
    const start = this.snap(this.navIndex(sx, sy));
    const goalRaw = this.navIndex(tx, ty);
    const goal = this.snap(goalRaw);
    if (start < 0 || goal < 0) return null;
    const exactGoal = goal === goalRaw;
    if (start === goal) return exactGoal ? [tx, ty] : [...this.navCenter(goal)];

    this.generation++;
    if (this.generation === 0xffffffff) {
      this.stamp.fill(0);
      this.closed.fill(0);
      this.generation = 1;
    }
    const gen = this.generation;
    const heap = this.heap;
    heap.clear();
    const gx = goal % this.cols;
    const gy = (goal - gx) / this.cols;
    this.g[start] = 0;
    this.stamp[start] = gen;
    this.came[start] = -1;
    heap.push(start, 0);
    let found = false;
    let expanded = 0;
    while (heap.size) {
      const cur = heap.pop();
      if (this.closed[cur] === gen) continue;
      this.closed[cur] = gen;
      if (cur === goal) {
        found = true;
        break;
      }
      if (++expanded > 60_000) break;
      const cx = cur % this.cols;
      const cy = (cur - cx) / this.cols;
      const gc = this.g[cur];
      for (const [dx, dy, w] of DIRS) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= this.cols || ny >= this.rows) continue;
        const n = ny * this.cols + nx;
        const c = this.cost[n];
        if (c === Infinity || this.closed[n] === gen) continue;
        if (dx !== 0 && dy !== 0) {
          // No corner cutting across impassable nodes.
          if (this.cost[cy * this.cols + nx] === Infinity || this.cost[ny * this.cols + cx] === Infinity) continue;
        }
        const ng = gc + w * (c + this.cost[cur]) * 0.5;
        if (this.stamp[n] !== gen || ng < this.g[n]) {
          this.stamp[n] = gen;
          this.g[n] = ng;
          this.came[n] = cur;
          const hx = Math.abs(nx - gx);
          const hy = Math.abs(ny - gy);
          const h = (Math.max(hx, hy) + (Math.SQRT2 - 1) * Math.min(hx, hy)) * this.minCost;
          heap.push(n, ng + h);
        }
      }
    }
    if (!found) return null;

    const nodes: number[] = [];
    for (let cur = goal; cur !== -1; cur = this.came[cur]) nodes.push(cur);
    nodes.reverse();
    const smoothed = this.smooth(nodes);
    const out: number[] = [];
    for (let i = 1; i < smoothed.length; i++) {
      const [x, y] = this.navCenter(smoothed[i]);
      out.push(x, y);
    }
    if (exactGoal) {
      out[out.length - 2] = tx;
      out[out.length - 1] = ty;
    }
    return out;
  }

  /** Greedy line-of-sight smoothing that never makes the route slower. */
  private smooth(nodes: number[]): number[] {
    if (nodes.length <= 2) return nodes;
    const out = [nodes[0]];
    let i = 0;
    while (i < nodes.length - 1) {
      let best = i + 1;
      let pathCost = 0;
      for (let j = i + 1; j < Math.min(nodes.length, i + 28); j++) {
        pathCost += this.stepCost(nodes[j - 1], nodes[j]);
        const line = this.lineCost(nodes[i], nodes[j]);
        if (line <= pathCost * 1.03) best = j;
      }
      out.push(nodes[best]);
      i = best;
    }
    return out;
  }

  private stepCost(a: number, b: number): number {
    const ax = a % this.cols;
    const bx = b % this.cols;
    const diag = ax !== bx && Math.floor(a / this.cols) !== Math.floor(b / this.cols);
    return (diag ? Math.SQRT2 : 1) * (this.cost[a] + this.cost[b]) * 0.5;
  }

  private lineCost(a: number, b: number): number {
    const ax = a % this.cols;
    const ay = (a - ax) / this.cols;
    const bx = b % this.cols;
    const by = (b - bx) / this.cols;
    const len = Math.hypot(bx - ax, by - ay);
    const steps = Math.max(1, Math.ceil(len * 2));
    let sum = 0;
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const x = Math.round(ax + (bx - ax) * t);
      const y = Math.round(ay + (by - ay) * t);
      const c = this.cost[y * this.cols + x];
      if (c === Infinity) return Infinity;
      sum += c;
    }
    return (sum / (steps + 1)) * len;
  }
}

export function terrainSpeed(t: Terrain): number {
  switch (t) {
    case Terrain.FOREST:
      return TERRAIN_SPEED.FOREST;
    case Terrain.HILLS:
      return TERRAIN_SPEED.HILLS;
    case Terrain.MARSH:
      return TERRAIN_SPEED.MARSH;
    case Terrain.WATER:
      return TERRAIN_SPEED.SEA;
    default:
      return TERRAIN_SPEED.PLAINS;
  }
}

const cache = new WeakMap<GeneratedMap, Pathfinder>();

export function getPathfinder(map: GeneratedMap): Pathfinder {
  let pf = cache.get(map);
  if (!pf) {
    pf = new Pathfinder(map);
    cache.set(map, pf);
  }
  return pf;
}
