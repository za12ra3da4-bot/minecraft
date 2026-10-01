import { formatNumber } from '@warfront/shared';
import type { Camera } from '../game/Camera';
import type { GameClient } from '../game/GameClient';
import { settings } from '../data/settings';
import { flagBitmap } from './FlagPainter';
import { UI_FONT, TITLE_FONT } from './palette';
import type { TerritoryLayer } from './TerritoryLayer';

interface Particle {
  kind: 'smoke' | 'flash' | 'spark';
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  max: number;
  size: number;
}

interface FloatText {
  x: number;
  y: number;
  text: string;
  color: string;
  life: number;
  max: number;
  size: number;
}

interface Ring {
  x: number;
  y: number;
  life: number;
  max: number;
  color: string;
  radius: number;
}

const MAX_PARTICLES = 900;

function sprite(inner: string, outer: string): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, inner);
  grad.addColorStop(1, outer);
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return c;
}

/** Battle smoke, muzzle flashes, casualty numbers and order/capture markers. */
export class EffectsLayer {
  private particles: Particle[] = [];
  private texts: FloatText[] = [];
  private rings: Ring[] = [];
  private smoke = sprite('rgba(214,206,190,0.75)', 'rgba(214,206,190,0)');
  private flash = sprite('rgba(255,246,200,1)', 'rgba(255,170,60,0)');
  private glow = sprite('rgba(220,40,24,0.55)', 'rgba(220,40,24,0)');
  /** Zoom level of the last frame; casualty numbers are hidden on the overview. */
  private lastLevel = 3;

  constructor(
    private game: GameClient,
    private territories: TerritoryLayer,
  ) {}

  update(dt: number): void {
    const game = this.game;
    for (const e of game.effects) {
      if (e.kind === 'loss') {
        if (this.lastLevel <= 1 && e.amount < 1500) continue;
        const big = e.amount >= 1000;
        this.texts.push({ x: e.x, y: e.y, text: `-${formatNumber(e.amount)}`, color: big ? '#ff6a50' : '#ff9a80', life: 0, max: 1.4, size: Math.min(26, 12 + Math.log10(Math.max(10, e.amount)) * 3) });
      } else if (e.kind === 'destroyed') {
        for (let i = 0; i < 18; i++) this.spawn('smoke', e.x, e.y, 18, 1.2 + Math.random(), 10 + Math.random() * 14);
        for (let i = 0; i < 10; i++) this.spawn('spark', e.x, e.y, 40, 0.5, 2.5);
        this.rings.push({ x: e.x, y: e.y, life: 0, max: 0.9, color: '255,90,60', radius: 46 });
      } else if (e.kind === 'capture') {
        this.territories.flash(e.territoryId);
        const t = game.replica.map.territories[e.territoryId];
        if (t) this.rings.push({ x: t.cx, y: t.cy, life: 0, max: 1.2, color: '255,226,140', radius: 90 });
      } else if (e.kind === 'order') {
        this.rings.push({ x: e.x, y: e.y, life: 0, max: 0.6, color: '255,224,140', radius: 18 });
      }
    }
    game.effects.length = 0;

    // Battle emitters.
    if (settings.value.battleEffects && !game.replica.paused) {
      for (const b of game.replica.battles) {
        const total = b.sides.reduce((s, x) => s + x.soldiers, 0);
        const rate = Math.min(30, 4 + Math.log10(Math.max(10, total)) * 4);
        let n = rate * dt;
        while (n > 0) {
          if (Math.random() < n) {
            const a = Math.random() * Math.PI * 2;
            const d = Math.sqrt(Math.random()) * b.radius * 0.8;
            const x = b.x + Math.cos(a) * d;
            const y = b.y + Math.sin(a) * d;
            this.spawn('smoke', x, y, 6, 2 + Math.random() * 2, 6 + Math.random() * 10);
            if (Math.random() < 0.8) this.spawn('flash', x + (Math.random() - 0.5) * 10, y + (Math.random() - 0.5) * 10, 0, 0.12 + Math.random() * 0.1, 4 + Math.random() * 5);
          }
          n -= 1;
        }
      }
    }

    for (const p of this.particles) {
      p.life += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vx *= 0.97;
      p.vy *= 0.97;
      if (p.kind === 'smoke') p.vy -= 2 * dt;
    }
    this.particles = this.particles.filter((p) => p.life < p.max);
    for (const t of this.texts) t.life += dt;
    this.texts = this.texts.filter((t) => t.life < t.max);
    for (const r of this.rings) r.life += dt;
    this.rings = this.rings.filter((r) => r.life < r.max);
  }

  private spawn(kind: Particle['kind'], x: number, y: number, speed: number, life: number, size: number): void {
    if (this.particles.length >= MAX_PARTICLES) this.particles.shift();
    const a = Math.random() * Math.PI * 2;
    const s = speed * (0.3 + Math.random() * 0.7);
    this.particles.push({ kind, x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 0, max: life, size });
  }

  /** Red glow under battles (drawn below the armies). */
  drawUnder(ctx: CanvasRenderingContext2D, camera: Camera, now: number): void {
    for (const b of this.game.replica.battles) {
      const sx = camera.worldToScreenX(b.x);
      const sy = camera.worldToScreenY(b.y);
      const r = Math.max(34, b.radius * camera.zoom * 1.5) * (1 + 0.08 * Math.sin(now / 300 + b.id));
      if (sx < -r || sy < -r || sx > camera.viewW + r || sy > camera.viewH + r) continue;
      ctx.drawImage(this.glow, sx - r, sy - r, r * 2, r * 2);
    }
  }

