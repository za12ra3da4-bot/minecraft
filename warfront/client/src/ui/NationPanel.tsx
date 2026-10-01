import { ARMY_TYPE_STATS, formatCompact, formatNumber } from '@warfront/shared';
import type { GameClient } from '../game/GameClient';

function Resource({ icon, label, value, rate }: { icon: string; label: string; value: number; rate: number }) {
  return (
    <div className="resource">
      <span className="icon">{icon}</span>
      <span className="k">{label}</span>
      <span className="v">{formatNumber(value)}</span>
      <span className={`d${rate < 0 ? ' neg' : ''}`}>
        {rate >= 0 ? '+' : ''}
        {formatNumber(rate)} / 분
      </span>
    </div>
  );
}

/** Left panel: the player's nation at a glance. */
export function NationPanel({ game, open }: { game: GameClient; open: boolean }) {
  const p = game.privateState;
  const you = game.you;
  const state = you ? game.replica.nations.get(you) : null;
  const total = game.replica.owners.length;
  return (
    <div className={`hud panel left-panel${open ? '' : ' desktop-only'}`}>
      <div className="panel-title">국고와 군사력</div>
      {p ? (
        <div>
          <Resource icon="⚑" label="인력" value={p.resources.manpower} rate={p.income.manpower} />
          <Resource icon="⚒" label="산업" value={p.resources.industry} rate={p.income.industry} />
          <Resource icon="❖" label="보급" value={p.resources.supplies} rate={p.income.supplies} />
        </div>
      ) : (
        <div className="hint">관전 중입니다.</div>
      )}
      {state && (
        <div className="stat-grid">
          <div className="stat">
            <div className="v">{formatCompact(state.soldiers)}</div>
            <div className="k">총 병력</div>
          </div>
          <div className="stat">
            <div className="v">{state.armies}</div>
            <div className="k">부대 수</div>
          </div>
          <div className="stat">
            <div className="v">{state.territories}</div>
            <div className="k">영토</div>
          </div>
          <div className="stat">
            <div className="v">{Math.round((state.territories / Math.max(1, total)) * 100)}%</div>
            <div className="k">지도 점유</div>
          </div>
        </div>
      )}
      {p && p.production.length > 0 && (
        <>
          <div className="panel-title">생산 중</div>
          {p.production.map((o) => {
            const city = game.replica.map.cities[o.cityId];
            return (
              <div key={o.id} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>
                    {formatNumber(o.soldiers)}명 {ARMY_TYPE_STATS[o.type].label} · {city?.name}
                  </span>
                  <span className="num">{Math.max(0, Math.ceil(o.total - o.progress))}초</span>
                </div>
                <div className="bar">
                  <div style={{ width: `${Math.min(100, (o.progress / o.total) * 100)}%` }} />
                </div>
              </div>
            );
          })}
        </>
      )}
      <div className="hint" style={{ fontSize: 12 }}>
        아래 [군대 만들기] 버튼이나 내 도시(★ ■)를 눌러 군대를 만드세요. 유지비: 분당 보급 {formatNumber(p?.upkeep ?? 0)}
      </div>
    </div>
  );
}
