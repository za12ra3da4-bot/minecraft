import {
  CellFlag,
  ECONOMY,
  Rng,
  Terrain,
  getRelation,
  relationKey,
  type DiploOffer,
  type DiploState,
  type EventKind,
  type GameEvent,
  type GameSettings,
  type NationId,
  type ProductionOrder,
  type Resources,
} from '@warfront/shared';
import type { GeneratedMap } from './map/MapGenerator';
import type { Unit } from './Unit';

export type Controller = 'PLAYER' | 'AI' | 'NONE';

export interface NationRuntime {
  id: NationId;
  controller: Controller;
  playerId: string | null;
  playerName: string | null;
  resources: Resources;
  /** Income per sim second, refreshed by the economy system. */
  incomeRate: Resources;
  upkeepRate: number;
  outOfSupply: boolean;
  capitalCity: number | null;
  originalCapital: number | null;
  eliminated: boolean;
  production: ProductionOrder[];
  /** Nation -> sim time until which war cannot be declared. */
  truces: Map<NationId, number>;
  kills: number;
  losses: number;
  unitCounters: Map<string, number>;
}

export interface BattleSide {
  nation: NationId;
  soldiers: number;
  losses: number;
}

export interface Battle {
  id: number;
  x: number;
  y: number;
  radius: number;
  name: string;
  unitIds: Set<number>;
  sides: Map<NationId, BattleSide>;
  startedAt: number;
  /** Total soldiers at start, used for event importance. */
  initialSoldiers: number;
  /** Set when the last participant left; the battle can be resumed for a few seconds. */
  dormantSince: number | null;
}

export interface CaptureState {
  territoryId: number;
  nation: NationId;
  progress: number;
  /** Sim time of last progress increase. */
  active: boolean;
}

/** Complete authoritative state of one running game. */
export class GameState {
  readonly map: GeneratedMap;
  readonly settings: GameSettings;
  readonly rng: Rng;
  readonly nationIds: NationId[];
  readonly nations = new Map<NationId, NationRuntime>();
  readonly units = new Map<number, Unit>();
  readonly owners: (NationId | null)[];
  readonly relations: Record<string, DiploState> = {};
  offers: DiploOffer[] = [];
  readonly battles = new Map<number, Battle>();
  readonly captures = new Map<number, CaptureState>();
  time = 0;
  tick = 0;
  speed: GameSettings['speed'];
  paused = false;
  over = false;

  /** Replication bookkeeping. */
  readonly ownerChanges: number[] = [];
  removedUnits: number[] = [];
  diplomacyVersion = 0;
  nationsVersion = 0;

  private nextEventId = 1;
  private nextBattleId = 1;
  private nextOfferId = 1;
  private nextOrderId = 1;
  readonly recentEvents: GameEvent[] = [];
  pendingEvents: GameEvent[] = [];

  constructor(map: GeneratedMap, settings: GameSettings, seed: number) {
    this.map = map;
    this.settings = settings;
    this.speed = settings.speed;
    this.rng = new Rng(seed);
    this.nationIds = map.def.nations.map((n) => n.nation);
    this.owners = new Array(map.data.territories.length).fill(null);
  }

  // ---------------------------------------------------------------- ids

  battleId(): number {
    return this.nextBattleId++;
  }

  offerId(): number {
    return this.nextOfferId++;
  }

  orderId(): number {
    return this.nextOrderId++;
  }

  // ---------------------------------------------------------------- nations

  createNation(id: NationId, controller: Controller, playerId: string | null, playerName: string | null): NationRuntime {
    const n: NationRuntime = {
      id,
      controller,
      playerId,
      playerName,
      resources: { ...ECONOMY.STARTING },
      incomeRate: { manpower: 0, industry: 0, supplies: 0 },
      upkeepRate: 0,
      outOfSupply: false,
      capitalCity: null,
      originalCapital: null,
      eliminated: controller === 'NONE',
      production: [],
      truces: new Map(),
      kills: 0,
      losses: 0,
      unitCounters: new Map(),
    };
    this.nations.set(id, n);
    return n;
  }

