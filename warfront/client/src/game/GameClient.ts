import {
  BROADCAST_EVERY_TICKS,
  ReplicaState,
  SERVER_TICK_MS,
  decodeRLE,
  base64ToBytes,
  type Ack,
  type ChatMessage,
  type GameCommand,
  type GameDelta,
  type GameEvent,
  type GameInit,
  type GameOverInfo,
  type MapGrids,
  type NationId,
  type PrivateState,
  type UnitNet,
} from '@warfront/shared';
import { sendCommand } from '../network/connection';
import { Store } from './store';

const INTERP_MS = SERVER_TICK_MS * BROADCAST_EVERY_TICKS * 1.15;
const LOSS_FLUSH_MS = 650;

/** Per-unit render state layered on top of the replicated unit. */
export interface RenderUnit {
  id: number;
  x: number;
  y: number;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  t0: number;
  /** Direction of travel (radians) for arrows. */
  heading: number;
  /** Animated troop count (counts down smoothly during battle). */
  shown: number;
  pendingLoss: number;
  lossAt: number;
}

export type EffectEvent =
  | { kind: 'loss'; x: number; y: number; amount: number; nation: NationId }
  | { kind: 'capture'; territoryId: number; nation: NationId | null }
  | { kind: 'destroyed'; x: number; y: number; nation: NationId }
  | { kind: 'order'; x: number; y: number };

export interface Toast {
  id: number;
  text: string;
  kind: 'major' | 'error' | 'info';
  until: number;
}

export type Selection =
  | { kind: 'none' }
  | { kind: 'units'; ids: number[] }
  | { kind: 'enemy'; id: number }
  | { kind: 'territory'; id: number };

/**
 * Client-side game state: the replicated world plus everything that only
 * matters for presentation (interpolation, selection, effects, logs).
 */
export class GameClient extends Store {
  readonly replica = new ReplicaState();
  readonly grids: MapGrids;
  readonly render = new Map<number, RenderUnit>();
  privateState: PrivateState | null = null;
  events: GameEvent[] = [];
  chat: ChatMessage[] = [];
  toasts: Toast[] = [];
  over: GameOverInfo | null = null;
  selection: Selection = { kind: 'none' };
  /** Touch range-select mode (one-finger drag selects instead of panning). */
  boxMode = false;
  /** Queue drained by the renderer. */
  effects: EffectEvent[] = [];
  /** Camera requests (e.g. minimap clicks, event clicks) consumed by the renderer. */
  focusRequest: { x: number; y: number; zoom?: number } | null = null;
  isHost = false;
  private nextToastId = 1;
  private lastUiNotify = 0;
  private uiTimer: number | null = null;

  constructor(init: GameInit) {
    super();
    this.replica.applyInit(init);
    const m = init.map;
    this.grids = {
      heights: base64ToBytes(m.heights),
      terrain: decodeRLE(m.terrain, new Uint8Array(m.cols * m.rows)),
      flags: decodeRLE(m.flags, new Uint8Array(m.cols * m.rows)),
      territoryGrid: decodeRLE(m.territoryGrid, new Int16Array(m.cols * m.rows)),
    };
    const now = performance.now();
    for (const u of this.replica.units.values()) this.render.set(u.id, this.newRender(u, now));
    this.events = init.events.slice();
  }


  get you(): NationId | null {
    return this.replica.you;
  }

  reinit(init: GameInit): void {
    this.replica.applyInit(init);
    const now = performance.now();
    this.render.clear();
    for (const u of this.replica.units.values()) this.render.set(u.id, this.newRender(u, now));
    this.pruneSelection();
    this.notify();
  }

  private newRender(u: UnitNet, now: number): RenderUnit {
    return { id: u.id, x: u.x, y: u.y, fromX: u.x, fromY: u.y, toX: u.x, toY: u.y, t0: now, heading: 0, shown: u.soldiers, pendingLoss: 0, lossAt: now };
  }

  applyDelta(d: GameDelta): void {
    const now = performance.now();
    const changes = this.replica.applyDelta(d);
    for (const u of changes.added) this.render.set(u.id, this.newRender(u, now));
    for (const u of changes.removed) {
      this.render.delete(u.id);
      // Units removed while fighting were destroyed (merges happen out of battle).
      if (u.battleId !== null) this.effects.push({ kind: 'destroyed', x: u.x, y: u.y, nation: u.nation });
    }
    for (const id of changes.moved.keys()) {
      const r = this.render.get(id);
      const u = this.replica.units.get(id);
      if (!r || !u) continue;
      this.sampleRender(r, now);
      r.fromX = r.x;
      r.fromY = r.y;
      r.toX = u.x;
      r.toY = u.y;
      r.t0 = now;
      const dx = r.toX - r.fromX;
      const dy = r.toY - r.fromY;
      if (dx * dx + dy * dy > 0.04) r.heading = Math.atan2(dy, dx);
    }
    for (const [id, loss] of changes.losses) {
      const r = this.render.get(id);
      if (r) r.pendingLoss += loss;
    }
    for (const [territoryId] of changes.owners) {
      this.effects.push({ kind: 'capture', territoryId, nation: this.replica.owners[territoryId] });
    }
    if (changes.removed.length) this.pruneSelection();
    this.notifyUi();
  }

