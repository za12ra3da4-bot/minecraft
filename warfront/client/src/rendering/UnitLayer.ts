import { ARMY_TYPE_STATS, clamp, formatCompact, formatNumber, getNation, type UnitNet } from '@warfront/shared';
import type { Camera } from '../game/Camera';
import type { GameClient, RenderUnit } from '../game/GameClient';
import { clusterUnits, type MapItem, type UnitEntry } from '../game/clustering';
import { settings } from '../data/settings';
import { FLAG_ASPECT, flagBitmap } from './FlagPainter';
import { UI_FONT, hexToRgb, rgba } from './palette';

export interface HitBox {
  item: MapItem;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** Armies above this size get the large "hero" troop number. */
const HERO_SOLDIERS = 35_000;
const RECLUSTER_MS = 140;

/** Army markers: flags, troop numbers, clusters, paths and selection. */
export class UnitLayer {
  hits: HitBox[] = [];
  private items: MapItem[] = [];
  private clusteredAt = 0;
  private clusterZoom = 0;
  private clusterLevel = 0;

  constructor(private game: GameClient) {}

  /** Forces re-clustering on the next frame (selection changes etc.). */
  invalidate(): void {
    this.clusteredAt = 0;
  }

  private visibleItems(camera: Camera, now: number): MapItem[] {
    const zoomChanged = Math.abs(camera.zoom - this.clusterZoom) / this.clusterZoom > 0.04 || camera.level !== this.clusterLevel;
    if (now - this.clusteredAt > RECLUSTER_MS || zoomChanged) {
      const b = camera.viewBounds(80);
      const entries: UnitEntry[] = [];
      for (const r of this.game.render.values()) {
        if (r.x < b.x0 || r.x > b.x1 || r.y < b.y0 || r.y > b.y1) continue;
        const unit = this.game.replica.units.get(r.id);
        if (unit) entries.push({ unit, r });
      }
      const sel = this.game.selection;
      const selected = new Set(sel.kind === 'units' ? sel.ids : sel.kind === 'enemy' ? [sel.id] : []);
      this.items = clusterUnits(entries, camera, selected);
      this.clusteredAt = now;
      this.clusterZoom = camera.zoom;
      this.clusterLevel = camera.level;
    } else {
      // Keep membership, refresh positions every frame for smooth motion.
      for (const item of this.items) {
        let sx = 0;
        let sy = 0;
        let w = 0;
        let soldiers = 0;
        for (const m of item.members) {
          const k = Math.max(1, m.unit.soldiers);
          sx += camera.worldToScreenX(m.r.x) * k;
          sy += camera.worldToScreenY(m.r.y) * k;
          w += k;
          soldiers += m.unit.soldiers;
        }
        item.sx = sx / w;
        item.sy = sy / w;
        item.soldiers = soldiers;
      }
    }
    // Drop members that no longer exist.
    return this.items.filter((item) => item.members.every((m) => this.game.replica.units.has(m.unit.id)));
  }

