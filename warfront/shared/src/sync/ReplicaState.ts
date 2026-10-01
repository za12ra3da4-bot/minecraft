import type {
  BattleNet,
  CaptureNet,
  DiplomacyNet,
  GameDelta,
  GameInit,
  GameSettings,
  GameSpeed,
  NationState,
} from '../types/game';
import type { MapData } from '../types/map';
import type { NationId } from '../types/nation';
import { UNIT_STATUSES, type UnitNet } from '../types/unit';

export interface DeltaChanges {
  /** Units created this delta. */
  added: UnitNet[];
  /** Units removed this delta (last known state). */
  removed: UnitNet[];
  /** Units that moved: id -> previous position. */
  moved: Map<number, { x: number; y: number }>;
  /** Soldiers lost per unit id this delta. */
  losses: Map<number, number>;
  /** Territories that changed owner: [territoryId, previousOwner]. */
  owners: [number, NationId | null][];
}

/**
 * Client-side mirror of the server state, built from the init packet and
 * kept in sync by deltas. Used by the browser and by integration tests.
 */
export class ReplicaState {
  map!: MapData;
  nationIds: NationId[] = [];
  nations = new Map<NationId, NationState>();
  owners: (NationId | null)[] = [];
  units = new Map<number, UnitNet>();
  battles: BattleNet[] = [];
  captures: CaptureNet[] = [];
  diplomacy: DiplomacyNet = { relations: {}, offers: [] };
  time = 0;
  tick = 0;
  speed: GameSpeed = 1;
  paused = false;
  you: NationId | null = null;
  settings!: GameSettings;
  /** Bumped whenever territory ownership changes (for cache invalidation). */
  ownersVersion = 0;
  diplomacyVersion = 0;

  applyInit(init: GameInit): void {
    this.map = init.map;
    this.nationIds = init.nationIds;
    this.nations = new Map(init.nations.map((n) => [n.id, n]));
    this.owners = init.owners.slice();
    this.units = new Map(init.units.map((u) => [u.id, u]));
    this.battles = init.battles;
    this.captures = init.captures;
    this.diplomacy = init.diplomacy;
    this.time = init.time;
    this.tick = init.tick;
    this.speed = init.speed;
    this.paused = init.paused;
    this.you = init.you;
    this.settings = init.settings;
    this.ownersVersion++;
    this.diplomacyVersion++;
  }

  applyDelta(d: GameDelta): DeltaChanges {
    const changes: DeltaChanges = { added: [], removed: [], moved: new Map(), losses: new Map(), owners: [] };
    this.tick = d.tick;
    this.time = d.time;
    this.speed = d.speed;
    this.paused = d.paused;

    for (const id of d.removed) {
      const u = this.units.get(id);
      if (u) {
        changes.removed.push(u);
        this.units.delete(id);
      }
    }
    for (const net of d.units) {
      const prev = this.units.get(net.id);
      if (!prev) {
        changes.added.push(net);
      } else {
        if (net.soldiers < prev.soldiers) changes.losses.set(net.id, prev.soldiers - net.soldiers);
        if (net.x !== prev.x || net.y !== prev.y) changes.moved.set(net.id, { x: prev.x, y: prev.y });
        // Paths are only sent when their revision changes.
        if (!net.path && net.pathRev === prev.pathRev) net.path = prev.path;
      }
      this.units.set(net.id, net);
    }
    for (let i = 0; i + 4 < d.stats.length; i += 5) {
      const u = this.units.get(d.stats[i]);
      if (!u) continue;
      const soldiers = d.stats[i + 1];
      if (soldiers < u.soldiers) changes.losses.set(u.id, (changes.losses.get(u.id) ?? 0) + u.soldiers - soldiers);
      u.soldiers = soldiers;
      u.morale = d.stats[i + 2];
      u.status = UNIT_STATUSES[d.stats[i + 3]] ?? u.status;
      u.pathIndex = d.stats[i + 4];
    }
    for (let i = 0; i + 2 < d.moves.length; i += 3) {
      const u = this.units.get(d.moves[i]);
      if (!u) continue;
      if (!changes.moved.has(u.id)) changes.moved.set(u.id, { x: u.x, y: u.y });
      u.x = d.moves[i + 1];
      u.y = d.moves[i + 2];
    }
    if (d.owners) {
      for (let i = 0; i + 1 < d.owners.length; i += 2) {
        const t = d.owners[i];
        const idx = d.owners[i + 1];
        changes.owners.push([t, this.owners[t]]);
        this.owners[t] = idx >= 0 ? this.nationIds[idx] : null;
      }
      if (changes.owners.length) this.ownersVersion++;
    }
    if (d.battles) this.battles = d.battles;
    if (d.captures) this.captures = d.captures;
    if (d.nations) for (const n of d.nations) this.nations.set(n.id, n);
    if (d.diplomacy) {
      this.diplomacy = d.diplomacy;
      this.diplomacyVersion++;
    }
    return changes;
  }
}
