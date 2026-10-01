import {
  ARMY_TYPE_STATS,
  CITY_TYPE_STATS,
  PRODUCTION,
  UNIT,
  getNation,
  type ArmyType,
  type GameCommand,
  type NationId,
  type TerritoryDef,
} from '@warfront/shared';
import { executeCommand } from '../game/CommandHandler';
import type { GameState, NationRuntime } from '../game/GameState';
import type { Unit } from '../game/Unit';
import { armyCost } from '../game/systems/ProductionSystem';
import { SpatialHash } from '../game/util/SpatialHash';

const MAX_ORDERS_PER_THINK = 10;

interface Assignment {
  territory: number;
  until: number;
}

/**
 * Rule-based strategic AI. It only acts through executeCommand, so it is
 * bound by exactly the same rules as human players.
 */
export class AIController {
  private thinkIn: number;
  private diploIn: number;
  private assignments = new Map<number, Assignment>();
  private answeredOffers = new Set<number>();
  private lastPeaceOffer = new Map<NationId, number>();
  private orders = 0;

  constructor(
    private state: GameState,
    readonly nation: NationId,
  ) {
    this.thinkIn = 0.5 + state.rng.next() * 2;
    this.diploIn = 4 + state.rng.next() * 4;
  }

  private get me(): NationRuntime {
    return this.state.nations.get(this.nation)!;
  }

  update(dt: number): void {
    if (!this.state.isActive(this.nation)) return;
    this.thinkIn -= dt;
    this.diploIn -= dt;
    if (this.thinkIn <= 0) {
      this.thinkIn = 1.8 + this.state.rng.next() * 0.8;
      this.orders = 0;
      this.produce();
      this.command();
    }
    if (this.diploIn <= 0) {
      this.diploIn = 5 + this.state.rng.next() * 4;
      this.diplomacy();
    }
  }

  private issue(cmd: GameCommand): boolean {
    if (this.orders >= MAX_ORDERS_PER_THINK) return false;
    this.orders++;
    return executeCommand(this.state, this.nation, cmd).ok;
  }

  private strength(nation: NationId): number {
    let s = 0;
    for (const u of this.state.units.values()) if (u.nation === nation) s += u.soldiers;
    return s;
  }

  private enemies(): NationId[] {
    return this.state.activeNations().map((n) => n.id).filter((id) => this.state.atWar(this.nation, id));
  }

  // ------------------------------------------------------------ production

  private produce(): void {
    const s = this.state;
    const me = this.me;
    if (me.production.length >= 2) return;
    const units = s.unitsOf(this.nation);
    if (units.length + me.production.length >= UNIT.MAX_UNITS_PER_NATION - 4) return;
    const netSupplies = me.incomeRate.supplies - me.upkeepRate;
    if (netSupplies < 0 && me.resources.supplies < 4000) return;

    const r = s.rng.next();
    let type: ArmyType = 'INFANTRY';
    if (r < 0.15) type = 'CAVALRY';
    else if (r < 0.27) type = 'ARTILLERY';
    else if (r < 0.31 && me.resources.industry > 3000) type = 'GUARD';
    else if (r < 0.36) type = 'RESERVE';
    const mult = ARMY_TYPE_STATS[type].cost;
    const byIndustry = me.resources.industry / (PRODUCTION.INDUSTRY_PER_SOLDIER * mult);
    const bySupplies = (me.resources.supplies * 0.7) / (PRODUCTION.SUPPLIES_PER_SOLDIER * mult);
    const cap = this.enemies().length ? 40_000 : 20_000;
    let soldiers = Math.floor(Math.min(me.resources.manpower * 0.55, byIndustry * 0.9, bySupplies, cap) / 500) * 500;
    if (soldiers < 6_000) return;
    soldiers = Math.min(soldiers, PRODUCTION.MAX_SOLDIERS);

    const cities = s.map.data.cities.filter(
      (c) => s.owners[c.territoryId] === this.nation && CITY_TYPE_STATS[c.type].canProduce && !me.production.some((o) => o.cityId === c.id),
    );
    if (!cities.length) return;
    const front = this.frontTerritories();
    let best = cities[0];
    let bestScore = Infinity;
    for (const c of cities) {
      let d = 3000;
      for (const t of front) d = Math.min(d, Math.hypot(t.cx - c.x, t.cy - c.y));
      const score = d * (0.7 + s.rng.next() * 0.6) - (c.type === 'CAPITAL' ? 150 : 0);
      if (score < bestScore) {
        bestScore = score;
        best = c;
      }
    }
    const cost = armyCost(soldiers, type);
    if (cost.industry > me.resources.industry || cost.supplies > me.resources.supplies) return;
    this.issue({ type: 'CREATE_ARMY', cityId: best.id, soldiers, armyType: type });
  }

