import {
  BROADCAST_EVERY_TICKS,
  CHAT,
  PRIVATE_EVERY_TICKS,
  getMapDef,
  getNation,
  type Ack,
  type ChatMessage,
  type GameSettings,
  type NationId,
  type RoomInfo,
  type RoomStatus,
} from '@warfront/shared';
import { randomInt } from 'node:crypto';
import { executeCommand } from '../game/CommandHandler';
import { Game } from '../game/Game';
import type { Participant } from '../game/GameSetup';
import type { IO } from '../network/types';
import { parseCommand, sanitizeSettings, sanitizeText } from '../network/validation';
import { RoomPlayer } from './RoomPlayer';

/** A disconnected player's nation is handed to the AI after this delay. */
const AI_TAKEOVER_MS = 20_000;
/** Lobby seats of disconnected players are released after this delay (allows page reloads). */
const LOBBY_GRACE_MS = 10_000;

/** A lobby or running match. All game logic is reached through here. */
export class Room {
  status: RoomStatus = 'LOBBY';
  readonly players = new Map<string, RoomPlayer>();
  hostId = '';
  game: Game | null = null;
  private chatLog: ChatMessage[] = [];
  private nextChatId = 1;
  private tickCount = 0;
  emptySince: number | null = null;
  readonly createdAt = Date.now();

  constructor(
    private io: IO,
    readonly code: string,
    public settings: GameSettings,
  ) {}

  private get channel(): string {
    return `room:${this.code}`;
  }

  info(): RoomInfo {
    const def = getMapDef(this.settings.mapId);
    return {
      code: this.code,
      status: this.status,
      settings: this.settings,
      players: [...this.players.values()].map((p) => p.info(this.hostId)),
      nations: def ? def.nations.map((n) => n.nation) : [],
      hostId: this.hostId,
    };
  }

  broadcastRoom(): void {
    this.io.to(this.channel).emit('room:state', this.info());
  }

  connectedCount(): number {
    let n = 0;
    for (const p of this.players.values()) if (p.connected) n++;
    return n;
  }

  // ------------------------------------------------------------- membership

  addPlayer(name: string): RoomPlayer | string {
    if (this.status !== 'LOBBY') return '이미 시작된 게임입니다';
    if (this.players.size >= this.settings.maxPlayers) return '방이 꽉 찼습니다';
    const player = new RoomPlayer(this.uniqueName(name));
    this.players.set(player.id, player);
    if (!this.hostId) this.hostId = player.id;
    this.systemChat(`${player.name}님이 입장했습니다`);
    return player;
  }

  private uniqueName(name: string): string {
    const taken = new Set([...this.players.values()].map((p) => p.name.toLowerCase()));
    if (!taken.has(name.toLowerCase())) return name;
    for (let i = 2; ; i++) if (!taken.has(`${name}${i}`.toLowerCase())) return `${name}${i}`;
  }

  attachSocket(player: RoomPlayer, socketId: string): void {
    player.socketId = socketId;
    player.disconnectedAt = null;
    this.emptySince = null;
    if (this.game && player.nation) {
      const n = this.game.state.nations.get(player.nation);
      if (n && n.controller === 'AI') {
        n.controller = 'PLAYER';
        this.game.setAIControl(player.nation, false);
        this.game.state.emit('PLAYER_JOINED', `${player.name}님이 ${getNation(player.nation).name} 지휘에 복귀했습니다`, [player.nation]);
      }
    }
  }

  detachSocket(player: RoomPlayer): void {
    player.socketId = null;
    player.disconnectedAt = Date.now();
    if (this.connectedCount() === 0) this.emptySince = Date.now();
    this.systemChat(`${player.name}님의 연결이 끊어졌습니다`);
    this.broadcastRoom();
  }

  removePlayer(id: string, message?: string): void {
    const player = this.players.get(id);
    if (!player) return;
    this.players.delete(id);
    if (message) this.systemChat(message);
    if (this.hostId === id) {
      const next = [...this.players.values()].find((p) => p.connected) ?? [...this.players.values()][0];
      this.hostId = next?.id ?? '';
      if (next) this.systemChat(`이제 ${next.name}님이 방장입니다`);
    }
    if (this.game && player.nation) this.handToAI(player.nation, player.name);
  }

