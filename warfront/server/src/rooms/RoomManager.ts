import { ROOM, SERVER_TICK_MS, isNationId, type CreateRoomRequest, type RoomJoinResult } from '@warfront/shared';
import { randomInt } from 'node:crypto';
import type { IO } from '../network/types';
import { sanitizePlayerName, sanitizeSettings } from '../network/validation';
import { Room } from './Room';
import type { RoomPlayer } from './RoomPlayer';

/** Owns every room, resolves reconnect tokens and drives the global tick loop. */
export class RoomManager {
  private rooms = new Map<string, Room>();
  private tokens = new Map<string, { code: string; playerId: string }>();
  private timer: NodeJS.Timeout | null = null;
  private lastTick = Date.now();

  constructor(private io: IO) {}

  get roomCount(): number {
    return this.rooms.size;
  }

  start(): void {
    this.lastTick = Date.now();
    this.timer = setInterval(() => this.tick(), SERVER_TICK_MS);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  get(code: string): Room | undefined {
    return this.rooms.get(code.toUpperCase());
  }

  private newCode(): string {
    for (;;) {
      let code = '';
      for (let i = 0; i < ROOM.CODE_LENGTH; i++) code += ROOM.CODE_ALPHABET[randomInt(ROOM.CODE_ALPHABET.length)];
      if (!this.rooms.has(code)) return code;
    }
  }

  private result(room: Room, player: RoomPlayer): RoomJoinResult {
    this.tokens.set(player.token, { code: room.code, playerId: player.id });
    return { ok: true, code: room.code, playerId: player.id, token: player.token, room: room.info() };
  }

  create(req: CreateRoomRequest): { room: Room; player: RoomPlayer; res: RoomJoinResult } | { res: RoomJoinResult } {
    if (this.rooms.size >= ROOM.MAX_ROOMS) return { res: { ok: false, error: 'Server is full, try again later' } };
    const singleplayer = req.singleplayer === true;
    const settings = sanitizeSettings(req?.settings);
    if (singleplayer) {
      settings.isPrivate = true;
      settings.maxPlayers = 1;
    }
    const room = new Room(this.io, this.newCode(), settings);
    this.rooms.set(room.code, room);
    const player = room.addPlayer(sanitizePlayerName(req?.playerName));
    if (typeof player === 'string') return { res: { ok: false, error: player } };
    if (singleplayer && isNationId(req.nation)) room.selectNation(player.id, req.nation);
    return { room, player, res: this.result(room, player) };
  }

  join(codeRaw: unknown, nameRaw: unknown): { room: Room; player: RoomPlayer; res: RoomJoinResult } | { res: RoomJoinResult } {
    const code = typeof codeRaw === 'string' ? codeRaw.trim().toUpperCase() : '';
    const room = this.rooms.get(code);
    if (!room) return { res: { ok: false, error: 'Room not found — check the code' } };
    const player = room.addPlayer(sanitizePlayerName(nameRaw));
    if (typeof player === 'string') return { res: { ok: false, error: player } };
    return { room, player, res: this.result(room, player) };
  }

  resume(token: unknown): { room: Room; player: RoomPlayer; res: RoomJoinResult } | { res: RoomJoinResult } {
    const entry = typeof token === 'string' ? this.tokens.get(token) : undefined;
    const room = entry && this.rooms.get(entry.code);
    const player = entry && room?.players.get(entry.playerId);
    if (!room || !player) return { res: { ok: false, error: 'Session expired' } };
    return { room, player, res: this.result(room, player) };
  }

  leave(room: Room, playerId: string): void {
    const player = room.players.get(playerId);
    if (player) this.tokens.delete(player.token);
    room.removePlayer(playerId, player ? `${player.name} left the room` : undefined);
    room.broadcastRoom();
  }

  private tick(): void {
    const now = Date.now();
    const dt = Math.min(0.5, (now - this.lastTick) / 1000);
    this.lastTick = now;
    for (const room of this.rooms.values()) {
      try {
        room.tick(dt);
      } catch (err) {
        console.error(`[room ${room.code}] tick failed`, err);
      }
      const empty = room.players.size === 0 || (room.emptySince !== null && now - room.emptySince > ROOM.EMPTY_ROOM_TTL_MS);
      const finishedLongAgo = room.status === 'FINISHED' && room.connectedCount() === 0;
      if (empty || finishedLongAgo) this.close(room);
    }
  }

  private close(room: Room): void {
    for (const p of room.players.values()) this.tokens.delete(p.token);
    this.rooms.delete(room.code);
    this.io.to(`room:${room.code}`).emit('room:closed', 'Room closed');
  }
}
