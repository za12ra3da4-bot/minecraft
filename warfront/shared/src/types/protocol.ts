import type {
  DiploAction,
  GameDelta,
  GameEvent,
  GameInit,
  GameOverInfo,
  GameSettings,
  GameSpeed,
  PrivateState,
} from './game';
import type { NationId } from './nation';
import type { ChatMessage, RoomInfo } from './room';
import type { ArmyType } from './unit';

/** Commands a client may send to the authoritative server. */
export type GameCommand =
  | { type: 'MOVE_UNIT'; unitIds: number[]; x: number; y: number }
  | { type: 'ATTACK'; unitIds: number[]; targetUnitId: number }
  | { type: 'JOIN_UNIT'; unitIds: number[]; targetUnitId: number }
  | { type: 'MERGE_UNIT'; unitIds: number[] }
  | { type: 'SPLIT_UNIT'; unitId: number; soldiers: number }
  | { type: 'HALT'; unitIds: number[] }
  | { type: 'CREATE_ARMY'; cityId: number; soldiers: number; armyType: ArmyType }
  | { type: 'CANCEL_PRODUCTION'; orderId: number }
  | { type: 'DIPLOMACY'; action: DiploAction; target: NationId; offerId?: number }
  | { type: 'SET_SPEED'; speed: GameSpeed }
  | { type: 'SET_PAUSED'; paused: boolean };

export type GameCommandType = GameCommand['type'];

export type Ack = { ok: true } | { ok: false; error: string };

export type RoomJoinResult =
  | { ok: true; code: string; playerId: string; token: string; room: RoomInfo }
  | { ok: false; error: string };

export interface CreateRoomRequest {
  playerName: string;
  settings: Partial<GameSettings>;
  /** Singleplayer: the room starts immediately with AI opponents. */
  singleplayer?: boolean;
  nation?: NationId;
}

export interface JoinRoomRequest {
  code: string;
  playerName: string;
}

export interface ClientToServerEvents {
  'room:create': (req: CreateRoomRequest, ack: (res: RoomJoinResult) => void) => void;
  'room:join': (req: JoinRoomRequest, ack: (res: RoomJoinResult) => void) => void;
  'room:resume': (token: string, ack: (res: RoomJoinResult) => void) => void;
  'room:leave': () => void;
  'lobby:nation': (nation: NationId | null, ack: (res: Ack) => void) => void;
  'lobby:ready': (ready: boolean) => void;
  'lobby:settings': (settings: Partial<GameSettings>, ack: (res: Ack) => void) => void;
  'lobby:start': (ack: (res: Ack) => void) => void;
  'game:command': (cmd: GameCommand, ack: (res: Ack) => void) => void;
  'game:sync': () => void;
  'chat:send': (text: string, ack: (res: Ack) => void) => void;
}

export interface ServerToClientEvents {
  'room:state': (room: RoomInfo) => void;
  'room:closed': (reason: string) => void;
  'game:init': (init: GameInit) => void;
  'game:delta': (delta: GameDelta) => void;
  'game:private': (state: PrivateState) => void;
  'game:events': (events: GameEvent[]) => void;
  'game:over': (info: GameOverInfo) => void;
  'chat:message': (msg: ChatMessage) => void;
  'chat:history': (msgs: ChatMessage[]) => void;
}