  /** Movement paths and order lines (drawn under the markers). */
  drawPaths(ctx: CanvasRenderingContext2D, camera: Camera, now: number): void {
    const game = this.game;
    const you = game.you;
    const sel = game.selection;
    const selected = new Set(sel.kind === 'units' ? sel.ids : sel.kind === 'enemy' ? [sel.id] : []);
    const showAll = settings.value.showPaths;
    const b = camera.viewBounds(200);
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    for (const u of game.replica.units.values()) {
      if (!u.path || u.pathIndex * 2 >= u.path.length) continue;
      const isSel = selected.has(u.id);
      const own = u.nation === you;
      if (!isSel && !(own && showAll)) continue;
      const r = game.render.get(u.id);
      if (!r) continue;
      if ((r.x < b.x0 || r.x > b.x1 || r.y < b.y0 || r.y > b.y1) && !isSel) continue;
      const color = own ? (isSel ? 'rgba(255,224,140,0.95)' : rgba(getNation(u.nation).color, 0.55)) : 'rgba(230,70,55,0.9)';
      ctx.beginPath();
      ctx.moveTo(camera.worldToScreenX(r.x), camera.worldToScreenY(r.y));
      for (let i = u.pathIndex * 2; i < u.path.length; i += 2) ctx.lineTo(camera.worldToScreenX(u.path[i]), camera.worldToScreenY(u.path[i + 1]));
      ctx.strokeStyle = 'rgba(20,16,10,0.45)';
      ctx.lineWidth = isSel ? 4.5 : 3;
      ctx.setLineDash([]);
      ctx.stroke();
      ctx.strokeStyle = color;
      ctx.lineWidth = isSel ? 2.2 : 1.4;
      ctx.setLineDash([7, 6]);
      ctx.lineDashOffset = -now / 40;
      ctx.stroke();
      ctx.setLineDash([]);
      // Destination marker.
      const ex = camera.worldToScreenX(u.path[u.path.length - 2]);
      const ey = camera.worldToScreenY(u.path[u.path.length - 1]);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(ex, ey, isSel ? 7 : 4, 0, Math.PI * 2);
      ctx.stroke();
      if (isSel) {
        ctx.beginPath();
        ctx.moveTo(ex - 11, ey);
        ctx.lineTo(ex + 11, ey);
        ctx.moveTo(ex, ey - 11);
        ctx.lineTo(ex, ey + 11);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  draw(ctx: CanvasRenderingContext2D, camera: Camera, now: number): void {
    const items = this.visibleItems(camera, now).sort((a, b) => a.sy - b.sy);
    const sel = this.game.selection;
    const selected = new Set(sel.kind === 'units' ? sel.ids : sel.kind === 'enemy' ? [sel.id] : []);
    this.hits = [];
    const deferred: MapItem[] = [];
    for (const item of items) {
      const hero = item.members.length === 1 && item.soldiers >= HERO_SOLDIERS;
      if (hero || item.members.some((m) => selected.has(m.unit.id))) deferred.push(item);
      else this.drawItem(ctx, camera, item, now, selected);
    }
    // Large armies and the selection are drawn last so they stay on top.
    for (const item of deferred) this.drawItem(ctx, camera, item, now, selected);
  }

  private drawItem(ctx: CanvasRenderingContext2D, camera: Camera, item: MapItem, now: number, selected: Set<number>): void {
    if (item.members.length === 1) this.drawUnit(ctx, camera, item, item.members[0].unit, item.members[0].r, now, selected.has(item.members[0].unit.id));
    else this.drawCluster(ctx, camera, item, now);
  }

  private zoomFactor(camera: Camera): number {
    return Math.pow(camera.relZoom, 0.28);
  }

  private drawUnit(ctx: CanvasRenderingContext2D, camera: Camera, item: MapItem, u: UnitNet, r: RenderUnit, now: number, isSelected: boolean): void {
    const level = camera.level;
    const zf = this.zoomFactor(camera);
    const sizeLog = Math.log2(Math.max(1, u.soldiers / 4000));
    const fh = clamp(9 * zf * (0.88 + 0.13 * sizeLog), 8, 32);
    const fw = fh * FLAG_ASPECT;
    const { sx, sy } = item;
    const own = u.nation === this.game.you;
    const nation = getNation(u.nation);
    const fighting = u.battleId !== null && u.status !== 'RETREATING';
    const retreating = u.status === 'RETREATING';
    const moving = (u.status === 'MOVING' || u.status === 'ATTACKING' || retreating) && !!u.path && u.pathIndex * 2 < u.path.length;

    // Formation blocks at the closest zoom: the army as battalions on the field.
    if (level >= 5) this.drawFormation(ctx, camera, u, r, nation.color);

    ctx.save();
    if (retreating) ctx.globalAlpha = 0.72;

    // Ground shadow.
    ctx.fillStyle = 'rgba(20,14,6,0.28)';
    ctx.beginPath();
    ctx.ellipse(sx, sy + fh * 0.62, fw * 0.55, fh * 0.2, 0, 0, Math.PI * 2);
    ctx.fill();

    if (isSelected) {
      const pulse = 0.6 + 0.4 * Math.sin(now / 220);
      ctx.strokeStyle = `rgba(255,214,110,${0.55 + 0.4 * pulse})`;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.ellipse(sx, sy + fh * 0.62, fw * 0.95, fh * 0.42, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Heading chevron for marching armies.
    if (moving) {
      const a = r.heading;
      const d = fw * 0.5 + 9;
      const hx = sx + Math.cos(a) * d;
      const hy = sy + Math.sin(a) * d;
      ctx.fillStyle = retreating ? 'rgba(240,240,240,0.9)' : u.status === 'ATTACKING' ? '#e6503c' : rgba(nation.color, 0.95);
      ctx.strokeStyle = 'rgba(16,12,8,0.85)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(hx + Math.cos(a) * 7, hy + Math.sin(a) * 7);
      ctx.lineTo(hx + Math.cos(a + 2.4) * 6, hy + Math.sin(a + 2.4) * 6);
      ctx.lineTo(hx + Math.cos(a) * 1.5, hy + Math.sin(a) * 1.5);
      ctx.lineTo(hx + Math.cos(a - 2.4) * 6, hy + Math.sin(a - 2.4) * 6);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Flag with dark frame (red, pulsing frame in battle).
    const fx = sx - fw / 2;
    const fy = sy - fh / 2;
    if (fighting) {
      const pulse = 0.5 + 0.5 * Math.sin(now / 130 + u.id);
      ctx.shadowColor = `rgba(255,70,40,${0.6 + 0.4 * pulse})`;
      ctx.shadowBlur = 10;
    } else if (isSelected) {
      ctx.shadowColor = 'rgba(255,214,110,0.9)';
      ctx.shadowBlur = 10;
    } else {
      ctx.shadowColor = 'rgba(0,0,0,0.45)';
      ctx.shadowBlur = 4;
      ctx.shadowOffsetY = 1;
    }
    ctx.fillStyle = fighting ? '#b3241a' : isSelected ? '#ffd56e' : '#15120d';
    ctx.fillRect(fx - 1.5, fy - 1.5, fw + 3, fh + 3);
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    ctx.drawImage(flagBitmap(u.nation, fh), fx, fy, fw, fh);
    if (retreating) {
      ctx.strokeStyle = 'rgba(255,255,255,0.9)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(fx, fy + fh);
      ctx.lineTo(fx + fw, fy);
      ctx.stroke();
    }

    // Army type glyph.
    if (level >= 3) {
      const s = Math.max(9, fh * 0.55);
      const gx = fx + fw - s * 0.35;
      const gy = fy - s * 0.35;
      ctx.fillStyle = '#15120d';
      ctx.fillRect(gx - s / 2, gy - s / 2, s, s);
      ctx.fillStyle = '#efe6cf';
      ctx.font = `700 ${Math.round(s * 0.8)}px ${UI_FONT}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(ARMY_TYPE_STATS[u.type].symbol, gx, gy + 0.5);
    }

    // Crossed swords while fighting.
    if (fighting) this.drawSwords(ctx, fx - 2, fy - 2, Math.max(10, fh * 0.6));

    // Troop number: size = base * zoom * army scale, clamped.
    const hero = u.soldiers >= HERO_SOLDIERS;
    const armyScale = 1 + 0.32 * sizeLog;
    let fontSize = clamp(11 * zf * armyScale, 10, 56);
    if (hero && level <= 4) fontSize = clamp(fontSize * 1.18, 18, 60);
    const text = level <= 2 && !hero ? formatCompact(r.shown) : formatNumber(r.shown);
    ctx.font = `700 ${Math.round(fontSize)}px ${UI_FONT}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    const ty = fy + fh + 2;
    ctx.lineJoin = 'round';
    ctx.lineWidth = Math.max(3, fontSize * 0.2);
    ctx.strokeStyle = 'rgba(14,11,7,0.92)';
    ctx.strokeText(text, sx, ty);
    if (hero) {
      const [cr, cg, cb] = hexToRgb(nation.color);
      ctx.shadowColor = `rgba(${cr},${cg},${cb},0.9)`;
      ctx.shadowBlur = fontSize * 0.35;
    }
    ctx.fillStyle = fighting ? '#ffd9c8' : own ? '#fff3cf' : '#f6f0e2';
    ctx.fillText(text, sx, ty);
    ctx.shadowBlur = 0;
    ctx.shadowColor = 'transparent';
    const textW = ctx.measureText(text).width;

    // Morale bar.
    if (level >= 4) {
      const bw = Math.max(fw, 26);
      const by = ty + fontSize + 3;
      ctx.fillStyle = 'rgba(14,11,7,0.8)';
      ctx.fillRect(sx - bw / 2 - 1, by - 1, bw + 2, 5);
      const m = u.morale / 100;
      ctx.fillStyle = m > 0.6 ? '#7fbf5a' : m > 0.3 ? '#e2b33c' : '#d6493a';
      ctx.fillRect(sx - bw / 2, by, bw * m, 3);
    }

    // Own army marker.
    if (own && level >= 2) {
      ctx.fillStyle = '#e6c25a';
      ctx.beginPath();
      ctx.moveTo(sx, fy - 5);
      ctx.lineTo(sx - 4, fy - 10);
      ctx.lineTo(sx + 4, fy - 10);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();

    const half = Math.max(fw / 2 + 4, textW / 2);
    this.hits.push({ item, x0: sx - half, y0: fy - 10, x1: sx + half, y1: ty + fontSize + 4 });
  }

  private drawCluster(ctx: CanvasRenderingContext2D, camera: Camera, item: MapItem, now: number): void {
    const zf = this.zoomFactor(camera);
    const sizeLog = Math.log2(Math.max(1, item.soldiers / 4000));
    const fh = clamp(10 * zf * (0.9 + 0.12 * sizeLog), 10, 30);
    const fw = fh * FLAG_ASPECT;
    const { sx, sy } = item;
    const bmp = flagBitmap(item.nation, fh);
    ctx.save();
    // Stacked flags read as "several armies here".
    for (let k = 2; k >= 1; k--) {
      const off = k * 3;
      ctx.fillStyle = '#15120d';
      ctx.fillRect(sx - fw / 2 + off - 1, sy - fh / 2 - off - 1, fw + 2, fh + 2);
      ctx.globalAlpha = 0.85;
      ctx.drawImage(bmp, sx - fw / 2 + off, sy - fh / 2 - off, fw, fh);
      ctx.globalAlpha = 1;
    }
    if (item.inBattle) {
      const pulse = 0.5 + 0.5 * Math.sin(now / 140);
      ctx.shadowColor = `rgba(255,70,40,${0.6 + 0.4 * pulse})`;
      ctx.shadowBlur = 12;
    } else {
      ctx.shadowColor = 'rgba(0,0,0,0.45)';
      ctx.shadowBlur = 5;
    }
    ctx.fillStyle = item.inBattle ? '#b3241a' : '#15120d';
    ctx.fillRect(sx - fw / 2 - 1.5, sy - fh / 2 - 1.5, fw + 3, fh + 3);
    ctx.shadowBlur = 0;
    ctx.shadowColor = 'transparent';
    ctx.drawImage(bmp, sx - fw / 2, sy - fh / 2, fw, fh);

    // Army count badge.
    const badge = `×${item.members.length}`;
    ctx.font = `700 ${Math.round(Math.max(10, fh * 0.55))}px ${UI_FONT}`;
    const bw = ctx.measureText(badge).width + 8;
    const bh = Math.max(12, fh * 0.62);
    const bx = sx + fw / 2 - 2;
    const by = sy - fh / 2 - bh / 2 - 3;
    ctx.fillStyle = item.nation === this.game.you ? '#e6c25a' : '#efe6cf';
    ctx.strokeStyle = '#15120d';
    ctx.lineWidth = 1.5;
    roundRect(ctx, bx, by, bw, bh, bh / 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#15120d';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(badge, bx + bw / 2, by + bh / 2 + 0.5);

    // Total troops.
    const fontSize = clamp(11 * zf * (1 + 0.3 * sizeLog), 11, 44);
    const text = formatCompact(item.soldiers);
    ctx.font = `700 ${Math.round(fontSize)}px ${UI_FONT}`;
    ctx.textBaseline = 'top';
    const ty = sy + fh / 2 + 2;
    ctx.lineJoin = 'round';
    ctx.lineWidth = Math.max(3, fontSize * 0.2);
    ctx.strokeStyle = 'rgba(14,11,7,0.92)';
    ctx.strokeText(text, sx, ty);
    ctx.fillStyle = item.nation === this.game.you ? '#fff3cf' : '#f6f0e2';
    ctx.fillText(text, sx, ty);
    const tw = ctx.measureText(text).width;
    ctx.restore();
    const half = Math.max(fw / 2 + 8, tw / 2);
    this.hits.push({ item, x0: sx - half, y0: sy - fh / 2 - 10, x1: sx + half + bw, y1: ty + fontSize + 2 });
  }

  private drawSwords(ctx: CanvasRenderingContext2D, x: number, y: number, s: number): void {
    ctx.save();
    ctx.translate(x, y);
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#15120d';
    ctx.lineWidth = s * 0.32;
    ctx.beginPath();
    ctx.moveTo(-s / 2, -s / 2);
    ctx.lineTo(s / 2, s / 2);
    ctx.moveTo(s / 2, -s / 2);
    ctx.lineTo(-s / 2, s / 2);
    ctx.stroke();
    ctx.strokeStyle = '#f2e1b8';
    ctx.lineWidth = s * 0.14;
    ctx.stroke();
    ctx.restore();
  }

  private drawFormation(ctx: CanvasRenderingContext2D, camera: Camera, u: UnitNet, r: RenderUnit, color: string): void {
    const blocks = Math.max(2, Math.min(24, Math.round(u.soldiers / 2500)));
    const perRow = Math.ceil(Math.sqrt(blocks * 2));
    const bw = 7 * camera.zoom * 0.5;
    const bh = 3.2 * camera.zoom * 0.5;
    const gap = 2.2 * camera.zoom * 0.5;
    ctx.save();
    ctx.translate(camera.worldToScreenX(r.x), camera.worldToScreenY(r.y));
    ctx.rotate(r.heading + Math.PI / 2);
    const rows = Math.ceil(blocks / perRow);
    ctx.fillStyle = rgba(color, 0.85);
    ctx.strokeStyle = 'rgba(20,14,8,0.85)';
    ctx.lineWidth = 1;
    for (let i = 0; i < blocks; i++) {
      const row = Math.floor(i / perRow);
      const col = i % perRow;
      const x = (col - (perRow - 1) / 2) * (bw + gap);
      const y = (row - (rows - 1) / 2) * (bh + gap * 1.6) + bh * 3;
      ctx.fillRect(x - bw / 2, y - bh / 2, bw, bh);
      ctx.strokeRect(x - bw / 2, y - bh / 2, bw, bh);
    }
    ctx.restore();
  }

  /** Topmost marker under a screen point. */
  hitTest(sx: number, sy: number, pad = 4): MapItem | null {
    for (let i = this.hits.length - 1; i >= 0; i--) {
      const h = this.hits[i];
      if (sx >= h.x0 - pad && sx <= h.x1 + pad && sy >= h.y0 - pad && sy <= h.y1 + pad) return h.item;
    }
    return null;
  }

  /** Markers inside a screen rectangle (box selection). */
  itemsIn(x0: number, y0: number, x1: number, y1: number): MapItem[] {
    return this.items.filter((it) => it.sx >= x0 && it.sx <= x1 && it.sy >= y0 && it.sy <= y1);
  }
}

export function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
