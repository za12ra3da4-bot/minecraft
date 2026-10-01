import type { MapDef, Rng } from '@warfront/shared';

/** Mutable working state shared by the map generation passes. */
export interface MapContext {
  def: MapDef;
  rng: Rng;
  cols: number;
  rows: number;
  cs: number;
  /** Raw elevation at vertices ((cols+1)*(rows+1)); land where > 0. */
  elev: Float32Array;
  /** Relief noise at vertices, normalised to 0..1 over the map. */
  relief: Float32Array;
  /** Final height bytes at vertices. */
  heights: Uint8Array;
  terrain: Uint8Array;
  flags: Uint8Array;
  territory: Int16Array;
}

export function cellIndex(ctx: MapContext, x: number, y: number): number {
  return y * ctx.cols + x;
}

export function cellAtWorld(ctx: MapContext, wx: number, wy: number): number {
  const x = Math.floor(wx / ctx.cs);
  const y = Math.floor(wy / ctx.cs);
  if (x < 0 || y < 0 || x >= ctx.cols || y >= ctx.rows) return -1;
  return y * ctx.cols + x;
}

export function cellCenter(ctx: MapContext, idx: number): [number, number] {
  const x = idx % ctx.cols;
  const y = (idx - x) / ctx.cols;
  return [(x + 0.5) * ctx.cs, (y + 0.5) * ctx.cs];
}

export const N4: [number, number][] = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

export const N8: [number, number, number][] = [
  [1, 0, 1],
  [-1, 0, 1],
  [0, 1, 1],
  [0, -1, 1],
  [1, 1, Math.SQRT2],
  [-1, 1, Math.SQRT2],
  [1, -1, Math.SQRT2],
  [-1, -1, Math.SQRT2],
];

/** Value below which `share` of the sorted samples lie. */
export function quantile(values: number[], share: number): number {
  if (!values.length) return 0;
  const sorted = values.slice().sort((a, b) => a - b);
  const i = Math.max(0, Math.min(sorted.length - 1, Math.floor(share * sorted.length)));
  return sorted[i];
}
