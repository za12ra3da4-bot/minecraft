import type { NationId } from './nation';

export const UNIT_STATUSES = ['IDLE', 'MOVING', 'ATTACKING', 'DEFENDING', 'RETREATING', 'DESTROYED'] as const;
export type UnitStatus = (typeof UNIT_STATUSES)[number];

export const ARMY_TYPES = ['INFANTRY', 'CAVALRY', 'ARTILLERY', 'GUARD', 'RESERVE'] as const;
export type ArmyType = (typeof ARMY_TYPES)[number];

/** Public state of a unit as replicated to every client. */
export interface UnitNet {
  id: number;
  nation: NationId;
  type: ArmyType;
  name: string;
  soldiers: number;
  maxSoldiers: number;
  x: number;
  y: number;
  status: UnitStatus;
  /** 0..100 */
  morale: number;
  attack: number;
  defense: number;
  /** World units per sim second on plains. */
  speed: number;
  /** Final destination, if any. */
  tx: number | null;
  ty: number | null;
  targetUnit: number | null;
  /** Unit id this unit will merge into on arrival. */
  joinUnit: number | null;
  /** Path revision. Clients keep the last path they received for this revision. */
  pathRev: number;
  /** Index of the next waypoint in the path. */
  pathIndex: number;
  /** Flat [x0,y0,x1,y1...] path waypoints, only sent when pathRev changed. */
  path?: number[];
  battleId: number | null;
}
