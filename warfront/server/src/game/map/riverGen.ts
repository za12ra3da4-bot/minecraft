import { CellFlag, Terrain, catmullRom, roundPoints, simplifyPolyline, type RiverDef } from '@warfront/shared';
import { fbm } from './noise';
import { cellAtWorld, type MapContext } from './MapContext';

/** Rivers follow designer control points with procedural meanders. */
export function generateRivers(ctx: MapContext): RiverDef[] {
  const { def, cs } = ctx;
  const rivers: RiverDef[] = [];
  def.rivers.forEach((river, ri) => {
    const control: number[] = [];
    for (const [nx, ny] of river.points) control.push(nx * def.width, ny * def.height);
    const spline = catmullRom(control, cs * 0.6);

    // Perpendicular meander offset driven by noise along the river length.
    const meandered: number[] = [];
    let along = 0;
    const n = spline.length / 2;
    for (let i = 0; i < n; i++) {
      const x = spline[i * 2];
      const y = spline[i * 2 + 1];
      const px = spline[Math.max(0, i - 1) * 2];
      const py = spline[Math.max(0, i - 1) * 2 + 1];
      const qx = spline[Math.min(n - 1, i + 1) * 2];
      const qy = spline[Math.min(n - 1, i + 1) * 2 + 1];
      if (i > 0) along += Math.hypot(x - px, y - py);
      const tx = qx - px;
      const ty = qy - py;
      const tl = Math.hypot(tx, ty) || 1;
      const off = fbm(along / 260, ri * 7.3, def.seed + 500, 3) * 70;
      meandered.push(x + (-ty / tl) * off, y + (tx / tl) * off);
    }

    // Clip to the stretch that runs over land, ending where it reaches water.
    const clipped: number[] = [];
    let started = false;
    for (let i = 0; i < meandered.length / 2; i++) {
      const x = meandered[i * 2];
      const y = meandered[i * 2 + 1];
      const c = cellAtWorld(ctx, x, y);
      const onLand = c >= 0 && ctx.terrain[c] !== Terrain.WATER;
      if (!started) {
        if (onLand) started = true;
        else continue;
      }
      clipped.push(x, y);
      if (!onLand) break;
    }
    if (clipped.length < 8) return;

    // Rasterise onto the grid.
    for (let i = 2; i < clipped.length; i += 2) {
      const ax = clipped[i - 2];
      const ay = clipped[i - 1];
      const bx = clipped[i];
      const by = clipped[i + 1];
      const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / (cs * 0.3)));
      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        const c = cellAtWorld(ctx, ax + (bx - ax) * t, ay + (by - ay) * t);
        if (c >= 0 && ctx.terrain[c] !== Terrain.WATER) {
          ctx.flags[c] |= CellFlag.RIVER;
          if (ctx.terrain[c] === Terrain.HILLS) ctx.terrain[c] = Terrain.PLAINS;
        }
      }
    }
    rivers.push({ points: roundPoints(simplifyPolyline(clipped, 1.5)), width: river.width });
  });
  return rivers;
}
