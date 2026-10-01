import { CellFlag, TERRAIN_SPEED, UNIT } from '@warfront/shared';
import type { GameState } from '../GameState';
import { getPathfinder, terrainSpeed } from '../Pathfinder';
import type { Unit } from '../Unit';
import { mergeUnits } from '../unitOps';

const REPATH_SECONDS = 1.2;

/** Effective speed of a unit at its current location. */
export function unitSpeed(state: GameState, u: Unit): number {
  const flags = state.flagsAt(u.x, u.y);
  let terrain = terrainSpeed(state.terrainAt(u.x, u.y));
  if (flags & CellFlag.ROAD) terrain = Math.max(terrain, TERRAIN_SPEED.ROAD);
  if (flags & CellFlag.RIVER && !(flags & CellFlag.BRIDGE)) terrain *= TERRAIN_SPEED.RIVER_CROSSING;
  const size = 1 - Math.min(UNIT.MAX_SIZE_SLOWDOWN, u.soldiers / UNIT.SIZE_SLOWDOWN_SOLDIERS);
  const retreat = u.status === 'RETREATING' ? 0.85 : 1;
  const supply = state.nations.get(u.nation)?.outOfSupply ? 0.75 : 1;
  return u.speed * terrain * size * retreat * supply;
}

/** Plans a path for `u` to (x, y). Returns false if unreachable. */
export function orderMove(state: GameState, u: Unit, x: number, y: number): boolean {
  const path = getPathfinder(state.map).findPath(u.x, u.y, x, y);
  if (!path) return false;
  u.setPath(path, path[path.length - 2], path[path.length - 1]);
  return true;
}

export function updateMovement(state: GameState, dt: number): void {
  for (const u of state.units.values()) {
    // Chasing an enemy or heading to a friendly unit to join it.
    const followId = u.targetUnit ?? u.joinUnit;
    if (followId !== null) {
      const target = state.units.get(followId);
      const valid =
        target &&
        target.alive &&
        (u.targetUnit !== null ? state.atWar(u.nation, target.nation) : target.nation === u.nation);
      if (!valid) {
        u.clearOrders();
        if (!u.inBattle && u.status !== 'RETREATING') u.status = 'IDLE';
        continue;
      }
      if (u.joinUnit !== null && Math.hypot(target.x - u.x, target.y - u.y) <= UNIT.MERGE_RADIUS * 0.6 && !u.inBattle && !target.inBattle) {
        const main = mergeUnits(state, [target, u]);
        if (main === u) {
          u.clearOrders();
          u.status = 'IDLE';
        }
        continue;
      }
      u.repathIn -= dt;
      if (u.repathIn <= 0 && !u.inBattle) {
        u.repathIn = REPATH_SECONDS;
        const moved = u.tx === null || u.ty === null || Math.hypot(target.x - u.tx, target.y - u.ty) > 12;
        if (moved || !u.hasPath) {
          const keepTarget = u.targetUnit;
          const keepJoin = u.joinUnit;
          if (orderMove(state, u, target.x, target.y)) {
            u.targetUnit = keepTarget;
            u.joinUnit = keepJoin;
          }
        }
      }
    }

    if (!u.hasPath) continue;
    // Units locked in battle hold position unless they are retreating.
    if (u.inBattle && u.status !== 'RETREATING') continue;
    if (u.status === 'IDLE' || u.status === 'DEFENDING') u.status = 'MOVING';

    let remaining = unitSpeed(state, u) * dt;
    while (remaining > 0 && u.hasPath) {
      const wx = u.path[u.pathIndex * 2];
      const wy = u.path[u.pathIndex * 2 + 1];
      const dx = wx - u.x;
      const dy = wy - u.y;
      const d = Math.hypot(dx, dy);
      if (d <= remaining) {
        u.x = wx;
        u.y = wy;
        remaining -= d;
        u.pathIndex++;
      } else {
        u.x += (dx / d) * remaining;
        u.y += (dy / d) * remaining;
        remaining = 0;
      }
    }
    if (!u.hasPath) onArrival(state, u);
  }
}

function onArrival(state: GameState, u: Unit): void {
  if (u.joinUnit !== null || u.targetUnit !== null) return; // keeps following
  u.path = [];
  u.pathIndex = 0;
  u.tx = null;
  u.ty = null;
  if (u.status === 'RETREATING') {
    if (!u.inBattle) u.status = 'IDLE';
  } else if (!u.inBattle) {
    u.status = 'IDLE';
  }
}
