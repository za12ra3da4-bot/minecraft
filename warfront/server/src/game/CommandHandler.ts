import {
  CITY_TYPE_STATS,
  PRODUCTION,
  UNIT,
  formatNumber,
  getNation,
  type ArmyType,
  type GameCommand,
  type NationId,
} from '@warfront/shared';
import type { GameState } from './GameState';
import type { Unit } from './Unit';
import { applyDiplomacy } from './systems/DiplomacySystem';
import { orderMove } from './systems/MovementSystem';
import { armyCost } from './systems/ProductionSystem';
import { mergeUnits, splitUnit } from './unitOps';

export type CommandResult = { ok: true } | { ok: false; error: string };

const fail = (error: string): CommandResult => ({ ok: false, error });
const OK: CommandResult = { ok: true };

/**
 * Executes a typed command on behalf of `nation`. Every rule is enforced here:
 * ownership, distances, resources and unit limits. Clients only ever send intents.
 * Speed / pause are room-level and handled by the Room.
 */
export function executeCommand(state: GameState, nation: NationId, cmd: GameCommand): CommandResult {
  if (state.over) return fail('Game is over');
  if (!state.isActive(nation)) return fail('Your nation has been eliminated');

  switch (cmd.type) {
    case 'MOVE_UNIT':
      return moveUnits(state, nation, cmd.unitIds, cmd.x, cmd.y);
    case 'ATTACK':
    case 'JOIN_UNIT':
      return followUnit(state, nation, cmd.unitIds, cmd.targetUnitId, cmd.type === 'JOIN_UNIT');
    case 'HALT': {
      const units = ownUnits(state, nation, cmd.unitIds);
      if (typeof units === 'string') return fail(units);
      for (const u of units) {
        u.clearOrders();
        if (!u.inBattle) u.status = 'IDLE';
      }
      return OK;
    }
    case 'MERGE_UNIT': {
      const units = ownUnits(state, nation, cmd.unitIds);
      if (typeof units === 'string') return fail(units);
      if (units.length < 2) return fail('Select at least two armies to merge');
      if (units.some((u) => u.inBattle)) return fail('Armies in battle cannot merge');
      const main = units.reduce((a, b) => (b.soldiers > a.soldiers ? b : a));
      if (units.some((u) => Math.hypot(u.x - main.x, u.y - main.y) > UNIT.MERGE_RADIUS)) {
        return fail('Armies are too far apart — move them together first');
      }
      if (units.reduce((s, u) => s + u.soldiers, 0) > UNIT.MAX_SOLDIERS) return fail('Merged army would be too large');
      const merged = mergeUnits(state, units);
      merged.clearOrders();
      merged.status = 'IDLE';
      return OK;
    }
    case 'SPLIT_UNIT': {
      const unit = state.units.get(cmd.unitId);
      if (!unit || unit.nation !== nation) return fail('Not your army');
      if (unit.inBattle) return fail('Armies in battle cannot split');
      if (cmd.soldiers < UNIT.MIN_SPLIT || cmd.soldiers > unit.soldiers - UNIT.MIN_SPLIT) return fail('Invalid split size');
      if (state.unitsOf(nation).length >= UNIT.MAX_UNITS_PER_NATION) return fail('Army limit reached');
      splitUnit(state, unit, cmd.soldiers);
      return OK;
    }
    case 'CREATE_ARMY':
      return createArmy(state, nation, cmd.cityId, cmd.soldiers, cmd.armyType);
    case 'CANCEL_PRODUCTION': {
      const n = state.nations.get(nation)!;
      const order = n.production.find((o) => o.id === cmd.orderId);
      if (!order) return fail('Order not found');
      const cost = armyCost(order.soldiers, order.type);
      const refund = order.progress > 0 ? 0.75 : 1;
      n.resources.manpower += cost.manpower * refund;
      n.resources.industry += cost.industry * refund;
      n.resources.supplies += cost.supplies * refund;
      n.production = n.production.filter((o) => o !== order);
      return OK;
    }
    case 'DIPLOMACY':
      return applyDiplomacy(state, nation, cmd.action, cmd.target, cmd.offerId);
    case 'SET_SPEED':
    case 'SET_PAUSED':
      return fail('Handled by the room');
  }
}

function ownUnits(state: GameState, nation: NationId, ids: number[]): Unit[] | string {
  const out: Unit[] = [];
  for (const id of ids) {
    const u = state.units.get(id);
    if (!u || !u.alive) return 'Army no longer exists';
    if (u.nation !== nation) return 'Not your army';
    out.push(u);
  }
  return out;
}

