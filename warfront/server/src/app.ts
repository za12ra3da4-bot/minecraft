import type { ClientToServerEvents, ServerToClientEvents } from '@warfront/shared';
import express from 'express';
import { existsSync } from 'node:fs';
import { createServer, type Server as HttpServer } from 'node:http';
import { resolve } from 'node:path';
import { Server } from 'socket.io';
import { registerSocketHandlers } from './network/socketHandlers';
import type { IO, SocketData } from './network/types';
import { RoomManager } from './rooms/RoomManager';

export interface GameServerOptions {
  clientOrigins: string[];
  /** Directories that may contain a built client (first match wins). */
  clientDistCandidates: string[];
}

export interface GameServer {
  httpServer: HttpServer;
  io: IO;
  rooms: RoomManager;
  close(): Promise<void>;
}

/** Creates the HTTP + Socket.IO server. Listening is left to the caller. */
export function createGameServer(options: GameServerOptions): GameServer {
  const app = express();
  app.disable('x-powered-by');
  const httpServer = createServer(app);

  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  const io = new Server<ClientToServerEvents, ServerToClientEvents, {}, SocketData>(httpServer, {
    cors: { origin: options.clientOrigins.length ? options.clientOrigins : true },
    maxHttpBufferSize: 64 * 1024,
    perMessageDeflate: { threshold: 2048 },
    pingInterval: 20_000,
    pingTimeout: 20_000,
  });

  const rooms = new RoomManager(io);
  registerSocketHandlers(io, rooms);
  rooms.start();

  app.get('/health', (_req, res) => {
    res.json({ ok: true, rooms: rooms.roomCount, uptime: Math.round(process.uptime()) });
  });

  // Serve the built client when available so a single service can host everything.
  const clientDist = options.clientDistCandidates.filter(Boolean).find((p) => existsSync(resolve(p, 'index.html')));
  if (clientDist) {
    app.use(express.static(clientDist, { maxAge: '1h', index: false }));
    app.get(/^\/(?!socket\.io|health).*/, (_req, res) => res.sendFile(resolve(clientDist, 'index.html')));
    console.log(`Serving client from ${clientDist}`);
  }

  return {
    httpServer,
    io,
    rooms,
    close: () =>
      new Promise<void>((done) => {
        rooms.stop();
        io.close();
        httpServer.close(() => done());
      }),
  };
}
