import {
  ReplicaState,
  type ChatMessage,
  type ClientToServerEvents,
  type GameEvent,
  type GameOverInfo,
  type PrivateState,
  type RoomInfo,
  type ServerToClientEvents,
} from '@warfront/shared';
import { io, type Socket } from 'socket.io-client';

type AckOf<E extends keyof ClientToServerEvents> = Parameters<ClientToServerEvents[E]> extends [...infer _A, (res: infer R) => void] ? R : never;
type ArgsOf<E extends keyof ClientToServerEvents> = Parameters<ClientToServerEvents[E]> extends [...infer A, (res: never) => void] ? A : never;

/** Headless game client used by integration tests (same sync code as the browser). */
export class TestClient {
  readonly socket: Socket<ServerToClientEvents, ClientToServerEvents>;
  readonly replica = new ReplicaState();
  room: RoomInfo | null = null;
  privateState: PrivateState | null = null;
  events: GameEvent[] = [];
  chat: ChatMessage[] = [];
  over: GameOverInfo | null = null;
  initialised = false;

  constructor(url: string) {
    this.socket = io(url, { transports: ['websocket'], forceNew: true });
    this.socket.on('room:state', (r) => (this.room = r));
    this.socket.on('game:init', (init) => {
      this.replica.applyInit(init);
      this.initialised = true;
    });
    this.socket.on('game:delta', (d) => {
      if (this.initialised) this.replica.applyDelta(d);
    });
    this.socket.on('game:private', (p) => (this.privateState = p));
    this.socket.on('game:events', (e) => this.events.push(...e));
    this.socket.on('chat:message', (m) => this.chat.push(m));
    this.socket.on('game:over', (o) => (this.over = o));
  }

  call<E extends keyof ClientToServerEvents>(event: E, ...args: ArgsOf<E>): Promise<AckOf<E>> {
    return new Promise((resolve) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (this.socket.emit as any)(event, ...args, resolve);
    });
  }

  async waitFor<T>(fn: () => T | undefined | null | false, timeoutMs: number, label: string): Promise<T> {
    const start = Date.now();
    for (;;) {
      const v = fn();
      if (v) return v;
      if (Date.now() - start > timeoutMs) throw new Error(`Timed out waiting for ${label}`);
      await new Promise((r) => setTimeout(r, 50));
    }
  }

  close(): void {
    this.socket.close();
  }
}
