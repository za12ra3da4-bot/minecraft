import type { MapData } from './map';
import type { NationId } from './nation';
import type { ArmyType, UnitNet } from './unit';

export const VICTORY_CONDITIONS = ['CONQUEST', 'DOMINATION', 'CAPITALS'] as const;
export type VictoryCondition = (typeof VICTORY_CONDITIONS)[number];

export const GAME_SPEEDS = [0.5, 1, 2, 4] as const;
export type GameSpeed = (typeof GAME_SPEEDS)[number];

export interface GameSettings {
  roomName: string;
  maxPlayers: number;
  mapId: string;
  speed: GameSpeed;
  victory: VictoryCondition;
  aiCount: number;
  /** When true every nation starts at war with every non-allied nation. */
  startAtWar: boolean;
  /** Private rooms are not listed (singleplayer rooms are always private). */
  isPrivate: boolean;
}

export const DIPLO_STATES = ['WAR', 'PEACE', 'ALLIANCE'] as const;
export type DiploState = (typeof DIPLO_STATES)[number];

export const DIPLO_ACTIONS = ['DECLARE_WAR', 'OFFER_PEACE', 'OFFER_ALLIANCE', 'ACCEPT_OFFER', 'REJECT_OFFER', 'BREAK_ALLIANCE'] as const;
export type DiploAction = (typeof DIPLO_ACTIONS)[number];

export interface DiploOffer {
  id: number;
  from: NationId;
  to: NationId;
  kind: 'PEACE' | 'ALLIANCE';
  /** Sim time when the offer expires. */
  expires: number;
}

export interface Resources {
  manpower: number;
  industry: number;
  supplies: number;
}

export interface ProductionOrder {
  id: number;
  cityId: number;
  soldiers: number;
  type: ArmyType;
  /** Sim seconds of work required / completed. */
  total: number;
  progress: number;
}

/** Public nation state visible to everyone. */
export interface NationState {
  id: NationId;
  /** Player name, 'AI' or null when the nation is not in play. */
  controller: 'PLAYER' | 'AI' | 'NONE';
  playerName: string | null;
  capitalCity: number | null;
  territories: number;
  soldiers: number;
  armies: number;
  eliminated: boolean;
}

export interface BattleNet {
  id: number;
  x: number;
  y: number;
  radius: number;
  name: string;
  /** Nations involved and their current soldier totals. */
  sides: { nation: NationId; soldiers: number; losses: number }[];
  startedAt: number;
}

export interface CaptureNet {
  territoryId: number;
  nation: NationId;
  /** 0..1 */
  progress: number;
}

export const EVENT_KINDS = [
  'WAR_DECLARED',
  'PEACE_SIGNED',
  'ALLIANCE_FORMED',
  'ALLIANCE_BROKEN',
  'OFFER',
  'OFFER_REJECTED',
  'BATTLE_STARTED',
  'BATTLE_ENDED',
  'TERRITORY_CAPTURED',
  'CAPITAL_ATTACKED',
  'CAPITAL_CAPTURED',
  'ARMY_DESTROYED',
  'ARMY_CREATED',
  'NATION_ELIMINATED',
  'PLAYER_JOINED',
  'PLAYER_LEFT',
  'INFO',
] as const;
export type EventKind = (typeof EVENT_KINDS)[number];

export interface GameEvent {
  id: number;
  time: number;
  kind: EventKind;
  text: string;
  /** Nations this event mainly concerns (used for highlighting). */
  nations: NationId[];
  x?: number;
  y?: number;
  /** Important events are also shown in the middle of the screen. */
  major?: boolean;
}

/** Private state only sent to the controlling player of a nation. */
export interface PrivateState {
  nation: NationId;
  resources: Resources;
  /** Per minute (real-time at 1x) income. */
  income: Resources;
  upkeep: number;
  production: ProductionOrder[];
  offers: DiploOffer[];
}

export interface DiplomacyNet {
  /** key "a|b" with a < b alphabetically. */
  relations: Record<string, DiploState>;
  offers: DiploOffer[];
}

export interface GameInit {
  map: MapData;
  nationIds: NationId[];
  nations: NationState[];
  owners: (NationId | null)[];
  units: UnitNet[];
  battles: BattleNet[];
  captures: CaptureNet[];
  diplomacy: DiplomacyNet;
  events: GameEvent[];
  time: number;
  tick: number;
  speed: GameSpeed;
  paused: boolean;
  you: NationId | null;
  settings: GameSettings;
}

export interface GameDelta {
  tick: number;
  time: number;
  speed: GameSpeed;
  paused: boolean;
  /** New units or units whose orders/identity changed (full records). */
  units: UnitNet[];
  /** Flat [id, soldiers, morale, statusIndex, pathIndex, ...] for units whose combat state changed. */
  stats: number[];
  /** Flat [id, x, y, id, x, y, ...] for units that moved. */
  moves: number[];
  removed: number[];
  /** Flat [territoryId, ownerIndex] where ownerIndex = index in nationIds or -1. */
  owners?: number[];
  battles?: BattleNet[];
  captures?: CaptureNet[];
  nations?: NationState[];
  diplomacy?: DiplomacyNet;
}

export interface GameOverInfo {
  winners: NationId[];
  reason: string;
  stats: { nation: NationId; territories: number; soldiers: number; kills: number; losses: number }[];
}
