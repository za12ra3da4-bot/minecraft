import { ARMY_TYPE_STATS, UNIT, formatNumber, getNation, type ArmyType } from '@warfront/shared';
import type { GameState, NationRuntime } from '../GameState';
import { Unit } from '../Unit';

/** Advances the first order of every city queue and spawns finished armies. */
export function updateProduction(state: GameState, dt: number): void {
  for (const n of state.nations.values()) {
    if (n.eliminated || !n.production.length) continue;
    const active = new Set<number>();
    for (const order of [...n.production]) {
      if (active.has(order.cityId)) continue;
      active.add(order.cityId);
      order.progress += dt;
      if (order.progress >= order.total) {
        if (state.unitsOf(n.id).length >= UNIT.MAX_UNITS_PER_NATION) continue; // waits for a free slot
        n.production.splice(n.production.indexOf(order), 1);
        spawnArmy(state, n, order.cityId, order.soldiers, order.type);
      }
    }
  }
}

function spawnArmy(state: GameState, n: NationRuntime, cityId: number, soldiers: number, type: ArmyType): Unit {
  const city = state.map.data.cities[cityId];
  const stats = ARMY_TYPE_STATS[type];
  let x = city.x;
  let y = city.y;
  for (let i = 0; i < 6; i++) {
    const a = state.rng.range(0, Math.PI * 2);
    const r = state.rng.range(10, 30);
    const px = city.x + Math.cos(a) * r;
    const py = city.y + Math.sin(a) * r;
    if (state.isLand(px, py) && state.territoryAt(px, py) === city.territoryId) {
      x = px;
      y = py;
      break;
    }
  }
  const unit = new Unit(n.id, type, state.nextUnitName(n, stats.label), soldiers, x, y);
  state.addUnit(unit);
  state.emit('ARMY_CREATED', `${getNation(n.id).adjective} ${unit.name} (${formatNumber(soldiers)}) raised at ${city.name}`, [n.id], { x, y });
  return unit;
}
