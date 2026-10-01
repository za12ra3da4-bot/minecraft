import { clamp } from '@warfront/shared';

export type ZoomLevel = 1 | 2 | 3 | 4 | 5;

/** Zoom thresholds relative to the "whole map fits" zoom. */
const LEVELS = [1.7, 3.2, 6, 11];

/** 2D camera: world units -> CSS pixels, with smooth zoom and inertia. */
export class Camera {
  x = 0;
  y = 0;
  zoom = 1;
  viewW = 1;
  viewH = 1;
  private targetZoom = 1;
  private zoomAnchor: { sx: number; sy: number } | null = null;
  private velX = 0;
  private velY = 0;
  private flyTo: { x: number; y: number; zoom: number; t: number; fromX: number; fromY: number; fromZoom: number } | null = null;

  constructor(
    readonly mapW: number,
    readonly mapH: number,
  ) {
    this.x = mapW / 2;
    this.y = mapH / 2;
  }

  get fitZoom(): number {
    return Math.min(this.viewW / this.mapW, this.viewH / this.mapH);
  }

  get minZoom(): number {
    return this.fitZoom * 0.85;
  }

  get maxZoom(): number {
    return Math.max(this.fitZoom * 22, 5);
  }

  /** 1 = whole theatre ... 5 = detailed battlefield. */
  get level(): ZoomLevel {
    const r = this.zoom / this.fitZoom;
    for (let i = 0; i < LEVELS.length; i++) if (r < LEVELS[i]) return (i + 1) as ZoomLevel;
    return 5;
  }

  /** Relative zoom (1 at full map view), handy for scaling labels. */
  get relZoom(): number {
    return this.zoom / this.fitZoom;
  }

  resize(w: number, h: number): void {
    const first = this.viewW <= 1;
    this.viewW = w;
    this.viewH = h;
    if (first) {
      this.zoom = this.targetZoom = this.fitZoom * 1.05;
    }
    this.clampAll();
  }

  worldToScreenX(wx: number): number {
    return (wx - this.x) * this.zoom + this.viewW / 2;
  }

  worldToScreenY(wy: number): number {
    return (wy - this.y) * this.zoom + this.viewH / 2;
  }

  screenToWorld(sx: number, sy: number): [number, number] {
    return [(sx - this.viewW / 2) / this.zoom + this.x, (sy - this.viewH / 2) / this.zoom + this.y];
  }

  /** Visible world rectangle with a margin in screen pixels. */
  viewBounds(marginPx = 0): { x0: number; y0: number; x1: number; y1: number } {
    const [x0, y0] = this.screenToWorld(-marginPx, -marginPx);
    const [x1, y1] = this.screenToWorld(this.viewW + marginPx, this.viewH + marginPx);
    return { x0, y0, x1, y1 };
  }

  pan(dxScreen: number, dyScreen: number): void {
    this.flyTo = null;
    this.x -= dxScreen / this.zoom;
    this.y -= dyScreen / this.zoom;
    this.clampAll();
  }

  /** Release velocity (screen px per second) for inertial panning. */
  fling(vx: number, vy: number): void {
    this.velX = vx;
    this.velY = vy;
  }

  stopInertia(): void {
    this.velX = 0;
    this.velY = 0;
  }

  /** Smooth zoom around a screen point. */
  zoomAt(sx: number, sy: number, factor: number): void {
    this.flyTo = null;
    this.targetZoom = clamp(this.targetZoom * factor, this.minZoom, this.maxZoom);
    this.zoomAnchor = { sx, sy };
  }

  /** Immediate zoom (pinch). */
  zoomNow(sx: number, sy: number, factor: number): void {
    this.flyTo = null;
    const [wx, wy] = this.screenToWorld(sx, sy);
    this.zoom = this.targetZoom = clamp(this.zoom * factor, this.minZoom, this.maxZoom);
    this.x = wx - (sx - this.viewW / 2) / this.zoom;
    this.y = wy - (sy - this.viewH / 2) / this.zoom;
    this.clampAll();
  }

  /** Jumps to a view immediately. */
  setView(x: number, y: number, zoom: number): void {
    this.flyTo = null;
    this.x = x;
    this.y = y;
    this.zoom = this.targetZoom = clamp(zoom, this.minZoom, this.maxZoom);
    this.clampAll();
  }

  /** Animated move to a world position (minimap, event clicks). */
  animateTo(x: number, y: number, zoom?: number): void {
    this.flyTo = { x, y, zoom: clamp(zoom ?? this.zoom, this.minZoom, this.maxZoom), t: 0, fromX: this.x, fromY: this.y, fromZoom: this.zoom };
    this.zoomAnchor = null;
  }

  update(dt: number): void {
    if (this.flyTo) {
      const f = this.flyTo;
      f.t = Math.min(1, f.t + dt / 0.6);
      const e = 1 - Math.pow(1 - f.t, 3);
      this.x = f.fromX + (f.x - f.fromX) * e;
      this.y = f.fromY + (f.y - f.fromY) * e;
      this.zoom = this.targetZoom = f.fromZoom * Math.pow(f.zoom / f.fromZoom, e);
      if (f.t >= 1) this.flyTo = null;
      this.clampAll();
      return;
    }
    if (Math.abs(this.targetZoom - this.zoom) > this.zoom * 0.001 && this.zoomAnchor) {
      const { sx, sy } = this.zoomAnchor;
      const [wx, wy] = this.screenToWorld(sx, sy);
      const k = 1 - Math.exp(-dt * 14);
      this.zoom = Math.exp(Math.log(this.zoom) + (Math.log(this.targetZoom) - Math.log(this.zoom)) * k);
      this.x = wx - (sx - this.viewW / 2) / this.zoom;
      this.y = wy - (sy - this.viewH / 2) / this.zoom;
    } else {
      this.zoom = this.targetZoom;
    }
    if (this.velX || this.velY) {
      this.x -= (this.velX * dt) / this.zoom;
      this.y -= (this.velY * dt) / this.zoom;
      const decay = Math.exp(-dt * 5);
      this.velX *= decay;
      this.velY *= decay;
      if (Math.hypot(this.velX, this.velY) < 8) this.velX = this.velY = 0;
    }
    this.clampAll();
  }

  private clampAll(): void {
    this.zoom = clamp(this.zoom, this.minZoom, this.maxZoom);
    const halfW = this.viewW / 2 / this.zoom;
    const halfH = this.viewH / 2 / this.zoom;
    const slack = 0.15;
    this.x = halfW * 2 >= this.mapW ? this.mapW / 2 : clamp(this.x, halfW - this.mapW * slack, this.mapW - halfW + this.mapW * slack);
    this.y = halfH * 2 >= this.mapH ? this.mapH / 2 : clamp(this.y, halfH - this.mapH * slack, this.mapH - halfH + this.mapH * slack);
  }
}
