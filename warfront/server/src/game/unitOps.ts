import { UNIT } from '@warfront/shared';
import type { GameState } from './GameState';
import { Unit } from './Unit';

/** Merges `units` into the largest one. Caller validates ownership and distance. */
export function mergeUnits(state: GameState, units: Unit[]): Unit {
  const sorted = units.slice().sort((a, b) => b.soldiers - a.soldiers);
  const main = sorted[0];
  let soldiers = 0;
  let max = 0;
  let atk = 0;
  let def = 0;
  let morale = 0;
  let speed = 0;
  for (const u of sorted) {
    soldiers += u.soldiers;
    max += u.maxSoldiers;
    atk += u.attack * u.soldiers;
    def += u.defense * u.soldiers;
    morale += u.morale * u.soldiers;
    speed = speed === 0 ? u.speed : Math.min(speed, u.speed);
  }
  main.soldiers = Math.min(UNIT.MAX_SOLDIERS, soldiers);
  main.maxSoldiers = Math.min(UNIT.MAX_SOLDIERS, max);
  main.attack = atk / soldiers;
  main.defense = def / soldiers;
  main.morale = morale / soldiers;
  main.speed = speed;
  main.kills = sorted.reduce((s, u) => s + u.kills, 0);
  for (const u of sorted.slice(1)) {
    state.removeUnit(u);
    // Anyone following a merged unit now follows the survivor.
    for (const other of state.units.values()) {
      if (other.joinUnit === u.id) other.joinUnit = main.id;
      if (other.targetUnit === u.id) other.targetUnit = main.id;
    }
  }
  if (main.joinUnit !== null && !state.units.has(main.joinUnit)) main.joinUnit = null;
  return main;
}

/** Splits `soldiers` off `unit` into a new unit placed next to it. */
export function splitUnit(state: GameState, unit: Unit, soldiers: number): Unit {
  const nation = state.nations.get(unit.nation)!;
  const share = soldiers / unit.soldiers;
  const name = state.nextUnitName(nation, 'Detachment');
  const angle = state.rng.range(0, Math.PI * 2);
  let nx = unit.x + Math.cos(angle) * 26;
  let ny = unit.y + Math.sin(angle) * 26;
  if (!state.isLand(nx, ny) || !state.inBounds(nx, ny)) {
    nx = unit.x;
    ny = unit.y;
  }
  const created = new Unit(unit.nation, unit.type, name, soldiers, nx, ny);
  created.maxSoldiers = Math.max(soldiers, Math.round(unit.maxSoldiers * share));
  created.attack = unit.attack;
  created.defense = unit.defense;
  created.speed = unit.speed;
  created.morale = unit.morale;
  unit.soldiers -= soldiers;
  unit.maxSoldiers = Math.max(unit.soldiers, unit.maxSoldiers - created.maxSoldiers);
  state.addUnit(created);
  return created;
}
