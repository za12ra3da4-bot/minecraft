import {
  type BattleNet,
  type CaptureNet,
  type DiplomacyNet,
  type GameDelta,
  type GameInit,
  type NationId,
  type NationState,
  type PrivateState,
} from '@warfront/shared';
import type { GameState } from './GameState';

/**
 * Turns the authoritative state into network packets. Units are only sent
 * when something changed; positions of moving units use a compact array.
 */
export class Replicator {
  private sentDiplomacy = -1;
  private sentNationsKey = '';
  private hadBattles = false;
  private hadCaptures = false;
  private broadcasts = 0;

  constructor(private state: GameState) {}

  buildInit(you: NationId | null): GameInit {
    const s = this.state;
    return {
      map: s.map.data,
      nationIds: s.nationIds,
      nations: this.nationStates(),
      owners: s.owners.slice(),
      units: [...s.units.values()].map((u) => u.toNet(true)),
      battles: this.battles(),
      captures: this.captures(),
      diplomacy: this.diplomacy(),
      events: s.recentEvents.slice(-40),
      time: s.time,
      tick: s.tick,
      speed: s.speed,
      paused: s.paused,
      you,
      settings: s.settings,
    };
  }

  buildDelta(): GameDelta {
    const s = this.state;
    this.broadcasts++;
    const delta: GameDelta = {
      tick: s.tick,
      time: Math.round(s.time * 100) / 100,
      speed: s.speed,
      paused: s.paused,
      units: [],
      stats: [],
      moves: [],
      removed: s.removedUnits,
    };
    s.removedUnits = [];

    for (const u of s.units.values()) {
      const cold = u.coldKey();
      const hot = u.hotKey();
      const x = Math.round(u.x * 2) / 2;
      const y = Math.round(u.y * 2) / 2;
      if (cold !== u.sentCold) {
        delta.units.push(u.toNet(u.pathRev !== u.sentPathRev));
        u.sentCold = cold;
        u.sentHot = hot;
        u.sentPathRev = u.pathRev;
        u.sentX = x;
        u.sentY = y;
        continue;
      }
      if (hot !== u.sentHot) {
        delta.stats.push(...u.hotTuple());
        u.sentHot = hot;
      }
      if (x !== u.sentX || y !== u.sentY) {
        delta.moves.push(u.id, x, y);
        u.sentX = x;
        u.sentY = y;
      }
    }

    if (s.ownerChanges.length) {
      delta.owners = s.ownerChanges.splice(0);
    }
    const battles = this.battles();
    if (battles.length || this.hadBattles) {
      delta.battles = battles;
      this.hadBattles = battles.length > 0;
    }
    if (s.captures.size || this.hadCaptures) {
      delta.captures = this.captures();
      this.hadCaptures = s.captures.size > 0;
    }
    if (s.diplomacyVersion !== this.sentDiplomacy) {
      delta.diplomacy = this.diplomacy();
      this.sentDiplomacy = s.diplomacyVersion;
    }
    if (this.broadcasts % 4 === 0) {
      const nations = this.nationStates();
      const key = JSON.stringify(nations);
      if (key !== this.sentNationsKey) {
        delta.nations = nations;
        this.sentNationsKey = key;
      }
    }
    return delta;
  }

  buildPrivate(nation: NationId): PrivateState {
    const n = this.state.nations.get(nation)!;
    const perMinute = (v: number): number => Math.round(v * 60);
    return {
      nation,
      resources: {
        manpower: Math.floor(n.resources.manpower),
        industry: Math.floor(n.resources.industry),
        supplies: Math.floor(n.resources.supplies),
      },
      income: {
        manpower: perMinute(n.incomeRate.manpower),
        industry: perMinute(n.incomeRate.industry),
        supplies: perMinute(n.incomeRate.supplies - n.upkeepRate),
      },
      upkeep: perMinute(n.upkeepRate),
      production: n.production.map((o) => ({ ...o, progress: Math.round(o.progress * 10) / 10, total: Math.round(o.total * 10) / 10 })),
      offers: this.state.offers.filter((o) => o.to === nation || o.from === nation),
    };
  }

  private nationStates(): NationState[] {
    const s = this.state;
    const soldiers = new Map<NationId, number>();
    const armies = new Map<NationId, number>();
    for (const u of s.units.values()) {
      soldiers.set(u.nation, (soldiers.get(u.nation) ?? 0) + u.soldiers);
      armies.set(u.nation, (armies.get(u.nation) ?? 0) + 1);
    }
    const territories = new Map<NationId, number>();
    for (const o of s.owners) if (o) territories.set(o, (territories.get(o) ?? 0) + 1);
    return s.nationIds.map((id) => {
      const n = s.nations.get(id)!;
      return {
        id,
        controller: n.controller,
        playerName: n.playerName,
        capitalCity: n.capitalCity,
        territories: territories.get(id) ?? 0,
        soldiers: Math.round((soldiers.get(id) ?? 0) / 100) * 100,
        armies: armies.get(id) ?? 0,
        eliminated: n.eliminated,
      };
    });
  }

  private battles(): BattleNet[] {
    return [...this.state.battles.values()].filter((b) => b.dormantSince === null).map((b) => ({
      id: b.id,
      x: Math.round(b.x),
      y: Math.round(b.y),
      radius: Math.round(b.radius),
      name: b.name,
      sides: [...b.sides.values()].map((s) => ({ nation: s.nation, soldiers: Math.round(s.soldiers), losses: Math.round(s.losses) })),
      startedAt: b.startedAt,
    }));
  }

  private captures(): CaptureNet[] {
    return [...this.state.captures.values()].map((c) => ({
      territoryId: c.territoryId,
      nation: c.nation,
      progress: Math.round(Math.min(1, Math.max(0, c.progress)) * 100) / 100,
    }));
  }

  private diplomacy(): DiplomacyNet {
    return { relations: { ...this.state.relations }, offers: this.state.offers.slice() };
  }
}
