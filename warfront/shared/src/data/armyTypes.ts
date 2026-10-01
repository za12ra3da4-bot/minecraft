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
  INFANTRY: { label: '전열 보병', symbol: 'X', attack: 1.0, defense: 1.0, speed: 1.0, cost: 1.0, description: '전열 보병. 균형 잡힌 주력 부대.' },
  CAVALRY: { label: '기병', symbol: '/', attack: 1.15, defense: 0.85, speed: 1.5, cost: 1.4, description: '경기병·용기병·흉갑기병. 빠르지만 방어가 약함.' },
  ARTILLERY: { label: '포병', symbol: '●', attack: 1.35, defense: 0.75, speed: 0.75, cost: 1.6, description: '대포병 진지. 화력이 강하지만 느리고 취약함.' },
  GUARD: { label: '근위대', symbol: '★', attack: 1.25, defense: 1.25, speed: 0.95, cost: 2.0, description: '최정예 근위 고참병. 비쌈.' },
  RESERVE: { label: '민병', symbol: 'R', attack: 0.8, defense: 0.9, speed: 1.0, cost: 0.7, description: '향토군과 민병대. 저렴함.' },
};