  /** Updates interpolated positions and animated numbers; called every frame. */
  frame(now: number, dt: number): void {
    const k = Math.min(1, dt * 7);
    for (const r of this.render.values()) {
      this.sampleRender(r, now);
      const u = this.replica.units.get(r.id);
      if (!u) continue;
      r.shown += (u.soldiers - r.shown) * k;
      if (Math.abs(u.soldiers - r.shown) < 1) r.shown = u.soldiers;
      if (r.pendingLoss >= 1 && now - r.lossAt > LOSS_FLUSH_MS) {
        this.effects.push({ kind: 'loss', x: r.x, y: r.y, amount: Math.round(r.pendingLoss), nation: u.nation });
        r.pendingLoss = 0;
        r.lossAt = now;
      }
    }
  }

  private sampleRender(r: RenderUnit, now: number): void {
    const t = Math.min(1, (now - r.t0) / INTERP_MS);
    r.x = r.fromX + (r.toX - r.fromX) * t;
    r.y = r.fromY + (r.toY - r.fromY) * t;
  }

  setPrivate(p: PrivateState): void {
    this.privateState = p;
    this.notifyUi();
  }

  addEvents(incoming: GameEvent[]): void {
    // The init packet may already contain the first events of the tick.
    const lastId = this.events.length ? this.events[this.events.length - 1].id : 0;
    const events = incoming.filter((e) => e.id > lastId);
    if (!events.length) return;
    this.events.push(...events);
    if (this.events.length > 150) this.events.splice(0, this.events.length - 150);
    const you = this.you;
    for (const e of events) {
      const mine = you !== null && e.nations.includes(you);
      if (e.major || (mine && (e.kind === 'WAR_DECLARED' || e.kind === 'OFFER' || e.kind === 'CAPITAL_ATTACKED'))) this.toast(e.text, 'major');
    }
    this.notifyUi();
  }

  addChat(msg: ChatMessage): void {
    this.chat.push(msg);
    if (this.chat.length > 100) this.chat.shift();
    this.notify();
  }

  setChatHistory(msgs: ChatMessage[]): void {
    this.chat = msgs.slice();
    this.notify();
  }

  setOver(info: GameOverInfo): void {
    this.over = info;
    this.notify();
  }

  toast(text: string, kind: Toast['kind'] = 'info'): void {
    const now = Date.now();
    this.toasts = [...this.toasts.filter((t) => t.until > now).slice(-3), { id: this.nextToastId++, text, kind, until: now + (kind === 'major' ? 4500 : 3000) }];
    this.notify();
  }

  // ------------------------------------------------------------- selection

  select(sel: Selection): void {
    this.selection = sel;
    this.notify();
  }

  selectedUnits(): UnitNet[] {
    if (this.selection.kind !== 'units') return [];
    const out: UnitNet[] = [];
    for (const id of this.selection.ids) {
      const u = this.replica.units.get(id);
      if (u) out.push(u);
    }
    return out;
  }

  private pruneSelection(): void {
    const sel = this.selection;
    if (sel.kind === 'units') {
      const ids = sel.ids.filter((id) => this.replica.units.has(id));
      if (ids.length !== sel.ids.length) this.selection = ids.length ? { kind: 'units', ids } : { kind: 'none' };
    } else if (sel.kind === 'enemy' && !this.replica.units.has(sel.id)) {
      this.selection = { kind: 'none' };
    }
  }

  // ------------------------------------------------------------- commands

  async command(cmd: GameCommand): Promise<Ack> {
    const res = await sendCommand(cmd);
    if (!res.ok) this.toast(res.error, 'error');
    return res;
  }

  focus(x: number, y: number, zoom?: number): void {
    this.focusRequest = { x, y, zoom };
  }

  /** UI panels refresh at most ~6 times per second. */
  private notifyUi(): void {
    const now = performance.now();
    if (now - this.lastUiNotify > 160) {
      this.lastUiNotify = now;
      this.notify();
    } else if (this.uiTimer === null) {
      this.uiTimer = window.setTimeout(() => {
        this.uiTimer = null;
        this.lastUiNotify = performance.now();
        this.notify();
      }, 170);
    }
  }
}
