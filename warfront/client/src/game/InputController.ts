import type { Camera } from './Camera';

export interface TapInfo {
  button: number;
  shift: boolean;
  /** Touch long-press. */
  long: boolean;
  touch: boolean;
}

export interface InputHandlers {
  tap(sx: number, sy: number, info: TapInfo): void;
  box(x0: number, y0: number, x1: number, y1: number): void;
  hover(sx: number, sy: number): void;
}

interface PointerState {
  x: number;
  y: number;
  startX: number;
  startY: number;
  startTime: number;
  button: number;
  touch: boolean;
}

const DRAG_THRESHOLD = 6;
const LONG_PRESS_MS = 520;

/**
 * Unified mouse / touch / pen input: drag to pan, wheel and pinch to zoom,
 * tap and long-press, shift-drag box selection.
 */
export class InputController {
  private pointers = new Map<number, PointerState>();
  private dragging = false;
  private boxing = false;
  private pinchDist = 0;
  private pinchMid: [number, number] = [0, 0];
  private longTimer: number | null = null;
  private longFired = false;
  private samples: { x: number; y: number; t: number }[] = [];
  box: { x0: number; y0: number; x1: number; y1: number } | null = null;

  constructor(
    private el: HTMLElement,
    private camera: Camera,
    private handlers: InputHandlers,
  ) {
    el.addEventListener('pointerdown', this.onDown);
    el.addEventListener('pointermove', this.onMove);
    el.addEventListener('pointerup', this.onUp);
    el.addEventListener('pointercancel', this.onCancel);
    el.addEventListener('wheel', this.onWheel, { passive: false });
    el.addEventListener('contextmenu', this.onContext);
  }

  destroy(): void {
    this.el.removeEventListener('pointerdown', this.onDown);
    this.el.removeEventListener('pointermove', this.onMove);
    this.el.removeEventListener('pointerup', this.onUp);
    this.el.removeEventListener('pointercancel', this.onCancel);
    this.el.removeEventListener('wheel', this.onWheel);
    this.el.removeEventListener('contextmenu', this.onContext);
  }

  private local(e: PointerEvent | WheelEvent): [number, number] {
    const r = this.el.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }

  private onContext = (e: Event): void => e.preventDefault();

  private onDown = (e: PointerEvent): void => {
    this.el.setPointerCapture(e.pointerId);
    const [x, y] = this.local(e);
    const touch = e.pointerType === 'touch';
    this.pointers.set(e.pointerId, { x, y, startX: x, startY: y, startTime: performance.now(), button: e.button, touch });
    this.camera.stopInertia();
    this.samples = [{ x, y, t: performance.now() }];
    this.longFired = false;
    if (this.pointers.size === 2) {
      this.clearLong();
      this.dragging = false;
      const [a, b] = [...this.pointers.values()];
      this.pinchDist = Math.hypot(a.x - b.x, a.y - b.y);
      this.pinchMid = [(a.x + b.x) / 2, (a.y + b.y) / 2];
      return;
    }
    if (e.shiftKey && e.button === 0 && !touch) {
      this.boxing = true;
      this.box = { x0: x, y0: y, x1: x, y1: y };
      return;
    }
    if (touch) {
      this.clearLong();
      this.longTimer = window.setTimeout(() => {
        const p = this.pointers.get(e.pointerId);
        if (!p || this.dragging || this.pointers.size !== 1) return;
        this.longFired = true;
        this.handlers.tap(p.x, p.y, { button: 0, shift: false, long: true, touch: true });
      }, LONG_PRESS_MS);
    }
  };

  private onMove = (e: PointerEvent): void => {
    const [x, y] = this.local(e);
    const p = this.pointers.get(e.pointerId);
    if (!p) {
      if (e.pointerType === 'mouse') this.handlers.hover(x, y);
      return;
    }
    const dx = x - p.x;
    const dy = y - p.y;
    p.x = x;
    p.y = y;

    if (this.pointers.size >= 2) {
      const [a, b] = [...this.pointers.values()];
      const dist = Math.hypot(a.x - b.x, a.y - b.y);
      const mid: [number, number] = [(a.x + b.x) / 2, (a.y + b.y) / 2];
      if (this.pinchDist > 0) this.camera.zoomNow(mid[0], mid[1], dist / this.pinchDist);
      this.camera.pan(mid[0] - this.pinchMid[0], mid[1] - this.pinchMid[1]);
      this.pinchDist = dist;
      this.pinchMid = mid;
      return;
    }
    if (this.boxing && this.box) {
      this.box.x1 = x;
      this.box.y1 = y;
      return;
    }
    if (!this.dragging && Math.hypot(x - p.startX, y - p.startY) > DRAG_THRESHOLD) {
      this.dragging = true;
      this.clearLong();
    }
    if (this.dragging) {
      this.camera.pan(dx, dy);
      const now = performance.now();
      this.samples.push({ x, y, t: now });
      while (this.samples.length > 2 && now - this.samples[0].t > 100) this.samples.shift();
    }
  };

  private onUp = (e: PointerEvent): void => {
    const p = this.pointers.get(e.pointerId);
    this.pointers.delete(e.pointerId);
    this.clearLong();
    if (!p) return;
    if (this.pointers.size > 0) {
      // Finished a pinch: wait for all fingers to lift.
      this.dragging = true;
      return;
    }
    if (this.boxing && this.box) {
      const b = this.box;
      this.box = null;
      this.boxing = false;
      if (Math.abs(b.x1 - b.x0) > 4 || Math.abs(b.y1 - b.y0) > 4) {
        this.handlers.box(Math.min(b.x0, b.x1), Math.min(b.y0, b.y1), Math.max(b.x0, b.x1), Math.max(b.y0, b.y1));
      } else {
        this.handlers.tap(p.x, p.y, { button: 0, shift: true, long: false, touch: false });
      }
      return;
    }
    if (this.dragging) {
      this.dragging = false;
      const first = this.samples[0];
      const last = this.samples[this.samples.length - 1];
      const dt = (last.t - first.t) / 1000;
      if (dt > 0.01 && performance.now() - last.t < 60) this.camera.fling((last.x - first.x) / dt, (last.y - first.y) / dt);
      return;
    }
    if (this.longFired) return;
    this.handlers.tap(p.x, p.y, { button: p.button, shift: e.shiftKey, long: false, touch: p.touch });
  };

  private onCancel = (e: PointerEvent): void => {
    this.pointers.delete(e.pointerId);
    this.clearLong();
    this.dragging = false;
    this.boxing = false;
    this.box = null;
  };

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault();
    const [x, y] = this.local(e);
    const delta = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
    this.camera.zoomAt(x, y, Math.exp(-delta * 0.0016));
  };

  private clearLong(): void {
    if (this.longTimer !== null) {
      clearTimeout(this.longTimer);
      this.longTimer = null;
    }
  }
}
