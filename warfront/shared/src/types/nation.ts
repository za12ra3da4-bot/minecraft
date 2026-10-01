export type NationId = string;

/**
 * Data driven flag description. Flags are painted procedurally on canvas
 * from these layers (see client/src/rendering/FlagPainter.ts).
 */
export type FlagLayer =
  | { kind: 'stripes-h'; colors: string[]; weights?: number[] }
  | { kind: 'stripes-v'; colors: string[]; weights?: number[] }
  | { kind: 'cross'; color: string; width: number; offsetX?: number }
  | { kind: 'saltire'; color: string; width: number }
  | { kind: 'border'; color: string; width: number }
  | { kind: 'disc'; color: string; x: number; y: number; r: number }
  | { kind: 'crescent'; color: string; x: number; y: number; r: number }
  | { kind: 'star'; color: string; x: number; y: number; r: number }
  | { kind: 'eagle'; color: string; x: number; y: number; size: number }
  | { kind: 'canton'; color: string; w: number; h: number };

export interface FlagSpec {
  field: string;
  layers: FlagLayer[];
}

export type NameStyleId = 'english' | 'french' | 'german' | 'dutch' | 'slavic' | 'spanish' | 'nordic' | 'turkish' | 'polish' | 'generic';

export interface AIPersonality {
  /** 0..1 how eager to declare war. */
  aggression: number;
  /** 0..1 how much it keeps troops home. */
  caution: number;
  /** 0..1 tendency to accept peace / alliances. */
  diplomacy: number;
}

export interface NationDef {
  id: NationId;
  name: string;
  adjective: string;
  /** 3 letter code used in compact UI. */
  code: string;
  color: string;
  flag: FlagSpec;
  nameStyle: NameStyleId;
  personality: AIPersonality;
}
