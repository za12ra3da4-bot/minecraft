import { getNation, type CityDef, type NationId } from '@warfront/shared';
import type { Camera } from '../game/Camera';
import type { GameClient } from '../game/GameClient';
import { settings } from '../data/settings';
import { LABEL_FONT, MAP_COLORS, TITLE_FONT, shade } from './palette';

interface NationLabel {
  nation: NationId;
  x: number;
  y: number;
  /** Approximate extent in world units, used for font size. */
  extent: number;
}

const CITY_RANK: Record<CityDef['type'], number> = { CAPITAL: 0, CITY: 1, PORT: 1, INDUSTRIAL_CITY: 1, VILLAGE: 2 };

/** Engraved-style place names and large nation names. */
export class LabelLayer {
  private nationLabels: NationLabel[] = [];
  private builtFor = -1;
  private sortedCities: CityDef[];

  constructor(private game: GameClient) {
    this.sortedCities = game.replica.map.cities.slice().sort((a, b) => CITY_RANK[a.type] - CITY_RANK[b.type]);
  }

  /** Nation name anchors: centroid of the largest connected block of territory. */
  private rebuild(): void {
    const r = this.game.replica;
    if (this.builtFor === r.ownersVersion) return;
    this.builtFor = r.ownersVersion;
    const territories = r.map.territories;
    const seen = new Uint8Array(territories.length);
    const best = new Map<NationId, { cells: number; sx: number; sy: number; ids: number[] }>();
    for (const t of territories) {
      const owner = r.owners[t.id];
      if (!owner || seen[t.id]) continue;
      const stack = [t.id];
      seen[t.id] = 1;
      let cells = 0;
      let sx = 0;
      let sy = 0;
      const ids: number[] = [];
      while (stack.length) {
        const id = stack.pop()!;
        const tt = territories[id];
        ids.push(id);
        cells += tt.cells;
        sx += tt.cx * tt.cells;
        sy += tt.cy * tt.cells;
        for (const n of tt.neighbors) {
          if (!seen[n] && r.owners[n] === owner) {
            seen[n] = 1;
            stack.push(n);
          }
        }
      }
      const prev = best.get(owner);
      if (!prev || cells > prev.cells) best.set(owner, { cells, sx, sy, ids });
    }
    const cs = r.map.cellSize;
    this.nationLabels = [...best.entries()].map(([nation, b]) => {
      const cx = b.sx / b.cells;
      const cy = b.sy / b.cells;
      // Snap to the territory centre closest to the centroid so the label sits on land.
      let lx = cx;
      let ly = cy;
      let d = Infinity;
      for (const id of b.ids) {
        const t = territories[id];
        const dd = (t.cx - cx) ** 2 + (t.cy - cy) ** 2;
        if (dd < d) {
          d = dd;
          lx = t.cx;
          ly = t.cy;
        }
      }
      return { nation, x: (lx + cx) / 2, y: (ly + cy) / 2, extent: Math.sqrt(b.cells) * cs };
    });
  }

  drawNationNames(ctx: CanvasRenderingContext2D, camera: Camera): void {
    const level = camera.level;
    if (level > 2) return;
    this.rebuild();
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (const l of this.nationLabels) {
      const size = Math.max(13, Math.min(56, l.extent * camera.zoom * 0.11));
      const sx = camera.worldToScreenX(l.x);
      const sy = camera.worldToScreenY(l.y);
      const name = getNation(l.nation).name.toUpperCase();
      ctx.font = `400 ${Math.round(size)}px ${TITLE_FONT}`;
      if ('letterSpacing' in ctx) (ctx as CanvasRenderingContext2D & { letterSpacing: string }).letterSpacing = `${Math.round(size * 0.22)}px`;
      ctx.globalAlpha = level === 1 ? 0.62 : 0.4;
      ctx.lineWidth = Math.max(2, size * 0.1);
      ctx.strokeStyle = 'rgba(240,230,205,0.55)';
      ctx.strokeText(name, sx, sy);
      ctx.fillStyle = shade(getNation(l.nation).color, -0.45);
      ctx.fillText(name, sx, sy);
    }
    ctx.restore();
  }

