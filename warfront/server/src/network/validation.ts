import {
  ARMY_TYPES,
  DIPLO_ACTIONS,
  GAME_SPEEDS,
  ROOM,
  UNIT,
  VICTORY_CONDITIONS,
  getMapDef,
  isNationId,
  type ArmyType,
  type DiploAction,
  type GameCommand,
  type GameSettings,
  type GameSpeed,
  type VictoryCondition,
} from '@warfront/shared';

/*
 * Every payload coming from a socket is untrusted. These guards turn unknown
 * JSON into typed values or reject it – nothing is passed through unchecked.
 */

type Obj = Record<string, unknown>;

function isObj(v: unknown): v is Obj {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function isFiniteNumber(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

function isId(v: unknown): v is number {
  return typeof v === 'number' && Number.isInteger(v) && v > 0 && v < 2 ** 31;
}

function idList(v: unknown): number[] | null {
  if (!Array.isArray(v) || v.length === 0 || v.length > UNIT.MAX_COMMAND_UNITS) return null;
  if (!v.every(isId)) return null;
  return [...new Set(v as number[])];
}

export function parseCommand(raw: unknown): GameCommand | null {
  if (!isObj(raw) || typeof raw.type !== 'string') return null;
  switch (raw.type) {
    case 'MOVE_UNIT': {
      const unitIds = idList(raw.unitIds);
      if (!unitIds || !isFiniteNumber(raw.x) || !isFiniteNumber(raw.y)) return null;
      return { type: 'MOVE_UNIT', unitIds, x: raw.x, y: raw.y };
    }
    case 'ATTACK':
    case 'JOIN_UNIT': {
      const unitIds = idList(raw.unitIds);
      if (!unitIds || !isId(raw.targetUnitId)) return null;
      return { type: raw.type, unitIds, targetUnitId: raw.targetUnitId };
    }
    case 'MERGE_UNIT':
    case 'HALT': {
      const unitIds = idList(raw.unitIds);
      if (!unitIds) return null;
      return { type: raw.type, unitIds };
    }
    case 'SPLIT_UNIT': {
      if (!isId(raw.unitId) || !isFiniteNumber(raw.soldiers) || !Number.isInteger(raw.soldiers)) return null;
      return { type: 'SPLIT_UNIT', unitId: raw.unitId, soldiers: raw.soldiers };
    }
    case 'CREATE_ARMY': {
      if (!Number.isInteger(raw.cityId) || (raw.cityId as number) < 0) return null;
      if (!isFiniteNumber(raw.soldiers) || !Number.isInteger(raw.soldiers)) return null;
      if (!ARMY_TYPES.includes(raw.armyType as ArmyType)) return null;
      return { type: 'CREATE_ARMY', cityId: raw.cityId as number, soldiers: raw.soldiers, armyType: raw.armyType as ArmyType };
    }
    case 'CANCEL_PRODUCTION': {
      if (!isId(raw.orderId)) return null;
      return { type: 'CANCEL_PRODUCTION', orderId: raw.orderId };
    }
    case 'DIPLOMACY': {
      if (!DIPLO_ACTIONS.includes(raw.action as DiploAction) || !isNationId(raw.target)) return null;
      if (raw.offerId !== undefined && !isId(raw.offerId)) return null;
      return { type: 'DIPLOMACY', action: raw.action as DiploAction, target: raw.target, offerId: raw.offerId as number | undefined };
    }
    case 'SET_SPEED': {
      if (!GAME_SPEEDS.includes(raw.speed as GameSpeed)) return null;
      return { type: 'SET_SPEED', speed: raw.speed as GameSpeed };
    }
    case 'SET_PAUSED': {
      if (typeof raw.paused !== 'boolean') return null;
      return { type: 'SET_PAUSED', paused: raw.paused };
    }
  }
  return null;
}

// Control characters, zero-width and bidi override characters.
const CONTROL_CHARS = new RegExp('[\\u0000-\\u001f\\u007f\\u200b-\\u200f\\u2028-\\u202e]', 'g');

export function sanitizeText(v: unknown, max: number): string | null {
  if (typeof v !== 'string') return null;
  // Strip control characters and collapse whitespace.
  const cleaned = v.replace(CONTROL_CHARS, '').replace(/\s+/g, ' ').trim();
  if (!cleaned) return null;
  return cleaned.slice(0, max);
}

export function sanitizePlayerName(v: unknown): string {
  return sanitizeText(v, ROOM.PLAYER_NAME_MAX) ?? `Commander${Math.floor(Math.random() * 900 + 100)}`;
}

export const DEFAULT_SETTINGS: GameSettings = {
  roomName: 'Waterloo',
  maxPlayers: 10,
  mapId: 'continental',
  speed: 1,
  victory: 'CONQUEST',
  aiCount: 5,
  startAtWar: true,
  isPrivate: false,
};

/** Merges a partial, untrusted settings object into valid settings. */
export function sanitizeSettings(raw: unknown, base: GameSettings = DEFAULT_SETTINGS): GameSettings {
  const s: GameSettings = { ...base };
  if (!isObj(raw)) return clampSettings(s);
  const name = sanitizeText(raw.roomName, ROOM.NAME_MAX);
  if (name) s.roomName = name;
  if (typeof raw.mapId === 'string' && getMapDef(raw.mapId)) s.mapId = raw.mapId;
  if (Number.isInteger(raw.maxPlayers)) s.maxPlayers = raw.maxPlayers as number;
  if (GAME_SPEEDS.includes(raw.speed as GameSpeed)) s.speed = raw.speed as GameSpeed;
  if (VICTORY_CONDITIONS.includes(raw.victory as VictoryCondition)) s.victory = raw.victory as VictoryCondition;
  if (Number.isInteger(raw.aiCount)) s.aiCount = raw.aiCount as number;
  if (typeof raw.startAtWar === 'boolean') s.startAtWar = raw.startAtWar;
  if (typeof raw.isPrivate === 'boolean') s.isPrivate = raw.isPrivate;
  return clampSettings(s);
}

function clampSettings(s: GameSettings): GameSettings {
  const nations = getMapDef(s.mapId)?.nations.length ?? 2;
  s.maxPlayers = Math.max(1, Math.min(ROOM.MAX_PLAYERS, nations, s.maxPlayers));
  s.aiCount = Math.max(0, Math.min(nations - 1, s.aiCount));
  return s;
}