  private handToAI(nation: NationId, name: string): void {
    if (!this.game) return;
    const n = this.game.state.nations.get(nation);
    if (!n || n.eliminated || n.controller !== 'PLAYER') return;
    n.controller = 'AI';
    this.game.setAIControl(nation, true);
    this.game.state.emit('PLAYER_LEFT', `${name}님이 나갔습니다 — ${getNation(nation).name}은(는) AI가 지휘합니다`, [nation]);
  }

  // ------------------------------------------------------------- lobby

  selectNation(playerId: string, nation: NationId | null): Ack {
    if (this.status !== 'LOBBY') return { ok: false, error: '이미 시작된 게임입니다' };
    const player = this.players.get(playerId);
    if (!player) return { ok: false, error: '방에 없습니다' };
    if (nation !== null) {
      if (!this.info().nations.includes(nation)) return { ok: false, error: '이 지도에 없는 나라입니다' };
      const taken = [...this.players.values()].some((p) => p.id !== playerId && p.nation === nation);
      if (taken) return { ok: false, error: '이미 선택된 나라입니다' };
    }
    player.nation = nation;
    player.ready = false;
    this.broadcastRoom();
    return { ok: true };
  }

  setReady(playerId: string, ready: boolean): void {
    const player = this.players.get(playerId);
    if (!player || this.status !== 'LOBBY') return;
    player.ready = ready && player.nation !== null;
    this.broadcastRoom();
  }

  updateSettings(playerId: string, raw: unknown): Ack {
    if (playerId !== this.hostId) return { ok: false, error: '방장만 설정을 바꿀 수 있습니다' };
    if (this.status !== 'LOBBY') return { ok: false, error: '이미 시작된 게임입니다' };
    const before = this.settings.mapId;
    const next = sanitizeSettings(raw, this.settings);
    next.maxPlayers = Math.max(next.maxPlayers, this.players.size);
    this.settings = next;
    const nations = this.info().nations;
    for (const p of this.players.values()) {
      if (before !== next.mapId && p.nation && !nations.includes(p.nation)) p.nation = null;
      p.ready = false;
    }
    this.broadcastRoom();
    return { ok: true };
  }

  start(playerId: string): Ack {
    if (playerId !== this.hostId) return { ok: false, error: '방장만 시작할 수 있습니다' };
    if (this.status !== 'LOBBY') return { ok: false, error: '이미 시작된 게임입니다' };
    const players = [...this.players.values()];
    if (players.some((p) => !p.nation)) return { ok: false, error: '모든 플레이어가 나라를 골라야 합니다' };
    if (players.some((p) => p.id !== this.hostId && !p.ready)) return { ok: false, error: '모든 플레이어가 준비 완료해야 합니다' };
    this.launch();
    return { ok: true };
  }

  /** Builds the match and sends every player their init packet. */
  launch(): void {
    const def = getMapDef(this.settings.mapId)!;
    const participants: Participant[] = [];
    for (const p of this.players.values()) {
      participants.push({ nation: p.nation!, controller: 'PLAYER', playerId: p.id, playerName: p.name });
    }
    const free = def.nations.map((n) => n.nation).filter((n) => !participants.some((p) => p.nation === n));
    for (let i = free.length - 1; i > 0; i--) {
      const j = randomInt(i + 1);
      [free[i], free[j]] = [free[j], free[i]];
    }
    for (const nation of free.slice(0, this.settings.aiCount)) {
      participants.push({ nation, controller: 'AI', playerId: null, playerName: null });
    }
    this.game = new Game(this.settings, participants, randomInt(1, 2 ** 31));
    this.status = 'PLAYING';
    this.broadcastRoom();
    for (const p of this.players.values()) this.sendInit(p);
  }

  sendInit(player: RoomPlayer): void {
    if (!this.game || !player.socketId) return;
    const socket = this.io.sockets.sockets.get(player.socketId);
    if (!socket) return;
    socket.emit('game:init', this.game.replicator.buildInit(player.nation));
    if (player.nation) socket.emit('game:private', this.game.privateState(player.nation));
    socket.emit('chat:history', this.chatLog);
    if (this.game.result) socket.emit('game:over', this.game.result);
  }

