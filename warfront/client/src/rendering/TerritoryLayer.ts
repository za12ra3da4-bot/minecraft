import { getRelation, type NationId } from '@warfront/shared';
import type { Camera } from '../game/Camera';
import type { GameClient } from '../game/GameClient';
import { MAP_COLORS, hexToRgb, nationColor } from './palette';
import { addPolyline, addRing, buildTerritoryGeometry, type TerritoryGeometry } from './TerritoryGeometry';

interface Flash {
  territoryId: number;
  start: number;
}

const FILL_ALPHA = 0.36;

/** Political layer: nation colours, borders, frontlines, captures. */
export class TerritoryLayer {
  readonly geo: TerritoryGeometry;
  private ownerPaths = new Map<NationId | null, Path2D>();
  private internalBorders = new Path2D();
  private nationalBorders = new Path2D();
  private frontlines = new Path2D();
  private builtOwners = -1;
  private builtDiplomacy = -1;
  private flashes: Flash[] = [];
  private patterns = new Map<string, CanvasPattern>();

  constructor(private game: GameClient) {
    this.geo = buildTerritoryGeometry(game.replica.map, game.grids);
  }

  flash(territoryId: number): void {
    this.flashes.push({ territoryId, start: performance.now() });
  }

  private rebuild(): void {
    const r = this.game.replica;
    if (this.builtOwners === r.ownersVersion && this.builtDiplomacy === r.diplomacyVersion) return;
    this.builtOwners = r.ownersVersion;
    this.builtDiplomacy = r.diplomacyVersion;
    this.ownerPaths.clear();
    r.owners.forEach((owner, t) => {
      let p = this.ownerPaths.get(owner);
      if (!p) this.ownerPaths.set(owner, (p = new Path2D()));
      for (const ring of this.geo.rings[t]) addRing(p, ring);
    });
    this.internalBorders = new Path2D();
    this.nationalBorders = new Path2D();
    this.frontlines = new Path2D();
    for (const b of this.geo.borders) {
      const oa = r.owners[b.a];
      const ob = r.owners[b.b];
      if (oa === ob) addPolyline(this.internalBorders, b.points);
      else if (oa && ob && getRelation(r.diplomacy.relations, oa, ob) === 'WAR') addPolyline(this.frontlines, b.points);
      else addPolyline(this.nationalBorders, b.points);
    }
  }

  private stripes(color: string, ctx: CanvasRenderingContext2D): CanvasPattern {
    let p = this.patterns.get(color);
    if (!p) {
      const c = document.createElement('canvas');
      c.width = c.height = 16;
      const g = c.getContext('2d')!;
      g.strokeStyle = color;
      g.lineWidth = 5;
      g.beginPath();
      for (let i = -16; i <= 32; i += 10) {
        g.moveTo(i, 16);
        g.lineTo(i + 16, 0);
      }
      g.stroke();
      p = ctx.createPattern(c, 'repeat')!;
      this.patterns.set(color, p);
    }
    return p;
  }

  /** Fills (drawn between the land and water terrain layers). */
  drawFills(ctx: CanvasRenderingContext2D, camera: Camera, now: number): void {
    this.rebuild();
    const r = this.game.replica;
    ctx.save();
    applyWorld(ctx, camera);
    for (const [owner, path] of this.ownerPaths) {
      if (owner === null) {
        ctx.fillStyle = 'rgba(120,108,88,0.16)';
      } else {
        const [cr, cg, cb] = hexToRgb(nationColor(owner));
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${FILL_ALPHA})`;
      }
      ctx.fill(path);
    }

    // Territories being captured: hatched in the attacker's colour.
    for (const cap of r.captures) {
      const path = this.geo.paths[cap.territoryId];
      if (!path) continue;
      ctx.save();
      ctx.globalAlpha = 0.25 + cap.progress * 0.55;
      const pattern = this.stripes(nationColor(cap.nation), ctx);
      pattern.setTransform(new DOMMatrix().scale(1 / camera.zoom));
      ctx.fillStyle = pattern;
      ctx.fill(path);
      ctx.restore();
    }

    // Ownership change flash.
    this.flashes = this.flashes.filter((f) => now - f.start < 1400);
    for (const f of this.flashes) {
      const t = (now - f.start) / 1400;
      const owner = r.owners[f.territoryId];
      const [cr, cg, cb] = hexToRgb(nationColor(owner));
      ctx.fillStyle = `rgba(${Math.round(cr + (255 - cr) * 0.6)},${Math.round(cg + (255 - cg) * 0.6)},${Math.round(cb + (255 - cb) * 0.6)},${0.75 * (1 - t)})`;
      ctx.fill(this.geo.paths[f.territoryId]);
    }
    ctx.restore();
  }

  /** Borders and frontlines (drawn before water so they stop at the coast). */
  drawBorders(ctx: CanvasRenderingContext2D, camera: Camera, now: number): void {
    const z = camera.zoom;
    const rel = camera.relZoom;
    ctx.save();
    applyWorld(ctx, camera);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    if (rel > 1.4) {
      ctx.strokeStyle = 'rgba(52,44,32,0.28)';
      ctx.lineWidth = 0.9 / z;
      ctx.setLineDash([3 / z, 3 / z]);
      ctx.stroke(this.internalBorders);
      ctx.setLineDash([]);
    }

    ctx.strokeStyle = 'rgba(30,26,20,0.75)';
    ctx.lineWidth = Math.min(2.6, 1.3 + rel * 0.08) / z;
    ctx.stroke(this.nationalBorders);

    // Frontline: glowing red band with a dark core and a pulse.
    const pulse = 0.75 + 0.25 * Math.sin(now / 420);
    ctx.strokeStyle = MAP_COLORS.frontGlow;
    ctx.globalAlpha = pulse;
    ctx.lineWidth = Math.min(11, 5 + rel * 0.4) / z;
    ctx.stroke(this.frontlines);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = MAP_COLORS.front;
    ctx.lineWidth = Math.min(3.4, 2 + rel * 0.1) / z;
    ctx.stroke(this.frontlines);
    ctx.strokeStyle = 'rgba(255,214,170,0.55)';
    ctx.lineWidth = 0.8 / z;
    ctx.setLineDash([6 / z, 9 / z]);
    ctx.lineDashOffset = -now / 60 / z;
    ctx.stroke(this.frontlines);
    ctx.setLineDash([]);

    // Selected territory outline.
    const sel = this.game.selection;
    if (sel.kind === 'territory') {
      ctx.strokeStyle = 'rgba(255,226,140,0.95)';
      ctx.lineWidth = 2.5 / z;
      ctx.stroke(this.geo.paths[sel.id]);
    }
    ctx.restore();
  }

  /** Territory id at a world position. */
  territoryAt(x: number, y: number): number {
    const m = this.game.replica.map;
    const cx = Math.floor(x / m.cellSize);
    const cy = Math.floor(y / m.cellSize);
    if (cx < 0 || cy < 0 || cx >= m.cols || cy >= m.rows) return -1;
    return this.game.grids.territoryGrid[cy * m.cols + cx];
  }
}

export function applyWorld(ctx: CanvasRenderingContext2D, camera: Camera): void {
  ctx.translate(camera.viewW / 2, camera.viewH / 2);
  ctx.scale(camera.zoom, camera.zoom);
  ctx.translate(-camera.x, -camera.y);
}
