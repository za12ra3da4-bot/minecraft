import { GAME_SPEEDS, formatNumber, getNation, toGameClock } from '@warfront/shared';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';

interface Props {
  game: GameClient;
  onDiplomacy: () => void;
  onHelp: () => void;
  onMenu: () => void;
  onToggle: (panel: 'nation' | 'events' | 'chat') => void;
}

export function TopBar({ game, onDiplomacy, onHelp, onMenu, onToggle }: Props) {
  const r = game.replica;
  const clock = toGameClock(r.time);
  const you = game.you;
  const p = game.privateState;
  const offers = p?.offers.filter((o) => o.to === you).length ?? 0;
  const atWar = you ? r.nationIds.filter((n) => n !== you && r.diplomacy.relations[you < n ? `${you}|${n}` : `${n}|${you}`] === 'WAR' && r.nations.get(n)?.controller !== 'NONE').length : 0;
  return (
    <div className="hud panel topbar">
      <button className="btn icon-btn mobile-only" onClick={() => onToggle('nation')} aria-label="나라 정보">
        ☰
      </button>
      <div className="nation">
        {you ? <Flag nation={you} height={26} /> : null}
        <span className="nation-name">{you ? getNation(you).name : '관전자'}</span>
      </div>
      <div className="divider desktop-only" />
      <div className="clock">
        <span className="day">{clock.date}</span>
        <span className="time">
          {String(clock.hour).padStart(2, '0')}:{String(clock.minute).padStart(2, '0')}
        </span>
        <span className="year">
          {clock.year}년 · {clock.day}일차
        </span>
      </div>
      <div className="divider desktop-only" />
      <div className="speed">
        <button
          className={`btn small${r.paused ? ' active' : ''}`}
          disabled={!game.isHost}
          title={game.isHost ? '일시정지 (스페이스바)' : '방장만 속도를 바꿀 수 있습니다'}
          onClick={() => void game.command({ type: 'SET_PAUSED', paused: !r.paused })}
        >
          {r.paused ? '▶' : '❚❚'}
        </button>
        {GAME_SPEEDS.map((s) => (
          <button key={s} className={`btn small desktop-only${r.speed === s && !r.paused ? ' active' : ''}`} disabled={!game.isHost} onClick={() => void game.command({ type: 'SET_SPEED', speed: s })}>
            {s}배
          </button>
        ))}
        <span className="mobile-only num" style={{ padding: '0 4px' }}>
          {r.speed}배
        </span>
      </div>
      <div className="spacer" />
      {p && (
        <div className="res-inline desktop-only">
          <div className="item">
            <span className="v">{formatNumber(p.resources.manpower)}</span>
            <span className="k">인력</span>
          </div>
          <div className="item">
            <span className="v">{formatNumber(p.resources.industry)}</span>
            <span className="k">산업</span>
          </div>
          <div className="item">
            <span className="v" style={{ color: p.resources.supplies < 1000 ? 'var(--red)' : undefined }}>
              {formatNumber(p.resources.supplies)}
            </span>
            <span className="k">보급</span>
          </div>
        </div>
      )}
      <button className={`btn small${offers ? ' active' : ''}`} onClick={onDiplomacy} data-testid="diplomacy">
        🤝 외교{atWar ? ` · ⚔${atWar}` : ''}
        {offers ? ` · ✉${offers}` : ''}
      </button>
      <button className="btn icon-btn mobile-only" onClick={() => onToggle('events')} aria-label="전황">
        ✦
      </button>
      <button className="btn icon-btn mobile-only" onClick={() => onToggle('chat')} aria-label="채팅">
        ✉
      </button>
      <button className="btn small" onClick={onHelp} title="조작 방법">
        ❓ 도움말
      </button>
      <button className="btn small ghost" onClick={onMenu}>
        메뉴
      </button>
    </div>
  );
}