  // ------------------------------------------------------------- game

  handleCommand(playerId: string, raw: unknown): Ack {
    const player = this.players.get(playerId);
    if (!player) return { ok: false, error: '방에 없습니다' };
    if (!this.game || this.status === 'LOBBY') return { ok: false, error: '게임이 진행 중이 아닙니다' };
    if (!player.commands.take()) return { ok: false, error: '명령이 너무 많습니다 — 잠시 후 다시' };
    const cmd = parseCommand(raw);
    if (!cmd) return { ok: false, error: '잘못된 명령' };
    const state = this.game.state;
    if (cmd.type === 'SET_SPEED' || cmd.type === 'SET_PAUSED') {
      if (playerId !== this.hostId) return { ok: false, error: '방장만 속도를 바꿀 수 있습니다' };
      if (cmd.type === 'SET_SPEED') state.speed = cmd.speed;
      else state.paused = cmd.paused;
      state.emit('INFO', cmd.type === 'SET_SPEED' ? `게임 속도 ${cmd.speed}배` : cmd.paused ? '일시정지' : '게임 재개', []);
      return { ok: true };
    }
    if (!player.nation) return { ok: false, error: '관전 중입니다' };
    return executeCommand(state, player.nation, cmd);
  }

  chat(playerId: string, raw: unknown): Ack {
    const player = this.players.get(playerId);
    if (!player) return { ok: false, error: '방에 없습니다' };
    const text = sanitizeText(raw, CHAT.MAX_LENGTH);
    if (!text) return { ok: false, error: '메시지를 입력하세요' };
    const now = Date.now();
    if (text === player.lastChat && now - player.lastChatAt < 5_000) return { ok: false, error: '같은 메시지를 연속으로 보낼 수 없습니다' };
    if (!player.chat.take()) return { ok: false, error: '메시지를 너무 빨리 보내고 있습니다' };
    player.lastChat = text;
    player.lastChatAt = now;
    this.pushChat({ id: this.nextChatId++, from: player.name, nation: player.nation, text, time: now });
    return { ok: true };
  }

  sendChatHistory(socketId: string): void {
    this.io.to(socketId).emit('chat:history', this.chatLog);
  }

  systemChat(text: string): void {
    this.pushChat({ id: this.nextChatId++, from: 'SYSTEM', nation: null, text, time: Date.now(), system: true });
  }

  private pushChat(msg: ChatMessage): void {
    this.chatLog.push(msg);
    if (this.chatLog.length > CHAT.HISTORY) this.chatLog.shift();
    this.io.to(this.channel).emit('chat:message', msg);
  }

  /** Called by the room manager every server tick. */
  tick(realDt: number): void {
    const now = Date.now();
    for (const p of [...this.players.values()]) {
      if (p.connected || p.disconnectedAt === null) continue;
      const away = now - p.disconnectedAt;
      if (this.status === 'LOBBY' && away > LOBBY_GRACE_MS) {
        this.removePlayer(p.id, `${p.name}님이 나갔습니다`);
        this.broadcastRoom();
      } else if (this.game && p.nation && away > AI_TAKEOVER_MS) {
        this.handToAI(p.nation, p.name);
      }
    }
    if (!this.game || this.status !== 'PLAYING') return;
    const game = this.game;
    game.step(realDt);
    this.tickCount++;

    const events = game.events();
    if (events.length) this.io.to(this.channel).emit('game:events', events);
    if (this.tickCount % BROADCAST_EVERY_TICKS === 0) this.io.to(this.channel).emit('game:delta', game.delta());
    if (this.tickCount % PRIVATE_EVERY_TICKS === 0) {
      for (const p of this.players.values()) {
        if (!p.socketId || !p.nation) continue;
        this.io.to(p.socketId).emit('game:private', game.privateState(p.nation));
      }
    }
    if (game.result) {
      this.io.to(this.channel).emit('game:delta', game.delta());
      this.io.to(this.channel).emit('game:over', game.result);
      this.status = 'FINISHED';
      this.broadcastRoom();
    }
  }
}
