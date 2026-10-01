import { CITY_TYPE_STATS, COMBAT, CellFlag, Terrain, UNIT, formatNumber, getNation, type NationId } from '@warfront/shared';
import type { Battle, GameState } from '../GameState';
import type { Unit } from '../Unit';
import { SpatialHash } from '../util/SpatialHash';
import { orderMove } from './MovementSystem';

const capitalAlertUntil = new WeakMap<GameState, Map<NationId, number>>();
/** Units already fighting each other stay engaged up to this distance (hysteresis). */
const DISENGAGE_RADIUS = UNIT.ENGAGE_RADIUS * 1.6;
/** A battle without participants is finalised after this many seconds. */
const DORMANT_SECONDS = 8;
/** New fighting this close to a dormant battle resumes it instead of starting a new one. */
const RESUME_DISTANCE = 160;

/**
 * Detects engagements between nations at war, groups them into battles and
 * resolves casualties and morale. All results are computed here, on the server.
 */
export function updateBattles(state: GameState, dt: number): void {
  const list = [...state.units.values()];
  const index = new Map<number, number>();
  list.forEach((u, i) => index.set(u.id, i));
  const parent = list.map((_, i) => i);
  const find = (i: number): number => {
    while (parent[i] !== i) i = parent[i] = parent[parent[i]];
    return i;
  };
  const engaged = new Uint8Array(list.length);
  const hash = new SpatialHash<Unit>(DISENGAGE_RADIUS);
  for (const u of list) hash.insert(u);
  const engage2 = UNIT.ENGAGE_RADIUS * UNIT.ENGAGE_RADIUS;
  list.forEach((u, i) => {
    hash.query(u.x, u.y, DISENGAGE_RADIUS, (v) => {
      if (v.id <= u.id || !state.atWar(u.nation, v.nation)) return;
      const sameBattle = u.battleId !== null && u.battleId === v.battleId;
      if (!sameBattle && (u.x - v.x) ** 2 + (u.y - v.y) ** 2 > engage2) return;
      const j = index.get(v.id)!;
      // Two routed armies do not keep fighting each other.
      if (u.status === 'RETREATING' && v.status === 'RETREATING') return;
      engaged[i] = 1;
      engaged[j] = 1;
      const ri = find(i);
      const rj = find(j);
      if (ri !== rj) parent[ri] = rj;
    });
  });

  const groups = new Map<number, Unit[]>();
  list.forEach((u, i) => {
    if (!engaged[i]) return;
    const r = find(i);
    let g = groups.get(r);
    if (!g) groups.set(r, (g = []));
    g.push(u);
  });

  // Match groups to existing battles so battles keep their identity.
  const claimed = new Set<number>();
  const assignments: { battle: Battle; units: Unit[] }[] = [];
  for (const units of groups.values()) {
    const counts = new Map<number, number>();
    for (const u of units) if (u.battleId !== null && state.battles.has(u.battleId)) counts.set(u.battleId, (counts.get(u.battleId) ?? 0) + 1);
    let bestId = -1;
    let best = 0;
    for (const [id, c] of counts) if (c > best && !claimed.has(id)) ((best = c), (bestId = id));
    if (bestId < 0) {
      // Resume a recently ended battle nearby rather than announcing a new one.
      const [gx, gy] = centroid(units);
      let bestD = RESUME_DISTANCE;
      for (const b of state.battles.values()) {
        if (b.dormantSince === null || claimed.has(b.id)) continue;
        const d = Math.hypot(b.x - gx, b.y - gy);
        if (d < bestD) {
          bestD = d;
          bestId = b.id;
        }
      }
    }
    let battle: Battle;
    if (bestId >= 0) {
      battle = state.battles.get(bestId)!;
      battle.dormantSince = null;
    } else {
      battle = startBattle(state, units);
    }
    claimed.add(battle.id);
    assignments.push({ battle, units });
  }

  // Battles without participants go dormant, then end.
  for (const battle of [...state.battles.values()]) {
    if (claimed.has(battle.id)) continue;
    if (battle.dormantSince === null) battle.dormantSince = state.time;
    else if (state.time - battle.dormantSince > DORMANT_SECONDS) endBattle(state, battle);
  }

  // Units that left battle return to their previous orders.
  for (const u of list) {
    if (!u.alive) continue;
    const i = index.get(u.id)!;
    if (!engaged[i] && u.battleId !== null) {
      u.battleId = null;
      if (u.status === 'ATTACKING' || u.status === 'DEFENDING') u.status = u.hasPath ? 'MOVING' : 'IDLE';
    }
  }

  for (const { battle, units } of assignments) resolveBattle(state, battle, units, dt);
}

