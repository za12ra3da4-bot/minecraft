import { PRODUCTION } from '../constants/game';
import { ARMY_TYPE_STATS } from '../data/armyTypes';
import type { ArmyType } from '../types/unit';

export interface ArmyCost {
  manpower: number;
  industry: number;
  supplies: number;
  seconds: number;
}

/** Cost of raising an army. Used by server validation, the AI and the UI preview. */
export function armyCost(soldiers: number, type: ArmyType): ArmyCost {
  const mult = ARMY_TYPE_STATS[type].cost;
  return {
    manpower: soldiers,
    industry: Math.ceil(soldiers * PRODUCTION.INDUSTRY_PER_SOLDIER * mult),
    supplies: Math.ceil(soldiers * PRODUCTION.SUPPLIES_PER_SOLDIER * mult),
    seconds: (PRODUCTION.BASE_SECONDS + soldiers / PRODUCTION.SOLDIERS_PER_SECOND) * Math.sqrt(mult),
  };
}
