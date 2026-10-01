import { formatNumber, hash2 } from '@warfront/shared';
import { FLAG_ASPECT, flagBitmap } from './FlagPainter';
import { TITLE_FONT, UI_FONT } from './palette';

interface Marker {
  nation: string;
  x: number;
  y: number;
  vx: number;
  soldiers: number;
}

function noise(x: number, y: number): number {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const fx = x - xi;
  const fy = y - yi;
  const s = (t: number) => t * t * (3 - 2 * t);
  const a = hash2(xi, yi, 3);
  const b = hash2(xi + 1, yi, 3);
  const c = hash2(xi, yi + 1, 3);
  const d = hash2(xi + 1, yi + 1, 3);
  return a + (b - a) * s(fx) + (c - a) * s(fy) + (a - b - c + d) * s(fx) * s(fy);
}

/**
 * Animated main-menu backdrop: a parchment battlefield with a moving front,
 * marching armies and falling troop counts — the game in one glance.
 */
export class MenuBackdrop {
  private raf = 0;
  private paper: HTMLCanvasElement | null = null;
  private markers: Marker[] = [];
  private t = 0;
  private last = performance.now();

  constructor(private canvas: HTMLCanvasElement) {
    for (let i = 0; i < 26; i++) {
      const west = i % 2 === 0;
      this.markers.push({
        nation: west ? (i % 6 === 0 ? 'prussia' : 'britain') : 'france',
        x: west ? 0.48 + Math.random() * 0.2 : 0.8 + Math.random() * 0.2,
        y: 0.08 + Math.random() * 0.84,
        vx: (west ? 1 : -1) * (0.004 + Math.random() * 0.006),
        soldiers: Math.round(2000 + Math.random() * Math.random() * 30000),
      });
    }
    this.markers[0].soldiers = 58456;
    this.markers[1].soldiers = 39900;
    this.raf = requestAnimationFrame(this.frame);
  }

  destroy(): void {
    cancelAnimationFrame(this.raf);
  }

  private buildPaper(w: number, h: number): HTMLCanvasElement {
    const c = document.createElement('canvas');
    c.width = Math.ceil(w / 2);
    c.height = Math.ceil(h / 2);
    const g = c.getContext('2d')!;
    const img = g.createImageData(c.width, c.height);
    for (let y = 0; y < c.height; y++) {
      for (let x = 0; x < c.width; x++) {
        const n = noise(x / 60, y / 60) * 0.6 + noise(x / 18, y / 18) * 0.3 + noise(x / 5, y / 5) * 0.1;
        const band = (n * 14) % 1;
        const line = band < 0.06 ? 0.86 : 1;
        const o = (y * c.width + x) * 4;
        img.data[o] = (214 + n * 26) * line;
        img.data[o + 1] = (200 + n * 22) * line;
        img.data[o + 2] = (164 + n * 16) * line;
        img.data[o + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
    // A river through the field.
    g.strokeStyle = 'rgba(93,143,168,0.9)';
    g.lineWidth = 3;
    g.beginPath();
    for (let y = 0; y <= c.height; y += 6) g.lineTo(c.width * 0.62 + Math.sin(y / 40) * 30 + noise(3, y / 50) * 40, y);
    g.stroke();
    return c;
  }

  private frame = (now: number): void => {
    this.raf = requestAnimationFrame(this.frame);
    const dt = Math.min(0.05, (now - this.last) / 1000);
    this.last = now;
    this.t += dt;
    const canvas = this.canvas;
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (canvas.width !== Math.round(rect.width * dpr)) {
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      this.paper = null;
    }
    const w = rect.width;
    const h = rect.height;
    const ctx = canvas.getContext('2d')!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!this.paper) this.paper = this.buildPaper(w, h);
    ctx.drawImage(this.paper, 0, 0, w, h);

    // Front line between the two sides, slowly shifting.
    const frontX = (y: number) => w * (0.7 + Math.sin(this.t * 0.15) * 0.03) + Math.sin(y / 70 + this.t * 0.4) * 18 + (noise(1, y / 90) - 0.5) * 90;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    for (let y = 0; y <= h; y += 10) ctx.lineTo(frontX(y), y);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = 'rgba(200,70,63,0.22)';
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(w, 0);
    for (let y = 0; y <= h; y += 10) ctx.lineTo(frontX(y), y);
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fillStyle = 'rgba(58,111,208,0.24)';
    ctx.fill();
    ctx.beginPath();
    for (let y = 0; y <= h; y += 10) ctx.lineTo(frontX(y), y);
    ctx.strokeStyle = 'rgba(214,52,36,0.45)';
    ctx.lineWidth = 9;
    ctx.stroke();
    ctx.strokeStyle = '#8e1b14';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Armies.
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.lineJoin = 'round';
    for (const m of this.markers) {
      const px = m.x * w;
      const py = m.y * h;
      const fx = frontX(py);
      const atFront = Math.abs(px - fx) < 26;
      if (!atFront) m.x += m.vx * dt;
      else {
        m.soldiers = Math.max(400, m.soldiers - dt * (60 + m.soldiers * 0.01));
        if (Math.random() < dt * 6) {
          ctx.fillStyle = 'rgba(255,230,160,0.9)';
          ctx.beginPath();
          ctx.arc(px + (Math.random() - 0.5) * 30, py + (Math.random() - 0.5) * 20, 2 + Math.random() * 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      if (m.x < -0.05 || m.x > 1.05) m.x = m.vx > 0 ? 0.45 : 1;
      const big = m.soldiers > 35000;
      const fh = big ? 22 : 13 + Math.log2(m.soldiers / 2000 + 1) * 2;
      const fw = fh * FLAG_ASPECT;
      ctx.fillStyle = atFront ? '#b3241a' : '#15120d';
      ctx.fillRect(px - fw / 2 - 1.5, py - fh / 2 - 1.5, fw + 3, fh + 3);
      ctx.drawImage(flagBitmap(m.nation, fh), px - fw / 2, py - fh / 2, fw, fh);
      const size = big ? 38 : 13 + Math.log2(m.soldiers / 2000 + 1) * 2.4;
      ctx.font = `700 ${Math.round(size)}px ${UI_FONT}`;
      ctx.lineWidth = Math.max(3, size * 0.2);
      ctx.strokeStyle = 'rgba(14,11,7,0.92)';
      const text = formatNumber(m.soldiers);
      ctx.strokeText(text, px, py + fh / 2 + 2);
      ctx.fillStyle = '#f6f0e2';
      ctx.fillText(text, px, py + fh / 2 + 2);
    }
    ctx.font = `400 15px ${TITLE_FONT}`;
    ctx.fillStyle = 'rgba(60,40,24,0.55)';
    ctx.fillText('⚔ ⚔ BATTLE OF VALOIS RIDGE', frontX(h * 0.18), h * 0.18 - 40);
  };
}