  isActive(id: NationId | null): boolean {
    if (!id) return false;
    const n = this.nations.get(id);
    return !!n && n.controller !== 'NONE' && !n.eliminated;
  }

  activeNations(): NationRuntime[] {
    return [...this.nations.values()].filter((n) => n.controller !== 'NONE' && !n.eliminated);
  }

  // ---------------------------------------------------------------- diplomacy

  relation(a: NationId, b: NationId): DiploState {
    return getRelation(this.relations, a, b);
  }

  setRelation(a: NationId, b: NationId, state: DiploState): void {
    this.relations[relationKey(a, b)] = state;
    this.diplomacyVersion++;
  }

  atWar(a: NationId, b: NationId): boolean {
    return a !== b && this.relation(a, b) === 'WAR';
  }

  friendly(a: NationId, b: NationId): boolean {
    return a === b || this.relation(a, b) === 'ALLIANCE';
  }

  /** True if `nation` may capture land owned by `owner` (null = unclaimed). */
  canCapture(nation: NationId, owner: NationId | null): boolean {
    if (owner === null) return true;
    if (owner === nation) return false;
    return this.atWar(nation, owner);
  }

  // ---------------------------------------------------------------- map queries

  cellAt(x: number, y: number): number {
    const { cols, rows, cellSize } = this.map.data;
    const cx = Math.floor(x / cellSize);
    const cy = Math.floor(y / cellSize);
    if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return -1;
    return cy * cols + cx;
  }

  territoryAt(x: number, y: number): number {
    const c = this.cellAt(x, y);
    return c < 0 ? -1 : this.map.territoryGrid[c];
  }

  terrainAt(x: number, y: number): Terrain {
    const c = this.cellAt(x, y);
    return c < 0 ? Terrain.WATER : (this.map.terrain[c] as Terrain);
  }

  flagsAt(x: number, y: number): number {
    const c = this.cellAt(x, y);
    return c < 0 ? 0 : this.map.flags[c];
  }

  isLand(x: number, y: number): boolean {
    return this.terrainAt(x, y) !== Terrain.WATER;
  }

  inBounds(x: number, y: number): boolean {
    return x >= 0 && y >= 0 && x < this.map.data.width && y < this.map.data.height;
  }

  /** Name of the nearest settlement, used for battle names and events. */
  nearestPlaceName(x: number, y: number): string {
    let best = '';
    let bestD = Infinity;
    for (const c of this.map.data.cities) {
      const d = (c.x - x) ** 2 + (c.y - y) ** 2;
      if (d < bestD) {
        bestD = d;
        best = c.name;
      }
    }
    return best;
  }

  townAt(x: number, y: number): boolean {
    return (this.flagsAt(x, y) & CellFlag.TOWN) !== 0;
  }

  // ---------------------------------------------------------------- units

  addUnit(unit: Unit): void {
    this.units.set(unit.id, unit);
  }

  removeUnit(unit: Unit): void {
    unit.status = 'DESTROYED';
    this.units.delete(unit.id);
    this.removedUnits.push(unit.id);
  }

  unitsOf(nation: NationId): Unit[] {
    const out: Unit[] = [];
    for (const u of this.units.values()) if (u.nation === nation) out.push(u);
    return out;
  }

  nextUnitName(nation: NationRuntime, typeLabel: string): string {
    const n = (nation.unitCounters.get(typeLabel) ?? 0) + 1;
    nation.unitCounters.set(typeLabel, n);
    return `${ordinal(n)} ${typeLabel}`;
  }

  // ---------------------------------------------------------------- events

  emit(kind: EventKind, text: string, nations: NationId[], extra: { x?: number; y?: number; major?: boolean } = {}): void {
    const ev: GameEvent = { id: this.nextEventId++, time: Math.round(this.time * 10) / 10, kind, text, nations, ...extra };
    this.pendingEvents.push(ev);
    this.recentEvents.push(ev);
    if (this.recentEvents.length > 80) this.recentEvents.shift();
  }

  flushEvents(): GameEvent[] {
    const out = this.pendingEvents;
    this.pendingEvents = [];
    return out;
  }
}

export function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
