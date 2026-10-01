import type { ChatMessage, CreateRoomRequest, RoomInfo, RoomJoinResult } from '@warfront/shared';
import { clearSession, getSocket, loadSession, request, saveSession } from '../network/connection';
import { GameClient } from './GameClient';
import { Store } from './store';

export type Screen = 'menu' | 'create' | 'join' | 'singleplayer' | 'lobby' | 'game' | 'howto' | 'settings';

/** Top level application state: screen routing, room membership and the active game. */
class AppState extends Store {
  screen: Screen = 'menu';
  room: RoomInfo | null = null;
  playerId: string | null = null;
  game: GameClient | null = null;
  lobbyChat: ChatMessage[] = [];
  connected = false;
  everConnected = false;
  error: string | null = null;
  busy = false;
  /** Room code from an invite link (?room=CODE). */
  inviteCode: string | null = null;

  init(): void {
    const params = new URLSearchParams(location.search);
    const invite = params.get('room');
    if (invite) {
      this.inviteCode = invite.toUpperCase();
      this.screen = 'join';
    }
    const socket = getSocket();
    socket.on('connect', () => {
      this.connected = true;
      this.everConnected = true;
      this.notify();
      const session = loadSession();
      if (session) void this.resume(session.token);
    });
    socket.on('disconnect', () => {
      this.connected = false;
      this.notify();
    });
    socket.on('room:state', (room) => {
      this.room = room;
      if (room.status === 'LOBBY' && this.screen !== 'lobby' && this.playerId) this.screen = 'lobby';
      if (this.game) this.game.isHost = room.hostId === this.playerId;
      this.notify();
    });
    socket.on('room:closed', (reason) => this.leaveToMenu(reason));
    socket.on('game:init', (init) => {
      if (this.game) this.game.reinit(init);
      else this.game = new GameClient(init);
      this.game.isHost = this.room?.hostId === this.playerId;
      this.screen = 'game';
      this.notify();
    });
    socket.on('game:delta', (d) => this.game?.applyDelta(d));
    socket.on('game:private', (p) => this.game?.setPrivate(p));
    socket.on('game:events', (e) => this.game?.addEvents(e));
    socket.on('game:over', (o) => this.game?.setOver(o));
    socket.on('chat:message', (m) => {
      if (this.game) this.game.addChat(m);
      else {
        this.lobbyChat = [...this.lobbyChat.slice(-80), m];
        this.notify();
      }
    });
    socket.on('chat:history', (msgs) => {
      if (this.game) this.game.setChatHistory(msgs);
      else {
        this.lobbyChat = msgs;
        this.notify();
      }
    });
  }

  go(screen: Screen): void {
    this.screen = screen;
    this.error = null;
    this.notify();
  }

  private async resume(token: string): Promise<void> {
    const res = await request('room:resume', token);
    if (!res.ok) {
      clearSession();
      if (this.screen === 'lobby' || this.screen === 'game') this.leaveToMenu('Your session expired');
      return;
    }
    this.accept(res);
  }

  private accept(res: RoomJoinResult): void {
    if (!res.ok) return;
    saveSession(res);
    this.playerId = res.playerId;
    this.room = res.room;
    if (res.room.status === 'LOBBY') this.screen = 'lobby';
    this.notify();
  }

  async createRoom(req: CreateRoomRequest): Promise<void> {
    await this.run(() => request('room:create', req));
  }

  async joinRoom(code: string, playerName: string): Promise<void> {
    await this.run(() => request('room:join', { code, playerName }));
  }

  private async run(fn: () => Promise<RoomJoinResult>): Promise<void> {
    this.busy = true;
    this.error = null;
    this.notify();
    const res = await fn();
    this.busy = false;
    if (!res.ok) {
      this.error = res.error;
      this.notify();
      return;
    }
    this.lobbyChat = [];
    this.accept(res);
  }

  leave(): void {
    getSocket().emit('room:leave');
    this.leaveToMenu(null);
  }

  leaveToMenu(reason: string | null): void {
    clearSession();
    this.room = null;
    this.playerId = null;
    this.game = null;
    this.lobbyChat = [];
    this.screen = 'menu';
    this.error = reason;
    if (location.search) history.replaceState(null, '', location.pathname);
    this.notify();
  }

  get isHost(): boolean {
    return !!this.room && this.room.hostId === this.playerId;
  }
}

export const app = new AppState();
