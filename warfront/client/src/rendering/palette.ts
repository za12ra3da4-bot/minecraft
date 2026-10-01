import { NEUTRAL_COLOR, getNation, type NationId } from '@warfront/shared';

/** Colours of the parchment war map. */
export const MAP_COLORS = {
  paperLow: [231, 220, 190],
  paperHigh: [196, 175, 132],
  forest: [128, 142, 96],
  seaDeep: [118, 152, 162],
  seaShallow: [170, 196, 196],
  coastInk: [62, 58, 48],
  river: '#5d8fa8',
  riverEdge: 'rgba(40,60,70,0.45)',
  road: 'rgba(110,84,52,0.75)',
  roadMajor: 'rgba(92,66,40,0.9)',
  ink: '#2b2720',
  labelHalo: 'rgba(240,230,205,0.85)',
  front: '#8e1b14',
  frontGlow: 'rgba(214,52,36,0.38)',
} as const;

export const UI_FONT = '"Barlow Condensed", "Arial Narrow", sans-serif';
export const LABEL_FONT = '"Spectral", Georgia, serif';
export const TITLE_FONT = '"IM Fell English SC", Georgia, serif';

const rgbCache = new Map<string, [number, number, number]>();

export function hexToRgb(hex: string): [number, number, number] {
  let c = rgbCache.get(hex);
  if (!c) {
    const v = parseInt(hex.slice(1), 16);
    c = [(v >> 16) & 255, (v >> 8) & 255, v & 255];
    rgbCache.set(hex, c);
  }
  return c;
}

export function nationColor(id: NationId | null): string {
  return id ? getNation(id).color : NEUTRAL_COLOR;
}

export function rgba(hex: string, a: number): string {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
}

/** Lighter/darker variant of a nation colour. */
export function shade(hex: string, amount: number): string {
  const [r, g, b] = hexToRgb(hex);
  const f = (v: number): number => Math.max(0, Math.min(255, Math.round(amount >= 0 ? v + (255 - v) * amount : v * (1 + amount))));
  return `rgb(${f(r)},${f(g)},${f(b)})`;
}
