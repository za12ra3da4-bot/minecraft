import { COMBAT, ECONOMY, getNation, type Resources } from '@warfront/shared';
import type { GameState, NationRuntime } from '../GameState';

/** Income from owned territories, army upkeep, supply shortages and morale recovery. */
export function updateEconomy(state: GameState, dt: number): void {
  const income = new Map<string, Resources>();
  const soldiers = new Map<string, number>();
  for (const n of state.nations.values()) {
    income.set(n.id, { manpower: 0, industry: 0, supplies: 0 });
    soldiers.set(n.id, 0);
  }
  const territories = state.map.data.territories;
  for (let t = 0; t < territories.length; t++) {
    const owner = state.owners[t];
    if (!owner) continue;
    const inc = income.get(owner);
    if (!inc) continue;
    const def = territories[t];
    const grain = def.resource === 'GRAIN' ? 1.15 : 1;
    const supplyBonus = def.resource === 'TIMBER' || def.resource === 'WINE' ? 1.15 : 1;
    inc.manpower += def.population * ECONOMY.MANPOWER_PER_POP * grain;
    inc.industry += def.industry * ECONOMY.INDUSTRY_PER_POINT;
    inc.supplies += (def.industry * ECONOMY.SUPPLIES_PER_POINT + ECONOMY.SUPPLIES_PER_TERRITORY) * supplyBonus;
  }
  for (const u of state.units.values()) soldiers.set(u.nation, (soldiers.get(u.nation) ?? 0) + u.soldiers);

  for (const n of state.nations.values()) {
    if (n.controller === 'NONE' || n.eliminated) continue;
    const inc = income.get(n.id)!;
    if (n.capitalCity !== null) {
      inc.manpower *= ECONOMY.CAPITAL_BONUS;
      inc.industry *= ECONOMY.CAPITAL_BONUS;
    }
    const upkeep = (soldiers.get(n.id) ?? 0) * ECONOMY.UPKEEP_PER_SOLDIER;
    n.incomeRate = inc;
    n.upkeepRate = upkeep;
    addResources(n, inc, dt);
    n.resources.supplies -= upkeep * dt;
    if (n.resources.supplies <= 0) {
      n.resources.supplies = 0;
      if (!n.outOfSupply) {
        n.outOfSupply = true;
        state.emit('INFO', `${getNation(n.id).name}: supplies exhausted! Armies are starving.`, [n.id], { major: n.controller === 'PLAYER' });
      }
    } else if (n.outOfSupply && n.resources.supplies > 200) {
      n.outOfSupply = false;
    }
  }

  // Morale recovery and attrition.
  for (const u of state.units.values()) {
    const nation = state.nations.get(u.nation)!;
    if (nation.outOfSupply) {
      u.morale = Math.max(0, u.morale - ECONOMY.OUT_OF_SUPPLY_MORALE_DRAIN * dt);
      u.soldiers -= u.soldiers * ECONOMY.OUT_OF_SUPPLY_ATTRITION * dt;
    } else if (!u.inBattle) {
      const rate = u.status === 'RETREATING' ? COMBAT.MORALE_RECOVERY * 0.6 : COMBAT.MORALE_RECOVERY;
      u.morale = Math.min(100, u.morale + rate * dt);
    }
  }
}

function addResources(n: NationRuntime, inc: Resources, dt: number): void {
  n.resources.manpower = Math.min(ECONOMY.MAX_STOCK.manpower, n.resources.manpower + inc.manpower * dt);
  n.resources.industry = Math.min(ECONOMY.MAX_STOCK.industry, n.resources.industry + inc.industry * dt);
  n.resources.supplies = Math.min(ECONOMY.MAX_STOCK.supplies, n.resources.supplies + inc.supplies * dt);
}
