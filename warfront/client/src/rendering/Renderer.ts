import type { GameSpeed, UnitNet } from '@warfront/shared';
import { Camera } from '../game/Camera';
import type { GameClient } from '../game/GameClient';
import { InputController, type TapInfo } from '../game/InputController';
import type { MapItem } from '../game/clustering';
import { settings } from '../data/settings';
import { EffectsLayer } from './EffectsLayer';
import { LabelLayer } from './LabelLayer';
import { TerrainLayer } from './TerrainLayer';
import { TerritoryLayer } from './TerritoryLayer';
import { UnitLayer } from './UnitLayer';

const KEY_PAN_SPEED = 900;

/**
 * Owns the canvas and the requestAnimationFrame loop. Rendering is fully
 * separated from the network: it only reads the GameClient store.
 */
export class Renderer {
  readonly camera: Camera;
  private ctx: CanvasRenderingContext2D;
  private terrain: TerrainLayer;
  private territories: TerritoryLayer;
  private units: UnitLayer;
  private effects: EffectsLayer;
  private labels: LabelLayer;
  private input: InputController;
  private raf = 0;
  private last = performance.now();
  private dpr = 1;
  private keys = new Set<string>();
  private resizeObserver: ResizeObserver;
  private lastSelection: unknown = null;
  /** Called every frame so the minimap can draw the camera rectangle. */
  onFrame: (() => void) | null = null;

