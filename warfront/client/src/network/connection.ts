import type { Ack, ClientToServerEvents, GameCommand, RoomJoinResult, ServerToClientEvents } from '@warfront/shared';
import { io, type Socket } from 'socket.io-client';

export type ClientSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

/**
 * Game server URL. Empty means "same origin" (dev proxy or single-service
 * deployment). Set VITE_SERVER_URL when the client is hosted separately.
 */
const SERVER_URL = (import.meta.env.VITE_SERVER_URL as string | undefined) || undefined;
const SESSION_KEY = 'warfront.session';
const REQUEST_TIMEOUT_MS = 8000;

let socket: ClientSocket | null = null;

export function getSocket(): ClientSocket {
  if (!socket) {
    socket = io(SERVER_URL ?? '', {
      transports: ['websocket', 'polling'],
      reconnectionDelay: 800,
      reconnectionDelayMax: 4000,
    });
  }
  return socket;
}

type AckOf<E extends keyof ClientToServerEvents> = Parameters<ClientToServerEvents[E]> extends [...infer _A, (res: infer R) => void] ? R : never;
type ArgsOf<E extends keyof ClientToServerEvents> = Parameters<ClientToServerEvents[E]> extends [...infer A, (res: never) => void] ? A : never;

/** Emits an event and resolves with the server's acknowledgement. */
export function request<E extends keyof ClientToServerEvents>(event: E, ...args: ArgsOf<E>): Promise<AckOf<E>> {
  const s = getSocket();
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve({ ok: false, error: '서버가 응답하지 않습니다' } as AckOf<E>), REQUEST_TIMEOUT_MS);
    const done = (res: AckOf<E>): void => {
      clearTimeout(timer);
      resolve(res);
    };
    (s.emit as (ev: string, ...rest: unknown[]) => void)(event, ...args, done);
  });
}

export function sendCommand(cmd: GameCommand): Promise<Ack> {
  return request('game:command', cmd);
}

export interface StoredSession {
  token: string;
  code: string;
}

export function saveSession(res: RoomJoinResult): void {
  if (!res.ok) return;
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ token: res.token, code: res.code } satisfies StoredSession));
  } catch {
    /* storage unavailable */
  }
}

export function loadSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}
