import { CellFlag, SEA_LEVEL_BYTE, Terrain, hash2, type MapData, type MapGrids } from '@warfront/shared';
import type { Camera } from '../game/Camera';
import { MAP_COLORS } from './palette';

const TILE = 256;
const BASE_SCALE = 0.125;
const MAX_LEVEL = 6;
const MAX_TILES = 240;
const FRAME_BUDGET_MS = 9;

interface Tile {
  land: HTMLCanvasElement | null;
  water: HTMLCanvasElement | null;
}

/**
 * Parchment war-map terrain rendered into cached tiles at several zoom
 * levels. Land and water are separate layers so territory colours can sit
 * between them and the coastline stays crisp.
 */
export class TerrainLayer {
  private tiles = new Map<string, Tile>();
  private readonly vcols: number;
  private readonly vrows: number;
  /** Per-vertex land colour (Gouraud shaded) and gradient magnitude. */
  private readonly colR: Float32Array;
  private readonly colG: Float32Array;
  private readonly colB: Float32Array;
  private readonly slope: Float32Array;
  private readonly grain: Float32Array;

  constructor(
    private map: MapData,
    private grids: MapGrids,
  ) {
    const { cols, rows, cellSize } = map;
    this.vcols = cols + 1;
    this.vrows = rows + 1;
    const n = this.vcols * this.vrows;
    this.colR = new Float32Array(n);
    this.colG = new Float32Array(n);
    this.colB = new Float32Array(n);
    this.slope = new Float32Array(n);
    const H = grids.heights;
    const outsideAt = (cx: number, cy: number): number => {
      if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return 0;
      return grids.flags[cy * cols + cx] & CellFlag.OUTSIDE ? 1 : 0;
    };
    const forestAt = (cx: number, cy: number): number => {
      if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return 0;
      return grids.terrain[cy * cols + cx] === Terrain.FOREST ? 1 : 0;
    };
    const h = (i: number, j: number): number => H[Math.min(this.vrows - 1, Math.max(0, j)) * this.vcols + Math.min(this.vcols - 1, Math.max(0, i))];
    const [lr, lg, lb] = MAP_COLORS.paperLow;
    const [hr, hg, hb] = MAP_COLORS.paperHigh;
    const [fr, fg, fb] = MAP_COLORS.forest;
    for (let j = 0; j < this.vrows; j++) {
      for (let i = 0; i < this.vcols; i++) {
        const v = j * this.vcols + i;
        const gx = (h(i + 1, j) - h(i - 1, j)) / (2 * cellSize);
        const gy = (h(i, j + 1) - h(i, j - 1)) / (2 * cellSize);
        this.slope[v] = Math.hypot(gx, gy);
        // Light from the north-west.
        const shadeV = Math.max(-0.4, Math.min(0.4, (-gx - gy) * 6));
        const elev = Math.max(0, Math.min(1, (H[v] - SEA_LEVEL_BYTE) / (255 - SEA_LEVEL_BYTE)));
        const e = Math.pow(elev, 1.8) * 0.75;
        let r = lr + (hr - lr) * e;
        let g = lg + (hg - lg) * e;
        let b = lb + (hb - lb) * e;
        const forest = (forestAt(i - 1, j - 1) + forestAt(i, j - 1) + forestAt(i - 1, j) + forestAt(i, j)) / 4;
        r += (fr - r) * forest * 0.3;
        g += (fg - g) * forest * 0.3;
        b += (fb - b) * forest * 0.3;
        // Land outside the theatre is drawn faded, like an unexplored margin.
        const outside = (outsideAt(i - 1, j - 1) + outsideAt(i, j - 1) + outsideAt(i - 1, j) + outsideAt(i, j)) / 4;
        const grey = (r + g + b) / 3;
        r += (grey * 0.86 - r) * outside;
        g += (grey * 0.86 - g) * outside;
        b += (grey * 0.84 - b) * outside;
        const lit = 1 + shadeV * 0.4;
        this.colR[v] = r * lit;
        this.colG[v] = g * lit;
        this.colB[v] = b * lit;
      }
    }
    // Paper grain texture, sampled in world space so tiles line up.
    this.grain = new Float32Array(256 * 256);
    for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) this.grain[y * 256 + x] = hash2(x, y, 99) - 0.5;
  }

  private levelFor(camera: Camera, dpr: number): number {
    const want = (camera.zoom * dpr) / 1.2;
    return Math.max(0, Math.min(MAX_LEVEL, Math.ceil(Math.log2(want / BASE_SCALE))));
  }

  /** Draws one layer of terrain for the current view. */
  draw(ctx: CanvasRenderingContext2D, camera: Camera, dpr: number, layer: 'land' | 'water'): void {
    const level = this.levelFor(camera, dpr);
    const scale = BASE_SCALE * 2 ** level;
    const tileWorld = TILE / scale;
    const b = camera.viewBounds(2);
    const tx0 = Math.max(0, Math.floor(b.x0 / tileWorld));
    const ty0 = Math.max(0, Math.floor(b.y0 / tileWorld));
    const tx1 = Math.min(Math.ceil(this.map.width / tileWorld) - 1, Math.floor(b.x1 / tileWorld));
    const ty1 = Math.min(Math.ceil(this.map.height / tileWorld) - 1, Math.floor(b.y1 / tileWorld));
    const start = performance.now();
    const cxTile = camera.x / tileWorld;
    const cyTile = camera.y / tileWorld;
    const order: [number, number][] = [];
    for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) order.push([tx, ty]);
    order.sort((p, q) => Math.hypot(p[0] + 0.5 - cxTile, p[1] + 0.5 - cyTile) - Math.hypot(q[0] + 0.5 - cxTile, q[1] + 0.5 - cyTile));

    ctx.imageSmoothingEnabled = true;
    for (const [tx, ty] of order) {
      let tile = this.get(level, tx, ty);
      if (!tile && (layer === 'land' && performance.now() - start < FRAME_BUDGET_MS)) tile = this.build(level, tx, ty);
      const sx = camera.worldToScreenX(tx * tileWorld);
      const sy = camera.worldToScreenY(ty * tileWorld);
      const size = tileWorld * camera.zoom;
      if (tile) {
        const img = tile[layer];
        if (img) ctx.drawImage(img, Math.floor(sx), Math.floor(sy), Math.ceil(size + sx - Math.floor(sx)) + 0.5, Math.ceil(size + sy - Math.floor(sy)) + 0.5);
        continue;
      }
      this.drawFallback(ctx, camera, level, tx, ty, layer);
    }
  }

  /** Draws a coarser cached tile scaled up while the sharp one is pending. */
  private drawFallback(ctx: CanvasRenderingContext2D, camera: Camera, level: number, tx: number, ty: number, layer: 'land' | 'water'): void {
    for (let l = level - 1; l >= 0; l--) {
      const ratio = 2 ** (level - l);
      const ptx = Math.floor(tx / ratio);
      const pty = Math.floor(ty / ratio);
      const parent = l === 0 ? (this.get(0, ptx, pty) ?? this.build(0, ptx, pty)) : this.get(l, ptx, pty);
      if (!parent) continue;
      const img = parent[layer];
      if (!img) return;
      const sub = TILE / ratio;
      const srcX = (tx - ptx * ratio) * sub;
      const srcY = (ty - pty * ratio) * sub;
      const tileWorld = TILE / (BASE_SCALE * 2 ** level);
      const sx = camera.worldToScreenX(tx * tileWorld);
      const sy = camera.worldToScreenY(ty * tileWorld);
      const size = tileWorld * camera.zoom;
      ctx.drawImage(img, srcX, srcY, sub, sub, Math.floor(sx), Math.floor(sy), Math.ceil(size) + 1, Math.ceil(size) + 1);
      return;
    }
  }

  private get(level: number, tx: number, ty: number): Tile | undefined {
    const key = `${level}:${tx}:${ty}`;
    const t = this.tiles.get(key);
    if (t) {
      this.tiles.delete(key);
      this.tiles.set(key, t);
    }
    return t;
  }

  private build(level: number, tx: number, ty: number): Tile {
    const tile = this.renderTile(level, tx, ty);
    this.tiles.set(`${level}:${tx}:${ty}`, tile);
    while (this.tiles.size > MAX_TILES) {
      const oldest = this.tiles.keys().next().value as string;
      if (oldest.startsWith('0:')) {
        // Keep the overview level forever.
        const t = this.tiles.get(oldest)!;
        this.tiles.delete(oldest);
        this.tiles.set(oldest, t);
        if (this.tiles.size <= MAX_TILES + 12) break;
        continue;
      }
      this.tiles.delete(oldest);
    }
    return tile;
  }

  private renderTile(level: number, tx: number, ty: number): Tile {
    const { cols, rows, cellSize: cs } = this.map;
    const scale = BASE_SCALE * 2 ** level;
    const tileWorld = TILE / scale;
    const ox = tx * tileWorld;
    const oy = ty * tileWorld;
    const H = this.grids.heights;
    const vcols = this.vcols;
    const landImg = new ImageData(TILE, TILE);
    const waterImg = new ImageData(TILE, TILE);
    const L = landImg.data;
    const W = waterImg.data;
    let anyLand = false;
    let anyWater = false;
    const [sdR, sdG, sdB] = MAP_COLORS.seaDeep;
    const [ssR, ssG, ssB] = MAP_COLORS.seaShallow;
    const [ciR, ciG, ciB] = MAP_COLORS.coastInk;
    const contours = level >= 2;
    const grainScale = Math.max(1, 1.5 / scale);

    for (let py = 0; py < TILE; py++) {
      const wy = oy + (py + 0.5) / scale;
      let gy = wy / cs;
      if (gy < 0) gy = 0;
      if (gy > rows - 0.0001) gy = rows - 0.0001;
      const iy = Math.floor(gy);
      const fy = gy - iy;
      for (let px = 0; px < TILE; px++) {
        const o = (py * TILE + px) * 4;
        const wx = ox + (px + 0.5) / scale;
        if (wx > this.map.width || wy > this.map.height) continue;
        let gx = wx / cs;
        if (gx > cols - 0.0001) gx = cols - 0.0001;
        const ix = Math.floor(gx);
        const fx = gx - ix;
        const v = iy * vcols + ix;
        const w00 = (1 - fx) * (1 - fy);
        const w10 = fx * (1 - fy);
        const w01 = (1 - fx) * fy;
        const w11 = fx * fy;
        const grain = this.grain[((Math.floor(wy / grainScale) & 255) << 8) | (Math.floor(wx / grainScale) & 255)];
        const h = H[v] * w00 + H[v + 1] * w10 + H[v + vcols] * w01 + H[v + vcols + 1] * w11 + grain * 1.2;
        const slope = this.slope[v] * w00 + this.slope[v + 1] * w10 + this.slope[v + vcols] * w01 + this.slope[v + vcols + 1] * w11;
        // Height change per pixel, used to draw 1px wide lines at any zoom.
        const dhpx = Math.max(0.05, slope / scale);
        const coast = Math.abs(h - SEA_LEVEL_BYTE) < dhpx * 0.9;

        if (h >= SEA_LEVEL_BYTE) {
          anyLand = true;
          let r = this.colR[v] * w00 + this.colR[v + 1] * w10 + this.colR[v + vcols] * w01 + this.colR[v + vcols + 1] * w11;
          let g = this.colG[v] * w00 + this.colG[v + 1] * w10 + this.colG[v + vcols] * w01 + this.colG[v + vcols + 1] * w11;
          let b = this.colB[v] * w00 + this.colB[v + 1] * w10 + this.colB[v + vcols] * w01 + this.colB[v + vcols + 1] * w11;
          const k = 1 + grain * 0.07;
          r *= k;
          g *= k;
          b *= k;
          if (contours) {
            const band = (h - SEA_LEVEL_BYTE) / 13;
            const f = band - Math.floor(band);
            const wdt = (dhpx / 13) * 1.1;
            if (f < wdt && band > 1) {
              r *= 0.86;
              g *= 0.84;
              b *= 0.8;
            }
          }
          if (coast) {
            r = ciR;
            g = ciG;
            b = ciB;
          }
          L[o] = r;
          L[o + 1] = g;
          L[o + 2] = b;
          L[o + 3] = 255;
        } else {
          anyWater = true;
          const depth = Math.min(1, (SEA_LEVEL_BYTE - h) / 40);
          let r = ssR + (sdR - ssR) * depth;
          let g = ssG + (sdG - ssG) * depth;
          let b = ssB + (sdB - ssB) * depth;
          // Engraved shoreline ripples.
          const band = (SEA_LEVEL_BYTE - h) / 3.2;
          if (band < 4) {
            const f = band - Math.floor(band);
            if (f < (dhpx / 3.2) * 1.2) {
              r += 22;
              g += 22;
              b += 18;
            }
          }
          const k = 1 + grain * 0.05;
          r *= k;
          g *= k;
          b *= k;
          if (coast) {
            r = ciR;
            g = ciG;
            b = ciB;
          }
          W[o] = r;
          W[o + 1] = g;
          W[o + 2] = b;
          W[o + 3] = 255;
          // Underlay so territory fills never show holes along the coast.
          L[o] = r;
          L[o + 1] = g;
          L[o + 2] = b;
          L[o + 3] = 255;
        }
      }
    }

    let land: HTMLCanvasElement | null = null;
    let water: HTMLCanvasElement | null = null;
    if (anyLand || anyWater) {
      land = document.createElement('canvas');
      land.width = land.height = TILE;
      const lctx = land.getContext('2d')!;
      lctx.putImageData(landImg, 0, 0);
      if (anyLand) this.drawVectors(lctx, level, scale, ox, oy, tileWorld);
    }
    if (anyWater) {
      water = document.createElement('canvas');
      water.width = water.height = TILE;
      water.getContext('2d')!.putImageData(waterImg, 0, 0);
    }
    return { land, water };
  }

  /** Rivers, roads, bridges, forests and towns drawn on top of the shaded relief. */
  private drawVectors(ctx: CanvasRenderingContext2D, level: number, scale: number, ox: number, oy: number, tileWorld: number): void {
    const m = this.map;
    const inTile = (pts: number[], pad: number): boolean => {
      for (let i = 0; i < pts.length; i += 2) {
        if (pts[i] > ox - pad && pts[i] < ox + tileWorld + pad && pts[i + 1] > oy - pad && pts[i + 1] < oy + tileWorld + pad) return true;
      }
      return false;
    };
    const path = (pts: number[]): void => {
      ctx.beginPath();
      ctx.moveTo((pts[0] - ox) * scale, (pts[1] - oy) * scale);
      for (let i = 2; i < pts.length; i += 2) ctx.lineTo((pts[i] - ox) * scale, (pts[i + 1] - oy) * scale);
    };
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Forest tree symbols.
    if (level >= 3) {
      const { cols, rows, cellSize: cs } = m;
      const cx0 = Math.max(0, Math.floor(ox / cs));
      const cy0 = Math.max(0, Math.floor(oy / cs));
      const cx1 = Math.min(cols - 1, Math.floor((ox + tileWorld) / cs));
      const cy1 = Math.min(rows - 1, Math.floor((oy + tileWorld) / cs));
      const per = Math.min(10, Math.max(1, Math.round((cs * scale) / 14) ** 2));
      const r = Math.max(1.6, Math.min(4.2, 2.6 * scale));
      ctx.lineWidth = Math.max(0.6, r * 0.28);
      for (let cy = cy0; cy <= cy1; cy++) {
        for (let cx = cx0; cx <= cx1; cx++) {
          const c = cy * cols + cx;
          if (this.grids.terrain[c] !== Terrain.FOREST || this.grids.flags[c] & (CellFlag.ROAD | CellFlag.RIVER | CellFlag.TOWN)) continue;
          for (let k = 0; k < per; k++) {
            const wx = (cx + hash2(cx, cy, k * 3 + 1)) * cs;
            const wy = (cy + hash2(cx, cy, k * 3 + 2)) * cs;
            const x = (wx - ox) * scale;
            const y = (wy - oy) * scale;
            ctx.fillStyle = 'rgba(92,112,70,0.85)';
            ctx.strokeStyle = 'rgba(48,58,36,0.75)';
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
          }
        }
      }
    }

    // Hill hachures: little engraved ridges like on period maps.
    if (level >= 3) {
      const { cols, rows, cellSize: cs } = m;
      const cx0 = Math.max(0, Math.floor(ox / cs));
      const cy0 = Math.max(0, Math.floor(oy / cs));
      const cx1 = Math.min(cols - 1, Math.floor((ox + tileWorld) / cs));
      const cy1 = Math.min(rows - 1, Math.floor((oy + tileWorld) / cs));
      const w = Math.max(3, Math.min(9, 5 * scale));
      ctx.strokeStyle = 'rgba(96,74,46,0.55)';
      ctx.lineWidth = Math.max(0.8, scale * 0.6);
      for (let cy = cy0; cy <= cy1; cy++) {
        for (let cx = cx0; cx <= cx1; cx++) {
          const c = cy * cols + cx;
          if (this.grids.terrain[c] !== Terrain.HILLS || this.grids.flags[c] & (CellFlag.ROAD | CellFlag.TOWN)) continue;
          const n = level >= 4 ? 2 : 1;
          for (let k = 0; k < n; k++) {
            const x = ((cx + 0.2 + hash2(cx, cy, 40 + k) * 0.6) * cs - ox) * scale;
            const y = ((cy + 0.3 + hash2(cx, cy, 50 + k) * 0.5) * cs - oy) * scale;
            ctx.beginPath();
            ctx.moveTo(x - w, y + w * 0.35);
            ctx.quadraticCurveTo(x, y - w * 0.7, x + w, y + w * 0.35);
            ctx.stroke();
          }
        }
      }
    }

    // Rivers.
    for (const river of m.rivers) {
      if (!inTile(river.points, 80)) continue;
      const w = Math.max(1.1, river.width * scale * 0.7);
      path(river.points);
      ctx.strokeStyle = MAP_COLORS.riverEdge;
      ctx.lineWidth = w + Math.max(1, scale * 1.5);
      ctx.stroke();
      ctx.strokeStyle = MAP_COLORS.river;
      ctx.lineWidth = w;
      ctx.stroke();
    }

    // Roads.
    if (level >= 2) {
      for (const road of m.roads) {
        if (!road.major && level < 3) continue;
        if (!inTile(road.points, 40)) continue;
        path(road.points);
        if (road.major && level >= 4) {
          ctx.setLineDash([]);
          ctx.strokeStyle = MAP_COLORS.roadMajor;
          ctx.lineWidth = Math.max(2, 3.2 * scale);
          ctx.stroke();
          ctx.strokeStyle = 'rgba(236,222,186,0.95)';
          ctx.lineWidth = Math.max(1, 1.8 * scale);
          ctx.stroke();
        } else {
          ctx.strokeStyle = road.major ? MAP_COLORS.roadMajor : MAP_COLORS.road;
          ctx.lineWidth = road.major ? Math.max(1.2, 1.6 * scale) : Math.max(0.8, 1.1 * scale);
          ctx.setLineDash(road.major ? [] : [Math.max(2, 4 * scale), Math.max(2, 3 * scale)]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    }

    // Bridges.
    if (level >= 3) {
      for (const br of m.bridges) {
        if (br.x < ox - 20 || br.x > ox + tileWorld + 20 || br.y < oy - 20 || br.y > oy + tileWorld + 20) continue;
        ctx.save();
        ctx.translate((br.x - ox) * scale, (br.y - oy) * scale);
        ctx.rotate(br.angle);
        const len = 16 * scale;
        const wid = 7 * scale;
        ctx.fillStyle = '#d9c7a0';
        ctx.strokeStyle = '#3d3326';
        ctx.lineWidth = Math.max(1, scale);
        ctx.fillRect(-len / 2, -wid / 2, len, wid);
        ctx.strokeRect(-len / 2, -wid / 2, len, wid);
        ctx.restore();
      }
    }

    // Towns: clusters of buildings.
    if (level >= 2) {
      for (const city of m.cities) {
        const radius = city.type === 'CAPITAL' ? 40 : city.type === 'VILLAGE' ? 12 : 26;
        if (city.x < ox - radius || city.x > ox + tileWorld + radius || city.y < oy - radius || city.y > oy + tileWorld + radius) continue;
        const count = city.type === 'CAPITAL' ? 34 : city.type === 'VILLAGE' ? 5 : 16;
        for (let k = 0; k < count; k++) {
          const a = hash2(city.id, k, 5) * Math.PI * 2;
          const d = Math.sqrt(hash2(city.id, k, 6)) * radius;
          const bx = city.x + Math.cos(a) * d;
          const by = city.y + Math.sin(a) * d;
          const bw = (3 + hash2(city.id, k, 7) * 4) * scale;
          const bh = (3 + hash2(city.id, k, 8) * 3) * scale;
          ctx.fillStyle = hash2(city.id, k, 9) < 0.6 ? '#9a5b45' : '#6f6658';
          ctx.fillRect((bx - ox) * scale - bw / 2, (by - oy) * scale - bh / 2, Math.max(1, bw), Math.max(1, bh));
        }
      }
    }
  }
}
