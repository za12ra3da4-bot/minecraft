import type { GameDelta, GameEvent, GameOverInfo, GameSettings, NationId, PrivateState } from '@warfront/shared';
import { AIController } from '../ai/AIController';
import { GameState } from './GameState';
import { setupGame, type Participant } from './GameSetup';
import { getGeneratedMap } from './map/MapGenerator';
import { Replicator } from './Replicator';
import { updateBattles } from './systems/BattleSystem';
import { updateCaptures } from './systems/CaptureSystem';
import { expireOffers } from './systems/DiplomacySystem';
import { updateEconomy } from './systems/EconomySystem';
import { updateMovement } from './systems/MovementSystem';
import { updateProduction } from './systems/ProductionSystem';
import { checkVictory } from './systems/VictorySystem';

const MAX_STEP = 0.2;

/** One running match: owns the state, the AI and the replicator. */
export class Game {
  readonly state: GameState;
  readonly replicator: Replicator;
  private ais = new Map<NationId, AIController>();
  private victoryCheckIn = 1;
  result: GameOverInfo | null = null;

  constructor(settings: GameSettings, participants: Participant[], seed: number) {
    const map = getGeneratedMap(settings.mapId);
    this.state = setupGame(map, settings, participants, seed);
    this.replicator = new Replicator(this.state);
    for (const p of participants) if (p.controller === 'AI') this.ais.set(p.nation, new AIController(this.state, p.nation));
  }

  /** Hands a nation to the AI (used when a player disconnects for too long). */
  setAIControl(nation: NationId, enabled: boolean): void {
    const n = this.state.nations.get(nation);
    if (!n) return;
    if (enabled && !this.ais.has(nation)) this.ais.set(nation, new AIController(this.state, nation));
    if (!enabled) this.ais.delete(nation);
    this.state.nationsVersion++;
  }

  /** Advances the simulation by `realDt` seconds of wall-clock time. */
  step(realDt: number): void {
    const s = this.state;
    if (s.over || s.paused) return;
    let remaining = realDt * s.speed;
    while (remaining > 1e-6) {
      const dt = Math.min(MAX_STEP, remaining);
      remaining -= dt;
      s.time += dt;
      expireOffers(s);
      for (const ai of this.ais.values()) ai.update(dt);
      updateProduction(s, dt);
      updateMovement(s, dt);
      updateBattles(s, dt);
      updateCaptures(s, dt);
      updateEconomy(s, dt);
      this.victoryCheckIn -= dt;
      if (this.victoryCheckIn <= 0) {
        this.victoryCheckIn = 1;
        const result = checkVictory(s);
        if (result) {
          s.over = true;
          this.result = result;
          s.emit('INFO', `🏆 ${result.reason}`, result.winners, { major: true });
          break;
        }
      }
    }
    s.tick++;
  }

  delta(): GameDelta {
    return this.replicator.buildDelta();
  }

  privateState(nation: NationId): PrivateState {
    return this.replicator.buildPrivate(nation);
  }

  events(): GameEvent[] {
    return this.state.flushEvents();
  }
}