  /** Territories we could capture next (enemy or unclaimed, adjacent to our land). */
  private frontTerritories(): TerritoryDef[] {
    const s = this.state;
    const out: TerritoryDef[] = [];
    for (const t of s.map.data.territories) {
      const owner = s.owners[t.id];
      if (owner === this.nation || !s.canCapture(this.nation, owner)) continue;
      if (t.neighbors.some((n) => s.owners[n] === this.nation)) out.push(t);
    }
    return out;
  }

  // ------------------------------------------------------------ armies

  private command(): void {
    const s = this.state;
    const mine = s.unitsOf(this.nation);
    if (!mine.length) return;
    const hostile = new SpatialHash<Unit>(160);
    const hostileList: Unit[] = [];
    for (const u of s.units.values()) {
      if (u.nation !== this.nation && s.atWar(this.nation, u.nation)) {
        hostile.insert(u);
        hostileList.push(u);
      }
    }
    const strengthNear = (x: number, y: number, r: number): number => {
      let sum = 0;
      hostile.query(x, y, r, (u) => (sum += u.soldiers));
      return sum;
    };

    const available = (u: Unit): boolean =>
      !u.inBattle && u.status !== 'RETREATING' && u.morale > 40 && u.joinUnit === null && u.targetUnit === null;

    // Drop finished or stale assignments.
    for (const [id, a] of this.assignments) {
      const u = s.units.get(id);
      if (!u || a.until < s.time || s.owners[a.territory] === this.nation || !s.canCapture(this.nation, s.owners[a.territory])) {
        this.assignments.delete(id);
      }
    }

    // 1. Defend: attack enemies standing on our land.
    const threats = hostileList
      .filter((h) => {
        const t = s.territoryAt(h.x, h.y);
        return t >= 0 && s.owners[t] === this.nation;
      })
      .sort((a, b) => b.soldiers - a.soldiers);
    const busy = new Set<number>();
    for (const threat of threats.slice(0, 4)) {
      const responders = mine
        .filter((u) => available(u) && !busy.has(u.id) && Math.hypot(u.x - threat.x, u.y - threat.y) < 700)
        .sort((a, b) => Math.hypot(a.x - threat.x, a.y - threat.y) - Math.hypot(b.x - threat.x, b.y - threat.y));
      let power = 0;
      const group: number[] = [];
      for (const u of responders) {
        if (power >= threat.soldiers * 1.25) break;
        power += u.soldiers;
        group.push(u.id);
      }
      if (group.length && power >= threat.soldiers * 0.7) {
        if (this.issue({ type: 'ATTACK', unitIds: group, targetUnitId: threat.id })) {
          group.forEach((id) => busy.add(id));
          group.forEach((id) => this.assignments.delete(id));
        }
      }
    }

    // 2. Reinforce battles we are losing.
    for (const b of s.battles.values()) {
      const mySide = b.sides.get(this.nation);
      if (!mySide) continue;
      let enemy = 0;
      for (const side of b.sides.values()) if (s.atWar(this.nation, side.nation)) enemy += side.soldiers;
      if (mySide.soldiers >= enemy * 1.1) continue;
      const helper = mine.find((u) => available(u) && !busy.has(u.id) && !this.assignments.has(u.id) && Math.hypot(u.x - b.x, u.y - b.y) < 500);
      if (!helper) continue;
      if (this.issue({ type: 'MOVE_UNIT', unitIds: [helper.id], x: b.x, y: b.y })) busy.add(helper.id);
    }

    // 3. Consolidate small idle armies.
    const idle = mine.filter((u) => available(u) && !busy.has(u.id) && !u.hasPath);
    for (const small of idle) {
      if (small.soldiers >= 7_000 || busy.has(small.id)) continue;
      const partner = idle.find((o) => o !== small && !busy.has(o.id) && o.soldiers >= small.soldiers && Math.hypot(o.x - small.x, o.y - small.y) < 160);
      if (!partner) continue;
      if (this.issue({ type: 'JOIN_UNIT', unitIds: [small.id], targetUnitId: partner.id })) {
        busy.add(small.id);
        busy.add(partner.id);
      }
    }

    // 4. Offensive: send idle armies to capture frontier territory.
    const front = this.frontTerritories();
    if (!front.length) return;
    const assignedPower = new Map<number, number>();
    for (const [id, a] of this.assignments) {
      const u = s.units.get(id);
      if (u) assignedPower.set(a.territory, (assignedPower.get(a.territory) ?? 0) + u.soldiers);
    }
    const capitalCity = this.me.capitalCity !== null ? s.map.data.cities[this.me.capitalCity] : null;
    const caution = getNation(this.nation).personality.caution;
    const candidates = mine
      .filter((u) => available(u) && !busy.has(u.id) && !this.assignments.has(u.id) && (!u.hasPath || u.status === 'IDLE'))
      .sort((a, b) => b.soldiers - a.soldiers);

    // Keep a home guard near the capital when enemies are close.
    if (capitalCity && strengthNear(capitalCity.x, capitalCity.y, 500) > 0) {
      const guard = candidates.find((u) => Math.hypot(u.x - capitalCity.x, u.y - capitalCity.y) < 120);
      if (guard && s.rng.next() < caution + 0.3) candidates.splice(candidates.indexOf(guard), 1);
    }

    // Split oversized idle armies when there are several fronts.
    if (front.length >= 3 && candidates.length && candidates[0].soldiers > 55_000 && s.unitsOf(this.nation).length < UNIT.MAX_UNITS_PER_NATION - 10) {
      this.issue({ type: 'SPLIT_UNIT', unitId: candidates[0].id, soldiers: Math.floor(candidates[0].soldiers / 2) });
    }

    for (const u of candidates) {
      let best: TerritoryDef | null = null;
      let bestScore = -Infinity;
      for (const t of front) {
        const owner = s.owners[t.id];
        const enemy = strengthNear(t.cx, t.cy, 220);
        const already = assignedPower.get(t.id) ?? 0;
        if (already > enemy * 1.6 + 12_000) continue;
        if (owner !== null && u.soldiers + already < enemy * 0.85) continue;
        const city = t.cityId !== null ? s.map.data.cities[t.cityId] : null;
        const value =
          t.population / 60_000 +
          t.industry / 8 +
          (city && city.type !== 'VILLAGE' ? 1.2 : 0) +
          (city?.type === 'CAPITAL' ? 4 : 0) +
          (owner === null ? 0.6 : 0);
        const d = Math.hypot(t.cx - u.x, t.cy - u.y);
        const score = value / (1 + enemy / 25_000) - d / 450 + s.rng.next() * 0.4;
        if (score > bestScore) {
          bestScore = score;
          best = t;
        }
      }
      if (!best) continue;
      const ox = s.rng.range(-20, 20);
      const oy = s.rng.range(-20, 20);
      if (!this.issue({ type: 'MOVE_UNIT', unitIds: [u.id], x: best.cx + ox, y: best.cy + oy })) {
        if (this.orders >= MAX_ORDERS_PER_THINK) break;
        continue;
      }
      this.assignments.set(u.id, { territory: best.id, until: s.time + 90 });
      assignedPower.set(best.id, (assignedPower.get(best.id) ?? 0) + u.soldiers);
    }
  }

