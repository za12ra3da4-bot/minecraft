import { ARMY_TYPE_STATS, getNation, type ArmyType, type GameSettings, type NationId } from '@warfront/shared';
import { GameState, type Controller, type NationRuntime } from './GameState';
import type { GeneratedMap } from './map/MapGenerator';
import { Unit } from './Unit';

export interface Participant {
  nation: NationId;
  controller: Exclude<Controller, 'NONE'>;
  playerId: string | null;
  playerName: string | null;
}

/** Builds the initial game: owners, capitals, relations and starting armies. */
export function setupGame(map: GeneratedMap, settings: GameSettings, participants: Participant[], seed: number): GameState {
  const state = new GameState(map, settings, seed);
  const byNation = new Map(participants.map((p) => [p.nation, p]));
  for (const slot of map.def.nations) {
    const p = byNation.get(slot.nation);
    const n = state.createNation(slot.nation, p?.controller ?? 'NONE', p?.playerId ?? null, p?.playerName ?? null);
    if (n.controller !== 'NONE') {
      n.capitalCity = map.capitals.get(slot.nation) ?? null;
      n.originalCapital = n.capitalCity;
    }
  }
  map.homeNation.forEach((home, t) => {
    state.owners[t] = home && state.isActive(home) ? home : null;
  });

  const active = state.activeNations().map((n) => n.id);
  for (let i = 0; i < active.length; i++) {
    for (let j = i + 1; j < active.length; j++) {
      state.setRelation(active[i], active[j], settings.startAtWar ? 'WAR' : 'PEACE');
    }
  }
  for (const r of map.def.initialRelations) {
    if (state.isActive(r.a) && state.isActive(r.b)) state.setRelation(r.a, r.b, r.state);
  }
  // Historical blocs and neutral powers.
  for (const n of map.def.neutrals ?? []) {
    for (const o of active) if (o !== n && state.isActive(n)) state.setRelation(n, o, 'PEACE');
  }
  for (const bloc of map.def.blocs ?? []) {
    const members = bloc.filter((n) => state.isActive(n));
    for (let i = 0; i < members.length; i++) for (let j = i + 1; j < members.length; j++) state.setRelation(members[i], members[j], 'ALLIANCE');
  }

  for (const slot of map.def.nations) {
    const n = state.nations.get(slot.nation)!;
    if (n.controller === 'NONE') continue;
    spawnStartingArmies(state, n, slot.armies.total, slot.armies.count, slot.armies.grand);
  }
  state.emit('INFO', `The campaign begins on ${map.def.name}.`, [], { major: false });
  return state;
}

const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];

function spawnStartingArmies(state: GameState, n: NationRuntime, total: number, count: number, grand: number): void {
  const { rng } = state;
  const territories = state.map.data.territories.filter((t) => state.owners[t.id] === n.id);
  if (!territories.length) return;
  const capital = n.capitalCity !== null ? state.map.data.cities[n.capitalCity] : null;
  const border = territories.filter((t) => t.neighbors.some((x) => state.owners[x] !== n.id));
  const interior = territories.filter((t) => !border.includes(t));
  const order = [...rng.shuffle(border.slice()), ...rng.shuffle(interior.slice())];
  const perTerritory = new Map<number, number>();

  const place = (tid: number, cx: number, cy: number): [number, number] => {
    const k = perTerritory.get(tid) ?? 0;
    perTerritory.set(tid, k + 1);
    for (let attempt = 0; attempt < 8; attempt++) {
      const a = rng.range(0, Math.PI * 2);
      const r = k === 0 && attempt === 0 ? rng.range(0, 10) : 22 + k * 20 + rng.range(-6, 6);
      const x = cx + Math.cos(a) * r;
      const y = cy + Math.sin(a) * r;
      if (state.isLand(x, y) && state.territoryAt(x, y) === tid) return [x, y];
    }
    return [cx + rng.range(-8, 8), cy + rng.range(-8, 8)];
  };

  let remaining = total;
  if (grand > 0 && capital) {
    const [x, y] = place(capital.territoryId, capital.x, capital.y);
    const style = getNation(n.id).military;
    const unit = new Unit(n.id, 'INFANTRY', `${style.fieldArmy} (${style.generals[0]})`, grand, x, y);
    state.addUnit(unit);
    remaining -= grand;
  }
  const others = Math.max(0, count - (grand > 0 ? 1 : 0));
  const weights = Array.from({ length: others }, () => rng.range(0.45, 1.5) ** 2);
  const wSum = weights.reduce((a, b) => a + b, 0) || 1;
  const generals = getNation(n.id).military.generals.slice(1);
  const corpsNames = new Map<number, string>();
  weights
    .map((w, i) => [w, i] as const)
    .sort((a, b) => b[0] - a[0])
    .slice(0, generals.length)
    .forEach(([, i], k) => corpsNames.set(i, `${ROMAN[k]} Corps (${generals[k]})`));
  weights.forEach((w, i) => {
    const soldiers = Math.max(1_500, Math.round((remaining * w) / wSum + rng.range(-180, 180)));
    let type: ArmyType = 'INFANTRY';
    const r = rng.next();
    if (i === 0 && others > 6) type = 'GUARD';
    else if (r < 0.15) type = 'CAVALRY';
    else if (r < 0.27) type = 'ARTILLERY';
    else if (r < 0.32) type = 'RESERVE';
    const t = type === 'GUARD' && capital ? state.map.data.territories[capital.territoryId] : order[i % order.length];
    const [x, y] = place(t.id, t.cx, t.cy);
    const unit = new Unit(n.id, type, state.nextUnitName(n, ARMY_TYPE_STATS[type].label), soldiers, x, y);
    // The largest formations become named corps under famous commanders.
    if (corpsNames.has(i)) unit.name = corpsNames.get(i)!;
    state.addUnit(unit);
  });
}