  constructor(
    private canvas: HTMLCanvasElement,
    private game: GameClient,
  ) {
    this.ctx = canvas.getContext('2d', { alpha: false })!;
    const map = game.replica.map;
    this.camera = new Camera(map.width, map.height);
    this.terrain = new TerrainLayer(map, game.grids);
    this.territories = new TerritoryLayer(game);
    this.units = new UnitLayer(game);
    this.effects = new EffectsLayer(game, this.territories);
    this.labels = new LabelLayer(game);
    this.input = new InputController(canvas, this.camera, {
      tap: (x, y, info) => this.onTap(x, y, info),
      box: (x0, y0, x1, y1, add) => this.onBox(x0, y0, x1, y1, add),
      hover: (x, y) => this.onHover(x, y),
      touchBoxMode: () => game.boxMode,
    });
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas);
    this.resize();
    this.focusHome();
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    window.addEventListener('blur', this.onBlur);
    this.raf = requestAnimationFrame(this.frame);
  }

  destroy(): void {
    cancelAnimationFrame(this.raf);
    this.input.destroy();
    this.resizeObserver.disconnect();
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    window.removeEventListener('blur', this.onBlur);
  }

  /** Opens on the player's capital at regional zoom. */
  private focusHome(): void {
    const r = this.game.replica;
    const you = r.you;
    const cap = you ? r.nations.get(you)?.capitalCity : null;
    if (cap !== null && cap !== undefined) {
      const c = r.map.cities[cap];
      this.camera.setView(c.x, c.y, this.camera.fitZoom * 2.2);
    }
  }

  private resize(): void {
    const rect = this.canvas.getBoundingClientRect();
    this.dpr = Math.min(2, window.devicePixelRatio || 1);
    this.canvas.width = Math.max(1, Math.round(rect.width * this.dpr));
    this.canvas.height = Math.max(1, Math.round(rect.height * this.dpr));
    this.camera.resize(rect.width, rect.height);
  }

  private frame = (now: number): void => {
    this.raf = requestAnimationFrame(this.frame);
    const dt = Math.min(0.1, (now - this.last) / 1000);
    this.last = now;
    const game = this.game;
    const camera = this.camera;

    if (game.focusRequest) {
      const f = game.focusRequest;
      game.focusRequest = null;
      camera.animateTo(f.x, f.y, f.zoom);
    }
    this.keyPan(dt);
    camera.update(dt);
    game.frame(now, dt);
    if (this.lastSelection !== game.selection) {
      this.lastSelection = game.selection;
      this.units.invalidate();
    }

    const ctx = this.ctx;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.fillStyle = '#7f9ea6';
    ctx.fillRect(0, 0, camera.viewW, camera.viewH);

    this.terrain.draw(ctx, camera, this.dpr, 'land');
    this.territories.drawFills(ctx, camera, now);
    this.territories.drawBorders(ctx, camera, now);
    this.terrain.draw(ctx, camera, this.dpr, 'water');
    this.labels.drawNationNames(ctx, camera);
    this.effects.drawUnder(ctx, camera, now);
    this.labels.drawCities(ctx, camera);
    this.units.drawPaths(ctx, camera, now);
    this.units.draw(ctx, camera, now);
    this.effects.update(dt);
    this.effects.drawOver(ctx, camera);
    this.drawBox(ctx);
    this.drawVignette(ctx);
    this.onFrame?.();
  };

  private drawBox(ctx: CanvasRenderingContext2D): void {
    const b = this.input.visibleBox;
    if (!b) return;
    ctx.fillStyle = 'rgba(255,214,110,0.12)';
    ctx.strokeStyle = 'rgba(255,214,110,0.9)';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 4]);
    const x = Math.min(b.x0, b.x1);
    const y = Math.min(b.y0, b.y1);
    ctx.fillRect(x, y, Math.abs(b.x1 - b.x0), Math.abs(b.y1 - b.y0));
    ctx.strokeRect(x, y, Math.abs(b.x1 - b.x0), Math.abs(b.y1 - b.y0));
    ctx.setLineDash([]);
  }

  private vignette: CanvasGradient | null = null;
  private vignetteSize = '';

  private drawVignette(ctx: CanvasRenderingContext2D): void {
    const { viewW: w, viewH: h } = this.camera;
    const key = `${w}x${h}`;
    if (!this.vignette || this.vignetteSize !== key) {
      const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.45, w / 2, h / 2, Math.max(w, h) * 0.78);
      g.addColorStop(0, 'rgba(10,8,6,0)');
      g.addColorStop(1, 'rgba(10,8,6,0.42)');
      this.vignette = g;
      this.vignetteSize = key;
    }
    ctx.fillStyle = this.vignette;
    ctx.fillRect(0, 0, w, h);
  }

  // ------------------------------------------------------------------ input

  private largest(item: MapItem): UnitNet {
    return item.members.reduce((a, b) => (b.unit.soldiers > a.unit.soldiers ? b : a)).unit;
  }

  private selectedOwn(): number[] {
    const sel = this.game.selection;
    return sel.kind === 'units' ? sel.ids : [];
  }

  private onTap(sx: number, sy: number, info: TapInfo): void {
    const game = this.game;
    const camera = this.camera;
    const you = game.you;
    const [wx, wy] = camera.screenToWorld(sx, sy);
    const item = this.units.hitTest(sx, sy, info.touch ? 10 : 4);
    const own = this.selectedOwn();

    if (info.long) {
      if (item) game.select(item.nation === you ? { kind: 'units', ids: item.members.map((m) => m.unit.id) } : { kind: 'enemy', id: this.largest(item).id });
      else this.selectGround(sx, sy, wx, wy);
      return;
    }

    if (info.button === 2) {
      if (own.length) this.order(own, item, wx, wy);
      return;
    }

    if (item) {
      if (item.nation === you) {
        const ids = item.members.map((m) => m.unit.id);
        if (info.shift) {
          const set = new Set(own);
          const allIn = ids.every((id) => set.has(id));
          for (const id of ids) {
            if (allIn) set.delete(id);
            else set.add(id);
          }
          game.select(set.size ? { kind: 'units', ids: [...set] } : { kind: 'none' });
        } else if (own.length === ids.length && ids.every((id) => own.includes(id))) {
          game.select({ kind: 'none' });
        } else {
          game.select({ kind: 'units', ids });
        }
        return;
      }
      const target = this.largest(item);
      if (own.length && you && game.replica.diplomacy.relations && this.atWar(you, item.nation)) {
        this.order(own, item, wx, wy);
        return;
      }
      game.select({ kind: 'enemy', id: target.id });
      return;
    }

    if (own.length) {
      this.order(own, null, wx, wy);
      return;
    }
    this.selectGround(sx, sy, wx, wy);
  }

  private atWar(a: string, b: string): boolean {
    const key = a < b ? `${a}|${b}` : `${b}|${a}`;
    return this.game.replica.diplomacy.relations[key] === 'WAR';
  }

  private selectGround(sx: number, sy: number, wx: number, wy: number): void {
    const city = this.labels.cityAt(this.camera, sx, sy);
    const t = city ? city.territoryId : this.territories.territoryAt(wx, wy);
    this.game.select(t >= 0 ? { kind: 'territory', id: t } : { kind: 'none' });
  }

  /** Right-click / tap with a selection: move, attack or join. */
  private order(ids: number[], item: MapItem | null, wx: number, wy: number): void {
    const game = this.game;
    const you = game.you;
    if (item && item.nation === you) {
      const target = this.largest(item);
      const movers = ids.filter((id) => id !== target.id);
      if (movers.length) void game.command({ type: 'JOIN_UNIT', unitIds: movers, targetUnitId: target.id });
      return;
    }
    if (item && you && this.atWar(you, item.nation)) {
      void game.command({ type: 'ATTACK', unitIds: ids, targetUnitId: this.largest(item).id });
      game.effects.push({ kind: 'order', x: wx, y: wy });
      return;
    }
    void game.command({ type: 'MOVE_UNIT', unitIds: ids, x: wx, y: wy });
    game.effects.push({ kind: 'order', x: wx, y: wy });
  }

  private onBox(x0: number, y0: number, x1: number, y1: number, add: boolean): void {
    const you = this.game.you;
    const ids = new Set(add ? this.selectedOwn() : []);
    for (const item of this.units.itemsIn(x0, y0, x1, y1)) {
      if (item.nation === you) for (const m of item.members) ids.add(m.unit.id);
    }
    if (ids.size) this.game.select({ kind: 'units', ids: [...ids] });
    else if (!add) this.game.select({ kind: 'none' });
  }

  /** Selects every army of the player (UI button / Ctrl+A). */
  selectAll(): void {
    const ids = [...this.game.replica.units.values()].filter((u) => u.nation === this.game.you).map((u) => u.id);
    this.game.select(ids.length ? { kind: 'units', ids } : { kind: 'none' });
    if (!ids.length) this.game.toast('남은 부대가 없습니다', 'info');
  }

  /** Centres on the capital and opens its panel (raise armies there). */
  openCapital(): void {
    const r = this.game.replica;
    const cap = r.you ? r.nations.get(r.you)?.capitalCity : null;
    if (cap === null || cap === undefined) return;
    const city = r.map.cities[cap];
    this.camera.animateTo(city.x, city.y, Math.max(this.camera.zoom, this.camera.fitZoom * 3));
    this.game.select({ kind: 'territory', id: city.territoryId });
  }

  private onHover(sx: number, sy: number): void {
    const item = this.units.hitTest(sx, sy);
    const own = this.selectedOwn().length > 0;
    this.canvas.style.cursor = item ? 'pointer' : own ? 'crosshair' : 'default';
  }

  // ------------------------------------------------------------------ keyboard

  private onKeyDown = (e: KeyboardEvent): void => {
    const target = e.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) return;
    const game = this.game;
    const key = e.key.toLowerCase();
    this.keys.add(key);
    const own = this.selectedOwn();
    if (key === 'escape') {
      game.select({ kind: 'none' });
    } else if (key === ' ' && game.isHost) {
      e.preventDefault();
      void game.command({ type: 'SET_PAUSED', paused: !game.replica.paused });
    } else if (['1', '2', '3', '4'].includes(key) && game.isHost) {
      const speeds: GameSpeed[] = [0.5, 1, 2, 4];
      void game.command({ type: 'SET_SPEED', speed: speeds[Number(key) - 1] });
    } else if (key === 'h' && own.length) {
      void game.command({ type: 'HALT', unitIds: own });
    } else if (key === 'm' && own.length > 1) {
      void game.command({ type: 'MERGE_UNIT', unitIds: own });
    } else if (key === 'f') {
      this.focusSelection();
    } else if (key === 'a' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      this.selectAll();
    } else if (key === '+' || key === '=') {
      this.camera.zoomAt(this.camera.viewW / 2, this.camera.viewH / 2, 1.4);
    } else if (key === '-' || key === '_') {
      this.camera.zoomAt(this.camera.viewW / 2, this.camera.viewH / 2, 1 / 1.4);
    }
  };

  private onKeyUp = (e: KeyboardEvent): void => {
    this.keys.delete(e.key.toLowerCase());
  };

  private onBlur = (): void => this.keys.clear();

  private keyPan(dt: number): void {
    if (!this.keys.size) return;
    const speed = KEY_PAN_SPEED * settings.value.panSpeed * dt;
    let dx = 0;
    let dy = 0;
    if (this.keys.has('arrowleft') || this.keys.has('a')) dx += speed;
    if (this.keys.has('arrowright') || this.keys.has('d')) dx -= speed;
    if (this.keys.has('arrowup') || this.keys.has('w')) dy += speed;
    if (this.keys.has('arrowdown') || this.keys.has('s')) dy -= speed;
    if (dx || dy) this.camera.pan(dx, dy);
  }

  focusSelection(): void {
    const game = this.game;
    const sel = game.selection;
    let x = 0;
    let y = 0;
    let n = 0;
    const ids = sel.kind === 'units' ? sel.ids : sel.kind === 'enemy' ? [sel.id] : [];
    for (const id of ids) {
      const r = game.render.get(id);
      if (r) {
        x += r.x;
        y += r.y;
        n++;
      }
    }
    if (n) this.camera.animateTo(x / n, y / n, Math.max(this.camera.zoom, this.camera.fitZoom * 5));
    else if (sel.kind === 'territory') {
      const t = game.replica.map.territories[sel.id];
      this.camera.animateTo(t.cx, t.cy, Math.max(this.camera.zoom, this.camera.fitZoom * 4));
    }
  }
}