  // ------------------------------------------------------------ diplomacy

  private diplomacy(): void {
    const s = this.state;
    const personality = getNation(this.nation).personality;
    const myStrength = this.strength(this.nation) + 1;

    for (const offer of s.offers) {
      if (offer.to !== this.nation || this.answeredOffers.has(offer.id)) continue;
      this.answeredOffers.add(offer.id);
      const theirs = this.strength(offer.from) + 1;
      let accept: boolean;
      if (offer.kind === 'PEACE') {
        const p = 0.15 + personality.diplomacy * 0.35 + (theirs / myStrength - 1) * 0.7 + (this.enemies().length > 1 ? 0.2 : 0);
        accept = s.rng.next() < Math.max(0.05, Math.min(0.95, p));
      } else {
        const shared = this.enemies().some((e) => s.atWar(offer.from, e));
        accept = s.rng.next() < (shared ? 0.25 + personality.diplomacy * 0.6 : personality.diplomacy * 0.2);
      }
      const action = accept ? 'ACCEPT_OFFER' : 'REJECT_OFFER';
      executeCommand(s, this.nation, { type: 'DIPLOMACY', action, target: offer.from, offerId: offer.id });
    }

    const enemies = this.enemies();
    // Sue for peace when clearly losing.
    for (const e of enemies) {
      const theirs = this.strength(e);
      const last = this.lastPeaceOffer.get(e) ?? -999;
      if (theirs > myStrength * 1.8 && s.time - last > 60 && s.rng.next() < 0.3 + personality.diplomacy * 0.4) {
        this.lastPeaceOffer.set(e, s.time);
        executeCommand(s, this.nation, { type: 'DIPLOMACY', action: 'OFFER_PEACE', target: e });
      }
    }

    // Look for a new war when idle.
    if (!enemies.length && s.time > 40) {
      const neighbours = new Set<NationId>();
      for (const t of s.map.data.territories) {
        if (s.owners[t.id] !== this.nation) continue;
        for (const n of t.neighbors) {
          const o = s.owners[n];
          if (o && o !== this.nation && s.isActive(o)) neighbours.add(o);
        }
      }
      let target: NationId | null = null;
      let bestRatio = 0;
      for (const n of neighbours) {
        if (s.relation(this.nation, n) !== 'PEACE') continue;
        const ratio = myStrength / (this.strength(n) + 1);
        if (ratio > bestRatio) {
          bestRatio = ratio;
          target = n;
        }
      }
      if (target && bestRatio > 1.3 - personality.aggression * 0.5 && s.rng.next() < personality.aggression * 0.5) {
        executeCommand(s, this.nation, { type: 'DIPLOMACY', action: 'DECLARE_WAR', target });
      }
    }
  }
}
