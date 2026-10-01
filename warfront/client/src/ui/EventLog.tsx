import { formatClock } from '@warfront/shared';
import { useState } from 'react';
import type { GameClient } from '../game/GameClient';

const ICON: Record<string, string> = {
  WAR_DECLARED: '⚔',
  BATTLE_STARTED: '⚔',
  BATTLE_ENDED: '⚑',
  TERRITORY_CAPTURED: '⚑',
  CAPITAL_CAPTURED: '★',
  CAPITAL_ATTACKED: '!',
  ARMY_DESTROYED: '✝',
  ARMY_CREATED: '+',
  PEACE_SIGNED: '☮',
  ALLIANCE_FORMED: '🤝',
  NATION_ELIMINATED: '☠',
};

export function EventLog({ game, open }: { game: GameClient; open: boolean }) {
  const [mineOnly, setMineOnly] = useState(false);
  const you = game.you;
  const events = game.events
    .filter((e) => !mineOnly || (you && e.nations.includes(you)))
    .filter((e) => e.kind !== 'ARMY_CREATED' || (you && e.nations.includes(you)))
    .slice(-60)
    .reverse();
  return (
    <div className={`hud panel event-log${open ? ' open' : ''}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div className="panel-title" style={{ flex: 1 }}>
          전황 보고
        </div>
        <button className={`btn small${mineOnly ? ' active' : ''}`} onClick={() => setMineOnly(!mineOnly)}>
          {mineOnly ? '내 나라' : '전체'}
        </button>
      </div>
      <div className="events">
        {events.map((e) => (
          <div
            key={e.id}
            className={`event${you && e.nations.includes(you) ? ' mine' : ''}${e.major ? ' major' : ''}`}
            onClick={() => e.x !== undefined && e.y !== undefined && game.focus(e.x, e.y)}
          >
            <span className="t">{formatClock(e.time)}</span>
            <span>{ICON[e.kind] ?? '·'}</span>
            <span>{e.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
