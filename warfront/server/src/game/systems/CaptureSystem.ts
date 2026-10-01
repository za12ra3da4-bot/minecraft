import { CAPTURE, CITY_TYPE_STATS, ECONOMY, getNation, type NationId } from '@warfront/shared';
import type { GameState } from '../GameState';

interface Presence {
  /** Soldiers per nation that could capture this territory. */
  capturers: Map<NationId, { soldiers: number; moving: boolean }>;
  defended: boolean;
}

/**
 * Armies standing in enemy (or unclaimed) territory capture it over time.
 * Any friendly army of the owner blocks the capture.
 */
export function updateCaptures(state: GameState, dt: number): void {
  const presence = new Map<number, Presence>();
  for (const u of state.units.values()) {
    if (u.status === 'RETREATING' || u.inBattle) {
      // Fighting/retreating armies still defend their own land.
      const t = state.territoryAt(u.x, u.y);
      if (t >= 0 && state.owners[t] && state.friendly(state.owners[t]!, u.nation)) getPresence(presence, t).defended = true;
      continue;
    }
    const t = state.territoryAt(u.x, u.y);
    if (t < 0) continue;
    const owner = state.owners[t];
    const p = getPresence(presence, t);
    if (owner && state.friendly(owner, u.nation)) {
      p.defended = true;
      continue;
    }
    if (!state.canCapture(u.nation, owner)) continue;
    const entry = p.capturers.get(u.nation) ?? { soldiers: 0, moving: true };
    entry.soldiers += u.soldiers;
    if (!u.hasPath) entry.moving = false;
    p.capturers.set(u.nation, entry);
  }

  // Progress or decay existing captures.
  for (const [tid, cap] of state.captures) {
    const p = presence.get(tid);
    const owner = state.owners[tid];
    const stillValid = state.isActive(cap.nation) && state.canCapture(cap.nation, owner);
    if (!stillValid || !p || p.defended || !p.capturers.has(cap.nation)) {
      cap.active = false;
      cap.progress -= CAPTURE.DECAY_PER_SECOND * dt;
      if (cap.progress <= 0 || !stillValid) state.captures.delete(tid);
    }
  }

  for (const [tid, p] of presence) {
    if (p.defended || p.capturers.size === 0) continue;
    let leader: NationId | null = null;
    let best = 0;
    for (const [n, e] of p.capturers) if (e.soldiers > best) ((best = e.soldiers), (leader = n));
    if (!leader) continue;
    const entry = p.capturers.get(leader)!;
    let cap = state.captures.get(tid);
    if (cap && cap.nation !== leader) {
      cap.progress -= CAPTURE.DECAY_PER_SECOND * 2 * dt;
      if (cap.progress > 0) continue;
      cap = undefined;
    }
    if (!cap) {
      cap = { territoryId: tid, nation: leader, progress: 0, active: true };
      state.captures.set(tid, cap);
    }
    const territory = state.map.data.territories[tid];
    const city = territory.cityId !== null ? state.map.data.cities[territory.cityId] : null;
    const cityFactor = city ? CITY_TYPE_STATS[city.type].captureFactor : 1;
    const strength = Math.max(0.35, Math.min(2.2, Math.sqrt(entry.soldiers / 10_000)));
    const moving = entry.moving ? CAPTURE.MOVING_FACTOR : 1;
    cap.active = true;
    cap.progress += (dt / CAPTURE.BASE_SECONDS) * strength * cityFactor * moving;
    if (cap.progress >= 1) {
      state.captures.delete(tid);
      transferTerritory(state, tid, leader);
    }
  }
}

function getPresence(map: Map<number, Presence>, t: number): Presence {
  let p = map.get(t);
  if (!p) map.set(t, (p = { capturers: new Map(), defended: false }));
  return p;
}

/** Changes ownership and applies capital loss / elimination consequences. */
export function transferTerritory(state: GameState, tid: number, to: NationId): void {
  const from = state.owners[tid];
  state.owners[tid] = to;
  state.ownerChanges.push(tid, state.nationIds.indexOf(to));
  state.nationsVersion++;
  const territory = state.map.data.territories[tid];
  const toName = getNation(to).name;
  state.emit(
    'TERRITORY_CAPTURED',
    from ? `점령: ${territory.name} (${getNation(from).name} → ${toName})` : `점령: ${territory.name} → ${toName}`,
    from ? [to, from] : [to],
    { x: territory.cx, y: territory.cy },
  );
  if (!from) return;
  const loser = state.nations.get(from);
  if (!loser) return;

  // Production queued in a lost city is cancelled.
  if (territory.cityId !== null) loser.production = loser.production.filter((o) => o.cityId !== territory.cityId);

  if (loser.capitalCity !== null && state.map.data.cities[loser.capitalCity].territoryId === tid) {
    const capitalName = state.map.data.cities[loser.capitalCity].name;
    for (const key of ['manpower', 'industry', 'supplies'] as const) {
      loser.resources[key] = Math.floor(loser.resources[key] * (1 - ECONOMY.CAPITAL_LOSS_SHARE));
    }
    for (const u of state.units.values()) {
      if (u.nation === from) u.morale = Math.max(0, u.morale - ECONOMY.CAPITAL_LOSS_MORALE);
    }
    loser.capitalCity = relocateCapital(state, from);
    const moved = loser.capitalCity !== null ? ` 수도 이전: ${state.map.data.cities[loser.capitalCity].name}` : '';
    state.emit('CAPITAL_CAPTURED', `수도 함락! ${capitalName} → ${toName}.${moved}`, [to, from], {
      x: territory.cx,
      y: territory.cy,
      major: true,
    });
  }

  if (!state.owners.some((o) => o === from)) eliminateNation(state, from, to);
}

function relocateCapital(state: GameState, nation: NationId): number | null {
  let best: number | null = null;
  let bestScore = -1;
  for (const t of state.map.data.territories) {
    if (state.owners[t.id] !== nation || t.cityId === null) continue;
    const city = state.map.data.cities[t.cityId];
    const score = t.population * (city.type === 'VILLAGE' ? 0.3 : 1);
    if (score > bestScore) {
      bestScore = score;
      best = city.id;
    }
  }
  return best;
}

export function eliminateNation(state: GameState, nation: NationId, by: NationId | null): void {
  const n = state.nations.get(nation);
  if (!n || n.eliminated) return;
  n.eliminated = true;
  n.capitalCity = null;
  n.production = [];
  state.nationsVersion++;
  for (const u of [...state.units.values()]) if (u.nation === nation) state.removeUnit(u);
  state.offers = state.offers.filter((o) => o.from !== nation && o.to !== nation);
  for (const [tid, cap] of state.captures) if (cap.nation === nation) state.captures.delete(tid);
  state.emit(
    'NATION_ELIMINATED',
    by ? `멸망: ${getNation(nation).name} (정복자 ${getNation(by).name})` : `멸망: ${getNation(nation).name}`,
    by ? [nation, by] : [nation],
    { major: true },
  );
}
