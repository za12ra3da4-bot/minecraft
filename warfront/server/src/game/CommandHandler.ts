import {
  armyCost,
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
import { getPathfinder } from './Pathfinder';
import { applyDiplomacy } from './systems/DiplomacySystem';
import { orderMove } from './systems/MovementSystem';
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
  if (state.over) return fail('게임이 끝났습니다');
  if (!state.isActive(nation)) return fail('우리 나라가 멸망했습니다');

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
      if (units.length < 2) return fail('합칠 부대를 2개 이상 선택하세요');
      if (units.some((u) => u.inBattle)) return fail('전투 중인 부대는 합칠 수 없습니다');
      const main = units.reduce((a, b) => (b.soldiers > a.soldiers ? b : a));
      if (units.some((u) => Math.hypot(u.x - main.x, u.y - main.y) > UNIT.MERGE_RADIUS)) {
        return fail('부대가 너무 멀리 떨어져 있습니다');
      }
      if (units.reduce((s, u) => s + u.soldiers, 0) > UNIT.MAX_SOLDIERS) return fail('합친 부대가 너무 큽니다');
      const merged = mergeUnits(state, units);
      merged.clearOrders();
      merged.status = 'IDLE';
      return OK;
    }
    case 'SPLIT_UNIT': {
      const unit = state.units.get(cmd.unitId);
      if (!unit || unit.nation !== nation) return fail('내 부대가 아닙니다');
      if (unit.inBattle) return fail('전투 중인 부대는 나눌 수 없습니다');
      if (cmd.soldiers < UNIT.MIN_SPLIT || cmd.soldiers > unit.soldiers - UNIT.MIN_SPLIT) return fail('나눌 병력 수가 올바르지 않습니다');
      if (state.unitsOf(nation).length >= UNIT.MAX_UNITS_PER_NATION) return fail('부대 수가 최대치입니다');
      splitUnit(state, unit, cmd.soldiers);
      return OK;
    }
    case 'CREATE_ARMY':
      return createArmy(state, nation, cmd.cityId, cmd.soldiers, cmd.armyType);
    case 'CANCEL_PRODUCTION': {
      const n = state.nations.get(nation)!;
      const order = n.production.find((o) => o.id === cmd.orderId);
      if (!order) return fail('생산 주문을 찾을 수 없습니다');
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
    if (!u || !u.alive) return '부대가 더 이상 존재하지 않습니다';
    if (u.nation !== nation) return '내 부대가 아닙니다';
    out.push(u);
  }
  return out;
}

function moveUnits(state: GameState, nation: NationId, ids: number[], x: number, y: number): CommandResult {
  if (!state.inBounds(x, y)) return fail('지도 밖으로는 이동할 수 없습니다');
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
    if (!state.inBounds(tx, ty) || !getPathfinder(state.map).passable(tx, ty)) {
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
  return moved ? OK : fail('갈 수 없는 곳입니다');
}

function followUnit(state: GameState, nation: NationId, ids: number[], targetId: number, join: boolean): CommandResult {
  const target = state.units.get(targetId);
  if (!target || !target.alive) return fail('목표가 사라졌습니다');
  if (join) {
    if (target.nation !== nation) return fail('내 부대에만 합류할 수 있습니다');
  } else if (!state.atWar(nation, target.nation)) {
    return fail(`${getNation(target.nation).name}과(와) 전쟁 중이 아닙니다 — 외교에서 선전포고하세요`);
  }
  const units = ownUnits(state, nation, ids.filter((id) => id !== targetId));
  if (typeof units === 'string') return fail(units);
  if (!units.length) return fail('선택한 부대가 없습니다');
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
  return ordered ? OK : fail('목표에 갈 수 없습니다');
}

function createArmy(state: GameState, nation: NationId, cityId: number, soldiers: number, type: ArmyType): CommandResult {
  const city = state.map.data.cities[cityId];
  if (!city) return fail('알 수 없는 도시');
  if (state.owners[city.territoryId] !== nation) return fail('내 도시가 아닙니다');
  if (!CITY_TYPE_STATS[city.type].canProduce) return fail('마을에서는 군대를 만들 수 없습니다');
  if (soldiers < PRODUCTION.MIN_SOLDIERS || soldiers > PRODUCTION.MAX_SOLDIERS) {
    return fail(`병력은 ${formatNumber(PRODUCTION.MIN_SOLDIERS)}~${formatNumber(PRODUCTION.MAX_SOLDIERS)}명이어야 합니다`);
  }
  const n = state.nations.get(nation)!;
  if (n.production.filter((o) => o.cityId === cityId).length >= PRODUCTION.MAX_QUEUE_PER_CITY) return fail('생산 대기열이 가득 찼습니다');
  if (state.unitsOf(nation).length + n.production.length >= UNIT.MAX_UNITS_PER_NATION) return fail('부대 수가 최대치입니다');
  const cost = armyCost(soldiers, type);
  if (n.resources.manpower < cost.manpower) return fail('인력이 부족합니다');
  if (n.resources.industry < cost.industry) return fail('산업력이 부족합니다');
  if (n.resources.supplies < cost.supplies) return fail('보급품이 부족합니다');
  n.resources.manpower -= cost.manpower;
  n.resources.industry -= cost.industry;
  n.resources.supplies -= cost.supplies;
  n.production.push({ id: state.orderId(), cityId, soldiers, type, total: cost.seconds, progress: 0 });
  return OK;
}