  /** Particles, rings, floating numbers and battle labels (drawn above armies). */
  drawOver(ctx: CanvasRenderingContext2D, camera: Camera): void {
    const z = camera.zoom;
    this.lastLevel = camera.level;
    ctx.save();
    for (const p of this.particles) {
      const sx = camera.worldToScreenX(p.x);
      const sy = camera.worldToScreenY(p.y);
      const t = p.life / p.max;
      if (p.kind === 'smoke') {
        const size = Math.max(6, p.size * z * (1 + t * 1.6));
        ctx.globalAlpha = 0.55 * (1 - t);
        ctx.drawImage(this.smoke, sx - size, sy - size, size * 2, size * 2);
      } else if (p.kind === 'flash') {
        const size = Math.max(3, p.size * Math.min(z, 3));
        ctx.globalAlpha = 1 - t;
        ctx.drawImage(this.flash, sx - size, sy - size, size * 2, size * 2);
      } else {
        ctx.globalAlpha = 1 - t;
        ctx.fillStyle = '#ffcf6a';
        ctx.fillRect(sx - 1.5, sy - 1.5, 3, 3);
      }
    }
    ctx.globalAlpha = 1;

    for (const r of this.rings) {
      const t = r.life / r.max;
      ctx.strokeStyle = `rgba(${r.color},${1 - t})`;
      ctx.lineWidth = 2.5 * (1 - t) + 0.5;
      ctx.beginPath();
      ctx.arc(camera.worldToScreenX(r.x), camera.worldToScreenY(r.y), Math.max(8, r.radius * Math.min(z, 2.5)) * (0.3 + t * 0.9), 0, Math.PI * 2);
      ctx.stroke();
    }

    this.drawBattleLabels(ctx, camera);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    for (const t of this.texts) {
      const k = t.life / t.max;
      const sx = camera.worldToScreenX(t.x) + 18;
      const sy = camera.worldToScreenY(t.y) - 14 - k * 34;
      ctx.globalAlpha = k < 0.15 ? k / 0.15 : 1 - Math.max(0, (k - 0.6) / 0.4);
      ctx.font = `700 ${Math.round(t.size)}px ${UI_FONT}`;
      ctx.lineWidth = 3.5;
      ctx.strokeStyle = 'rgba(20,6,4,0.9)';
      ctx.strokeText(t.text, sx, sy);
      ctx.fillStyle = t.color;
      ctx.fillText(t.text, sx, sy);
    }
    ctx.restore();
  }

  private drawBattleLabels(ctx: CanvasRenderingContext2D, camera: Camera): void {
    const level = camera.level;
    for (const b of this.game.replica.battles) {
      const total = b.sides.reduce((s, x) => s + x.soldiers, 0);
      if (level === 1 && total < 40_000) continue;
      const sx = camera.worldToScreenX(b.x);
      const sy = camera.worldToScreenY(b.y) - Math.max(30, b.radius * camera.zoom) - 26;
      if (sx < -200 || sy < -60 || sx > camera.viewW + 200 || sy > camera.viewH + 60) continue;
      const sides = b.sides.slice(0, 3).sort((p, q) => q.soldiers - p.soldiers);
      ctx.save();
      ctx.font = `600 11px ${TITLE_FONT}`;
      const title = `⚔ ${b.name.toUpperCase()}`;
      const titleW = ctx.measureText(title).width;
      ctx.font = `700 15px ${UI_FONT}`;
      const parts = sides.map((s) => formatNumber(s.soldiers));
      const partsW = parts.reduce((w, p) => w + ctx.measureText(p).width + 26, 0) + (parts.length - 1) * 14;
      const w = Math.max(titleW, partsW) + 20;
      const h = 40;
      const x = sx - w / 2;
      const y = sy - h / 2;
      ctx.fillStyle = 'rgba(18,10,8,0.82)';
      ctx.strokeStyle = 'rgba(214,72,50,0.85)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + w, y);
      ctx.lineTo(x + w, y + h);
      ctx.lineTo(sx + 6, y + h);
      ctx.lineTo(sx, y + h + 6);
      ctx.lineTo(sx - 6, y + h);
      ctx.lineTo(x, y + h);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      ctx.font = `600 11px ${TITLE_FONT}`;
      ctx.fillStyle = '#f0b8a4';
      ctx.fillText(title, sx, y + 11);
      ctx.font = `700 15px ${UI_FONT}`;
      let cx = sx - partsW / 2;
      sides.forEach((s, i) => {
        ctx.drawImage(flagBitmap(s.nation, 12), cx, y + 22, 18, 12);
        ctx.textAlign = 'left';
        ctx.fillStyle = '#f6f0e2';
        ctx.fillText(parts[i], cx + 22, y + 28.5);
        cx += ctx.measureText(parts[i]).width + 26;
        if (i < sides.length - 1) {
          ctx.fillStyle = '#d6483a';
          ctx.textAlign = 'center';
          ctx.fillText('·', cx + 4, y + 28);
          cx += 14;
        }
      });
      ctx.restore();
    }
  }
}
