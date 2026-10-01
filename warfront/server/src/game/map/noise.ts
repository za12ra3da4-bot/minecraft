import { hash2 } from '@warfront/shared';

const GRADS: [number, number][] = [];
for (let i = 0; i < 16; i++) {
  const a = (i / 16) * Math.PI * 2;
  GRADS.push([Math.cos(a), Math.sin(a)]);
}

function fade(t: number): number {
  return t * t * t * (t * (t * 6 - 15) + 10);
}

/** Seeded 2D gradient noise in roughly [-1, 1]. */
export function gradientNoise(x: number, y: number, seed: number): number {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const fx = x - x0;
  const fy = y - y0;
  const dot = (ix: number, iy: number, dx: number, dy: number): number => {
    const g = GRADS[Math.floor(hash2(ix, iy, seed) * 16)];
    return g[0] * dx + g[1] * dy;
  };
  const n00 = dot(x0, y0, fx, fy);
  const n10 = dot(x0 + 1, y0, fx - 1, fy);
  const n01 = dot(x0, y0 + 1, fx, fy - 1);
  const n11 = dot(x0 + 1, y0 + 1, fx - 1, fy - 1);
  const u = fade(fx);
  const v = fade(fy);
  const nx0 = n00 + (n10 - n00) * u;
  const nx1 = n01 + (n11 - n01) * u;
  return (nx0 + (nx1 - nx0) * v) * 1.41;
}

/** Fractal brownian motion of gradient noise, roughly [-1, 1]. */
export function fbm(x: number, y: number, seed: number, octaves = 5): number {
  let amp = 1;
  let freq = 1;
  let sum = 0;
  let norm = 0;
  for (let o = 0; o < octaves; o++) {
    sum += gradientNoise(x * freq, y * freq, seed + o * 1013) * amp;
    norm += amp;
    amp *= 0.5;
    freq *= 2.03;
  }
  return sum / norm;
}
