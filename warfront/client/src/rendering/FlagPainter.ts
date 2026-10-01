import { getNation, type FlagLayer, type FlagSpec, type NationId } from '@warfront/shared';

/** Flags are 3:2. */
export const FLAG_ASPECT = 1.5;

function paintLayer(ctx: CanvasRenderingContext2D, layer: FlagLayer, w: number, h: number): void {
  switch (layer.kind) {
    case 'stripes-h':
    case 'stripes-v': {
      const weights = layer.weights ?? layer.colors.map(() => 1);
      const total = weights.reduce((a, b) => a + b, 0);
      let pos = 0;
      layer.colors.forEach((color, i) => {
        const size = (weights[i] / total) * (layer.kind === 'stripes-h' ? h : w);
        ctx.fillStyle = color;
        if (layer.kind === 'stripes-h') ctx.fillRect(0, pos, w, size + 0.5);
        else ctx.fillRect(pos, 0, size + 0.5, h);
        pos += size;
      });
      break;
    }
    case 'cross': {
      const t = layer.width * h;
      const cx = w / 2 + (layer.offsetX ?? 0) * w;
      ctx.fillStyle = layer.color;
      ctx.fillRect(cx - t / 2, 0, t, h);
      ctx.fillRect(0, h / 2 - t / 2, w, t);
      break;
    }
    case 'saltire': {
      ctx.strokeStyle = layer.color;
      ctx.lineWidth = layer.width * h;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(w, h);
      ctx.moveTo(w, 0);
      ctx.lineTo(0, h);
      ctx.stroke();
      break;
    }
    case 'border': {
      ctx.strokeStyle = layer.color;
      ctx.lineWidth = layer.width * h;
      ctx.strokeRect(0, 0, w, h);
      break;
    }
    case 'canton': {
      ctx.fillStyle = layer.color;
      ctx.fillRect(0, 0, layer.w * w, layer.h * h);
      break;
    }
    case 'disc': {
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      ctx.arc(layer.x * w, layer.y * h, layer.r * h, 0, Math.PI * 2);
      ctx.fill();
      break;
    }
    case 'crescent': {
      const x = layer.x * w;
      const y = layer.y * h;
      const r = layer.r * h;
      ctx.save();
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath();
      ctx.arc(x + r * 0.32, y, r * 0.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      break;
    }
    case 'star': {
      const x = layer.x * w;
      const y = layer.y * h;
      const r = layer.r * h;
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      for (let i = 0; i < 10; i++) {
        const a = -Math.PI / 2 + (i * Math.PI) / 5;
        const rr = i % 2 === 0 ? r : r * 0.45;
        ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
      }
      ctx.closePath();
      ctx.fill();
      break;
    }
    case 'eagle': {
      // Stylised spread-wing emblem.
      const x = layer.x * w;
      const y = layer.y * h;
      const s = layer.size * h;
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      ctx.moveTo(x, y - s * 0.5);
      ctx.lineTo(x + s * 0.12, y - s * 0.2);
      ctx.lineTo(x + s * 0.75, y - s * 0.38);
      ctx.lineTo(x + s * 0.5, y + s * 0.02);
      ctx.lineTo(x + s * 0.18, y + s * 0.08);
      ctx.lineTo(x + s * 0.28, y + s * 0.5);
      ctx.lineTo(x, y + s * 0.3);
      ctx.lineTo(x - s * 0.28, y + s * 0.5);
      ctx.lineTo(x - s * 0.18, y + s * 0.08);
      ctx.lineTo(x - s * 0.5, y + s * 0.02);
      ctx.lineTo(x - s * 0.75, y - s * 0.38);
      ctx.lineTo(x - s * 0.12, y - s * 0.2);
      ctx.closePath();
      ctx.fill();
      break;
    }
  }
}

/** Paints a flag spec at (0,0) with size w*h on the given context. */
export function paintFlag(ctx: CanvasRenderingContext2D, spec: FlagSpec, w: number, h: number): void {
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, 0, w, h);
  ctx.clip();
  ctx.fillStyle = spec.field;
  ctx.fillRect(0, 0, w, h);
  for (const layer of spec.layers) paintLayer(ctx, layer, w, h);
  // Subtle cloth shading.
  const g = ctx.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, 'rgba(255,255,255,0.18)');
  g.addColorStop(0.5, 'rgba(255,255,255,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.2)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);
  ctx.restore();
}

const cache = new Map<string, HTMLCanvasElement>();

/**
 * Pre-rendered flag bitmap. Heights are bucketed so the cache stays small
 * while flags stay crisp at every zoom level.
 */
export function flagBitmap(nation: NationId, height: number): HTMLCanvasElement {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const bucket = Math.max(8, Math.min(96, Math.ceil((height * dpr) / 8) * 8));
  const key = `${nation}:${bucket}`;
  let c = cache.get(key);
  if (!c) {
    c = document.createElement('canvas');
    const h = bucket;
    const w = Math.round(h * FLAG_ASPECT);
    c.width = w;
    c.height = h;
    paintFlag(c.getContext('2d')!, getNation(nation).flag, w, h);
    cache.set(key, c);
  }
  return c;
}

const urlCache = new Map<string, string>();

/** Data URL of a flag for use in <img> elements. */
export function flagDataUrl(nation: NationId, height = 28): string {
  const key = `${nation}:${height}`;
  let url = urlCache.get(key);
  if (!url) {
    const c = document.createElement('canvas');
    c.height = height * 2;
    c.width = Math.round(height * 2 * FLAG_ASPECT);
    paintFlag(c.getContext('2d')!, getNation(nation).flag, c.width, c.height);
    url = c.toDataURL();
    urlCache.set(key, url);
  }
  return url;
}
