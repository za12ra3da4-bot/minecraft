import type { GameSettings } from './game';
import type { NationId } from './nation';

export type RoomStatus = 'LOBBY' | 'PLAYING' | 'FINISHED';

export interface PlayerInfo {
  id: string;
  name: string;
  nation: NationId | null;
  ready: boolean;
  isHost: boolean;
  connected: boolean;
}

export interface RoomInfo {
  code: string;
  status: RoomStatus;
  settings: GameSettings;
  players: PlayerInfo[];
  /** Nations available on the selected map. */
  nations: NationId[];
  hostId: string;
}

export interface ChatMessage {
  id: number;
  from: string;
  nation: NationId | null;
  text: string;
  time: number;
  system?: boolean;
}