function moveUnits(state: GameState, nation: NationId, ids: number[], x: number, y: number): CommandResult {
  if (!state.inBounds(x, y)) return fail('Destination outside the map');
  const units = ownUnits(state, nation, ids);
  if (typeof units === 'string') return fail(units);
  // Keep a loose formation: preserve relative offsets, compressed.
  let cx = 0;
  let cy = 0;
  for (const u of units) {
    cx += u.x;
    cy += u.y;
  }
  cx /= units.length;
  cy /= units.length;
  let moved = 0;
  for (const u of units) {
    let ox = 0;
    let oy = 0;
    if (units.length > 1) {
      ox = (u.x - cx) * 0.35;
      oy = (u.y - cy) * 0.35;
      const len = Math.hypot(ox, oy);
      const max = 24 + Math.sqrt(units.length) * 14;
      if (len > max) {
        ox = (ox / len) * max;
        oy = (oy / len) * max;
      }
    }
    let tx = x + ox;
    let ty = y + oy;
    if (!state.inBounds(tx, ty) || !state.isLand(tx, ty)) {
      tx = x;
      ty = y;
    }
    const wasFighting = u.inBattle;
    const target = u.targetUnit;
    u.targetUnit = null;
    u.joinUnit = null;
    if (orderMove(state, u, tx, ty)) {
      moved++;
      // Leaving an ongoing battle is a retreat: slower and it keeps taking fire.
      u.status = wasFighting ? 'RETREATING' : 'MOVING';
    } else {
      u.targetUnit = target;
    }
  }
  return moved ? OK : fail('Destination is unreachable');
}

function followUnit(state: GameState, nation: NationId, ids: number[], targetId: number, join: boolean): CommandResult {
  const target = state.units.get(targetId);
  if (!target || !target.alive) return fail('Target no longer exists');
  if (join) {
    if (target.nation !== nation) return fail('You can only join your own armies');
  } else if (!state.atWar(nation, target.nation)) {
    return fail(`You are not at war with ${getNation(target.nation).name}`);
  }
  const units = ownUnits(state, nation, ids.filter((id) => id !== targetId));
  if (typeof units === 'string') return fail(units);
  if (!units.length) return fail('No armies selected');
  let ordered = 0;
  for (const u of units) {
    const wasFighting = u.inBattle;
    if (!orderMove(state, u, target.x, target.y)) continue;
    u.targetUnit = join ? null : target.id;
    u.joinUnit = join ? target.id : null;
    u.repathIn = 1;
    u.status = wasFighting ? 'RETREATING' : 'MOVING';
    ordered++;
  }
  return ordered ? OK : fail('Target is unreachable');
}

function createArmy(state: GameState, nation: NationId, cityId: number, soldiers: number, type: ArmyType): CommandResult {
  const city = state.map.data.cities[cityId];
  if (!city) return fail('Unknown city');
  if (state.owners[city.territoryId] !== nation) return fail('You do not control this city');
  if (!CITY_TYPE_STATS[city.type].canProduce) return fail('Villages cannot raise armies');
  if (soldiers < PRODUCTION.MIN_SOLDIERS || soldiers > PRODUCTION.MAX_SOLDIERS) {
    return fail(`Army size must be ${formatNumber(PRODUCTION.MIN_SOLDIERS)}–${formatNumber(PRODUCTION.MAX_SOLDIERS)}`);
  }
  const n = state.nations.get(nation)!;
  if (n.production.filter((o) => o.cityId === cityId).length >= PRODUCTION.MAX_QUEUE_PER_CITY) return fail('Production queue is full');
  if (state.unitsOf(nation).length + n.production.length >= UNIT.MAX_UNITS_PER_NATION) return fail('Army limit reached');
  const cost = armyCost(soldiers, type);
  if (n.resources.manpower < cost.manpower) return fail('Not enough manpower');
  if (n.resources.industry < cost.industry) return fail('Not enough industry');
  if (n.resources.supplies < cost.supplies) return fail('Not enough supplies');
  n.resources.manpower -= cost.manpower;
  n.resources.industry -= cost.industry;
  n.resources.supplies -= cost.supplies;
  n.production.push({ id: state.orderId(), cityId, soldiers, type, total: cost.seconds, progress: 0 });
  return OK;
}
