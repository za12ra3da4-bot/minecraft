import { GAME_SPEEDS, MAPS, VICTORY_CONDITIONS, type GameSettings } from '@warfront/shared';

export const VICTORY_LABELS: Record<GameSettings['victory'], { label: string; about: string }> = {
  CONQUEST: { label: 'Conquest', about: 'Last nation or alliance standing wins' },
  DOMINATION: { label: 'Domination', about: 'Control 60% of all territories' },
  CAPITALS: { label: 'Capitals', about: 'Hold every starting capital' },
};

export const SPEED_OPTIONS = GAME_SPEEDS;
export const VICTORY_OPTIONS = VICTORY_CONDITIONS;
export const MAP_OPTIONS = MAPS;

export function defaultSettings(): GameSettings {
  return { roomName: 'Waterloo', maxPlayers: 10, mapId: 'europe', speed: 1, victory: 'CONQUEST', aiCount: 5, startAtWar: true, isPrivate: false };
}