  drawCities(ctx: CanvasRenderingContext2D, camera: Camera): void {
    if (!settings.value.showCityNames && camera.level < 4) return;
    const level = camera.level;
    const maxRank = level === 1 ? 0 : level === 2 ? 1 : 2;
    const b = camera.viewBounds(60);
    const placed: [number, number, number, number][] = [];
    const r = this.game.replica;
    ctx.save();
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    for (const c of this.sortedCities) {
      const rank = CITY_RANK[c.type];
      if (rank > maxRank) break;
      if (c.x < b.x0 || c.x > b.x1 || c.y < b.y0 || c.y > b.y1) continue;
      const sx = camera.worldToScreenX(c.x);
      const sy = camera.worldToScreenY(c.y);
      const owner = r.owners[c.territoryId];
      const isCapital = owner !== null && r.nations.get(owner)?.capitalCity === c.id;
      const size = rank === 0 ? 14 : rank === 1 ? 12.5 : 11;
      ctx.font = rank === 0 ? `700 ${size}px ${LABEL_FONT}` : rank === 1 ? `600 ${size}px ${LABEL_FONT}` : `italic 500 ${size}px ${LABEL_FONT}`;
      const text = rank === 0 ? c.name.toUpperCase() : c.name;
      const w = ctx.measureText(text).width;
      // Label sits to the upper-right of the town marker so it does not hide armies.
      const lx = sx + 9;
      const ly = sy - 12;
      const box: [number, number, number, number] = [lx - 2, ly - size / 2 - 2, lx + w + 2, ly + size / 2 + 2];
      if (placed.some((p) => box[0] < p[2] && box[2] > p[0] && box[1] < p[3] && box[3] > p[1])) continue;
      placed.push(box);

      // Town marker.
      ctx.fillStyle = MAP_COLORS.ink;
      ctx.strokeStyle = MAP_COLORS.labelHalo;
      ctx.lineWidth = 2;
      if (isCapital || c.type === 'CAPITAL') {
        star(ctx, sx, sy, 7, isCapital ? '#e8c35a' : '#8b8170');
      } else if (rank === 1) {
        ctx.strokeRect(sx - 3.5, sy - 3.5, 7, 7);
        ctx.fillRect(sx - 3.5, sy - 3.5, 7, 7);
        if (c.type === 'PORT') {
          ctx.fillStyle = '#5d8fa8';
          ctx.fillRect(sx - 1.5, sy - 1.5, 3, 3);
        } else if (c.type === 'INDUSTRIAL_CITY') {
          ctx.fillStyle = '#c9a24a';
          ctx.fillRect(sx - 1.5, sy - 1.5, 3, 3);
        }
      } else {
        ctx.beginPath();
        ctx.arc(sx, sy, 2.6, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fill();
      }
      ctx.lineWidth = 3;
      ctx.strokeStyle = MAP_COLORS.labelHalo;
      ctx.textAlign = 'left';
      ctx.strokeText(text, lx, ly);
      ctx.fillStyle = rank === 2 ? '#4a4234' : MAP_COLORS.ink;
      ctx.fillText(text, lx, ly);
    }
    ctx.restore();
  }

  /** City under a screen point (for selecting cities to raise armies). */
  cityAt(camera: Camera, sx: number, sy: number): CityDef | null {
    const level = camera.level;
    const maxRank = level === 1 ? 0 : level === 2 ? 1 : 2;
    let best: CityDef | null = null;
    let bestD = 12 * 12;
    for (const c of this.sortedCities) {
      if (CITY_RANK[c.type] > maxRank) continue;
      const d = (camera.worldToScreenX(c.x) - sx) ** 2 + (camera.worldToScreenY(c.y) - sy) ** 2;
      if (d < bestD) {
        bestD = d;
        best = c;
      }
    }
    return best;
  }
}

function star(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, fill: string): void {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / 5;
    const rr = i % 2 === 0 ? r : r * 0.45;
    ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  ctx.closePath();
  ctx.lineWidth = 3;
  ctx.strokeStyle = 'rgba(25,20,14,0.9)';
  ctx.stroke();
  ctx.fillStyle = fill;
  ctx.fill();
}
