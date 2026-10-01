import { VICTORY, getNation, type GameOverInfo, type NationId } from '@warfront/shared';
import type { GameState } from '../GameState';

/** Returns game over information once the room's victory condition is met. */
export function checkVictory(state: GameState): GameOverInfo | null {
  const active = state.activeNations();
  if (!active.length) return finish(state, [], '모든 나라가 멸망했습니다');

  const blocOf = (n: NationId): NationId[] => active.filter((o) => state.friendly(n, o.id)).map((o) => o.id);

  // Last nation (or alliance) standing always wins.
  const first = active[0].id;
  if (active.every((n) => state.friendly(first, n.id) && active.every((m) => state.friendly(n.id, m.id)))) {
    const names = active.map((n) => getNation(n.id).name).join(' & ');
    return finish(state, active.map((n) => n.id), `${names} 승리 — 모든 적국을 정복했습니다`);
  }

  if (state.settings.victory === 'DOMINATION') {
    const total = state.owners.length;
    for (const n of active) {
      const owned = state.owners.filter((o) => o === n.id).length;
      if (owned / total >= VICTORY.DOMINATION_SHARE) {
        return finish(state, blocOf(n.id), `${getNation(n.id).name} 승리 — 지도의 ${Math.round((owned / total) * 100)}%를 지배`);
      }
    }
  }

  if (state.settings.victory === 'CAPITALS') {
    const capitals = [...state.nations.values()]
      .filter((n) => n.controller !== 'NONE' && n.originalCapital !== null)
      .map((n) => state.map.data.cities[n.originalCapital!].territoryId);
    for (const n of active) {
      const bloc = blocOf(n.id);
      const held = capitals.filter((t) => {
        const o = state.owners[t];
        return o !== null && bloc.includes(o);
      }).length;
      if (capitals.length > 1 && held === capitals.length) {
        return finish(state, bloc, `${getNation(n.id).name} 승리 — 모든 수도 점령`);
      }
    }
  }
  return null;
}

function finish(state: GameState, winners: NationId[], reason: string): GameOverInfo {
  const stats = [...state.nations.values()]
    .filter((n) => n.controller !== 'NONE')
    .map((n) => ({
      nation: n.id,
      territories: state.owners.filter((o) => o === n.id).length,
      soldiers: Math.round(state.unitsOf(n.id).reduce((s, u) => s + u.soldiers, 0)),
      kills: Math.round(n.kills),
      losses: Math.round(n.losses),
    }))
    .sort((a, b) => b.territories - a.territories);
  return { winners, reason, stats };
}
