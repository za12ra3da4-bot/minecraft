import type { ClientToServerEvents, ServerToClientEvents } from '@warfront/shared';
import type { Server, Socket } from 'socket.io';

export interface SocketData {
  roomCode: string | null;
  playerId: string | null;
}

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export type IO = Server<ClientToServerEvents, ServerToClientEvents, {}, SocketData>;
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export type GameSocket = Socket<ClientToServerEvents, ServerToClientEvents, {}, SocketData>;
