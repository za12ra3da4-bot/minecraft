import { RATE_LIMIT, type Ack, type RoomJoinResult } from '@warfront/shared';
import type { Room } from '../rooms/Room';
import type { RoomManager } from '../rooms/RoomManager';
import type { RoomPlayer } from '../rooms/RoomPlayer';
import { TokenBucket } from './RateLimiter';
import type { GameSocket, IO } from './types';

const NOT_IN_ROOM: Ack = { ok: false, error: '방에 없습니다' };

function safeAck<T>(ack: unknown): (res: T) => void {
  return typeof ack === 'function' ? (ack as (res: T) => void) : () => undefined;
}

export function registerSocketHandlers(io: IO, rooms: RoomManager): void {
  io.on('connection', (socket: GameSocket) => {
    socket.data.roomCode = null;
    socket.data.playerId = null;
    const roomActions = new TokenBucket(10, RATE_LIMIT.ROOM_ACTIONS_PER_MINUTE / 60);

    const current = (): { room: Room; player: RoomPlayer } | null => {
      if (!socket.data.roomCode || !socket.data.playerId) return null;
      const room = rooms.get(socket.data.roomCode);
      const player = room?.players.get(socket.data.playerId);
      return room && player ? { room, player } : null;
    };

    const enter = (room: Room, player: RoomPlayer): void => {
      const prev = current();
      if (prev && (prev.room !== room || prev.player !== player)) rooms.leave(prev.room, prev.player.id);
      // A newer socket replaces an older one for the same seat.
      if (player.socketId && player.socketId !== socket.id) io.sockets.sockets.get(player.socketId)?.disconnect(true);
      socket.join(`room:${room.code}`);
      socket.data.roomCode = room.code;
      socket.data.playerId = player.id;
      room.attachSocket(player, socket.id);
      room.broadcastRoom();
      if (room.status === 'LOBBY') room.sendChatHistory(socket.id);
      else room.sendInit(player);
    };

    const joinFlow = (fn: () => { room?: Room; player?: RoomPlayer; res: RoomJoinResult }, ack: (r: RoomJoinResult) => void): void => {
      if (!roomActions.take()) return ack({ ok: false, error: '요청이 너무 많습니다. 잠시 기다리세요' });
      const out = fn();
      if (out.res.ok && out.room && out.player) enter(out.room, out.player);
      ack(out.res);
    };

    socket.on('room:create', (req, ack) => {
      const reply = safeAck<RoomJoinResult>(ack);
      joinFlow(() => {
        const out = rooms.create(req ?? { playerName: '', settings: {} });
        if ('room' in out && req?.singleplayer) {
          // Singleplayer starts immediately once the seat is attached.
          setImmediate(() => {
            if (out.room.status === 'LOBBY' && out.player.nation) {
              out.room.launch();
            }
          });
        }
        return out;
      }, reply);
    });

    socket.on('room:join', (req, ack) => {
      joinFlow(() => rooms.join(req?.code, req?.playerName), safeAck<RoomJoinResult>(ack));
    });

    socket.on('room:resume', (token, ack) => {
      joinFlow(() => rooms.resume(token), safeAck<RoomJoinResult>(ack));
    });

    socket.on('room:leave', () => {
      const c = current();
      if (!c) return;
      socket.leave(`room:${c.room.code}`);
      rooms.leave(c.room, c.player.id);
      socket.data.roomCode = null;
      socket.data.playerId = null;
    });

    socket.on('lobby:nation', (nation, ack) => {
      const c = current();
      safeAck<Ack>(ack)(c ? c.room.selectNation(c.player.id, typeof nation === 'string' ? nation : null) : NOT_IN_ROOM);
    });

    socket.on('lobby:ready', (ready) => {
      const c = current();
      if (c) c.room.setReady(c.player.id, ready === true);
    });

    socket.on('lobby:settings', (settings, ack) => {
      const c = current();
      safeAck<Ack>(ack)(c ? c.room.updateSettings(c.player.id, settings) : NOT_IN_ROOM);
    });

    socket.on('lobby:start', (ack) => {
      const c = current();
      safeAck<Ack>(ack)(c ? c.room.start(c.player.id) : NOT_IN_ROOM);
    });

    socket.on('game:command', (cmd, ack) => {
      const c = current();
      safeAck<Ack>(ack)(c ? c.room.handleCommand(c.player.id, cmd) : NOT_IN_ROOM);
    });

    socket.on('game:sync', () => {
      const c = current();
      if (c && roomActions.take()) c.room.sendInit(c.player);
    });

    socket.on('chat:send', (text, ack) => {
      const c = current();
      safeAck<Ack>(ack)(c ? c.room.chat(c.player.id, text) : NOT_IN_ROOM);
    });

    socket.on('disconnect', () => {
      const c = current();
      if (c && c.player.socketId === socket.id) c.room.detachSocket(c.player);
    });
  });
}