function startBattle(state: GameState, units: Unit[]): Battle {
  const [x, y] = centroid(units);
  const place = state.nearestPlaceName(x, y);
  const battle: Battle = {
    id: state.battleId(),
    x,
    y,
    radius: 40,
    name: `${place} 전투`,
    unitIds: new Set(units.map((u) => u.id)),
    sides: new Map(),
    startedAt: state.time,
    initialSoldiers: units.reduce((s, u) => s + u.soldiers, 0),
    dormantSince: null,
  };
  for (const u of units) {
    const side = battle.sides.get(u.nation) ?? { nation: u.nation, soldiers: 0, losses: 0 };
    side.soldiers += u.soldiers;
    battle.sides.set(u.nation, side);
  }
  state.battles.set(battle.id, battle);
  const names = [...battle.sides.keys()].map((n) => getNation(n).name);
  state.emit(
    'BATTLE_STARTED',
    `⚔ ${battle.name}: ${names.join(' 대 ')} (${formatNumber(battle.initialSoldiers)}명)`,
    [...battle.sides.keys()],
    { x, y, major: battle.initialSoldiers >= 60_000 },
  );

  const t = state.territoryAt(x, y);
  const owner = t >= 0 ? state.owners[t] : null;
  if (owner) {
    const cap = state.nations.get(owner)?.capitalCity;
    if (cap !== null && cap !== undefined && state.map.data.cities[cap].territoryId === t) {
      let alerts = capitalAlertUntil.get(state);
      if (!alerts) capitalAlertUntil.set(state, (alerts = new Map()));
      if ((alerts.get(owner) ?? -1) < state.time) {
        alerts.set(owner, state.time + 30);
        state.emit('CAPITAL_ATTACKED', `수도 공격당함! ${state.map.data.cities[cap].name} (${getNation(owner).name})`, [owner], { x, y, major: true });
      }
    }
  }
  return battle;
}

function endBattle(state: GameState, battle: Battle): void {
  state.battles.delete(battle.id);
  const remaining = new Map<NationId, number>();
  for (const id of battle.unitIds) {
    const u = state.units.get(id);
    if (!u || u.status === 'RETREATING') continue;
    remaining.set(u.nation, (remaining.get(u.nation) ?? 0) + u.soldiers);
  }
  let winner: NationId | null = null;
  let best = 0;
  for (const [n, s] of remaining) if (s > best) ((best = s), (winner = n));
  const losses = [...battle.sides.values()].reduce((s, side) => s + side.losses, 0);
  if (losses < 200) return;
  const text = winner
    ? `${battle.name} 승리: ${getNation(winner).name} — 사상자 ${formatNumber(losses)}명`
    : `${battle.name} 종료 — 사상자 ${formatNumber(losses)}명`;
  state.emit('BATTLE_ENDED', text, [...battle.sides.keys()], { x: battle.x, y: battle.y, major: losses >= 25_000 });
}

function centroid(units: Unit[]): [number, number] {
  let sx = 0;
  let sy = 0;
  let w = 0;
  for (const u of units) {
    const k = Math.max(1, u.soldiers);
    sx += u.x * k;
    sy += u.y * k;
    w += k;
  }
  return [sx / w, sy / w];
}

function defenseModifier(state: GameState, u: Unit): number {
  let mod = u.status === 'DEFENDING' ? COMBAT.DEFENDER_BONUS : 1;
  const terrain = state.terrainAt(u.x, u.y);
  if (terrain === Terrain.HILLS) mod *= COMBAT.HILLS_DEFENSE;
  else if (terrain === Terrain.FOREST) mod *= COMBAT.FOREST_DEFENSE;
  if (state.townAt(u.x, u.y)) {
    const t = state.territoryAt(u.x, u.y);
    const city = t >= 0 ? state.map.data.territories[t].cityId : null;
    mod *= city !== null ? CITY_TYPE_STATS[state.map.data.cities[city].type].defense : COMBAT.TOWN_DEFENSE;
  }
  return mod;
}

