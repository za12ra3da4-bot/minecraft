import { CHAT, RATE_LIMIT, type NationId, type PlayerInfo } from '@warfront/shared';
import { randomBytes } from 'node:crypto';
import { TokenBucket } from '../network/RateLimiter';

export class RoomPlayer {
  readonly id = randomBytes(6).toString('hex');
  /** Secret used to resume the seat after a reconnect. Never broadcast. */
  readonly token = randomBytes(18).toString('base64url');
  nation: NationId | null = null;
  ready = false;
  socketId: string | null = null;
  disconnectedAt: number | null = null;
  readonly commands = new TokenBucket(RATE_LIMIT.COMMAND_BURST, RATE_LIMIT.COMMANDS_PER_SECOND);
  readonly chat = new TokenBucket(CHAT.BURST, CHAT.BURST / (CHAT.WINDOW_MS / 1000));
  lastChat = '';
  lastChatAt = 0;

  constructor(public name: string) {}

  get connected(): boolean {
    return this.socketId !== null;
  }

  info(hostId: string): PlayerInfo {
    return { id: this.id, name: this.name, nation: this.nation, ready: this.ready, isHost: this.id === hostId, connected: this.connected };
  }
}
