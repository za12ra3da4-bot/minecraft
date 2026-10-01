import type { ArmyType } from '../types/unit';

export interface ArmyTypeStats {
  label: string;
  /** Short NATO-like glyph drawn on the flag corner. */
  symbol: string;
  attack: number;
  defense: number;
  speed: number;
  /** Multiplies industry and supply cost. */
  cost: number;
  description: string;
}

/**
 * Army type modifiers. Differences are intentionally small for now; the
 * structure exists so new types and abilities can be added later.
 */
export const ARMY_TYPE_STATS: Record<ArmyType, ArmyTypeStats> = {
  INFANTRY: { label: 'Line Infantry', symbol: 'X', attack: 1.0, defense: 1.0, speed: 1.0, cost: 1.0, description: 'Line infantry. Reliable all-rounders.' },
  CAVALRY: { label: 'Cavalry', symbol: '/', attack: 1.15, defense: 0.85, speed: 1.5, cost: 1.4, description: 'Hussars, dragoons and cuirassiers: fast, weaker on defence.' },
  ARTILLERY: { label: 'Artillery', symbol: '●', attack: 1.35, defense: 0.75, speed: 0.75, cost: 1.6, description: 'Grand batteries of cannon: heavy firepower, slow and vulnerable.' },
  GUARD: { label: 'Guard', symbol: '★', attack: 1.25, defense: 1.25, speed: 0.95, cost: 2.0, description: 'Elite veterans of the Guard. Expensive.' },
  RESERVE: { label: 'Militia', symbol: 'R', attack: 0.8, defense: 0.9, speed: 1.0, cost: 0.7, description: 'Landwehr and militia levies. Cheap.' },
};