function resolveBattle(state: GameState, battle: Battle, units: Unit[], dt: number): void {
  for (const u of units) {
    if (u.battleId !== battle.id) {
      if (u.status !== 'RETREATING') u.status = u.hasPath || u.targetUnit !== null ? 'ATTACKING' : 'DEFENDING';
      u.battleId = battle.id;
    }
    battle.unitIds.add(u.id);
    if (!battle.sides.has(u.nation)) battle.sides.set(u.nation, { nation: u.nation, soldiers: 0, losses: 0 });
  }

  const pending = new Map<Unit, number>();
  for (const u of units) {
    if (u.status === 'RETREATING') continue;
    const enemies = units.filter((e) => state.atWar(u.nation, e.nation));
    if (!enemies.length) continue;
    const enemyTotal = enemies.reduce((s, e) => s + e.soldiers, 0);
    const nation = state.nations.get(u.nation)!;
    const flags = state.flagsAt(u.x, u.y);
    const river = flags & CellFlag.RIVER && !(flags & CellFlag.BRIDGE) ? COMBAT.RIVER_ATTACK_PENALTY : 1;
    const moraleFactor = 0.45 + 0.55 * (u.morale / 100);
    const jitter = 1 + (state.rng.next() * 2 - 1) * COMBAT.DAMAGE_JITTER;
    const out = u.soldiers * u.attack * moraleFactor * river * (nation.outOfSupply ? 0.75 : 1) * COMBAT.BASE_DAMAGE * dt * jitter;
    for (const e of enemies) {
      const share = (out * e.soldiers) / enemyTotal;
      const retreatMul = e.status === 'RETREATING' ? COMBAT.RETREAT_DAMAGE_TAKEN : 1;
      const loss = (share / (e.defense * defenseModifier(state, e))) * retreatMul;
      pending.set(e, (pending.get(e) ?? 0) + loss);
      u.kills += loss;
      nation.kills += loss;
    }
  }

  for (const [e, rawLoss] of pending) {
    const before = e.soldiers;
    const loss = Math.min(rawLoss, before);
    e.soldiers -= loss;
    const nation = state.nations.get(e.nation)!;
    nation.losses += loss;
    battle.sides.get(e.nation)!.losses += loss;
    e.morale = Math.max(0, e.morale - (loss / Math.max(1, before)) * 100 * COMBAT.MORALE_PER_LOSS_PCT - COMBAT.MORALE_DRAIN * dt);
    if (e.soldiers < UNIT.MIN_SOLDIERS) {
      destroyUnit(state, e);
    } else if (e.morale < COMBAT.ROUT_MORALE && e.status !== 'RETREATING') {
      rout(state, e, battle);
    }
  }

  // Refresh battle summary.
  const alive = units.filter((u) => u.alive);
  if (alive.length) {
    const [x, y] = centroid(alive);
    battle.x = x;
    battle.y = y;
    battle.radius = Math.max(36, ...alive.map((u) => Math.hypot(u.x - x, u.y - y))) + 18;
  }
  for (const side of battle.sides.values()) side.soldiers = 0;
  for (const u of alive) battle.sides.get(u.nation)!.soldiers += u.soldiers;
}

function destroyUnit(state: GameState, u: Unit): void {
  const place = state.nearestPlaceName(u.x, u.y);
  if (u.maxSoldiers >= 4000) {
    state.emit('ARMY_DESTROYED', `전멸: ${getNation(u.nation).adjective} ${u.name} (${place} 부근)`, [u.nation], {
      x: u.x,
      y: u.y,
      major: u.maxSoldiers >= 40_000,
    });
  }
  state.removeUnit(u);
}

/** Broken army falls back toward friendly territory, away from the fight. */
export function rout(state: GameState, u: Unit, battle: { x: number; y: number }): void {
  u.clearOrders();
  u.status = 'RETREATING';
  const awayX = u.x - battle.x;
  const awayY = u.y - battle.y;
  let best: { x: number; y: number } | null = null;
  let bestScore = Infinity;
  for (const t of state.map.data.territories) {
    const owner = state.owners[t.id];
    if (!owner || !state.friendly(owner, u.nation)) continue;
    const dx = t.cx - u.x;
    const dy = t.cy - u.y;
    const d = Math.hypot(dx, dy);
    if (d < 60) continue;
    const away = dx * awayX + dy * awayY >= 0 ? 0 : 400;
    const score = d + away;
    if (score < bestScore) {
      bestScore = score;
      best = { x: t.cx, y: t.cy };
    }
  }
  if (!best) {
    const len = Math.hypot(awayX, awayY) || 1;
    best = { x: u.x + (awayX / len) * 200, y: u.y + (awayY / len) * 200 };
  }
  orderMove(state, u, best.x, best.y);
  if (u.soldiers >= 15_000) {
    state.emit('INFO', `후퇴: ${getNation(u.nation).adjective} ${u.name} (${formatNumber(u.soldiers)}명)`, [u.nation], { x: u.x, y: u.y });
  }
}
