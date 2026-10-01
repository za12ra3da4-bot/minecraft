import type { DiploState } from '../types/game';
import type { NationId } from '../types/nation';

export function relationKey(a: NationId, b: NationId): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

export function getRelation(relations: Record<string, DiploState>, a: NationId, b: NationId): DiploState {
  if (a === b) return 'ALLIANCE';
  return relations[relationKey(a, b)] ?? 'PEACE';
}
