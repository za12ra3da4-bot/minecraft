import { GAME_SPEEDS, MAPS, VICTORY_CONDITIONS, type GameSettings } from '@warfront/shared';

export const VICTORY_LABELS: Record<GameSettings['victory'], { label: string; about: string }> = {
  CONQUEST: { label: '정복', about: '마지막까지 살아남은 나라(동맹)가 승리' },
  DOMINATION: { label: '지배', about: '전체 영토의 60%를 차지하면 승리' },
  CAPITALS: { label: '수도', about: '모든 나라의 수도를 차지하면 승리' },
};

export const SPEED_OPTIONS = GAME_SPEEDS;
export const VICTORY_OPTIONS = VICTORY_CONDITIONS;
export const MAP_OPTIONS = MAPS;

export function defaultSettings(): GameSettings {
  return { roomName: '워털루', maxPlayers: 10, mapId: 'europe', speed: 1, victory: 'CONQUEST', aiCount: 5, startAtWar: true, isPrivate: false };
}
